#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import deque
from itertools import combinations
from pathlib import Path

from pysat.solvers import Cadical195

from separator_interface import P, Q, UPSTREAM_SHA, build, components_without, min_vertex_cut, rgs

K = 5
S_EXPECTED = [0, 6, 8, 9, 10, 266]
TARGETS = [(5, 6), (0, 10), (8, 9)]
MAX_ENUM_CUT = 8


def remap_subgraph(nodes, edges):
    old = sorted(nodes)
    to_new = {v: i for i, v in enumerate(old)}
    es = []
    V = set(old)
    for u, v in edges:
        if u in V and v in V:
            es.append((to_new[u], to_new[v]))
    return old, to_new, sorted(es)


def make_bag_solver(nodes, edges):
    ns = sorted(nodes)
    idx = {v: i for i, v in enumerate(ns)}
    cls = []
    def X(v, c): return idx[v] * K + c + 1
    for v in ns:
        lits = [X(v, c) for c in range(K)]
        cls.append(lits)
        for a, b in combinations(lits, 2):
            cls.append([-a, -b])
    V = set(ns)
    for u, v in edges:
        if u in V and v in V:
            for c in range(K):
                cls.append([-X(u, c), -X(v, c)])
    return Cadical195(bootstrap_with=cls), X


def options(sol, X, sep, state, v):
    base = [X(x, state[i]) for i, x in enumerate(sep)]
    return [c for c in range(K) if sol.solve(assumptions=base + [X(v, c)])]


def analyze_pair(left_nodes, left_edges, pair):
    old, to_new, es = remap_subgraph(left_nodes, left_edges)
    u0, v0 = pair
    u, v = to_new[u0], to_new[v0]
    val, cut_new = min_vertex_cut(len(old), es, u, v)
    cut = [old[x] for x in cut_new]
    comps_new = components_without(len(old), es, cut_new)
    ucomp_new = next(c for c in comps_new if u in c)
    vcomp_new = next(c for c in comps_new if v in c)
    comps = [[old[x] for x in c] for c in comps_new]
    ucomp = [old[x] for x in ucomp_new]
    vcomp = [old[x] for x in vcomp_new]
    other = [c for c in comps if c != ucomp and c != vcomp]

    rep = {
        'pair': list(pair),
        'min_vertex_cut_value': val,
        'separator_qnodes': cut,
        'component_sizes': sorted(len(c) for c in comps),
        'u_component_size': len(ucomp),
        'v_component_size': len(vcomp),
        'other_component_sizes': sorted(len(c) for c in other),
        'enumerated': val <= MAX_ENUM_CUT,
    }
    if val > MAX_ENUM_CUT:
        return rep

    bags = []
    for comp in comps:
        sol, X = make_bag_solver(set(comp) | set(cut), left_edges)
        bags.append((comp, sol, X))
    rows = []
    total = 0
    try:
        for st in rgs(len(cut)):
            total += 1
            ok = True
            for comp, sol, X in bags:
                ass = [X(x, st[i]) for i, x in enumerate(cut)]
                if not sol.solve(assumptions=ass):
                    ok = False
                    break
            if not ok:
                continue
            ubag = next(z for z in bags if u0 in z[0])
            vbag = next(z for z in bags if v0 in z[0])
            ucols = options(ubag[1], ubag[2], cut, st, u0)
            vcols = options(vbag[1], vbag[2], cut, st, v0)
            rows.append({
                'boundary_state': ''.join(map(str, st)),
                'u_colors': ucols,
                'v_colors': vcols,
                'all_cross_pairs_equal': all(a == b for a in ucols for b in vcols),
            })
    finally:
        for _, sol, _ in bags:
            sol.delete()

    bad = [r for r in rows if not r['all_cross_pairs_equal']]
    rep.update({
        'all_canonical_boundary_states': total,
        'viable_boundary_state_count': len(rows),
        'all_viable_states_force_equal': not bad,
        'bad_state_count': len(bad),
        'singleton_equal_state_count': sum(len(r['u_colors']) == len(r['v_colors']) == 1 and r['u_colors'] == r['v_colors'] for r in rows),
        'viable_states': rows if len(rows) <= 80 else None,
        'viable_state_keys': [r['boundary_state'] for r in rows],
    })
    return rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data-dir', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()

    C, R, vq, E = build(args.data_dir)
    n = len(R)
    p, q = vq[P], vq[Q]
    val, S = min_vertex_cut(n, E, p, q)
    if p != 5 or S != S_EXPECTED:
        raise RuntimeError((p, q, val, S))
    cc = components_without(n, E, S)
    pc = next(x for x in cc if p in x)
    left = set(pc) | set(S)
    left_edges = [(u, v) for u, v in E if u in left and v in left]

    reports = [analyze_pair(left, left_edges, pair) for pair in TARGETS]
    rep = {
        'upstream_sha': UPSTREAM_SHA,
        'left_bag_size': len(left),
        'left_bag_edge_count': len(left_edges),
        'outer_separator_qnodes': S,
        'targets': reports,
        'interpretation': 'Each forced equality is recursively factored through a minimum vertex separator inside the 267-qnode left bag. For cuts of size at most eight, all canonical color partitions are enumerated exactly and the two endpoint-side color option sets are checked independently across the cut.'
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(rep, indent=2) + '\n')
    print(json.dumps({
        'targets': [
            {
                'pair': r['pair'],
                'cut': r['min_vertex_cut_value'],
                'separator': r['separator_qnodes'],
                'component_sizes': r['component_sizes'],
                'enumerated': r['enumerated'],
                'viable': r.get('viable_boundary_state_count'),
                'forces_equal': r.get('all_viable_states_force_equal'),
            }
            for r in reports
        ]
    }, indent=2))


if __name__ == '__main__':
    main()
