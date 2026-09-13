#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, time
from pathlib import Path
from pysat.solvers import Solver

GRAPH_SHA='632ab11f24bf084221db31fec8e1eda522a18eba8d95dbd3bddf9cbcae1fe49d'

def cnf5(n,edges):
    clauses=[]
    for v in range(n):
        xs=[v*5+c+1 for c in range(5)]; clauses.append(xs)
        for a in range(5):
            for b in range(a+1,5): clauses.append([-xs[a],-xs[b]])
    for u,v in edges:
        for c in range(5): clauses.append([-(u*5+c+1),-(v*5+c+1)])
    return clauses

def model_colors(model,n):
    p=set(x for x in model if x>0)
    return [next(c for c in range(5) if v*5+c+1 in p) for v in range(n)]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--graph',type=Path,required=True); ap.add_argument('--pair',nargs=2,type=int,required=True); ap.add_argument('--third',type=int); ap.add_argument('--solver',required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    assert hashlib.sha256(a.graph.read_bytes()).hexdigest()==GRAPH_SHA
    G=json.loads(a.graph.read_text()); n=len(G['pts']); edges=[tuple(e) for e in G['edges']]; assert n==9115 and len(edges)==81068
    u,v=a.pair; clauses=cnf5(n,edges)
    # WLOG for an unequal coloring: map c(u),c(v) to 0,1.
    clauses += [[u*5+1],[v*5+2]]
    if a.third is not None:
        w=a.third
        # Caller must choose w adjacent to both u and v. Then w cannot use 0/1,
        # so the residual permutation symmetry among colors 2/3/4 permits c(w)=2 WLOG.
        E={tuple(sorted(e)) for e in edges}; assert tuple(sorted((u,w))) in E and tuple(sorted((v,w))) in E
        clauses += [[w*5+3]]
    t=time.time()
    with Solver(name=a.solver,bootstrap_with=clauses) as s:
        ans=s.solve(); model=s.get_model() if ans else None
    out={'solver':a.solver,'pair':[u,v],'third':a.third,'result':'SAT' if ans else 'UNSAT','seconds':round(time.time()-t,3),'graph_sha256':GRAPH_SHA}
    if ans:
        c=model_colors(model,n); assert c[u]!=c[v] and all(c[x]!=c[y] for x,y in edges)
        out['proper_5_coloring_verified']=True; out['colors']=c
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(out,separators=(',',':')))
    print(json.dumps({k:v for k,v in out.items() if k!='colors'},indent=2),flush=True)
if __name__=='__main__':main()
