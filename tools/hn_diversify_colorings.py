#!/usr/bin/env python3
"""Diversify a validated proper 5-coloring by perturb-and-repair.

Each accepted model is revalidated on every exact edge. Failed perturbation repairs
are non-evidence. Models are canonicalized only for duplicate detection; saved
models retain their actual color labels. Signature statistics are reported so the
family can seed rigorous pair separation.
"""
from __future__ import annotations
import argparse,json,random,time
from collections import Counter
from pathlib import Path
from hn_exact import K2,unit_modulus
from hn_unconditional_scan import valid_coloring,write_json
from hn_seeded_tabucol import load_seed,search
from hn_closed_copy_assembly import canonical_coloring,signature_stats


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--graph',type=Path,required=True); ap.add_argument('--seed-coloring',type=Path,required=True)
    ap.add_argument('--out-dir',type=Path,required=True); ap.add_argument('--models',type=int,default=40)
    ap.add_argument('--seconds',type=float,default=2400); ap.add_argument('--repair-seconds',type=float,default=45)
    ap.add_argument('--iterations',type=int,default=500000); ap.add_argument('--perturb-min',type=int,default=8)
    ap.add_argument('--perturb-max',type=int,default=80); ap.add_argument('--seed',type=int,default=20260914)
    a=ap.parse_args(); a.out_dir.mkdir(parents=True,exist_ok=True)
    d=json.loads(a.graph.read_text()); pts=[K2(p['a'],p['b'],p['den']) for p in d['pts']]
    edges=sorted({tuple(map(int,e)) for e in d['edges']}); n=len(pts)
    assert len(set(pts))==n and all(unit_modulus(pts[u]-pts[v]) for u,v in edges)
    base=load_seed(a.seed_coloring,n); assert valid_coloring(base,n,edges)
    witnesses=[base]; seen={canonical_coloring(base)}; rng=random.Random(a.seed); records=[]; started=time.monotonic(); attempt=0
    while len(witnesses)<a.models and time.monotonic()-started<a.seconds:
        attempt+=1; src=list(rng.choice(witnesses)); p=rng.randint(a.perturb_min,a.perturb_max)
        for v in rng.sample(range(n),min(n,p)):
            old=src[v]; src[v]=rng.choice([c for c in range(5) if c!=old])
        start_conf=sum(1 for u,v in edges if src[u]==src[v])
        remaining=max(.1,a.seconds-(time.monotonic()-started))
        color,meta=search(src,edges,5,rng.randrange(1<<62),4,a.iterations,min(a.repair_seconds,remaining),max(16,p//2))
        rec={'attempt':attempt,'perturbed_vertices':p,'start_conflicts':start_conf,'success':color is not None}
        if color is not None:
            assert valid_coloring(color,n,edges); can=canonical_coloring(color)
            rec['canonical_new']=can not in seen
            if can not in seen:
                seen.add(can); witnesses.append(color); rec['models']=len(witnesses)
        records.append(rec)
        if attempt%10==0 or rec.get('canonical_new'):
            print(json.dumps(rec),flush=True)
    assert all(valid_coloring(c,n,edges) for c in witnesses)
    stats=signature_stats(witnesses,n)
    out={'status':'VALIDATED_COLORING_FAMILY','vertices':n,'edges':len(edges),'requested_models':a.models,
         'generated_models':len(witnesses),'attempts':attempt,'signature_stats':stats,
         'all_models_validated_on_all_edges':True,'repair_failure_is_evidence':False,
         'elapsed_seconds':round(time.monotonic()-started,3),'records':records}
    write_json(a.out_dir/'MODELS.json',{'models':witnesses}); write_json(a.out_dir/'STATS.json',out)
    print(json.dumps({k:v for k,v in out.items() if k!='records'},indent=2))

if __name__=='__main__': main()
