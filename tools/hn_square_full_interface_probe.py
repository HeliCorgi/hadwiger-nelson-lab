#!/usr/bin/env python3
"""Test a finite family of lower-square colorings against every full cube edge.

For a fixed lower coloring, all 886 non-layer cube edges become unary forbidden
colors on upper-square vertices. Together with 115 shared-vertex color equalities,
we solve only the upper square CNF. Any SAT model is merged and validated on all
57,488 exact cube edges. Exhausting the finite lower witness family without SAT is
explicitly non-evidence for whole-graph UNSAT.
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
    ap=argparse.ArgumentParser(); ap.add_argument('--square',type=Path,required=True); ap.add_argument('--cube',type=Path,required=True)
    ap.add_argument('--layer-map',type=Path,required=True); ap.add_argument('--witnesses',type=Path,required=True); ap.add_argument('--out-dir',type=Path,required=True)
    a=ap.parse_args(); a.out_dir.mkdir(parents=True,exist_ok=True)
    sq=json.loads(a.square.read_text()); cube=json.loads(a.cube.read_text()); lm=json.loads(a.layer_map.read_text()); wd=json.loads(a.witnesses.read_text())
    sp=[K2(p['a'],p['b'],p['den']) for p in sq['pts']]; se=sorted({tuple(map(int,e)) for e in sq['edges']}); sn=len(sp)
    cp=[K2(p['a'],p['b'],p['den']) for p in cube['pts']]; ce=sorted({tuple(map(int,e)) for e in cube['edges']}); cn=len(cp)
    assert sn==lm['lower_n']; tmap=list(map(int,lm['t3map'])); inv={g:i for i,g in enumerate(tmap)}; assert len(inv)==sn
    assert all(unit_modulus(sp[u]-sp[v]) for u,v in se) and all(unit_modulus(cp[u]-cp[v]) for u,v in ce)
    lower_set=set(range(sn)); upper_set=set(tmap); shared=sorted(lower_set & upper_set); assert len(shared)==115
    overlap=set(se)
    for u,v in se:
        x,y=tmap[u],tmap[v]
        if x!=y: overlap.add((min(x,y),max(x,y)))
    extras=sorted(set(ce)-overlap); assert len(extras)==886
    cross=[]
    for u,v in extras:
        if u in lower_set and v in upper_set and v not in lower_set: cross.append((u,inv[v]))
        elif v in lower_set and u in upper_set and u not in lower_set: cross.append((v,inv[u]))
        else: raise AssertionError(('unexpected extra',u,v))
    witnesses=wd['models']; assert all(valid_coloring(list(map(int,c)),sn,se) for c in witnesses)
    clauses=color_cnf(sn,se); records=[]; found=None
    with Cadical195(bootstrap_with=clauses) as solver:
        for wi,raw in enumerate(witnesses):
            lower=list(map(int,raw))
            assumptions={inv[g]*5+lower[g]+1 for g in shared}
            assumptions.update(-(ui*5+lower[lo]+1) for lo,ui in cross)
            ans=solver.solve(assumptions=sorted(assumptions,key=lambda x:(abs(x),x)))
            rec={'lower_witness_index':wi,'assumption_literals':len(assumptions),'status':'SAT' if ans is True else 'UNSAT'}; records.append(rec)
            if ans is not True: continue
            upper=extract(solver.get_model(),sn); assert valid_coloring(upper,sn,se)
            colors=[-1]*cn
            for i,c in enumerate(lower): colors[i]=c
            for i,c in enumerate(upper):
                g=tmap[i]
                if colors[g]>=0: assert colors[g]==c
                colors[g]=c
            assert valid_coloring(colors,cn,ce)
            found=(wi,colors); break
    if found:
        wi,colors=found; out={'status':'SAT','classification':'NOT_A','lower_witness_index':wi,'tested_lower_witnesses':len(records),
             'total_lower_witnesses':len(witnesses),'vertices':cn,'edges':len(ce),'shared_vertices':len(shared),'inter_layer_edges':len(extras),
             'all_edges_validated':True,'records':records}; (a.out_dir/'COLORING.txt').write_text(''.join(map(str,colors))+'\n')
    else:
        out={'status':'NO_SAT_IN_FINITE_LOWER_WITNESS_FAMILY','classification':None,'tested_lower_witnesses':len(records),'total_lower_witnesses':len(witnesses),
             'vertices':cn,'edges':len(ce),'shared_vertices':len(shared),'inter_layer_edges':len(extras),'finite_family_failure_is_whole_graph_evidence':False,'records':records}
    write_json(a.out_dir/'FULL_INTERFACE.json',out); print(json.dumps({k:v for k,v in out.items() if k!='records'},indent=2))

if __name__=='__main__': main()
