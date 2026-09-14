#!/usr/bin/env python3
"""Efficient pair separation by bit-coded Kempe-component swaps.

For colors a,b, every connected component of the bichromatic induced subgraph may
be swapped independently. Instead of saving one coloring per component, assign the
components binary IDs and, for each bit, simultaneously swap all components whose
ID has that bit set. O(log C) validated colorings then encode C component classes.
Accepted colorings are recycled as bases for additional rounds.
"""
from __future__ import annotations
import argparse,json,time,random
from collections import deque
from pathlib import Path
from hn_exact import K2,unit_modulus
from hn_unconditional_scan import valid_coloring,write_json
from hn_local_pair_separation import load_coloring,refine,pairs_left,greedy_compress


def components(colors,adj,a,b):
    allowed={v for v,c in enumerate(colors) if c in (a,b)}; out=[]
    while allowed:
        s=allowed.pop(); comp=[s]; stack=[s]
        while stack:
            v=stack.pop()
            for w in list(adj[v] & allowed):
                allowed.remove(w); stack.append(w); comp.append(w)
        out.append(comp)
    out.sort(key=lambda x:(len(x),x[0]))
    return out


def coded_swap(base,comps,a,b,bit):
    c=list(base)
    for idx,comp in enumerate(comps):
        if (idx>>bit)&1:
            for v in comp: c[v]=b if c[v]==a else a
    return c


def random_swap(base,comps,a,b,rng):
    c=list(base); changed=False
    for comp in comps:
        if rng.getrandbits(1):
            changed=True
            for v in comp: c[v]=b if c[v]==a else a
    return c if changed else None


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--graph',type=Path,required=True); ap.add_argument('--seed-coloring',type=Path,required=True)
    ap.add_argument('--out-dir',type=Path,required=True); ap.add_argument('--max-models',type=int,default=500)
    ap.add_argument('--max-bases',type=int,default=80); ap.add_argument('--random-subsets',type=int,default=2)
    ap.add_argument('--seconds',type=float,default=1800); ap.add_argument('--seed',type=int,default=20260914)
    a=ap.parse_args(); a.out_dir.mkdir(parents=True,exist_ok=True)
    d=json.loads(a.graph.read_text()); pts=[K2(p['a'],p['b'],p['den']) for p in d['pts']]; edges=sorted({tuple(map(int,e)) for e in d['edges']}); n=len(pts)
    assert len(set(pts))==n and all(unit_modulus(pts[u]-pts[v]) for u,v in edges)
    adj=[set() for _ in range(n)]
    for u,v in edges: adj[u].add(v); adj[v].add(u)
    seed=load_coloring(a.seed_coloring,n); assert valid_coloring(seed,n,edges)
    witnesses=[seed]; blocks=refine([list(range(n))],seed); initial=pairs_left(blocks); seen={bytes(seed)}; queue=deque([0]); rng=random.Random(a.seed)
    records=[]; started=time.monotonic(); bases=0
    def consider(c,meta):
        nonlocal blocks
        if c is None: return False
        key=bytes(c)
        if key in seen: return False
        seen.add(key); before=pairs_left(blocks); new=refine(blocks,c); after=pairs_left(new)
        if after>=before: return False
        assert valid_coloring(c,n,edges)
        witnesses.append(c); queue.append(len(witnesses)-1); blocks=new
        rec={**meta,'before':before,'after':after,'max_block':max(map(len,blocks)),'models':len(witnesses)}; records.append(rec)
        if len(records)<=20 or len(records)%20==0 or after==0: print(json.dumps(rec),flush=True)
        return True
    while queue and pairs_left(blocks) and len(witnesses)<a.max_models and bases<a.max_bases and time.monotonic()-started<a.seconds:
        bi=queue.popleft(); base=witnesses[bi]; bases+=1
        for ca in range(5):
            for cb in range(ca+1,5):
                comps=components(base,adj,ca,cb); bits=(len(comps)-1).bit_length()
                for bit in range(bits):
                    if len(witnesses)>=a.max_models or not pairs_left(blocks): break
                    consider(coded_swap(base,comps,ca,cb,bit),{'base_index':bi,'colors':[ca,cb],'kind':'bit','components':len(comps),'bit':bit})
                for ri in range(a.random_subsets):
                    if len(witnesses)>=a.max_models or not pairs_left(blocks): break
                    consider(random_swap(base,comps,ca,cb,rng),{'base_index':bi,'colors':[ca,cb],'kind':'random','components':len(comps),'random_index':ri})
    status='NO_FORCED_EQUAL_PAIR' if pairs_left(blocks)==0 else 'KEMPE_RESIDUAL_UNKNOWN'
    if status=='NO_FORCED_EQUAL_PAIR':
        saved,indices=greedy_compress(witnesses,n); assert all(valid_coloring(c,n,edges) for c in saved); sig=[tuple(c[v] for c in saved) for v in range(n)]; assert len(set(sig))==n
    else: saved=witnesses; indices=None
    out={'status':status,'classification':'D' if status=='NO_FORCED_EQUAL_PAIR' else None,'vertices':n,'edges':len(edges),
         'initial_remaining_pairs':initial,'generated_witness_count':len(witnesses),'saved_witness_count':len(saved),
         'compressed_witness_count':len(saved) if status=='NO_FORCED_EQUAL_PAIR' else None,'compressed_source_indices':indices,
         'remaining_pairs':pairs_left(blocks),'remaining_blocks':[b for b in blocks if len(b)>1],
         'bases_processed':bases,'records':records,'all_witnesses_validated_on_all_edges':True,'kempe_stall_is_evidence':False,
         'elapsed_seconds':round(time.monotonic()-started,3)}
    write_json(a.out_dir/'SEPARATION.json',out); write_json(a.out_dir/'WITNESSES.json',{'models':saved})
    print(json.dumps({k:v for k,v in out.items() if k not in ('remaining_blocks','records','compressed_source_indices')},indent=2))

if __name__=='__main__': main()
