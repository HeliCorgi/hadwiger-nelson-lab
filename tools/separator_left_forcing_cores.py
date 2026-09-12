#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path

from pysat.solvers import Cadical195, Glucose4

from separator_interface import P, Q, UPSTREAM_SHA, build, components_without, min_vertex_cut

K = 5
FORCED_EQUAL_PAIRS = [(5, 6), (0, 10), (8, 9)]
SEPARATOR = [0, 6, 8, 9, 10, 266]
TRACKED = [5] + SEPARATOR


def activation_cnf(nodes, edges):
    ns = sorted(nodes)
    idx = {v: i for i, v in enumerate(ns)}
    color_vars = len(ns) * K

    def X(v, c):
        return idx[v] * K + c + 1

    def A(v):
        return color_vars + idx[v] + 1

    cls = []
    for v in ns:
        av = A(v)
        cls.append([-av] + [X(v, c) for c in range(K)])
        for a, b in combinations(range(K), 2):
            cls.append([-av, -X(v, a), -X(v, b)])
    node_set = set(ns)
    for u, v in edges:
        if u in node_set and v in node_set:
            for c in range(K):
                cls.append([-A(u), -A(v), -X(u, c), -X(v, c)])
    return ns, cls, X, A


def direct_cnf(nodes, edges, neq_pair=None):
    ns = sorted(nodes)
    idx = {v: i for i, v in enumerate(ns)}

    def X(v, c):
        return idx[v] * K + c + 1

    cls = []
    for v in ns:
        lits = [X(v, c) for c in range(K)]
        cls.append(lits)
        for a, b in combinations(lits, 2):
            cls.append([-a, -b])
    node_set = set(ns)
    for u, v in edges:
        if u in node_set and v in node_set:
            for c in range(K):
                cls.append([-X(u, c), -X(v, c)])
    if neq_pair is not None:
        u, v = neq_pair
        for c in range(K):
            cls.append([-X(u, c), -X(v, c)])
    return cls


def solve_direct(nodes, edges, pair, Solver):
    cls = direct_cnf(nodes, edges, pair)
    with Solver(bootstrap_with=cls) as s:
        return s.solve()


def verify_forced_equal(nodes, edges, pair):
    # SAT of base graph and UNSAT after forcing endpoints different.
    base = direct_cnf(nodes, edges, None)
    with Cadical195(bootstrap_with=base) as s:
        base_cadical = s.solve()
    with Glucose4(bootstrap_with=base) as s:
        base_glucose = s.solve()
    cadical_neq_sat = solve_direct(nodes, edges, pair, Cadical195)
    glucose_neq_sat = solve_direct(nodes, edges, pair, Glucose4)
    return {
        "base_5colorable_cadical195": base_cadical,
        "base_5colorable_glucose4": base_glucose,
        "neq_sat_cadical195": cadical_neq_sat,
        "neq_sat_glucose4": glucose_neq_sat,
        "forced_equal_verified_both": (
            base_cadical and base_glucose and not cadical_neq_sat and not glucose_neq_sat
        ),
    }


def induced_edges(nodes, edges):
    V = set(nodes)
    return [(u, v) for u, v in edges if u in V and v in V]


def degree_order(nodes, edges, reverse=False):
    V = set(nodes)
    deg = {v: 0 for v in V}
    for u, v in edges:
        if u in V and v in V:
            deg[u] += 1
            deg[v] += 1
    return sorted(V, key=lambda v: (deg[v], v), reverse=reverse)


def minimize_shared(left_nodes, edges, order_name):
    ns, cls, X, A = activation_cnf(left_nodes, edges)
    solvers = []
    for u, v in FORCED_EQUAL_PAIRS:
        extra = [[-X(u, c), -X(v, c)] for c in range(K)]
        solvers.append(Cadical195(bootstrap_with=cls + extra))

    try:
        active = set(left_nodes)
        protected = set(TRACKED)
        if order_name == "qnode-asc":
            order = sorted(active)
        elif order_name == "qnode-desc":
            order = sorted(active, reverse=True)
        elif order_name == "degree-asc":
            order = degree_order(active, edges, reverse=False)
        elif order_name == "degree-desc":
            order = degree_order(active, edges, reverse=True)
        else:
            raise ValueError(order_name)

        attempts = 0
        removed = []
        for v in order:
            if v in protected or v not in active:
                continue
            trial = active - {v}
            ass = [A(x) if x in trial else -A(x) for x in ns]
            attempts += 1
            if all(not s.solve(assumptions=ass) for s in solvers):
                active = trial
                removed.append(v)

        # Monotonicity means one exhaustive pass over the fixed order is enough:
        # if a vertex was not removable earlier, further deletions only relax the graph,
        # so it cannot become removable later while preserving UNSAT.
        critical = []
        for v in sorted(active - protected):
            trial = active - {v}
            ass = [A(x) if x in trial else -A(x) for x in ns]
            broken = []
            for pair, s in zip(FORCED_EQUAL_PAIRS, solvers):
                if s.solve(assumptions=ass):
                    broken.append(list(pair))
            critical.append({"vertex": v, "equalities_broken_if_deleted": broken})
            if not broken:
                raise RuntimeError(f"shared core not inclusion-minimal at {v}")

        return {
            "order": order_name,
            "active_vertices": sorted(active),
            "vertex_count": len(active),
            "edge_count": len(induced_edges(active, edges)),
            "removed_count": len(removed),
            "search_attempts": attempts,
            "deletion_criticality": critical,
        }
    finally:
        for s in solvers:
            s.delete()


