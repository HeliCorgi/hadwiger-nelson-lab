#!/usr/bin/env python3
"""Sample many upper-square colorings compatible with one lower-square witness.

Every sampled upper model is a validated proper square coloring satisfying the 115
shared-vertex colors. We rank samples by conflicts on the full exact cube edge set.
A zero-conflict sample is a rigorous full-cube proper 5-coloring after validation.
Failure to sample one is non-evidence.
"""
from __future__ import annotations
import argparse,json,random
from pathlib import Path
from pysat.solvers import Cadical195
from hn_exact import K2,unit_modulus
from hn_unconditional_scan import color_cnf,valid_coloring,write_json


def extract(model,n):
    pos={x for x in model if x>0}
    return [next(c for c in range(5) if v*5+c+1 in pos) for v in range(n)]


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--square',type=Path,required=True); ap.add_argument('--cube',type=Path,required=True)
    ap.add_argument('--layer-map',type=Path,required=True); ap.add_argument('--witnesses',type=Path,required=True)
    ap.add_argument('--witness-index',type=int,default=89); ap.add_argument('--samples',type=int,default=600)
    ap.add_argument('--seed',type=int,default=20260914); ap.add_argument('--out-dir',type=Path,required=True)
    a=ap.parse_args(); a.out_dir.mkdir(parents=True,exist_ok=True)
    sq=json.loads(a.square.read_text()); cube=json.loads(a.cube.read_text()); lm=json.loads(a.layer_map.read_text()); wd=json.loads(a.witnesses.read_text())
    sp=[K2(p['a'],p['b'],p['den']) for p in sq['pts']]; se=sorted({tuple(map(int,e)) for e in sq['edges']}); sn=len(sp)
    cp=[K2(p['a'],p['b'],p['den']) for p in cube['pts']]; ce=sorted({tuple(map(int,e)) for e in cube['edges']}); cn=len(cp)
    assert sn==lm['lower_n']; tmap=list(map(int,lm['t3map'])); inv={g:i for i,g in enumerate(tmap)}; assert len(inv)==sn
    assert all(unit_modulus(sp[u]-sp[v]) for u,v in se) and all(unit_modulus(cp[u]-cp[v]) for u,v in ce)
    lower=list(map(int,wd['models'][a.witness_index])); assert valid_coloring(lower,sn,se)
    shared=[(g,inv[g]) for g in range(sn) if g in inv]; assert len(shared)==115
    assumptions=[ui*5+lower[g]+1 for g,ui in shared]
    clauses=color_cnf(sn,se); rng=random.Random(a.seed); best=None; records=[]; seen=0
    with Cadical195(bootstrap_with=clauses) as solver:
        for it in range(a.samples):
            phases=[v*5+rng.randrange(5)+1 for v in range(sn)]; solver.set_phases(phases)
            ans=solver.solve(assumptions=assumptions)
            if ans is not True: break
            upper=extract(solver.get_model(),sn); assert valid_coloring(upper,sn,se)
            colors=[-1]*cn
            for i,c in enumerate(lower): colors[i]=c
            for i,c in enumerate(upper):
                g=tmap[i]
                if colors[g]>=0: assert colors[g]==c
                colors[g]=c
            assert all(c>=0 for c in colors)
            conf=sum(1 for u,v in ce if colors[u]==colors[v]); seen+=1
            if best is None or conf<best[0]:
                best=(conf,colors,it); records.append({'sample':it,'best_conflicts':conf}); print(json.dumps(records[-1]),flush=True)
                if conf==0: break
            solver.add_clause([-(v*5+upper[v]+1) for v in range(sn)])
    assert best is not None
    conf,colors,it=best
    if conf==0: assert valid_coloring(colors,cn,ce)
    out={'status':'FOUND_ZERO_CONFLICT' if conf==0 else 'SAMPLED_NONZERO','classification':'NOT_A' if conf==0 else None,
         'lower_witness_index':a.witness_index,'requested_samples':a.samples,'generated_samples':seen,'best_sample':it,
         'best_cube_conflicts':conf,'vertices':cn,'edges':len(ce),'all_edges_validated_if_zero':conf==0,
         'sampling_failure_is_evidence':False,'improvement_records':records}
    write_json(a.out_dir/'SAMPLE.json',out); (a.out_dir/'COLORING_SEED.txt').write_text(''.join(map(str,colors))+'\n')
    print(json.dumps({k:v for k,v in out.items() if k!='improvement_records'},indent=2))

if __name__=='__main__': main()
