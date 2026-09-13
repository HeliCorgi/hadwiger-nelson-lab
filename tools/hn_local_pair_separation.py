#!/usr/bin/env python3
"""Targeted local-repair separation of residual same-color vertex pairs.

Input is an exact unit-distance graph plus at least one validated proper 5-coloring.
For a residual pair (u,v) that is same-colored in every retained witness, we exploit
only global color-name symmetry: if any unequal coloring exists, one exists with
u fixed to its current color and v fixed to one chosen different color. We then
run a TabuCol-style repair with those two vertices frozen.

A successful repair is a rigorous separation witness after full-edge validation.
Failure/timeout is explicitly non-evidence and never establishes forced equality.
After complete separation, the witness family is greedily compressed while retaining
unique color signatures for every vertex.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
import random
import time
from pathlib import Path

from hn_exact import K2, unit_modulus
from hn_unconditional_scan import valid_coloring, write_json


def refine(blocks, colors):
    out=[]
    for block in blocks:
        buckets=defaultdict(list)
        for v in block:
            buckets[colors[v]].append(v)
        out.extend(buckets.values())
    return out


def pairs_left(blocks):
    return sum(len(b)*(len(b)-1)//2 for b in blocks)


def greedy_compress(witnesses, n):
    """Retain a small subfamily that still separates every vertex pair."""
    blocks=[list(range(n))]
    remaining=list(range(len(witnesses)))
    chosen=[]
    while pairs_left(blocks):
        best_i=None; best_blocks=None; best_pairs=pairs_left(blocks)
        for i in remaining:
            candidate=refine(blocks,witnesses[i])
            p=pairs_left(candidate)
            if p<best_pairs:
                best_i=i; best_blocks=candidate; best_pairs=p
                if p==0: break
        if best_i is None:
            raise AssertionError('full witness family separates all pairs but greedy compression stalled')
        chosen.append(best_i); remaining.remove(best_i); blocks=best_blocks
    compact=[witnesses[i] for i in chosen]
    assert not pairs_left(blocks)
    return compact,chosen


def constrained_repair(base, edges, adj, u, v, seed, seconds, iterations, perturb):
    """Try to repair base after forcing u/v unequal. Failure has no meaning."""
    n=len(base); k=5; rng=random.Random(seed); deadline=time.monotonic()+seconds
    cu=base[u]; cv=(cu+1)%k
    fixed={u:cu,v:cv}
    best_seen=len(edges)

    for restart in range(4):
        if time.monotonic()>=deadline: break
        colors=list(base)
        colors[u]=cu; colors[v]=cv
        if restart:
            pool=[x for x in range(n) if x not in fixed]
            for x in rng.sample(pool,min(len(pool),perturb*(restart+1))):
                colors[x]=rng.randrange(k)
        for x,c in fixed.items(): colors[x]=c

        counts=[[0]*k for _ in range(n)]
        for x in range(n):
            for w in adj[x]: counts[x][colors[w]]+=1
        conflicts=sum(1 for a,b in edges if colors[a]==colors[b])
        tabu=[[0]*k for _ in range(n)]
        local_best=conflicts

        for it in range(iterations):
            if conflicts==0:
                assert colors[u]!=colors[v]
                assert valid_coloring(colors,n,edges)
                return list(colors),{'restart':restart,'iterations':it,'best_conflicts':0}
            if (it & 1023)==0 and time.monotonic()>=deadline: break
            bad=[x for x in range(n) if x not in fixed and counts[x][colors[x]]>0]
            if not bad: break
            sample=bad if len(bad)<=48 else rng.sample(bad,48)
            move=None; key_best=None
            for x in sample:
                old=colors[x]; oldc=counts[x][old]
                for c in range(k):
                    if c==old: continue
                    delta=counts[x][c]-oldc
                    new_conf=conflicts+delta
                    if it<tabu[x][c] and new_conf>=local_best: continue
                    key=(delta,counts[x][c],rng.random())
                    if key_best is None or key<key_best:
                        key_best=key; move=(x,c,old,new_conf)
            if move is None:
                x=rng.choice(bad); old=colors[x]
                c=rng.choice([z for z in range(k) if z!=old])
                move=(x,c,old,conflicts+counts[x][c]-counts[x][old])
            x,c,old,new_conf=move
            colors[x]=c; conflicts=new_conf
            for w in adj[x]:
                counts[w][old]-=1; counts[w][c]+=1
            tabu[x][old]=it+5+rng.randrange(8)+int(0.6*conflicts)
            if conflicts<local_best: local_best=conflicts
            if conflicts<best_seen: best_seen=conflicts
            if it and it%120000==0 and conflicts:
                mutable=[z for z in bad if z not in fixed]
                for z in rng.sample(mutable,min(len(mutable),max(1,perturb//4))):
                    oldz=colors[z]; cz=rng.randrange(k)
                    if cz==oldz: continue
                    conflicts += counts[z][cz]-counts[z][oldz]
                    colors[z]=cz
                    for w in adj[z]: counts[w][oldz]-=1; counts[w][cz]+=1
    return None,{'best_conflicts':best_seen}


def load_coloring(path, n):
    s=path.read_text().strip()
    if len(s)==n and all(ch in '01234' for ch in s): return [int(ch) for ch in s]
    d=json.loads(path.read_text())
    if isinstance(d,dict):
        for key in ('colors','coloring'):
            if key in d: return list(map(int,d[key]))
    raise ValueError(f'no coloring in {path}')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--graph',type=Path,required=True)
    ap.add_argument('--seed-coloring',type=Path,required=True)
    ap.add_argument('--out-dir',type=Path,required=True)
    ap.add_argument('--seconds',type=float,default=1500)
    ap.add_argument('--pair-seconds',type=float,default=20)
    ap.add_argument('--iterations',type=int,default=400000)
    ap.add_argument('--perturb',type=int,default=24)
    ap.add_argument('--max-failures',type=int,default=12)
    ap.add_argument('--seed',type=int,default=20260914)
    a=ap.parse_args(); a.out_dir.mkdir(parents=True,exist_ok=True)

    d=json.loads(a.graph.read_text())
    pts=[K2(p['a'],p['b'],p['den']) for p in d['pts']]
    edges=sorted({tuple(map(int,e)) for e in d['edges']}); n=len(pts)
    assert len(set(pts))==n and all(unit_modulus(pts[u]-pts[v]) for u,v in edges)
    adj=[[] for _ in range(n)]
    for u,v in edges: adj[u].append(v); adj[v].append(u)

    initial=load_coloring(a.seed_coloring,n)
    assert valid_coloring(initial,n,edges)
    witnesses=[initial]
    blocks=refine([list(range(n))],initial)
    records=[]; failures=[]; started=time.monotonic(); rng=random.Random(a.seed)
    compact_count=None; compact_indices=None

    def save(status, models=None):
        saved_models=witnesses if models is None else models
        payload={
            'status':status,
            'classification':'D' if status=='NO_FORCED_EQUAL_PAIR' else None,
            'vertices':n,'edges':len(edges),'generated_witness_count':len(witnesses),
            'saved_witness_count':len(saved_models),
            'compressed_witness_count':compact_count,
            'compressed_source_indices':compact_indices,
            'remaining_pairs':pairs_left(blocks),
            'remaining_blocks':[b for b in blocks if len(b)>1],
            'records':records,'failures':failures,
            'timeout_or_repair_failure_is_evidence':False,
            'all_witnesses_validated_on_all_edges':True,
            'elapsed_seconds':round(time.monotonic()-started,3),
        }
        write_json(a.out_dir/'SEPARATION.json',payload)
        write_json(a.out_dir/'WITNESSES.json',{'models':saved_models})
        return payload

    save('ACTIVE')
    while pairs_left(blocks) and time.monotonic()-started<a.seconds:
        candidates=sorted((b for b in blocks if len(b)>1), key=len, reverse=True)
        progressed=False
        for block in candidates[:min(12,len(candidates))]:
            if time.monotonic()-started>=a.seconds: break
            u=block[0]; v=block[-1]; base=witnesses[-1]
            assert all(c[u]==c[v] for c in witnesses)
            color,meta=constrained_repair(base,edges,adj,u,v,rng.randrange(1<<62),
                                          min(a.pair_seconds,max(0.1,a.seconds-(time.monotonic()-started))),
                                          a.iterations,a.perturb)
            if color is None:
                failures.append({'pair':[u,v],**meta})
                if len(failures)>=a.max_failures:
                    out=save('RESIDUAL_UNKNOWN')
                    print(json.dumps({k:v for k,v in out.items() if k not in ('remaining_blocks','records')},indent=2)); return
                continue
            assert color[u]!=color[v] and valid_coloring(color,n,edges)
            before=pairs_left(blocks); new=refine(blocks,color); after=pairs_left(new)
            assert after<before
            blocks=new; witnesses.append(color)
            rec={'target':[u,v],'before':before,'after':after,
                 'max_block':max(map(len,blocks)),'repair':meta}
            records.append(rec)
            print(json.dumps(rec),flush=True)
            progressed=True
            break
        if not progressed and failures: break

    status='NO_FORCED_EQUAL_PAIR' if not pairs_left(blocks) else 'RESIDUAL_UNKNOWN'
    if status=='NO_FORCED_EQUAL_PAIR':
        compact,indices=greedy_compress(witnesses,n)
        assert all(valid_coloring(c,n,edges) for c in compact)
        compact_count=len(compact); compact_indices=indices
        out=save(status,compact)
    else:
        out=save(status)
    print(json.dumps({k:v for k,v in out.items() if k not in ('remaining_blocks','records')},indent=2))

if __name__=='__main__': main()
