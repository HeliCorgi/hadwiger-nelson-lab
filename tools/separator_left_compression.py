#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path

from pysat.solvers import Glucose4

from separator_interface import (
    K,
    P,
    Q,
    UPSTREAM_SHA,
    build,
    components_without,
    min_vertex_cut,
    rgs,
)


def make_cnf(nodes, edges):
    ns = sorted(nodes)
    idx = {v: i for i, v in enumerate(ns)}
    clauses = []

    def X(v, c):
        return idx[v] * K + c + 1

    for v in ns:
        lits = [X(v, c) for c in range(K)]
        clauses.append(lits)
        for a, b in combinations(lits, 2):
            clauses.append([-a, -b])
    for u, v in edges:
        if u in idx and v in idx:
            for c in range(K):
                clauses.append([-X(u, c), -X(v, c)])
    return ns, clauses, X


def sat_pair_relation(sol, X, u, v):
    can_equal = any(sol.solve(assumptions=[X(u, c), X(v, c)]) for c in range(K))
    can_diff = any(
        sol.solve(assumptions=[X(u, a), X(v, b)])
        for a in range(K)
        for b in range(K)
        if a != b
    )
    if can_equal and can_diff:
        return "flexible"
    if can_equal:
        return "forced_equal"
    if can_diff:
        return "forced_different"
    raise RuntimeError((u, v, can_equal, can_diff))


def canonical_state(parts):
    mp = {}
    out = []
    for x in parts:
        if x not in mp:
            mp[x] = len(mp)
        out.append(mp[x])
    return tuple(out)


def relation_holds(state, i, j, kind):
    eq = state[i] == state[j]
    return eq if kind == "eq" else not eq


def minimal_relation_bases(all_states, allowed):
    allowed_set = set(allowed)
    common = []
    n = len(allowed[0])
    for i, j in combinations(range(n), 2):
        vals = {s[i] == s[j] for s in allowed}
        if len(vals) == 1:
            kind = "eq" if True in vals else "neq"
            common.append((i, j, kind))

    bad = [s for s in all_states if s not in allowed_set]
    excludes = []
    full = (1 << len(bad)) - 1
    for rel in common:
        m = 0
        for k, st in enumerate(bad):
            if not relation_holds(st, *rel):
                m |= 1 << k
        excludes.append(m)

    bases = []
    for size in range(1, len(common) + 1):
        for inds in combinations(range(len(common)), size):
            m = 0
            for i in inds:
                m |= excludes[i]
            if m == full:
                bases.append([common[i] for i in inds])
        if bases:
            break
    return common, bases


def is_k_colorable(vertices, edges, k):
    vertices = list(vertices)
    adj = {v: set() for v in vertices}
    for u, v in edges:
        if u in adj and v in adj:
            adj[u].add(v)
            adj[v].add(u)

    colors = {}

    def pick_vertex():
        uncolored = [v for v in vertices if v not in colors]
        if not uncolored:
            return None
        return max(
            uncolored,
            key=lambda v: (len({colors[w] for w in adj[v] if w in colors}), len(adj[v])),
        )

    def rec():
        v = pick_vertex()
        if v is None:
            return True
        used = {colors[w] for w in adj[v] if w in colors}
        for c in range(k):
            if c not in used:
                colors[v] = c
                if rec():
                    return True
                del colors[v]
        return False

    return rec()


def minimize_non3colorable(vertices, edges):
    cur = sorted(vertices)
    if is_k_colorable(cur, edges, 3):
        return None
    changed = True
    while changed:
        changed = False
        for v in list(cur):
            trial = [x for x in cur if x != v]
            if trial and not is_k_colorable(trial, edges, 3):
                cur = trial
                changed = True
                break
    return cur


def edge_list_on(vertices, edges):
    V = set(vertices)
    return [[u, v] for u, v in edges if u in V and v in V]


