#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path

from pysat.solvers import Cadical195, Glucose4

from separator_interface import P, Q, UPSTREAM_SHA, build, components_without, min_vertex_cut

K = 5
OUTER = [0, 6, 8, 9, 10, 266]
INNER = [14, 18, 54, 55, 256]
TARGET = (18, 256)


def coloring_cnf(nodes, edges, colors):
    ns = sorted(nodes)
    idx = {v: i for i, v in enumerate(ns)}
    def X(v, c): return idx[v] * colors + c + 1
    cls = []
    V = set(ns)
    for v in ns:
        lits = [X(v, c) for c in range(colors)]
        cls.append(lits)
        for a, b in combinations(lits, 2):
            cls.append([-a, -b])
    for u, v in edges:
        if u in V and v in V:
            for c in range(colors):
                cls.append([-X(u, c), -X(v, c)])
    return cls, X


def sat_colorable(nodes, edges, colors, Solver):
    cls, _ = coloring_cnf(nodes, edges, colors)
    with Solver(bootstrap_with=cls) as s:
        return s.solve()


def forced_distinct(nodes, edges, pair, Solver):
    cls, X = coloring_cnf(nodes, edges, K)
    u, v = pair
    for c in range(K):
        cls.append([-X(u, c), X(v, c)])
        cls.append([-X(v, c), X(u, c)])
    with Solver(bootstrap_with=cls) as s:
        return not s.solve()


def induced_edges(nodes, edges):
    V = set(nodes)
    return [(u, v) for u, v in edges if u in V and v in V]


def minimize_non4(nodes, edges):
    active = set(nodes)
    order = sorted(active, key=lambda v: (sum(1 for a,b in edges if (a==v and b in active) or (b==v and a in active)), v))
    for v in order:
        trial = active - {v}
        if trial and not sat_colorable(trial, edges, 4, Cadical195):
            active = trial
    # Verify inclusion-minimality for this deletion order result.
    critical = []
    for v in sorted(active):
        sat = sat_colorable(active - {v}, edges, 4, Cadical195)
        critical.append({'vertex': v, 'four_colorable_if_deleted': sat})
        if not sat:
            raise RuntimeError(('nonminimal 4-color obstruction', v))
    return sorted(active), critical


def neighbors(v, nodes, edges):
    V = set(nodes)
    out = set()
    for a,b in edges:
        if a == v and b in V: out.add(b)
        if b == v and a in V: out.add(a)
    return sorted(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data-dir', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()

    C, R, vq, E = build(args.data_dir)
    n = len(R)
    p, q = vq[P], vq[Q]
    val, S = min_vertex_cut(n, E, p, q)
    if p != 5 or S != OUTER:
        raise RuntimeError((p, q, S))

    comps = components_without(n, E, S)
    pc = next(x for x in comps if p in x)
    left = set(pc) | set(S)
    ledges = induced_edges(left, E)

    # Reconstruct q0=q10 minimum separator and the q0-side bag.
    old = sorted(left)
    mp = {v:i for i,v in enumerate(old)}
    redges = [(mp[u],mp[v]) for u,v in ledges]
    cutval, cutnew = min_vertex_cut(len(old), redges, mp[0], mp[10])
    sep = [old[x] for x in cutnew]
    if cutval != 5 or sep != INNER:
        raise RuntimeError((cutval, sep))
    comps2 = components_without(len(old), redges, cutnew)
    comps2_old = [[old[x] for x in cc] for cc in comps2]
    q0comp = next(cc for cc in comps2_old if 0 in cc)
    q0bag = set(q0comp) | set(sep)
    q0edges = induced_edges(q0bag, ledges)

    u, v = TARGET
    Nu = neighbors(u, q0bag, q0edges)
    Nv = neighbors(v, q0bag, q0edges)
    union = sorted((set(Nu) | set(Nv)) - {u,v})
    union_edges = induced_edges(union, q0edges)

    checks = {}
    for name, Solver in [('Cadical195', Cadical195), ('Glucose4', Glucose4)]:
        checks[name] = {
            'q0bag_5colorable': sat_colorable(q0bag, q0edges, 5, Solver),
            'target_forced_distinct': forced_distinct(q0bag, q0edges, TARGET, Solver),
            'union_neighborhood_4colorable': sat_colorable(union, q0edges, 4, Solver),
            'union_neighborhood_5colorable': sat_colorable(union, q0edges, 5, Solver),
        }

    local_lemma_applies = all(
        x['q0bag_5colorable'] and x['target_forced_distinct'] and
        (not x['union_neighborhood_4colorable']) and x['union_neighborhood_5colorable']
        for x in checks.values()
    )

    core = []
    core_edges = []
    critical = []
    core_checks = {}
    if local_lemma_applies:
        core, critical = minimize_non4(union, q0edges)
        core_edges = induced_edges(core, q0edges)
        for name, Solver in [('Cadical195', Cadical195), ('Glucose4', Glucose4)]:
            core_checks[name] = {
                'four_colorable': sat_colorable(core, q0edges, 4, Solver),
                'five_colorable': sat_colorable(core, q0edges, 5, Solver),
            }

    # Also expose the graph-theoretic separation around the pair.
    oldq = sorted(q0bag)
    mq = {x:i for i,x in enumerate(oldq)}
    qe = [(mq[a],mq[b]) for a,b in q0edges]
    pair_cut_value, pair_cut_new = min_vertex_cut(len(oldq), qe, mq[u], mq[v])
    pair_cut = [oldq[x] for x in pair_cut_new]

    report = {
        'upstream_sha': UPSTREAM_SHA,
        'q0_side_bag_size': len(q0bag),
        'q0_side_edge_count': len(q0edges),
        'target_pair': list(TARGET),
        'q18_degree': len(Nu),
        'q256_degree': len(Nv),
        'q18_neighbors': Nu,
        'q256_neighbors': Nv,
        'union_neighborhood_size': len(union),
        'union_neighborhood_edge_count': len(union_edges),
        'solver_checks': checks,
        'union_neighborhood_five_chromatic_verified_both': local_lemma_applies,
        'local_disequality_lemma': (
            'In a proper 5-coloring, if u and v have the same color then every vertex in N(u) union N(v) '
            'must use one of the other four colors. Therefore chi(G[N(u) union N(v)]) >= 5 forces u != v.'
        ),
        'deletion_minimal_union_core': {
            'vertices': core,
            'vertex_count': len(core),
            'edges': [list(e) for e in core_edges],
            'edge_count': len(core_edges),
            'deletion_criticality': critical,
            'solver_checks': core_checks,
            'original_components': {str(x): C[R[x]] for x in core},
        },
        'pair_min_vertex_cut_value_in_q0_side': pair_cut_value,
        'pair_min_vertex_cut_qnodes': pair_cut,
        'interpretation': (
            'This isolates the only q0-side boundary disequality not explained by an edge between already-forced equality classes. '
            'If the union-neighborhood is 5-chromatic, the missing relation q18!=q256 has a direct graph-theoretic proof; '
            'the deletion-minimal non-4-colorable induced core is then a compact witness, not necessarily minimum-size.'
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({
        'target': TARGET,
        'degrees': [len(Nu), len(Nv)],
        'union_size': len(union),
        'union_edges': len(union_edges),
        'local_lemma_applies': local_lemma_applies,
        'core_size': len(core),
        'core_edges': len(core_edges),
        'pair_cut_value': pair_cut_value,
        'pair_cut': pair_cut,
        'solver_checks': checks,
        'core_checks': core_checks,
    }, indent=2))

if __name__ == '__main__':
    main()
