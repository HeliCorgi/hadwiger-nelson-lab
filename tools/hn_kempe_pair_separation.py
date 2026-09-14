#!/usr/bin/env python3
"""Separate vertex pairs using only rigorously valid Kempe swaps.

Given one proper 5-coloring, for any two colors a,b the subgraph induced by
vertices of colors a or b decomposes into connected components. Swapping a<->b
on any one component preserves properness. We greedily add only swaps that refine
the current vertex-signature partition. Newly accepted colorings are themselves
used as bases for further Kempe swaps.

If signatures become unique, the saved coloring family is a direct certificate
that no distinct vertex pair is forced equal in every proper 5-coloring. Stalling
is non-evidence for forced equality because Kempe-equivalent colorings are only a
subset of all colorings.
"""
from __future__ import annotations

import argparse,json,time
from collections import deque
from pathlib import Path

from hn_exact import K2,unit_modulus
from hn_unconditional_scan import valid_coloring,write_json
from hn_local_pair_separation import load_coloring,refine,pairs_left,greedy_compress


def bichromatic_components(colors,adj,a,b):
    allowed={v for v,c in enumerate(colors) if c==a or c==b}
    comps=[]
    while allowed:
        s=allowed.pop(); comp=[s]; stack=[s]
        while stack:
            v=stack.pop()
            nxt=[w for w in adj[v] if w in allowed and (colors[w]==a or colors[w]==b)]
            for w in nxt: allowed.remove(w); stack.append(w); comp.append(w)
        comps.append(comp)
    return comps


def swapped(colors,comp,a,b):
    c=list(colors)
    for v in comp:
        if c[v]==a: c[v]=b
        elif c[v]==b: c[v]=a
        else: raise AssertionError
    return c


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--graph',type=Path,required=True); ap.add_argument('--seed-coloring',type=Path,required=True)
    ap.add_argument('--out-dir',type=Path,required=True); ap.add_argument('--max-models',type=int,default=600)
    ap.add_argument('--max-bases',type=int,default=300); ap.add_argument('--seconds',type=float,default=1800)
    a=ap.parse_args(); a.out_dir.mkdir(parents=True,exist_ok=True)
    d=json.loads(a.graph.read_text()); pts=[K2(p['a'],p['b'],p['den']) for p in d['pts']]
    edges=sorted({tuple(map(int,e)) for e in d['edges']}); n=len(pts)
    assert len(set(pts))==n and all(unit_modulus(pts[u]-pts[v]) for u,v in edges)
    adj=[set() for _ in range(n)]
    for u,v in edges: adj[u].add(v); adj[v].add(u)
    seed=load_coloring(a.seed_coloring,n); assert valid_coloring(seed,n,edges)
    witnesses=[seed]; blocks=refine([list(range(n))],seed); initial=pairs_left(blocks)
    queue=deque([0]); seen={bytes(seed)}; records=[]; started=time.monotonic(); bases=0
    while queue and pairs_left(blocks) and len(witnesses)<a.max_models and bases<a.max_bases and time.monotonic()-started<a.seconds:
        bi=queue.popleft(); base=witnesses[bi]; bases+=1
        for ca in range(5):
            for cb in range(ca+1,5):
                comps=bichromatic_components(base,adj,ca,cb)
                # Small components first often give more localized signature splits.
                comps.sort(key=len)
                for comp in comps:
                    if len(witnesses)>=a.max_models or not pairs_left(blocks): break
                    c=swapped(base,comp,ca,cb); key=bytes(c)
                    if key in seen: continue
                    seen.add(key)
                    before=pairs_left(blocks); new=refine(blocks,c); after=pairs_left(new)
                    if after>=before: continue
                    assert valid_coloring(c,n,edges)
                    witnesses.append(c); queue.append(len(witnesses)-1); blocks=new
                    rec={'base_index':bi,'colors':[ca,cb],'component_size':len(comp),'before':before,'after':after,
                         'max_block':max(map(len,blocks)),'models':len(witnesses)}
                    records.append(rec)
                    if len(records)<=20 or len(records)%25==0 or after==0: print(json.dumps(rec),flush=True)
    status='NO_FORCED_EQUAL_PAIR' if pairs_left(blocks)==0 else 'KEMPE_RESIDUAL_UNKNOWN'
    compact=None; indices=None
    if status=='NO_FORCED_EQUAL_PAIR':
        compact,indices=greedy_compress(witnesses,n)
        assert all(valid_coloring(c,n,edges) for c in compact)
        sig=[tuple(c[v] for c in compact) for v in range(n)]; assert len(set(sig))==n
        saved=compact
    else: saved=witnesses
    out={'status':status,'classification':'D' if status=='NO_FORCED_EQUAL_PAIR' else None,
         'vertices':n,'edges':len(edges),'initial_remaining_pairs':initial,'generated_witness_count':len(witnesses),
         'saved_witness_count':len(saved),'compressed_witness_count':len(compact) if compact is not None else None,
         'compressed_source_indices':indices,'remaining_pairs':pairs_left(blocks),
         'remaining_blocks':[b for b in blocks if len(b)>1], 'bases_processed':bases,'records':records,
         'all_witnesses_validated_on_all_edges':True,'kempe_stall_is_evidence':False,
         'elapsed_seconds':round(time.monotonic()-started,3)}
    write_json(a.out_dir/'SEPARATION.json',out); write_json(a.out_dir/'WITNESSES.json',{'models':saved})
    print(json.dumps({k:v for k,v in out.items() if k not in ('remaining_blocks','records','compressed_source_indices')},indent=2))

if __name__=='__main__': main()
