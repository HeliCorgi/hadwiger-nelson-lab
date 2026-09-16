#!/usr/bin/env python3
"""Restore audited local checkpoints from transparent exact placement recipes.

Rebuilds points and all unit edges; reproduces color banks by positive-only
library extension. No SAT calls and no opaque executable payloads are used.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from hn_cegis_contact import initialize, load, dump, semantic, sha, proposal, library_extension, canonical, validate
from hn_cegis_geometry import P, K, unit

ROOT=Path(__file__).resolve().parents[1]/'results/cegis-contact-2026-09-16'

def sparse_point(value):
    fields=[]
    for name in ('a','b'):
        q=value[name];v=[0]*48;used=set()
        for i,c in q['nz']:
            if type(i)!=int or not 0<=i<48 or i in used or type(c)!=int:
                raise ValueError('invalid sparse exact coefficient')
            used.add(i);v[i]=c
        fields.append(K(tuple(v),q['den']))
    return P(*fields)

def restore(source,source_coloring,recipe_path,case,out):
    manifest=load(recipe_path);record=manifest['cases'][case]
    if manifest['schema']!=1:raise ValueError('unknown recipe schema')
    if hashlib.sha256(source_coloring.read_bytes()).hexdigest()!=manifest['source_coloring_sha256']:
        raise ValueError('source coloring file hash mismatch')
    if out.exists():raise ValueError('restore requires a new output directory')
    out.mkdir(parents=True)
    args=SimpleNamespace(calibration=False,source=source,source_coloring=source_coloring)
    points,colors,k,g,bank=initialize(args,out)
    for step in record['accepted']:
        if step['method']!='first_valid_library_extension_then_canonical':raise ValueError('unknown replay method')
        rotation=sparse_point(step['rotation']);anchor=sparse_point(step['anchor'])
        if not unit(rotation):raise ValueError('non-isometric replay')
        child,copy,_=proposal(g,points,rotation,anchor)
        if semantic(child)!=step['graph_sha256']:raise ValueError('replayed graph differs')
        model=library_extension(child,bank[0],colors,copy,k)
        if model is None:raise ValueError('saved positive extension did not reproduce')
        bank=[canonical(model)];g=child
        validate(g,bank[0],k)
    if (len(g['pts']),len(g['edges']),semantic(g),sha(bank))!=(record['vertices'],record['edges'],record['current_graph_sha256'],record['bank_sha256']):
        raise ValueError('checkpoint graph or complete color bank mismatch')
    checkpoint={key:record[key] for key in ('next_round','seed','mode','current_graph_sha256','k')}
    checkpoint.update(bank=bank,stores_solver_learned_clauses=False)
    dump(out/'LEGACY_CHECKPOINT.json',checkpoint)
    if hashlib.sha256((out/'LEGACY_CHECKPOINT.json').read_bytes()).hexdigest()!=record['original_checkpoint_file_sha256']:
        raise ValueError('original checkpoint bytes do not match')
    checkpoint['seen_graph_sha256']=record['seen_graph_sha256']
    dump(out/'CHECKPOINT.json',checkpoint);dump(out/'CURRENT.json.gz',g)
    report={'status':'RESTORED_EXACT_CHECKPOINT','case':case,'next_round':record['next_round'],
            'vertices':len(g['pts']),'edges':len(g['edges']),'graph_sha256':semantic(g),
            'bank_sha256':sha(bank),'legacy_checkpoint_bytes_match':True,'SAT_solver_used':False,
            'seen_candidates_preserved':len(record['seen_graph_sha256'])}
    dump(out/'RESTORE.json',report);print(json.dumps(report),flush=True)
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--source-coloring',type=Path,default=ROOT/'INPUT_G3_COLORING.txt')
    p.add_argument('--recipes',type=Path,default=ROOT/'RESUME_RECIPES.json')
    p.add_argument('--case',choices=('11-guided','11-random','29-guided','29-random'),required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();restore(a.source,a.source_coloring,a.recipes,a.case,a.out)

if __name__=='__main__':main()