def common_neighborhood_witness(u, v, nodes, edges, C, R):
    adj = {x: set() for x in nodes}
    for a, b in edges:
        if a in adj and b in adj:
            adj[a].add(b)
            adj[b].add(a)
    cn = sorted(adj[u] & adj[v])
    cn_edges = [(a, b) for a, b in edges if a in set(cn) and b in set(cn)]
    non3 = not is_k_colorable(cn, cn_edges, 3)
    out = {
        "pair": [u, v],
        "common_neighbor_count": len(cn),
        "common_neighbors": cn,
        "common_neighborhood_not_3_colorable": non3,
    }
    if non3:
        w = minimize_non3colorable(cn, cn_edges)
        we = edge_list_on(w, cn_edges)
        out.update(
            {
                "minimal_vertex_witness": w,
                "minimal_witness_edges": we,
                "minimal_witness_edge_count": len(we),
                "minimal_witness_is_K4": len(w) == 4 and len(we) == 6,
                "minimal_witness_3_colorable": is_k_colorable(w, cn_edges, 3),
                "minimal_witness_4_colorable": is_k_colorable(w, cn_edges, 4),
                "minimal_witness_original_components": [C[R[x]] for x in w],
            }
        )
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    C, R, vq, E = build(args.data_dir)
    n = len(R)
    p, q = vq[P], vq[Q]
    cut_value, S = min_vertex_cut(n, E, p, q)
    comps = components_without(n, E, S)
    pc = next(x for x in comps if p in x)
    qc = next(x for x in comps if q in x)
    left_nodes = set(pc) | set(S)

    _, clauses, X = make_cnf(left_nodes, E)
    sol = Glucose4(bootstrap_with=clauses)
    try:
        left_states = []
        left_state_port_colors = {}
        for st in rgs(len(S)):
            ass = [X(v, st[i]) for i, v in enumerate(S)]
            if sol.solve(assumptions=ass):
                key = "".join(map(str, st))
                left_states.append(tuple(st))
                left_state_port_colors[key] = [
                    c for c in range(K) if sol.solve(assumptions=ass + [X(p, c)])
                ]

        tracked = [p] + list(S)
        tracked_relations = []
        for u, v in combinations(tracked, 2):
            tracked_relations.append(
                {
                    "pair": [u, v],
                    "relation": sat_pair_relation(sol, X, u, v),
                    "direct_edge": (min(u, v), max(u, v)) in set(E),
                }
            )
    finally:
        sol.delete()

    all_states = list(rgs(len(S)))
    common_relations, bases = minimal_relation_bases(all_states, left_states)
    boundary_edge_set = {
        (min(u, v), max(u, v)) for u, v in E if u in set(S) and v in set(S)
    }

    def rel_json(rel):
        i, j, kind = rel
        u, v = S[i], S[j]
        return {
            "positions": [i, j],
            "qnodes": [u, v],
            "kind": kind,
            "direct_boundary_edge": (min(u, v), max(u, v)) in boundary_edge_set,
        }

    forced_equal_pairs = [
        tuple(x["pair"])
        for x in tracked_relations
        if x["relation"] == "forced_equal"
    ]
    witnesses = [
        common_neighborhood_witness(u, v, left_nodes, E, C, R)
        for u, v in forced_equal_pairs
    ]

    report = {
        "upstream_sha": UPSTREAM_SHA,
        "quotient_vertices": n,
        "quotient_edges": len(E),
        "p_qnodes": [p, q],
        "separator_qnodes": S,
        "separator_original_components": [C[R[x]] for x in S],
        "cut_value": cut_value,
        "left_component_size_without_boundary": len(pc),
        "right_component_size_without_boundary": len(qc),
        "left_bag_size_with_boundary": len(left_nodes),
        "all_boundary_states": len(all_states),
        "left_extendable_states": ["".join(map(str, s)) for s in left_states],
        "left_state_port_colors": left_state_port_colors,
        "boundary_induced_edges": [list(e) for e in sorted(boundary_edge_set)],
        "tracked_nodes_p_plus_boundary": tracked,
        "tracked_pair_relations": tracked_relations,
        "common_boundary_pair_relations": [rel_json(r) for r in common_relations],
        "minimum_pairwise_relation_basis_size": len(bases[0]) if bases else 0,
        "minimum_pairwise_relation_bases": [
            [rel_json(r) for r in basis] for basis in bases[:100]
        ],
        "minimum_pairwise_relation_basis_count": len(bases),
        "forced_equal_common_neighborhood_witnesses": witnesses,
        "interpretation": (
            "The p-side boundary table is compressed into pairwise equality/inequality relations. "
            "Minimum relation bases are exact over all 202 canonical boundary partitions. "
            "For each globally forced-equal pair among p plus the six boundary qnodes, the script also "
            "tests the human-readable common-neighborhood lemma: a non-3-colorable common-neighborhood "
            "forces equality in every proper 5-coloring."
        ),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "left_extendable_states": report["left_extendable_states"],
                "left_state_port_colors": left_state_port_colors,
                "boundary_induced_edges": report["boundary_induced_edges"],
                "minimum_pairwise_relation_basis_size": report[
                    "minimum_pairwise_relation_basis_size"
                ],
                "minimum_pairwise_relation_basis_count": report[
                    "minimum_pairwise_relation_basis_count"
                ],
                "forced_equal_common_neighborhood_witnesses": witnesses,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