def minimize_single(start_nodes, edges, pair, order_name="degree-asc"):
    ns, cls, X, A = activation_cnf(start_nodes, edges)
    u, v = pair
    extra = [[-X(u, c), -X(v, c)] for c in range(K)]
    sol = Cadical195(bootstrap_with=cls + extra)
    try:
        active = set(start_nodes)
        protected = {u, v}
        order = degree_order(active, edges, reverse=(order_name == "degree-desc"))
        for x in order:
            if x in protected or x not in active:
                continue
            trial = active - {x}
            ass = [A(z) if z in trial else -A(z) for z in ns]
            if not sol.solve(assumptions=ass):
                active = trial

        critical = []
        for x in sorted(active - protected):
            trial = active - {x}
            ass = [A(z) if z in trial else -A(z) for z in ns]
            sat = sol.solve(assumptions=ass)
            critical.append({"vertex": x, "neq_becomes_sat_if_deleted": sat})
            if not sat:
                raise RuntimeError((pair, x, "single core not inclusion-minimal"))
        return sorted(active), critical
    finally:
        sol.delete()


def contracted_tracked_graph(edges):
    classes = [
        [5, 6],
        [0, 10],
        [8, 9],
        [266],
    ]
    cls_of = {}
    for i, c in enumerate(classes):
        for v in c:
            cls_of[v] = i
    cedges = set()
    direct = []
    tracked_set = set(TRACKED)
    for u, v in edges:
        if u in tracked_set and v in tracked_set:
            direct.append([u, v])
            a, b = cls_of[u], cls_of[v]
            if a != b:
                cedges.add((min(a, b), max(a, b)))
    complete4 = set(combinations(range(4), 2))
    missing = sorted(complete4 - cedges)
    return {
        "classes": classes,
        "direct_edges_on_tracked_nodes": sorted(direct),
        "contracted_edges": [list(x) for x in sorted(cedges)],
        "missing_class_edges_from_K4": [list(x) for x in missing],
        "is_K4_minus_one_edge": len(cedges) == 5 and len(missing) == 1,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    C, R, vq, E = build(args.data_dir)
    n = len(R)
    p, q = vq[P], vq[Q]
    val, S = min_vertex_cut(n, E, p, q)
    if S != SEPARATOR or p != 5:
        raise RuntimeError((p, q, S))
    comps = components_without(n, E, S)
    pc = next(x for x in comps if p in x)
    left_nodes = set(pc) | set(S)

    orders = ["qnode-asc", "qnode-desc", "degree-asc", "degree-desc"]
    shared_trials = [minimize_shared(left_nodes, E, order) for order in orders]
    best = min(shared_trials, key=lambda x: (x["vertex_count"], x["edge_count"], x["order"]))
    shared_nodes = set(best["active_vertices"])

    shared_verification = {
        f"{u}-{v}": verify_forced_equal(shared_nodes, E, (u, v))
        for u, v in FORCED_EQUAL_PAIRS
    }

    single_cores = {}
    for pair in FORCED_EQUAL_PAIRS:
        best_single = None
        for order in ["degree-asc", "degree-desc"]:
            nodes, crit = minimize_single(shared_nodes, E, pair, order)
            rec = {
                "order": order,
                "vertices": nodes,
                "vertex_count": len(nodes),
                "edges": [list(e) for e in induced_edges(nodes, E)],
                "edge_count": len(induced_edges(nodes, E)),
                "deletion_criticality": crit,
                "verification": verify_forced_equal(nodes, E, pair),
                "original_components": {str(v): C[R[v]] for v in nodes},
            }
            if best_single is None or (rec["vertex_count"], rec["edge_count"]) < (
                best_single["vertex_count"],
                best_single["edge_count"],
            ):
                best_single = rec
        single_cores[f"{pair[0]}-{pair[1]}"] = best_single

    report = {
        "upstream_sha": UPSTREAM_SHA,
        "separator_qnodes": S,
        "p_qnode": p,
        "left_bag_original_vertex_count": len(left_nodes),
        "forced_equal_pairs": [list(x) for x in FORCED_EQUAL_PAIRS],
        "tracked_relation_graph_after_contraction": contracted_tracked_graph(E),
        "shared_core_trials": [
            {k: v for k, v in x.items() if k != "deletion_criticality"}
            for x in shared_trials
        ],
        "best_shared_core": best,
        "best_shared_core_edges": [list(e) for e in induced_edges(shared_nodes, E)],
        "best_shared_core_original_components": {str(v): C[R[v]] for v in sorted(shared_nodes)},
        "best_shared_core_verification": shared_verification,
        "individual_forcing_cores": single_cores,
        "interpretation": (
            "The p-side two-state boundary behavior is implied by three forced equalities "
            "p=q6, q0=q10, q8=q9 together with ordinary graph edges. Contracting those equalities "
            "on p plus the six separator nodes gives K4 minus exactly one edge; the missing edge is "
            "between the {q8,q9} class and q266, explaining the two boundary states. The extracted "
            "cores are inclusion-minimal induced subgraphs for the stated forcing property, not "
            "minimum-size gadgets. Final equality checks are repeated with both CaDiCaL195 and Glucose4."
        ),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "tracked_contraction": report["tracked_relation_graph_after_contraction"],
        "shared_trials": report["shared_core_trials"],
        "best_shared_core_size": best["vertex_count"],
        "individual_core_sizes": {k: v["vertex_count"] for k, v in single_cores.items()},
        "shared_verified": {k: v["forced_equal_verified_both"] for k, v in shared_verification.items()},
    }, indent=2))


if __name__ == "__main__":
    main()
