#!/usr/bin/env python3
"""Unbudgeted whole-graph 5-color SAT solve with sound triangle color symmetry.

SAT returns a full coloring validated on every supplied exact edge. UNSAT is the
solver's completed result; use multiple independent solvers/certificates before a
final mathematical claim.

With --neq-pair u,v, the geometric graph is left unchanged and five CNF clauses
require u and v to have different colors. SAT then gives a validated separating
coloring; UNSAT makes that distinct pair a forced-equal B candidate requiring
independent confirmation.
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

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--graph',type=Path,required=True); ap.add_argument('--out-dir',type=Path,required=True); ap.add_argument('--solver',choices=sorted(SOLVERS),required=True)
    ap.add_argument('--neq-pair',default=None,help='optional distinct vertex pair u,v required to have different colors')
    ap.add_argument('--seed-coloring',type=Path,default=None,help='optional validated proper coloring used only as solver phase hints')
    a=ap.parse_args(); a.out_dir.mkdir(parents=True,exist_ok=True)
    raw=a.graph.read_bytes(); d=json.loads(raw); pts=[K2(p['a'],p['b'],p['den']) for p in d['pts']]; edges=sorted({tuple(map(int,e)) for e in d['edges']}); n=len(pts)
    assert len(set(pts))==n and all(unit_modulus(pts[u]-pts[v]) for u,v in edges)
    tri=find_triangle(n,edges); assert tri is not None; assumptions=[tri[0]*5+1,tri[1]*5+2,tri[2]*5+3]; clauses=color_cnf(n,edges)
    pair=None
    if a.neq_pair is not None:
        u,v=map(int,a.neq_pair.split(',')); u,v=sorted((u,v)); assert 0<=u<v<n and (u,v) not in set(edges); pair=[u,v]
        for c in range(5): clauses.append([-(u*5+c+1),-(v*5+c+1)])
    seed=None
    if a.seed_coloring is not None:
        seed=load_seed(a.seed_coloring,n); assert valid_coloring(seed,n,edges)
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
