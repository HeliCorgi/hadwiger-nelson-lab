#!/usr/bin/env python3
"""Close residual same-signature pairs starting from a validated coloring family.

Every successful local repair is revalidated on every exact graph edge. Failure or
timeout is non-evidence. If all vertex signatures become unique, the retained
proper-coloring family is a direct D certificate for fixed-pair forcing.
"""
from __future__ import annotations
import argparse, json, random, time
from pathlib import Path

from hn_exact import K2, unit_modulus
from hn_unconditional_scan import valid_coloring, write_json
from hn_local_pair_separation import refine, pairs_left, constrained_repair, greedy_compress


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--graph',type=Path,required=True)
    ap.add_argument('--models',type=Path,required=True)
    ap.add_argument('--out-dir',type=Path,required=True)
    ap.add_argument('--seconds',type=float,default=1200)
    ap.add_argument('--pair-seconds',type=float,default=20)
    ap.add_argument('--iterations',type=int,default=500000)
    ap.add_argument('--perturb',type=int,default=28)
    ap.add_argument('--max-failures',type=int,default=20)
    ap.add_argument('--seed',type=int,default=20260914)
    a=ap.parse_args(); a.out_dir.mkdir(parents=True,exist_ok=True)

    d=json.loads(a.graph.read_text())
    pts=[K2(p['a'],p['b'],p['den']) for p in d['pts']]
    edges=sorted({tuple(map(int,e)) for e in d['edges']}); n=len(pts)
    assert len(set(pts))==n and all(unit_modulus(pts[u]-pts[v]) for u,v in edges)
    adj=[[] for _ in range(n)]
    for u,v in edges: adj[u].append(v); adj[v].append(u)

    md=json.loads(a.models.read_text()); witnesses=[list(map(int,c)) for c in md['models']]
    assert witnesses and all(valid_coloring(c,n,edges) for c in witnesses)
    blocks=[list(range(n))]
    for c in witnesses: blocks=refine(blocks,c)
    initial_pairs=pairs_left(blocks)
    initial_models=len(witnesses)
    records=[]; failures=[]; started=time.monotonic(); rng=random.Random(a.seed)
    compact_count=None; compact_indices=None

    def save(status, saved=None):
        models=witnesses if saved is None else saved
        payload={
            'status':status,
            'classification':'D' if status=='NO_FORCED_EQUAL_PAIR' else None,
            'vertices':n,'edges':len(edges),
            'initial_model_count':initial_models,'initial_remaining_pairs':initial_pairs,
            'generated_witness_count':len(witnesses),'saved_witness_count':len(models),
            'compressed_witness_count':compact_count,'compressed_source_indices':compact_indices,
            'remaining_pairs':pairs_left(blocks),
            'remaining_blocks':[b for b in blocks if len(b)>1],
            'records':records,'failures':failures,
            'timeout_or_repair_failure_is_evidence':False,
            'all_witnesses_validated_on_all_edges':True,
            'elapsed_seconds':round(time.monotonic()-started,3),
        }
        write_json(a.out_dir/'SEPARATION.json',payload)
        write_json(a.out_dir/'WITNESSES.json',{'models':models})
        return payload

    save('ACTIVE')
    while pairs_left(blocks) and time.monotonic()-started<a.seconds:
        candidates=sorted((b for b in blocks if len(b)>1),key=len,reverse=True)
        progressed=False
        for block in candidates[:min(20,len(candidates))]:
            if time.monotonic()-started>=a.seconds: break
            u,v=block[0],block[-1]
            assert all(c[u]==c[v] for c in witnesses)
            base=witnesses[-1]
            color,meta=constrained_repair(
                base,edges,adj,u,v,rng.randrange(1<<62),
                min(a.pair_seconds,max(.1,a.seconds-(time.monotonic()-started))),
                a.iterations,a.perturb)
            if color is None:
                failures.append({'pair':[u,v],**meta})
                if len(failures)>=a.max_failures:
                    out=save('RESIDUAL_UNKNOWN')
                    print(json.dumps({k:v for k,v in out.items() if k not in ('remaining_blocks','records')},indent=2)); return
                continue
            assert color[u]!=color[v] and valid_coloring(color,n,edges)
            before=pairs_left(blocks); blocks=refine(blocks,color); after=pairs_left(blocks)
            assert after<before
            witnesses.append(color)
            rec={'target':[u,v],'before':before,'after':after,'max_block':max(map(len,blocks)),'repair':meta}
            records.append(rec); print(json.dumps(rec),flush=True); progressed=True; break
        if not progressed: break

    status='NO_FORCED_EQUAL_PAIR' if not pairs_left(blocks) else 'RESIDUAL_UNKNOWN'
    if status=='NO_FORCED_EQUAL_PAIR':
        compact,indices=greedy_compress(witnesses,n)
        assert all(valid_coloring(c,n,edges) for c in compact)
        sigs=[tuple(c[v] for c in compact) for v in range(n)]
        assert len(set(sigs))==n
        compact_count=len(compact); compact_indices=indices
        out=save(status,compact)
    else:
        out=save(status)
    print(json.dumps({k:v for k,v in out.items() if k not in ('remaining_blocks','records')},indent=2))

if __name__=='__main__': main()
