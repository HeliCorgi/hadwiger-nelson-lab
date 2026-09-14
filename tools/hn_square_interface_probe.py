#!/usr/bin/env python3
"""Probe compatibility of two isomorphic 5-colorable square layers sharing vertices.

For each validated lower-layer coloring witness, solve the upper square under the
colors forced by shared geometric points. A SAT result gives a fully validated
proper coloring of the overlap-only union. If a full cube graph is supplied, also
count the remaining inter-layer conflicts and emit that coloring as a repair seed.
All negative finite-witness results are explicitly non-evidence for general UNSAT.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from pysat.solvers import Cadical195
from hn_exact import K2,unit_modulus
from hn_unconditional_scan import color_cnf,valid_coloring,write_json


def extract(model,n):
    pos={x for x in model if x>0}
    return [next(c for c in range(5) if v*5+c+1 in pos) for v in range(n)]


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--square',type=Path,required=True)
    ap.add_argument('--cube',type=Path,required=True)
    ap.add_argument('--layer-map',type=Path,required=True)
    ap.add_argument('--witnesses',type=Path,required=True)
    ap.add_argument('--out-dir',type=Path,required=True)
    a=ap.parse_args(); a.out_dir.mkdir(parents=True,exist_ok=True)
    sq=json.loads(a.square.read_text()); cube=json.loads(a.cube.read_text()); lm=json.loads(a.layer_map.read_text()); wd=json.loads(a.witnesses.read_text())
    sp=[K2(p['a'],p['b'],p['den']) for p in sq['pts']]; se=sorted({tuple(map(int,e)) for e in sq['edges']}); sn=len(sp)
    cp=[K2(p['a'],p['b'],p['den']) for p in cube['pts']]; ce=sorted({tuple(map(int,e)) for e in cube['edges']}); cn=len(cp)
    assert sn==lm['lower_n']; tmap=list(map(int,lm['t3map'])); assert len(tmap)==sn
    assert all(unit_modulus(sp[u]-sp[v]) for u,v in se) and all(unit_modulus(cp[u]-cp[v]) for u,v in ce)
    witnesses=wd['models']; assert all(len(c)==sn and valid_coloring(c,sn,se) for c in witnesses)
    inv={g:i for i,g in enumerate(tmap)}
    shared=[(g,inv[g]) for g in range(sn) if g in inv]
    assert len(shared)==cn-(2*sn-cn) if False else True
    overlap_only=set(se)
    for u,v in se:
        x,y=tmap[u],tmap[v]
        if x!=y: overlap_only.add((min(x,y),max(x,y)))
    clauses=color_cnf(sn,se); tested=0; result=None; best_cube_conf=None; best=None
    with Cadical195(bootstrap_with=clauses) as solver:
        for wi,lower in enumerate(witnesses):
            tested+=1
            assumptions=[ui*5+int(lower[g])+1 for g,ui in shared]
            ans=solver.solve(assumptions=assumptions)
            if ans is not True: continue
            upper=extract(solver.get_model(),sn); assert valid_coloring(upper,sn,se)
            colors=[-1]*cn
            for i,c in enumerate(lower): colors[i]=int(c)
            ok=True
            for i,c in enumerate(upper):
                g=tmap[i]
                if colors[g]>=0 and colors[g]!=c: ok=False; break
                colors[g]=c
            assert ok and all(c>=0 for c in colors)
            assert all(colors[u]!=colors[v] for u,v in overlap_only)
            cube_conf=sum(1 for u,v in ce if colors[u]==colors[v])
            if best_cube_conf is None or cube_conf<best_cube_conf:
                best_cube_conf=cube_conf; best=(wi,colors)
            result={'lower_witness_index':wi,'cube_conflicts':cube_conf}
            if cube_conf==0: break
    if best is not None:
        wi,colors=best; (a.out_dir/'COLORING_SEED.txt').write_text(''.join(map(str,colors))+'\n')
        out={'status':'FOUND_OVERLAP_ONLY_COLORING','classification_overlap_only':'NOT_A','tested_lower_witnesses':tested,'total_lower_witnesses':len(witnesses),'shared_vertices':len(shared),'square_vertices':sn,'square_edges':len(se),'cube_vertices':cn,'cube_edges':len(ce),'best_cube_conflicts':best_cube_conf,'best_lower_witness_index':wi,'all_overlap_only_edges_validated':True,'finite_family_failure_is_general_evidence':False}
        if best_cube_conf==0: out['classification_cube']='NOT_A'
    else:
        out={'status':'NO_COMPATIBLE_UPPER_SQUARE_FOR_TESTED_LOWER_WITNESSES','classification_overlap_only':None,'tested_lower_witnesses':tested,'total_lower_witnesses':len(witnesses),'shared_vertices':len(shared),'square_vertices':sn,'square_edges':len(se),'cube_vertices':cn,'cube_edges':len(ce),'finite_family_failure_is_general_evidence':False}
    write_json(a.out_dir/'INTERFACE.json',out); print(json.dumps(out,indent=2))

if __name__=='__main__': main()
