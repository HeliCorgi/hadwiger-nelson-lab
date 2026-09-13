#!/usr/bin/env python3
"""Validated TabuCol-style proper 5-coloring witness search.

Success is rigorous after validating the returned coloring on every supplied exact
edge. Failure/timeout is explicitly non-evidence and is never labelled UNSAT.
"""
from __future__ import annotations
import argparse, json, random, time
from pathlib import Path
from hn_exact import K2, unit_modulus
from hn_unconditional_scan import valid_coloring, write_json


def tabu_search(n, edges, k, seed, restarts, iterations, seconds):
    adj=[[] for _ in range(n)]
    for u,v in edges:
        adj[u].append(v); adj[v].append(u)
    rng=random.Random(seed); deadline=time.monotonic()+seconds
    best_global=len(edges); records=[]

    # degree-biased greedy start followed by random perturbation on later restarts
    order=sorted(range(n),key=lambda v:len(adj[v]),reverse=True)
    for restart in range(restarts):
        if time.monotonic()>=deadline: break
        colors=[-1]*n
        for v in order:
            counts=[0]*k
            for w in adj[v]:
                if colors[w]>=0: counts[colors[w]]+=1
            m=min(counts); choices=[c for c,x in enumerate(counts) if x==m]
            colors[v]=rng.choice(choices)
        if restart:
            for v in rng.sample(range(n), min(n, max(10,n//20))): colors[v]=rng.randrange(k)

        neigh_counts=[[0]*k for _ in range(n)]
        for v in range(n):
            for w in adj[v]: neigh_counts[v][colors[w]]+=1
        conflicts=sum(1 for u,v in edges if colors[u]==colors[v])
        tabu_until=[[0]*k for _ in range(n)]
        best=conflicts

        for it in range(iterations):
            if conflicts==0:
                assert valid_coloring(colors,n,edges)
                records.append({'restart':restart,'iterations':it,'best_conflicts':0})
                return list(colors),records
            if (it & 1023)==0 and time.monotonic()>=deadline: break
            bad=[v for v in range(n) if neigh_counts[v][colors[v]]>0]
            if not bad: break
            # Sample several conflicted vertices; select the best admissible move.
            sample=bad if len(bad)<=32 else rng.sample(bad,32)
            best_move=None
            best_key=None
            for v in sample:
                old=colors[v]; oldc=neigh_counts[v][old]
                for c in range(k):
                    if c==old: continue
                    delta=neigh_counts[v][c]-oldc
                    new_conf=conflicts+delta
                    admissible=(it>=tabu_until[v][c]) or (new_conf<best)
                    if not admissible: continue
                    key=(delta,neigh_counts[v][c],rng.random())
                    if best_key is None or key<best_key:
                        best_key=key; best_move=(v,c,old,new_conf)
            if best_move is None:
                v=rng.choice(bad); old=colors[v]; c=rng.choice([x for x in range(k) if x!=old])
                best_move=(v,c,old,conflicts+neigh_counts[v][c]-neigh_counts[v][old])
            v,c,old,new_conf=best_move
            colors[v]=c; conflicts=new_conf
            for w in adj[v]:
                neigh_counts[w][old]-=1; neigh_counts[w][c]+=1
            tenure=5+rng.randrange(8)+int(0.6*conflicts)
            tabu_until[v][old]=it+tenure
            if conflicts<best:
                best=conflicts
                if best<best_global:
                    best_global=best
                    print(json.dumps({'restart':restart,'iteration':it,'best_conflicts':best_global}),flush=True)
            # diversification if stuck near a plateau
            if it and it%100000==0 and conflicts>0:
                for v2 in rng.sample(bad,min(len(bad),max(1,n//200))):
                    old2=colors[v2]; c2=rng.randrange(k)
                    if c2==old2: continue
                    conflicts += neigh_counts[v2][c2]-neigh_counts[v2][old2]
                    colors[v2]=c2
                    for w in adj[v2]: neigh_counts[w][old2]-=1; neigh_counts[w][c2]+=1
        records.append({'restart':restart,'best_conflicts':best})
    return None,records


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--graph',type=Path,required=True)
    ap.add_argument('--out-dir',type=Path,required=True)
    ap.add_argument('--colors',type=int,default=5)
    ap.add_argument('--seconds',type=float,default=600)
    ap.add_argument('--restarts',type=int,default=12)
    ap.add_argument('--iterations',type=int,default=1000000)
    ap.add_argument('--seed',type=int,default=20260914)
    a=ap.parse_args(); a.out_dir.mkdir(parents=True,exist_ok=True)
    d=json.loads(a.graph.read_text()); pts=[K2(p['a'],p['b'],p['den']) for p in d['pts']]
    edges=sorted({tuple(map(int,e)) for e in d['edges']}); n=len(pts)
    assert len(set(pts))==n and all(unit_modulus(pts[u]-pts[v]) for u,v in edges)
    colors,records=tabu_search(n,edges,a.colors,a.seed,a.restarts,a.iterations,a.seconds)
    if colors is None:
        out={'status':'NO_WITNESS_WITHIN_BUDGET','classification':None,'vertices':n,'edges':len(edges),
             'heuristic_failure_is_evidence':False,'records':records}
    else:
        assert valid_coloring(colors,n,edges)
        out={'status':'VALIDATED_PROPER_5_COLORING','classification':'NOT_A','vertices':n,'edges':len(edges),
             'all_edges_validated':True,'colors':colors,'records':records}
        (a.out_dir/'COLORING.txt').write_text(''.join(map(str,colors))+'\n')
    write_json(a.out_dir/'TABUCOL.json',out)
    print(json.dumps({k:v for k,v in out.items() if k!='colors'},indent=2))

if __name__=='__main__': main()
