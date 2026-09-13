#!/usr/bin/env python3
"""Closed cyclic multi-copy search for unconditional Hadwiger--Nelson candidates.

This is deliberately a new mechanism after Cycle 7. A complete exact base graph
is copied around a finite root-of-unity orbit. For an anchor pair (a,b), copy i
is placed by

    f_i(p) = R^i (p-a) + s_i,   s_{i+1}=s_i+R^i(b-a),

where R has finite order m. Hence f_i(b)=f_{i+1}(a) and s_m=s_0: the last/first
seam is present by construction. Copies are exact isometries in K2.

Floating point is used only to propose extra cross-copy unit pairs. Every edge
that reaches SAT is independently checked by exact K2 arithmetic. The screening
graph need not be induced; the selected candidate is intended for a subsequent
all-pairs exact completion before any D/B conclusion about the geometric point set.
An UNSAT screening subgraph, however, already consists solely of literal unit edges
and is therefore a legitimate A candidate (still requiring independent certificate).
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
from time import monotonic

import numpy as np
from scipy.spatial import cKDTree
from pysat.solvers import Cadical195, Glucose4

from hn_exact import K2, ONE, Z0, zpow, unit_modulus
from hn_unconditional_scan import color_cnf, valid_coloring, write_json

ZERO = K2(Z0)


def pack(z: K2) -> dict:
    return {"a": z.a, "b": z.b, "den": z.den}


def canonical_coloring(colors):
    remap = {}
    nxt = 0
    out = []
    for c in colors:
        if c not in remap:
            remap[c] = nxt
            nxt += 1
        out.append(remap[c])
    return tuple(out)


def choose_anchors(xy: np.ndarray, edges, count: int, seed: int):
    """Deterministic geometric portfolio, not an exhaustive anchor search."""
    n = len(xy)
    all_pairs = []
    for i in range(n):
        d = xy[i + 1:] - xy[i]
        ds = np.sqrt(np.einsum("ij,ij->i", d, d))
        all_pairs.extend((float(dist), i, i + 1 + j) for j, dist in enumerate(ds))
    all_pairs.sort()

    rng = random.Random(seed)
    chosen = []
    seen = set()

    def add(a, b, source):
        if a > b:
            a, b = b, a
        if a == b or (a, b) in seen or len(chosen) >= count:
            return
        seen.add((a, b))
        chosen.append({"pair": [a, b], "source": source,
                       "distance_float": float(np.linalg.norm(xy[a] - xy[b]))})

    for _, a, b in all_pairs[: max(4, count // 3)]:
        add(a, b, "short-distance")

    edge_list = sorted(tuple(map(int, e)) for e in edges)
    if edge_list:
        idx = list(range(len(edge_list)))
        rng.shuffle(idx)
        for k in idx[: max(4, count // 3)]:
            add(*edge_list[k], "unit-edge")

    need = max(1, count - len(chosen))
    if all_pairs:
        for q in np.linspace(0.05, 0.95, need):
            k = min(len(all_pairs) - 1, int(q * (len(all_pairs) - 1)))
            _, a, b = all_pairs[k]
            add(a, b, "distance-quantile")

    while len(chosen) < count:
        a, b = sorted(rng.sample(range(n), 2))
        add(a, b, "deterministic-random")
    return chosen


def build_ring(base_pts, base_edges, anchor, order):
    if 30 % order:
        raise ValueError(f"order {order} must divide 30 for zeta30 orbit")
    a, b = anchor
    R = zpow(30 // order)
    rot = ONE
    shift = ZERO
    delta = base_pts[b] - base_pts[a]

    point_index = {}
    points = []
    copy_maps = []
    inherited = set()

    for _copy_no in range(order):
        cmap = []
        for p in base_pts:
            q = rot * (p - base_pts[a]) + shift
            gi = point_index.get(q)
            if gi is None:
                gi = len(points)
                point_index[q] = gi
                points.append(q)
            cmap.append(gi)
        copy_maps.append(cmap)
        for u, v in base_edges:
            x, y = cmap[u], cmap[v]
            if x != y:
                inherited.add((min(x, y), max(x, y)))
        shift = shift + rot * delta
        rot = rot * R

    assert shift == ZERO, "cyclic seam failed to close"
    assert rot == ONE, "rotation did not close"
    for i in range(order):
        assert copy_maps[i][b] == copy_maps[(i + 1) % order][a]
    return points, inherited, copy_maps


def discover_exact_cross_edges(points, inherited, tolerance):
    """Float-near proposal followed by exact unit validation.

    This is a screening edge set only. It is never labelled induced/complete.
    """
    xy = np.array([[p.emb().real, p.emb().imag] for p in points], dtype=np.float64)
    tree = cKDTree(xy)
    pairs = tree.query_pairs(r=1.0 + tolerance, output_type="ndarray")
    if not len(pairs):
        return set(inherited), set(), {"float_near_pairs": 0, "exact_checked_proposals": 0}
    d = xy[pairs[:, 0]] - xy[pairs[:, 1]]
    d2 = np.einsum("ij,ij->i", d, d)
    pairs = pairs[d2 >= (1.0 - tolerance) ** 2]
    added = set()
    for u0, v0 in pairs:
        u, v = int(u0), int(v0)
        e = (u, v) if u < v else (v, u)
        if e in inherited:
            continue
        if unit_modulus(points[u] - points[v]):
            added.add(e)
    edges = set(inherited)
    edges.update(added)
    assert all(unit_modulus(points[u] - points[v]) for u, v in edges)
    return edges, added, {"float_near_pairs": int(len(pairs)),
                          "exact_checked_proposals": int(len(pairs))}


def solve_once(cls, clauses, n, edges, conflicts, phases=None, assumptions=()):
    with cls(bootstrap_with=clauses) as solver:
        solver.conf_budget(conflicts)
        if phases is not None:
            solver.set_phases(phases)
        ans = solver.solve_limited(assumptions=list(assumptions))
        if ans is not True:
            return ans, None
        positive = set(x for x in solver.get_model() if x > 0)
        colors = [next(c for c in range(5) if v * 5 + c + 1 in positive) for v in range(n)]
        assert valid_coloring(colors, n, edges)
        return True, colors


def sample_models(n, edges, count, conflicts, seed, first_model=None):
    clauses = color_cnf(n, sorted(edges))
    rng = random.Random(seed)
    models = []
    canonical_seen = set()
    if first_model is not None:
        can = canonical_coloring(first_model)
        canonical_seen.add(can)
        models.append(list(first_model))

    with Cadical195(bootstrap_with=clauses) as solver:
        attempts = 0
        while len(models) < count and attempts < max(20, 8 * count):
            attempts += 1
            solver.conf_budget(conflicts)
            phases = [v * 5 + rng.randrange(5) + 1 for v in range(n)]
            solver.set_phases(phases)
            ans = solver.solve_limited()
            if ans is not True:
                if ans is False:
                    break
                continue
            pos = set(x for x in solver.get_model() if x > 0)
            c = [next(k for k in range(5) if v * 5 + k + 1 in pos) for v in range(n)]
            assert valid_coloring(c, n, edges)
            can = canonical_coloring(c)
            solver.add_clause([-(v * 5 + c[v] + 1) for v in range(n)])
            if can not in canonical_seen:
                canonical_seen.add(can)
                models.append(c)
    return models


def signature_stats(models, n):
    if not models:
        return {"models": 0, "distinct_signatures": 0,
                "remaining_unseparated_pairs": n * (n - 1) // 2,
                "remaining_pair_ratio": 1.0, "max_signature_block": n}
    sigs = [bytes(model[v] for model in models) for v in range(n)]
    counts = Counter(sigs)
    remaining = sum(k * (k - 1) // 2 for k in counts.values())
    total = n * (n - 1) // 2
    return {"models": len(models), "distinct_signatures": len(counts),
            "remaining_unseparated_pairs": int(remaining),
            "remaining_pair_ratio": (remaining / total if total else 0.0),
            "max_signature_block": max(counts.values(), default=0)}


def candidate_key(record):
    s = record.get("signature_stats") or {}
    return (float(s.get("remaining_pair_ratio", -1.0)),
            int(s.get("max_signature_block", -1)),
            int(record.get("added_cross_edges", -1)),
            -int(record.get("vertices", 10**9)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--graph", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--orders", default="3,5,6")
    ap.add_argument("--anchor-count", type=int, default=18)
    ap.add_argument("--geometry-keep", type=int, default=4)
    ap.add_argument("--sample-models", type=int, default=8)
    ap.add_argument("--conflicts", type=int, default=600_000)
    ap.add_argument("--float-tolerance", type=float, default=3e-7)
    ap.add_argument("--seed", type=int, default=20260914)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    started = monotonic()

    raw = args.graph.read_bytes()
    data = json.loads(raw)
    base_pts = [K2(p["a"], p["b"], p["den"]) for p in data["pts"]]
    base_edges = sorted({tuple(map(int, e)) for e in data["edges"]})
    assert len(set(base_pts)) == len(base_pts)
    assert all(unit_modulus(base_pts[u] - base_pts[v]) for u, v in base_edges)
    xy = np.array([[p.emb().real, p.emb().imag] for p in base_pts], dtype=np.float64)
    orders = [int(x) for x in args.orders.split(",") if x.strip()]
    assert all(o >= 3 and 30 % o == 0 for o in orders)

    anchors = choose_anchors(xy, base_edges, args.anchor_count, args.seed)
    write_json(args.out_dir / "ANCHORS.json", {"base_graph_sha256": hashlib.sha256(raw).hexdigest(),
                                                "anchors": anchors, "orders": orders})

    geometry = []
    for order in orders:
        for row in anchors:
            a, b = row["pair"]
            points, inherited, _ = build_ring(base_pts, base_edges, (a, b), order)
            edges, added, proposal = discover_exact_cross_edges(points, inherited, args.float_tolerance)
            rec = {"order": order, "anchor": [a, b], "anchor_source": row["source"],
                   "anchor_distance_float": row["distance_float"], "vertices": len(points),
                   "inherited_edges": len(inherited), "added_cross_edges": len(added),
                   "screen_edges": len(edges), **proposal,
                   "screen_edges_all_exact_unit": True, "screen_induced_complete": False}
            geometry.append(rec)
            print(json.dumps({"stage": "geometry", **rec}, sort_keys=True), flush=True)
    write_json(args.out_dir / "GEOMETRY_SCREEN.json", {"records": geometry})

    keep = []
    for order in orders:
        rows = [r for r in geometry if r["order"] == order]
        rows.sort(key=lambda r: (r["added_cross_edges"], -r["vertices"]), reverse=True)
        keep.extend(rows[: args.geometry_keep])

    evaluated = []
    selected_graph = None
    a_candidate = None
    for idx, rec0 in enumerate(keep):
        order = rec0["order"]
        a, b = rec0["anchor"]
        points, inherited, _ = build_ring(base_pts, base_edges, (a, b), order)
        edges, _added, _ = discover_exact_cross_edges(points, inherited, args.float_tolerance)
        n = len(points)
        edge_list = sorted(edges)
        clauses = color_cnf(n, edge_list)
        phases = [v * 5 + ((args.seed + 17 * idx + v) % 5) + 1 for v in range(n)]
        ca, model = solve_once(Cadical195, clauses, n, edge_list, args.conflicts, phases)
        rec = dict(rec0)
        rec["cadical195"] = "SAT" if ca is True else "UNSAT" if ca is False else "UNKNOWN"
        if ca is False:
            gl, _ = solve_once(Glucose4, clauses, n, edge_list, args.conflicts * 2)
            rec["glucose4"] = "SAT" if gl is True else "UNSAT" if gl is False else "UNKNOWN"
            if gl is False:
                rec["classification"] = "A_CANDIDATE_EXACT_SUBGRAPH_DUAL_UNSAT"
                a_candidate = rec
                selected_graph = {"pts": [pack(p) for p in points], "edges": [list(e) for e in edge_list],
                                  "construction": "closed cyclic multi-copy screening subgraph",
                                  "base_graph_sha256": hashlib.sha256(raw).hexdigest(),
                                  "order": order, "anchor": [a, b],
                                  "no_conditional_constraints": True,
                                  "all_saved_edges_exact_unit": True,
                                  "induced_unit_edge_completion_pending": True}
                evaluated.append(rec)
                break
        elif ca is True:
            models = sample_models(n, edge_list, args.sample_models, max(100_000, args.conflicts // 2),
                                   args.seed + 1000 + idx, first_model=model)
            rec["signature_stats"] = signature_stats(models, n)
            rec["classification"] = "SAT_SCREENING_CANDIDATE"
        else:
            rec["classification"] = "SCREENING_UNKNOWN"
        evaluated.append(rec)
        print(json.dumps({"stage": "sat", **rec}, sort_keys=True), flush=True)

    if selected_graph is None:
        sat_rows = [r for r in evaluated if r.get("cadical195") == "SAT"]
        if sat_rows:
            best = max(sat_rows, key=candidate_key)
        else:
            best = max(keep, key=lambda r: (r["added_cross_edges"], -r["vertices"]))
        a, b = best["anchor"]
        points, inherited, _ = build_ring(base_pts, base_edges, (a, b), best["order"])
        edges, _, _ = discover_exact_cross_edges(points, inherited, args.float_tolerance)
        selected_graph = {"pts": [pack(p) for p in points], "edges": [list(e) for e in sorted(edges)],
                          "construction": "closed cyclic multi-copy selected for exact completion",
                          "base_graph_sha256": hashlib.sha256(raw).hexdigest(),
                          "order": best["order"], "anchor": [a, b],
                          "selection_objective": "maximize sampled 5-coloring signature rigidity; cross-edge count secondary",
                          "no_conditional_constraints": True,
                          "all_saved_edges_exact_unit": True,
                          "induced_unit_edge_completion_pending": True}
        selection = best
    else:
        selection = a_candidate

    write_json(args.out_dir / "SAT_SCREEN.json", {"evaluated": evaluated})
    write_json(args.out_dir / "SELECTED.json", {"selection": selection,
                                                 "dual_unsat_screening_subgraph": a_candidate is not None,
                                                 "elapsed_seconds": round(monotonic() - started, 3),
                                                 "scope": "finite closed-copy portfolio; not exhaustive"})
    write_json(args.out_dir / "SELECTED_GRAPH.json", selected_graph)
    print(json.dumps({"selected": selection, "vertices": len(selected_graph["pts"]),
                      "edges": len(selected_graph["edges"]),
                      "elapsed_seconds": round(monotonic() - started, 3)}, indent=2), flush=True)


if __name__ == "__main__":
    main()
