#!/usr/bin/env python3
"""Validated TabuCol search from a supplied near-coloring seed.

Success is evidence only after validating every exact graph edge. Failure or timeout
has no evidentiary meaning.
"""
from __future__ import annotations
import argparse,json,random,time
from pathlib import Path
from hn_exact import K2,unit_modulus
from hn_unconditional_scan import valid_coloring,write_json


def load_seed(path,n):
    s=path.read_text().strip()
    if len(s)==n and all(ch in '01234' for ch in s): return [int(ch) for ch in s]
    d=json.loads(path.read_text())
    for k in ('colors','coloring'):
        if isinstance(d,dict) and k in d:
            c=list(map(int,d[k])); assert len(c)==n; return c
    raise ValueError('no coloring seed')


def search(seed,edges,k,rng_seed,restarts,iterations,seconds,perturb):
    n=len(seed); adj=[[] for _ in range(n)]
    for u,v in edges: adj[u].append(v); adj[v].append(u)
    rng=random.Random(rng_seed); deadline=time.monotonic()+seconds; records=[]; best_global=len(edges)
    for restart in range(restarts):
        if time.monotonic()>=deadline: break
        colors=list(seed)
        if restart:
            pool=list(range(n)); rng.shuffle(pool)
            for v in pool[:min(n,perturb*restart)]: colors[v]=rng.randrange(k)
        counts=[[0]*k for _ in range(n)]
        for v in range(n):
            for w in adj[v]: counts[v][colors[w]]+=1
        conflicts=sum(1 for u,v in edges if colors[u]==colors[v]); start_conf=conflicts
        tabu=[[0]*k for _ in range(n)]; best=conflicts
        if conflicts<best_global:
            best_global=conflicts; print(json.dumps({'restart':restart,'iteration':0,'best_conflicts':best_global}),flush=True)
        for it in range(iterations):
            if conflicts==0:
                assert valid_coloring(colors,n,edges)
                records.append({'restart':restart,'start_conflicts':start_conf,'iterations':it,'best_conflicts':0})
                return list(colors),records
            if (it&1023)==0 and time.monotonic()>=deadline: break
            bad=[v for v in range(n) if counts[v][colors[v]]>0]
            if not bad: break
            sample=bad if len(bad)<=48 else rng.sample(bad,48)
            move=None; best_key=None
            for v in sample:
                old=colors[v]; oldc=counts[v][old]
                for c in range(k):
                    if c==old: continue
                    delta=counts[v][c]-oldc; new=conflicts+delta
                    if it<tabu[v][c] and new>=best: continue
                    key=(delta,counts[v][c],rng.random())
                    if best_key is None or key<best_key: best_key=key; move=(v,c,old,new)
            if move is None:
                v=rng.choice(bad); old=colors[v]; c=rng.choice([x for x in range(k) if x!=old]); move=(v,c,old,conflicts+counts[v][c]-counts[v][old])
            v,c,old,new=move; colors[v]=c; conflicts=new
            for w in adj[v]: counts[w][old]-=1; counts[w][c]+=1
            tabu[v][old]=it+5+rng.randrange(8)+int(.6*conflicts)
            if conflicts<best:
                best=conflicts
                if best<best_global:
                    best_global=best; print(json.dumps({'restart':restart,'iteration':it,'best_conflicts':best_global}),flush=True)
            if it and it%120000==0 and conflicts:
                bad=[v for v in range(n) if counts[v][colors[v]]>0]
                for v in rng.sample(bad,min(len(bad),max(1,perturb//3))):
                    old=colors[v]; c=rng.randrange(k)
                    if c==old: continue
                    conflicts += counts[v][c]-counts[v][old]; colors[v]=c
                    for w in adj[v]: counts[w][old]-=1; counts[w][c]+=1
        records.append({'restart':restart,'start_conflicts':start_conf,'best_conflicts':best})
    return None,records


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--graph',type=Path,required=True); ap.add_argument('--seed-coloring',type=Path,required=True); ap.add_argument('--out-dir',type=Path,required=True)
    ap.add_argument('--colors',type=int,default=5); ap.add_argument('--seconds',type=float,default=1200); ap.add_argument('--restarts',type=int,default=20); ap.add_argument('--iterations',type=int,default=1800000); ap.add_argument('--perturb',type=int,default=50); ap.add_argument('--seed',type=int,default=20260914)
    a=ap.parse_args(); a.out_dir.mkdir(parents=True,exist_ok=True)
    d=json.loads(a.graph.read_text()); pts=[K2(p['a'],p['b'],p['den']) for p in d['pts']]; edges=sorted({tuple(map(int,e)) for e in d['edges']}); n=len(pts)
    assert len(set(pts))==n and all(unit_modulus(pts[u]-pts[v]) for u,v in edges)
    seed=load_seed(a.seed_coloring,n); assert all(0<=x<a.colors for x in seed)
    start=sum(1 for u,v in edges if seed[u]==seed[v]); colors,records=search(seed,edges,a.colors,a.seed,a.restarts,a.iterations,a.seconds,a.perturb)
    if colors is None:
        out={'status':'NO_WITNESS_WITHIN_BUDGET','classification':None,'vertices':n,'edges':len(edges),'seed_conflicts':start,'heuristic_failure_is_evidence':False,'records':records}
    else:
        assert valid_coloring(colors,n,edges); out={'status':'VALIDATED_PROPER_5_COLORING','classification':'NOT_A','vertices':n,'edges':len(edges),'seed_conflicts':start,'all_edges_validated':True,'colors':colors,'records':records}; (a.out_dir/'COLORING.txt').write_text(''.join(map(str,colors))+'\n')
    write_json(a.out_dir/'SEEDED_TABUCOL.json',out); print(json.dumps({k:v for k,v in out.items() if k!='colors'},indent=2))

if __name__=='__main__': main()
