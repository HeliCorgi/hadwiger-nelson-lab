#!/usr/bin/env python3
"""Optimize p1q7 two-square interface conflicts for a fixed lower witness.

The lower square coloring is fixed. The upper square must be a proper 5-coloring
and must agree on every shared geometric vertex. The cube edges not internal to
either square layer are added as unit-weight soft clauses. RC2 therefore returns
an upper coloring with the exact minimum number of remaining inter-layer conflicts
for this fixed lower witness. Cost zero is a rigorous full-cube proper coloring
after full-edge validation; positive optimum is only conditional on the chosen
lower witness.
"""
from __future__ import annotations

import argparse, json
from pathlib import Path
from pysat.formula import WCNF
from pysat.examples.rc2 import RC2

from hn_exact import K2, unit_modulus
from hn_unconditional_scan import color_cnf, valid_coloring, write_json


def extract(model, n):
    pos = {x for x in model if x > 0}
    return [next(c for c in range(5) if v * 5 + c + 1 in pos) for v in range(n)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--square', type=Path, required=True)
    ap.add_argument('--cube', type=Path, required=True)
    ap.add_argument('--layer-map', type=Path, required=True)
    ap.add_argument('--witnesses', type=Path, required=True)
    ap.add_argument('--witness-index', type=int, default=89)
    ap.add_argument('--out-dir', type=Path, required=True)
    a = ap.parse_args(); a.out_dir.mkdir(parents=True, exist_ok=True)

    sq = json.loads(a.square.read_text()); cube = json.loads(a.cube.read_text())
    lm = json.loads(a.layer_map.read_text()); wd = json.loads(a.witnesses.read_text())
    sp = [K2(p['a'], p['b'], p['den']) for p in sq['pts']]
    se = sorted({tuple(map(int, e)) for e in sq['edges']}); sn = len(sp)
    cp = [K2(p['a'], p['b'], p['den']) for p in cube['pts']]
    ce = sorted({tuple(map(int, e)) for e in cube['edges']}); cn = len(cp)
    assert sn == lm['lower_n'] == 4742
    tmap = list(map(int, lm['t3map'])); assert len(tmap) == sn
    assert all(unit_modulus(sp[u]-sp[v]) for u,v in se)
    assert all(unit_modulus(cp[u]-cp[v]) for u,v in ce)
    lower = list(map(int, wd['models'][a.witness_index]))
    assert valid_coloring(lower, sn, se)

    lower_set = set(range(sn)); upper_set = set(tmap); inv = {g:i for i,g in enumerate(tmap)}
    assert len(inv) == sn
    shared = sorted(lower_set & upper_set)
    assert len(shared) == 115
    overlap = set(se)
    for u,v in se:
        x,y=tmap[u],tmap[v]
        if x != y: overlap.add((min(x,y), max(x,y)))
    extras = sorted(set(ce) - overlap)
    assert len(extras) == 886

    w = WCNF()
    for cl in color_cnf(sn, se):
        w.append(cl)
    for g in shared:
        ui = inv[g]
        w.append([ui * 5 + lower[g] + 1])

    soft_meta = []
    for u,v in extras:
        # Exact completion of each square implies a non-overlap edge must connect
        # a lower-only vertex to an upper-only vertex.
        if u in lower_set and v in upper_set and v not in lower_set:
            lo, ug = u, v
        elif v in lower_set and u in upper_set and u not in lower_set:
            lo, ug = v, u
        else:
            raise AssertionError(('unexpected extra edge', u, v,
                                  u in lower_set, u in upper_set,
                                  v in lower_set, v in upper_set))
        ui = inv[ug]; c = lower[lo]
        w.append([-(ui * 5 + c + 1)], weight=1)
        soft_meta.append((lo, ug, ui, c))

    with RC2(w, solver='cadical195', adapt=True, exhaust=False, verbose=0) as rc2:
        model = rc2.compute(); optimum = int(rc2.cost)
    assert model is not None
    upper = extract(model, sn)
    assert valid_coloring(upper, sn, se)

    colors = [-1] * cn
    for i,c in enumerate(lower): colors[i] = c
    for i,c in enumerate(upper):
        g=tmap[i]
        if colors[g] >= 0: assert colors[g] == c
        colors[g] = c
    assert all(c >= 0 for c in colors)
    assert all(colors[u] != colors[v] for u,v in overlap)
    actual = sum(1 for u,v in ce if colors[u] == colors[v])
    assert actual == optimum

    out = {'status': 'OPTIMUM', 'lower_witness_index': a.witness_index,
           'vertices': cn, 'edges': len(ce), 'square_vertices': sn,
           'shared_vertices': len(shared), 'inter_layer_soft_edges': len(extras),
           'optimum_cube_conflicts': optimum,
           'classification': 'NOT_A' if optimum == 0 else None,
           'optimum_is_only_for_fixed_lower_witness': True,
           'all_edges_validated_if_zero': optimum == 0}
    write_json(a.out_dir/'MAXSAT.json', out)
    (a.out_dir/'COLORING_SEED.txt').write_text(''.join(map(str, colors))+'\n')
    if optimum == 0:
        assert valid_coloring(colors, cn, ce)
    print(json.dumps(out, indent=2))

if __name__ == '__main__':
    main()
