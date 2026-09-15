#!/usr/bin/env python3
"""Incremental-conflict TabuCol from a supplied seed.

This is the same heuristic role as hn_seeded_tabucol, but maintains the set of
currently conflicting vertices incrementally instead of rescanning every vertex
on every iteration. Any returned proper coloring is independently validated on
every saved exact edge. The best near-coloring is also checkpointed for rigorous
follow-up, but a nonzero conflict count is never evidence.
"""
from __future__ import annotations
import argparse,json,random,time
from pathlib import Path
from hn_exact import K2,unit_modulus
from hn_seeded_tabucol import load_seed
from hn_unconditional_scan import valid_coloring,write_json


def search(seed,edges,k,rng_seed,restarts,iterations,seconds,perturb):
    n=len(seed); adj=[[] for _ in range(n)]
    for u,v in edges: adj[u].append(v);adj[v].append(u)
    rng=random.Random(rng_seed); deadline=time.monotonic()+seconds; records=[]
    best_global=len(edges)+1;best_global_colors=None
    for restart in range(restarts):
        if time.monotonic()>=deadline: break
        colors=list(seed)
        if restart:
            pool=list(range(n));rng.shuffle(pool)
            for v in pool[:min(n,perturb*restart)]: colors[v]=rng.randrange(k)
        counts=[[0]*k for _ in range(n)]
        for v in range(n):
            for w in adj[v]: counts[v][colors[w]]+=1
        conflicts=sum(1 for u,v in edges if colors[u]==colors[v]);start_conf=conflicts
        bad={v for v in range(n) if counts[v][colors[v]]>0}
        tabu=[[0]*k for _ in range(n)];best=conflicts
        if conflicts<best_global:
            best_global=conflicts;best_global_colors=list(colors)
            print(json.dumps({'restart':restart,'iteration':0,'best_conflicts':best_global}),flush=True)
        for it in range(iterations):
            if conflicts==0:
                assert not bad and valid_coloring(colors,n,edges)
                records.append({'restart':restart,'start_conflicts':start_conf,'iterations':it,'best_conflicts':0})
                return list(colors),records,list(colors),0
            if (it&4095)==0 and time.monotonic()>=deadline: break
            if not bad: raise AssertionError('zero bad set with nonzero conflict count')
            if len(bad)<=48: sample=list(bad)
            else: sample=rng.sample(tuple(bad),48)
            move=None;best_key=None
            for v in sample:
                old=colors[v];oldc=counts[v][old]
                for c in range(k):
                    if c==old: continue
                    delta=counts[v][c]-oldc;new=conflicts+delta
                    if it<tabu[v][c] and new>=best: continue
                    key=(delta,counts[v][c],rng.random())
                    if best_key is None or key<best_key:best_key=key;move=(v,c,old,new)
            if move is None:
                v=rng.choice(tuple(bad));old=colors[v];c=rng.choice([x for x in range(k) if x!=old]);move=(v,c,old,conflicts+counts[v][c]-counts[v][old])
            v,c,old,new=move;colors[v]=c;conflicts=new
            for w in adj[v]:
                counts[w][old]-=1;counts[w][c]+=1
                if counts[w][colors[w]]>0:bad.add(w)
                else:bad.discard(w)
            if counts[v][colors[v]]>0:bad.add(v)
            else:bad.discard(v)
            tabu[v][old]=it+5+rng.randrange(8)+int(.6*conflicts)
            if conflicts<best:
                best=conflicts
                if best<best_global:
                    best_global=best;best_global_colors=list(colors)
                    print(json.dumps({'restart':restart,'iteration':it,'best_conflicts':best_global}),flush=True)
            if it and it%120000==0 and conflicts:
                perturb_vs=rng.sample(tuple(bad),min(len(bad),max(1,perturb//3)))
                for v in perturb_vs:
                    old=colors[v];c=rng.randrange(k)
                    if c==old:continue
                    conflicts+=counts[v][c]-counts[v][old];colors[v]=c
                    for w in adj[v]:
                        counts[w][old]-=1;counts[w][c]+=1
                        if counts[w][colors[w]]>0:bad.add(w)
                        else:bad.discard(w)
                    if counts[v][colors[v]]>0:bad.add(v)
                    else:bad.discard(v)
        records.append({'restart':restart,'start_conflicts':start_conf,'best_conflicts':best})
    return None,records,best_global_colors,best_global


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--graph',type=Path,required=True);ap.add_argument('--seed-coloring',type=Path,required=True);ap.add_argument('--out-dir',type=Path,required=True)
    ap.add_argument('--colors',type=int,default=5);ap.add_argument('--seconds',type=float,default=3600);ap.add_argument('--restarts',type=int,default=40);ap.add_argument('--iterations',type=int,default=12000000);ap.add_argument('--perturb',type=int,default=90);ap.add_argument('--seed',type=int,default=20260915)
    a=ap.parse_args();a.out_dir.mkdir(parents=True,exist_ok=True)
    d=json.loads(a.graph.read_text());pts=[K2(p['a'],p['b'],p['den']) for p in d['pts']];edges=sorted({tuple(map(int,e)) for e in d['edges']});n=len(pts)
    assert len(set(pts))==n and all(unit_modulus(pts[u]-pts[v]) for u,v in edges)
    seed=load_seed(a.seed_coloring,n);start=sum(seed[u]==seed[v] for u,v in edges)
    color,records,best_near,best_conflicts=search(seed,edges,a.colors,a.seed,a.restarts,a.iterations,a.seconds,a.perturb)
    if color is None:
        assert best_near is not None
        check=sum(best_near[u]==best_near[v] for u,v in edges);assert check==best_conflicts and check>0
        (a.out_dir/'BEST_NEAR_COLORING.txt').write_text(''.join(map(str,best_near))+'\n')
        out={'status':'NO_WITNESS_WITHIN_BUDGET','classification':None,'vertices':n,'edges':len(edges),'seed_conflicts':start,
             'best_global_conflicts':best_conflicts,'best_near_coloring_saved':True,
             'heuristic_failure_is_evidence':False,'records':records}
    else:
        assert valid_coloring(color,n,edges)
        out={'status':'VALIDATED_PROPER_5_COLORING','classification':'NOT_A','vertices':n,'edges':len(edges),'seed_conflicts':start,
             'best_global_conflicts':0,'all_edges_validated':True,'colors':color,'records':records}
        (a.out_dir/'COLORING.txt').write_text(''.join(map(str,color))+'\n')
    write_json(a.out_dir/'FAST_TABUCOL.json',out);print(json.dumps({k:v for k,v in out.items() if k!='colors'},indent=2))

if __name__=='__main__':main()
