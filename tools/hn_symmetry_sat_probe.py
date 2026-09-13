#!/usr/bin/env python3
"""Fast ordinary 5-colorability probe with sound global color-symmetry breaking.

For any actual triangle (a,b,c), every proper coloring assigns three distinct
colors. A global permutation of the five color names maps those colors to 0,1,2,
so assumptions c(a)=0,c(b)=1,c(c)=2 preserve SAT/UNSAT of the unlabelled coloring
problem. This tool is only for whole-graph 5-colorability; pair-forcing queries use
the unrestricted probe because fixing a triangle consumes color-permutation freedom.
"""
from __future__ import annotations
import argparse, hashlib, json, random
from pathlib import Path
from pysat.solvers import Cadical195, Glucose4
from hn_exact import K2, unit_modulus
from hn_unconditional_scan import color_cnf, valid_coloring, write_json


def find_triangle(n, edges):
    adj=[set() for _ in range(n)]
    for u,v in edges:
        adj[u].add(v); adj[v].add(u)
    for u in range(n):
        for v in adj[u]:
            if v <= u: continue
            common=adj[u] & adj[v]
            if common:
                w=min(common)
                return (u,v,w)
    return None


def extract(model,n):
    pos=set(x for x in model if x>0)
    return [next(c for c in range(5) if v*5+c+1 in pos) for v in range(n)]


def solve(cls,clauses,assumptions,conflicts,phases=None):
    with cls(bootstrap_with=clauses) as s:
        s.conf_budget(conflicts)
        if phases is not None: s.set_phases(phases)
        ans=s.solve_limited(assumptions=assumptions)
        return ans, None if ans is not True else s.get_model()


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--graph',type=Path,required=True)
    ap.add_argument('--out-dir',type=Path,required=True)
    ap.add_argument('--conflicts',type=int,default=2_000_000)
    ap.add_argument('--attempts',type=int,default=6)
    ap.add_argument('--seed',type=int,default=20260914)
    a=ap.parse_args(); a.out_dir.mkdir(parents=True,exist_ok=True)
    raw=a.graph.read_bytes(); d=json.loads(raw)
    pts=[K2(p['a'],p['b'],p['den']) for p in d['pts']]
    edges=sorted({tuple(map(int,e)) for e in d['edges']}); n=len(pts)
    assert len(set(pts))==n and all(unit_modulus(pts[u]-pts[v]) for u,v in edges)
    tri=find_triangle(n,edges)
    if tri is None: raise SystemExit('no triangle for symmetry fixing')
    assumptions=[tri[0]*5+1,tri[1]*5+2,tri[2]*5+3]
    clauses=color_cnf(n,edges); rng=random.Random(a.seed)
    records=[]
    for attempt in range(a.attempts):
        phases=[v*5+rng.randrange(5)+1 for v in range(n)]
        for v,c in zip(tri,(0,1,2)): phases[v]=v*5+c+1
        ans,model=solve(Cadical195,clauses,assumptions,a.conflicts,phases)
        records.append({'attempt':attempt,'cadical195':'SAT' if ans is True else 'UNSAT' if ans is False else 'UNKNOWN'})
        if ans is True:
            colors=extract(model,n); assert valid_coloring(colors,n,edges)
            out={'status':'SAT','classification':'NOT_A','vertices':n,'edges':len(edges),
                 'graph_sha256':hashlib.sha256(raw).hexdigest(),'triangle':list(tri),
                 'symmetry_assumptions_sound':True,'records':records,'colors':colors}
            write_json(a.out_dir/'SYMMETRY_SAT.json',out); print(json.dumps({k:v for k,v in out.items() if k!='colors'},indent=2)); return
        if ans is False:
            g,_=solve(Glucose4,clauses,assumptions,a.conflicts*2)
            records[-1]['glucose4']='UNSAT' if g is False else 'SAT' if g is True else 'UNKNOWN'
            out={'status':'DUAL_UNSAT' if g is False else 'UNCONFIRMED_UNSAT',
                 'classification':'A_CANDIDATE_REQUIRES_CERTIFICATE' if g is False else 'C',
                 'vertices':n,'edges':len(edges),'graph_sha256':hashlib.sha256(raw).hexdigest(),
                 'triangle':list(tri),'symmetry_assumptions_sound':True,'records':records}
            write_json(a.out_dir/'SYMMETRY_SAT.json',out); print(json.dumps(out,indent=2)); return
    out={'status':'UNKNOWN','classification':'C','vertices':n,'edges':len(edges),
         'graph_sha256':hashlib.sha256(raw).hexdigest(),'triangle':list(tri),
         'symmetry_assumptions_sound':True,'records':records}
    write_json(a.out_dir/'SYMMETRY_SAT.json',out); print(json.dumps(out,indent=2))

if __name__=='__main__': main()
