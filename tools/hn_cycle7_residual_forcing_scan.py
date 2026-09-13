#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, random, time
from pathlib import Path
from pysat.solvers import Cadical195, Glucose4

GRAPH_SHA='632ab11f24bf084221db31fec8e1eda522a18eba8d95dbd3bddf9cbcae1fe49d'

def color_cnf(n, edges):
    clauses=[]
    for v in range(n):
        xs=[v*5+c+1 for c in range(5)]
        clauses.append(xs)
        for a in range(5):
            for b in range(a+1,5): clauses.append([-xs[a],-xs[b]])
    for u,v in edges:
        for c in range(5): clauses.append([-(u*5+c+1),-(v*5+c+1)])
    return clauses

def colors_from_model(model,n):
    pos=set(x for x in model if x>0)
    return [next(c for c in range(5) if v*5+c+1 in pos) for v in range(n)]

def valid(c,n,edges):
    return len(c)==n and all(0<=x<5 for x in c) and all(c[u]!=c[v] for u,v in edges)

def refine(blocks,c):
    out=[]
    for b in blocks:
        if len(b)<=1:
            out.append(b); continue
        buckets=[[] for _ in range(5)]
        for v in b: buckets[c[v]].append(v)
        out.extend(x for x in buckets if x)
    return out

def pairs_left(blocks):
    return sum(len(b)*(len(b)-1)//2 for b in blocks)

def save(out,status,n,edges,blocks,witnesses,records,candidate=None):
    data={
        'status':status,
        'classification':'B_CANDIDATE' if status=='DUAL_UNSAT_PAIR' else ('D_RESIDUAL_CLOSED' if pairs_left(blocks)==0 else None),
        'graph_sha256':GRAPH_SHA,'vertices':n,'edges':len(edges),
        'remaining_pairs':pairs_left(blocks),
        'remaining_blocks':[b for b in blocks if len(b)>1],
        'new_sat_witness_count':len(witnesses),'progress':records,
        'candidate':candidate,
        'no_conditional_constraints':True,
        'note':'Initial residual blocks came from 406 locally validated proper colorings; this run searches only pairs still unresolved by that family.'
    }
    out.write_text(json.dumps(data,indent=2))
    if witnesses:
        (out.parent/'SAT_WITNESSES.json').write_text(json.dumps({'models':witnesses},separators=(',',':')))
    return data

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--graph',type=Path,required=True)
    ap.add_argument('--coloring',type=Path,required=True)
    ap.add_argument('--blocks',type=Path,required=True)
    ap.add_argument('--out-dir',type=Path,required=True)
    ap.add_argument('--seconds',type=float,default=5400)
    ap.add_argument('--conflicts',type=int,default=2000000)
    args=ap.parse_args(); args.out_dir.mkdir(parents=True,exist_ok=True)
    out=args.out_dir/'SCAN.json'
    assert hashlib.sha256(args.graph.read_bytes()).hexdigest()==GRAPH_SHA
    G=json.loads(args.graph.read_text()); n=len(G['pts']); edges=[tuple(e) for e in G['edges']]
    assert n==9115 and len(edges)==81068
    initial=list(map(int,args.coloring.read_text().strip()))
    assert valid(initial,n,edges)
    R=json.loads(args.blocks.read_text()); assert R['graph_sha256']==GRAPH_SHA
    blocks=[list(map(int,b)) for b in R['remaining_blocks']]
    assert pairs_left(blocks)==R['remaining_pairs']==13877
    clauses=color_cnf(n,edges)
    witnesses=[]; records=[]; rng=random.Random(20260913); started=time.monotonic()
    with Cadical195(bootstrap_with=clauses) as solver:
        while pairs_left(blocks) and time.monotonic()-started<args.seconds:
            block=max((b for b in blocks if len(b)>1), key=len)
            u,v=block[0],block[1]
            # If any unequal coloring exists, a global color permutation maps c(u),c(v) to 0,1.
            assumptions=[u*5+1,v*5+2]
            ans=None
            for attempt,budget in enumerate((args.conflicts,args.conflicts*4)):
                solver.conf_budget(budget)
                phase=[x*5+rng.randrange(5)+1 for x in range(n)]
                phase[u]=u*5+1; phase[v]=v*5+2
                solver.set_phases(phase)
                ans=solver.solve_limited(assumptions=assumptions)
                if ans is not None: break
            if ans is None:
                candidate={'pair':[u,v],'cadical195':'UNKNOWN','reason':'conflict budgets exhausted'}
                save(out,'UNKNOWN',n,edges,blocks,witnesses,records,candidate)
                print(json.dumps(candidate,indent=2),flush=True); return
            if ans is False:
                # Cross-check the same WLOG inequality with a second solver before surfacing a B candidate.
                with Glucose4(bootstrap_with=clauses) as gs:
                    gs.conf_budget(args.conflicts*4)
                    g=gs.solve_limited(assumptions=assumptions)
                candidate={'pair':[u,v],'cadical195':'UNSAT','glucose4':'UNSAT' if g is False else ('SAT' if g is True else 'UNKNOWN')}
                if g is False:
                    # Exact distinctness at the coordinate-representation level; identical packed points would be byte-identical dicts.
                    candidate['distinct_exact_points']=G['pts'][u]!=G['pts'][v]
                    save(out,'DUAL_UNSAT_PAIR',n,edges,blocks,witnesses,records,candidate)
                else:
                    save(out,'SOLVER_DISAGREEMENT_OR_UNKNOWN',n,edges,blocks,witnesses,records,candidate)
                print(json.dumps(candidate,indent=2),flush=True); return
            c=colors_from_model(solver.get_model(),n)
            assert c[u]!=c[v] and valid(c,n,edges)
            before=pairs_left(blocks); blocks=refine(blocks,c); after=pairs_left(blocks)
            assert after<before
            witnesses.append(c)
            records.append({'target':[u,v],'before':before,'after':after,'max_block':max(map(len,blocks))})
            save(out,'ACTIVE',n,edges,blocks,witnesses,records)
            print(json.dumps(records[-1]),flush=True)
    status='D_RESIDUAL_CLOSED' if not pairs_left(blocks) else 'TIME_LIMIT'
    data=save(out,status,n,edges,blocks,witnesses,records)
    print(json.dumps({k:v for k,v in data.items() if k not in ('remaining_blocks','progress')},indent=2),flush=True)

if __name__=='__main__': main()
