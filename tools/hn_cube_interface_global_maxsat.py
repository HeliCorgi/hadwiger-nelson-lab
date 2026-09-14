#!/usr/bin/env python3
"""Exact global MaxSAT over the two square layers of the p1q7 cube.

Two independent square colorings are hard-constrained to be proper and equal on
all shared geometric vertices. The 886 exact cube edges not internal to either
square layer are soft constraints, one unit of cost per monochromatic edge.
Hence optimum 0 is exactly a proper 5-coloring of the full cube. A positive exact
optimum is a whole-cube non-5-colorability result, but should be independently
confirmed/certified before promoting to a final A witness.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
from pysat.formula import WCNF
from pysat.examples.rc2 import RC2

from hn_exact import K2, unit_modulus
from hn_unconditional_scan import color_cnf, valid_coloring, write_json


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--square',type=Path,required=True)
    ap.add_argument('--cube',type=Path,required=True)
    ap.add_argument('--layer-map',type=Path,required=True)
    ap.add_argument('--out-dir',type=Path,required=True)
    a=ap.parse_args(); a.out_dir.mkdir(parents=True,exist_ok=True)

    sq=json.loads(a.square.read_text()); cube=json.loads(a.cube.read_text()); lm=json.loads(a.layer_map.read_text())
    sp=[K2(p['a'],p['b'],p['den']) for p in sq['pts']]; se=sorted({tuple(map(int,e)) for e in sq['edges']}); sn=len(sp)
    cp=[K2(p['a'],p['b'],p['den']) for p in cube['pts']]; ce=sorted({tuple(map(int,e)) for e in cube['edges']}); cn=len(cp)
    assert sn==lm['lower_n']==4742; tmap=list(map(int,lm['t3map'])); assert len(tmap)==sn
    assert all(unit_modulus(sp[u]-sp[v]) for u,v in se) and all(unit_modulus(cp[u]-cp[v]) for u,v in ce)
    lower_set=set(range(sn)); upper_set=set(tmap); inv={g:i for i,g in enumerate(tmap)}; assert len(inv)==sn
    shared=sorted(lower_set & upper_set); assert len(shared)==115
    overlap=set(se)
    for u,v in se:
        x,y=tmap[u],tmap[v]
        if x!=y: overlap.add((min(x,y),max(x,y)))
    extras=sorted(set(ce)-overlap); assert len(extras)==886

    off=sn*5
    def lv(i,c): return i*5+c+1
    def uv(i,c): return off+i*5+c+1
    w=WCNF()
    base=color_cnf(sn,se)
    for cl in base: w.append(cl)
    for cl in base:
        w.append([(x+off if x>0 else x-off) for x in cl])
    # Shared global vertex g is lower abstract g and upper abstract inv[g].
    for g in shared:
        ui=inv[g]
        for c in range(5):
            w.append([-lv(g,c),uv(ui,c)])
            w.append([lv(g,c),-uv(ui,c)])

    for u,v in extras:
        if u in lower_set and v in upper_set and v not in lower_set:
            lo,ui=u,inv[v]
        elif v in lower_set and u in upper_set and u not in lower_set:
            lo,ui=v,inv[u]
        else:
            raise AssertionError(('unexpected extra',u,v))
        # Exactly one of these five soft clauses is violated iff the edge is monochromatic.
        for c in range(5):
            w.append([-lv(lo,c),-uv(ui,c)],weight=1)

    with RC2(w,solver='cadical195',adapt=True,exhaust=False,verbose=0) as rc2:
        model=rc2.compute(); optimum=int(rc2.cost)
    assert model is not None
    pos={x for x in model if x>0}
    lower=[next(c for c in range(5) if lv(i,c) in pos) for i in range(sn)]
    upper=[next(c for c in range(5) if uv(i,c) in pos) for i in range(sn)]
    assert valid_coloring(lower,sn,se) and valid_coloring(upper,sn,se)
    colors=[-1]*cn
    for i,c in enumerate(lower): colors[i]=c
    for i,c in enumerate(upper):
        g=tmap[i]
        if colors[g]>=0: assert colors[g]==c
        colors[g]=c
    assert all(c>=0 for c in colors)
    actual=sum(1 for u,v in ce if colors[u]==colors[v]); assert actual==optimum
    if optimum==0: assert valid_coloring(colors,cn,ce)
    out={'status':'OPTIMUM','vertices':cn,'edges':len(ce),'square_vertices':sn,'shared_vertices':len(shared),
         'inter_layer_edges':len(extras),'optimum_cube_conflicts':optimum,
         'classification':'NOT_A' if optimum==0 else 'A_CANDIDATE_REQUIRES_INDEPENDENT_CONFIRMATION',
         'global_equivalence_to_full_5_coloring':True,'all_edges_validated_if_zero':optimum==0}
    write_json(a.out_dir/'GLOBAL_MAXSAT.json',out)
    (a.out_dir/'COLORING.txt').write_text(''.join(map(str,colors))+'\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__': main()
