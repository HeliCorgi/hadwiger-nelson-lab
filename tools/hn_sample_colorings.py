#!/usr/bin/env python3
"""Generate a validated family of proper 5-colorings and signature statistics."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

from hn_exact import K2, unit_modulus
from hn_closed_copy_assembly import sample_models, signature_stats
from hn_unconditional_scan import valid_coloring, write_json


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--graph',type=Path,required=True)
    ap.add_argument('--out-dir',type=Path,required=True)
    ap.add_argument('--models',type=int,default=16)
    ap.add_argument('--conflicts',type=int,default=800000)
    ap.add_argument('--seed',type=int,default=20260914)
    a=ap.parse_args(); a.out_dir.mkdir(parents=True,exist_ok=True)

    raw=a.graph.read_bytes(); d=json.loads(raw)
    pts=[K2(p['a'],p['b'],p['den']) for p in d['pts']]
    edges=sorted({tuple(map(int,e)) for e in d['edges']}); n=len(pts)
    assert len(set(pts))==n and all(unit_modulus(pts[u]-pts[v]) for u,v in edges)
    models=sample_models(n,edges,a.models,a.conflicts,a.seed)
    assert models and all(valid_coloring(c,n,edges) for c in models)
    stats=signature_stats(models,n)
    out={
        'status':'VALIDATED_COLORING_FAMILY','vertices':n,'edges':len(edges),
        'graph_sha256':hashlib.sha256(raw).hexdigest(),'models':len(models),
        'signature_stats':stats,'all_models_validated_on_all_edges':True,
    }
    write_json(a.out_dir/'MODELS.json',{'models':models})
    write_json(a.out_dir/'STATS.json',out)
    print(json.dumps(out,indent=2))

if __name__=='__main__': main()
