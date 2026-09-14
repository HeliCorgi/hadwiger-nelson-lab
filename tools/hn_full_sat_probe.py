#!/usr/bin/env python3
"""Unbudgeted whole-graph 5-color SAT solve with sound triangle color symmetry.

SAT returns a full coloring validated on every supplied exact edge. UNSAT is the
solver's completed result; use multiple independent solvers/certificates before a
final mathematical claim.

With --neq-pair u,v, the geometric graph is left unchanged and five CNF clauses
require u and v to have different colors. SAT then gives a validated separating
coloring; UNSAT makes that distinct pair a forced-equal B candidate requiring
independent confirmation.

With --witnesses and --iterate-pairs N, repeatedly target the largest remaining
same-signature block. Each temporary pair inequality is guarded by a fresh selector
literal and activated only by an assumption, so previous pair tests do not alter the
base coloring problem. Every SAT model is validated on all exact graph edges before
it is retained.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from pysat.solvers import Cadical195,Glucose4
from hn_exact import K2,unit_modulus
from hn_unconditional_scan import color_cnf,valid_coloring,write_json
from hn_symmetry_sat_probe import find_triangle,extract

SOLVERS={'cadical195':Cadical195,'glucose4':Glucose4}

def load_seed(path,n):
    s=path.read_text().strip()
    if len(s)==n and all(ch in '01234' for ch in s): return [int(ch) for ch in s]
    d=json.loads(path.read_text())
    for k in ('colors','coloring'):
        if isinstance(d,dict) and k in d:
            c=list(map(int,d[k])); assert len(c)==n; return c
    raise ValueError('no coloring seed')

def load_models(path,n,edges):
    d=json.loads(path.read_text()); ms=[list(map(int,c)) for c in d['models']]
    assert ms and all(len(c)==n and valid_coloring(c,n,edges) for c in ms)
    return ms

def signature_blocks(models,n):
    groups={}
    for v in range(n): groups.setdefault(tuple(c[v] for c in models),[]).append(v)
    blocks=[b for b in groups.values() if len(b)>1]
    blocks.sort(key=lambda b:(-len(b),b[0],b[-1]))
    pairs=sum(len(b)*(len(b)-1)//2 for b in blocks)
    return blocks,pairs,len(groups)

def run_iterative(a,raw,n,edges,tri,clauses,seed):
    models=load_models(a.witnesses,n,edges)
    initial_count=len(models); blocks,pairs,distinct=signature_blocks(models,n)
    initial_pairs=pairs; records=[]; base_vars=n*5
    cls=SOLVERS[a.solver]
    status='ITERATION_LIMIT'; candidate=None
    with cls(bootstrap_with=clauses) as s:
        for i in range(a.iterate_pairs):
            blocks,pairs,distinct=signature_blocks(models,n)
            if not blocks:
                status='NO_FORCED_EQUAL_PAIR'; break
            block=blocks[0]; u,v=block[0],block[-1]
            selector=base_vars+i+1
            for c in range(5): s.add_clause([-selector,-(u*5+c+1),-(v*5+c+1)])
            phase=models[-1] if models else seed
            if phase is not None and hasattr(s,'set_phases'):
                s.set_phases([x*5+int(phase[x])+1 for x in range(n)])
            ans=s.solve(assumptions=[tri[0]*5+1,tri[1]*5+2,tri[2]*5+3,selector])
            if ans is False:
                status='UNSAT_PAIR_FORCED_EQUAL_CANDIDATE'; candidate=[u,v]
                records.append({'iteration':i,'pair':[u,v],'before_pairs':pairs,'block_size':len(block),'status':'UNSAT'})
                break
            if ans is not True:
                status='UNKNOWN'; records.append({'iteration':i,'pair':[u,v],'before_pairs':pairs,'block_size':len(block),'status':'UNKNOWN'}); break
            colors=extract(s.get_model(),n); assert valid_coloring(colors,n,edges) and colors[u]!=colors[v]
            before=pairs; models.append(colors); new_blocks,after,_=signature_blocks(models,n); assert after<before
            rec={'iteration':i,'pair':[u,v],'before_pairs':before,'after_pairs':after,'block_size':len(block),'max_block_after':len(new_blocks[0]) if new_blocks else 1,'status':'SAT'}
            records.append(rec); print(json.dumps(rec),flush=True)
        else:
            blocks,pairs,distinct=signature_blocks(models,n)
    blocks,pairs,distinct=signature_blocks(models,n)
    out={'status':status,'classification':'D' if status=='NO_FORCED_EQUAL_PAIR' else ('B_CANDIDATE_REQUIRES_INDEPENDENT_CONFIRMATION' if status=='UNSAT_PAIR_FORCED_EQUAL_CANDIDATE' else None),'solver':a.solver,'vertices':n,'edges':len(edges),'graph_sha256':hashlib.sha256(raw).hexdigest(),'triangle':list(tri),'symmetry_assumptions_sound':True,'initial_model_count':initial_count,'generated_model_count':len(models),'initial_remaining_pairs':initial_pairs,'remaining_pairs':pairs,'distinct_signatures':distinct,'remaining_block_count':len(blocks),'max_remaining_block':len(blocks[0]) if blocks else 1,'candidate_pair':candidate,'records':records,'all_retained_models_validated_on_all_edges':True,'timeout_or_unknown_is_evidence':False}
    write_json(a.out_dir/'ITERATIVE_PAIR_SAT.json',out)
    write_json(a.out_dir/'ITERATIVE_WITNESSES.json',{'models':models})
    print(json.dumps({k:v for k,v in out.items() if k!='records'},indent=2))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--graph',type=Path,required=True); ap.add_argument('--out-dir',type=Path,required=True); ap.add_argument('--solver',choices=sorted(SOLVERS),required=True)
    ap.add_argument('--neq-pair',default=None,help='optional distinct vertex pair u,v required to have different colors')
    ap.add_argument('--seed-coloring',type=Path,default=None,help='optional validated proper coloring used only as solver phase hints')
    ap.add_argument('--witnesses',type=Path,default=None,help='validated model family for incremental pair separation')
    ap.add_argument('--iterate-pairs',type=int,default=0,help='number of largest-block exact pair tests to run incrementally')
    a=ap.parse_args(); a.out_dir.mkdir(parents=True,exist_ok=True)
    raw=a.graph.read_bytes(); d=json.loads(raw); pts=[K2(p['a'],p['b'],p['den']) for p in d['pts']]; edges=sorted({tuple(map(int,e)) for e in d['edges']}); n=len(pts)
    assert len(set(pts))==n and all(unit_modulus(pts[u]-pts[v]) for u,v in edges)
    tri=find_triangle(n,edges); assert tri is not None; assumptions=[tri[0]*5+1,tri[1]*5+2,tri[2]*5+3]; clauses=color_cnf(n,edges)
    seed=None
    if a.seed_coloring is not None:
        seed=load_seed(a.seed_coloring,n); assert valid_coloring(seed,n,edges)
    if a.iterate_pairs:
        assert a.witnesses is not None and a.neq_pair is None
        run_iterative(a,raw,n,edges,tri,clauses,seed); return
    pair=None
    if a.neq_pair is not None:
        u,v=map(int,a.neq_pair.split(',')); u,v=sorted((u,v)); assert 0<=u<v<n and (u,v) not in set(edges); pair=[u,v]
        for c in range(5): clauses.append([-(u*5+c+1),-(v*5+c+1)])
    cls=SOLVERS[a.solver]
    with cls(bootstrap_with=clauses) as s:
        if seed is not None and hasattr(s,'set_phases'):
            s.set_phases([v*5+seed[v]+1 for v in range(n)])
        ans=s.solve(assumptions=assumptions); model=s.get_model() if ans else None
    if ans:
        colors=extract(model,n); assert valid_coloring(colors,n,edges)
        if pair is not None: assert colors[pair[0]]!=colors[pair[1]]
        out={'status':'SAT','classification':'NOT_A' if pair is None else 'NOT_FORCED_EQUAL','solver':a.solver,'vertices':n,'edges':len(edges),'graph_sha256':hashlib.sha256(raw).hexdigest(),'triangle':list(tri),'symmetry_assumptions_sound':True,'all_edges_validated':True,'colors':colors}
        if pair is not None: out.update({'pair':pair,'pair_colors':[colors[pair[0]],colors[pair[1]]],'pair_inequality_validated':True})
        (a.out_dir/'COLORING.txt').write_text(''.join(map(str,colors))+'\n')
    else:
        out={'status':'UNSAT','classification':'A_CANDIDATE_REQUIRES_CERTIFICATE' if pair is None else 'B_CANDIDATE_REQUIRES_INDEPENDENT_CONFIRMATION','solver':a.solver,'vertices':n,'edges':len(edges),'graph_sha256':hashlib.sha256(raw).hexdigest(),'triangle':list(tri),'symmetry_assumptions_sound':True}
        if pair is not None: out.update({'pair':pair,'distinct_pair':True,'positive_distance_follows_from_distinct_exact_points':True})
    write_json(a.out_dir/'FULL_SAT.json',out); print(json.dumps({k:v for k,v in out.items() if k!='colors'},indent=2))

if __name__=='__main__': main()
