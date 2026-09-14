#!/usr/bin/env python3
"""Direct-A search by palette exhaustion on exact unit circles.

Given an exact, induced-complete unit-distance graph G, generate exact candidate
centers x in the same K2 field.  Adding x constrains x to avoid every color used
by its unit-neighborhood N(x).  If N(x) uses all five colors in a current proper
5-coloring, adding x kills that coloring immediately.

The CEGIS loop repeatedly:
  1. solves the current exact graph for a proper 5-coloring;
  2. chooses an unselected candidate center whose *exact* current neighborhood
     uses all five colors in that model;
  3. adds the center and every exact unit edge from it to all current vertices.

If the current graph becomes UNSAT, the output is only an A candidate and still
requires the repository's independent completion / solver-certificate protocol.
If no library candidate kills the current model, that is non-evidence.

Candidate generation is deliberately separate from the claim layer: centers are
formed as p+d where p is a graph point and d is an exact unit displacement taken
from a bounded direction dictionary.  Every retained candidate is then checked
against *all* base vertices with exact K2 unit_modulus before it can be used.
"""
from __future__ import annotations

import argparse
import hashlib
import heapq
import json
from collections import Counter
from itertools import combinations
from pathlib import Path

from pysat.solvers import Cadical195

from hn_exact import K2, unit_modulus
from hn_symmetry_sat_probe import extract
from hn_unconditional_scan import color_cnf, valid_coloring, write_json


def pack(x: K2):
    return {"a": x.a, "b": x.b, "den": x.den}


def neg(x: K2):
    return K2([-v for v in x.a], [-v for v in x.b], x.den)


def load_graph(path: Path):
    raw = path.read_bytes()
    d = json.loads(raw)
    pts = [K2(p["a"], p["b"], p["den"]) for p in d["pts"]]
    edges = sorted({tuple(map(int, e)) for e in d["edges"]})
    assert len(set(pts)) == len(pts)
    assert all(0 <= u < v < len(pts) for u, v in edges)
    assert all(unit_modulus(pts[u] - pts[v]) for u, v in edges)
    return raw, d, pts, edges


def load_models(path: Path | None, n: int, edges):
    if path is None:
        return []
    d = json.loads(path.read_text())
    models = d.get("models", d.get("colorings", []))
    out = []
    for c in models:
        c = list(map(int, c))
        assert valid_coloring(c, n, edges)
        out.append(c)
    return out


def unit_directions(pts, edges, vertex_limit: int):
    out = set()
    for u, v in edges:
        if u >= vertex_limit or v >= vertex_limit:
            continue
        d = pts[v] - pts[u]
        out.add(d)
        out.add(neg(d))
    assert out and all(unit_modulus(d) for d in out)
    return out


def build_candidates(pts, dirs, candidate_count: int, models):
    point_set = set(pts)
    known = Counter()
    for p in pts:
        for d in dirs:
            x = p + d
            if x not in point_set:
                known[x] += 1

    top = heapq.nlargest(candidate_count, known.items(), key=lambda kv: kv[1])
    candidates = []
    for x, known_count in top:
        neigh = [i for i, p in enumerate(pts) if unit_modulus(p - x)]
        assert neigh and len(neigh) >= known_count
        hist = Counter()
        min_colors = 5
        rainbow = 0
        for c in models:
            k = len({c[v] for v in neigh})
            hist[k] += 1
            min_colors = min(min_colors, k)
            if k == 5:
                rainbow += 1
        candidates.append({
            "point": x,
            "base_neighbors": neigh,
            "known_direction_neighbors": known_count,
            "exact_base_neighbors": len(neigh),
            "sample_min_colors": min_colors if models else None,
            "sample_rainbow_count": rainbow if models else None,
            "sample_histogram": dict(sorted(hist.items())),
        })

    # Prefer candidates already maximally constraining on validated witness models.
    candidates.sort(key=lambda z: (
        -(z["sample_min_colors"] if z["sample_min_colors"] is not None else -1),
        -(z["sample_rainbow_count"] if z["sample_rainbow_count"] is not None else -1),
        -z["exact_base_neighbors"],
        -z["known_direction_neighbors"],
        z["point"].den,
        tuple(z["point"].a), tuple(z["point"].b),
    ))
    return candidates


def add_vertex_clauses(solver, v: int):
    xs = [v * 5 + c + 1 for c in range(5)]
    solver.add_clause(xs)
    for a, b in combinations(xs, 2):
        solver.add_clause([-a, -b])


def add_edge_clauses(solver, u: int, v: int):
    for c in range(5):
        solver.add_clause([-(u * 5 + c + 1), -(v * 5 + c + 1)])


def semantic_sha(pts, edges):
    obj = {"pts": [pack(p) for p in pts], "edges": [list(e) for e in sorted(edges)]}
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--graph", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--witnesses", type=Path, default=None)
    ap.add_argument("--seed-coloring", type=Path, default=None)
    ap.add_argument("--direction-vertices", type=int, default=1192,
                    help="only edges wholly inside [0,N) contribute candidate directions")
    ap.add_argument("--candidate-count", type=int, default=160)
    ap.add_argument("--max-additions", type=int, default=24)
    a = ap.parse_args()
    a.out_dir.mkdir(parents=True, exist_ok=True)

    raw, gd, base_pts, base_edges = load_graph(a.graph)
    n0 = len(base_pts)
    assert 1 <= a.direction_vertices <= n0
    models = load_models(a.witnesses, n0, base_edges)
    dirs = unit_directions(base_pts, base_edges, a.direction_vertices)
    candidates = build_candidates(base_pts, dirs, a.candidate_count, models)

    seed = None
    if a.seed_coloring is not None:
        s = a.seed_coloring.read_text().strip()
        assert len(s) == n0 and all(ch in "01234" for ch in s)
        seed = [int(ch) for ch in s]
        assert valid_coloring(seed, n0, base_edges)

    cur_pts = list(base_pts)
    cur_edges = set(base_edges)
    selected = []
    records = []
    status = "ITERATION_LIMIT"
    final_colors = None

    with Cadical195(bootstrap_with=color_cnf(n0, base_edges)) as solver:
        if seed is not None and hasattr(solver, "set_phases"):
            solver.set_phases([v * 5 + seed[v] + 1 for v in range(n0)])

        for iteration in range(a.max_additions + 1):
            ans = solver.solve()
            if ans is False:
                status = "A_CANDIDATE_REQUIRES_INDEPENDENT_CONFIRMATION"
                final_colors = None
                break
            model = solver.get_model()
            colors = extract(model, len(cur_pts))
            assert valid_coloring(colors, len(cur_pts), sorted(cur_edges))
            final_colors = colors

            if iteration == a.max_additions:
                status = "ITERATION_LIMIT"
                break

            best = None
            for ci, cand in enumerate(candidates):
                if cand.get("selected"):
                    continue
                neigh = list(cand["base_neighbors"])
                x = cand["point"]
                # Added centers were not present during candidate precomputation.
                for j in range(n0, len(cur_pts)):
                    if unit_modulus(cur_pts[j] - x):
                        neigh.append(j)
                palette = sorted({colors[v] for v in neigh})
                if len(palette) != 5:
                    continue
                score = (len(neigh),
                         cand["sample_rainbow_count"] if cand["sample_rainbow_count"] is not None else -1,
                         cand["exact_base_neighbors"],
                         cand["known_direction_neighbors"])
                if best is None or score > best[0]:
                    best = (score, ci, neigh)

            if best is None:
                status = "NO_KILLER_IN_LIBRARY"
                break

            _, ci, neigh = best
            cand = candidates[ci]
            x = cand["point"]
            new_v = len(cur_pts)
            # Recompute against all current vertices, not just the screening neighborhood.
            exact_neigh = [j for j, p in enumerate(cur_pts) if unit_modulus(p - x)]
            assert set(neigh) == set(exact_neigh)
            assert len({colors[v] for v in exact_neigh}) == 5

            add_vertex_clauses(solver, new_v)
            for v in exact_neigh:
                u, w = sorted((v, new_v))
                cur_edges.add((u, w))
                add_edge_clauses(solver, u, w)
            cur_pts.append(x)
            cand["selected"] = True
            selected.append(ci)
            rec = {
                "iteration": iteration,
                "candidate_index": ci,
                "new_vertex": new_v,
                "point": pack(x),
                "exact_unit_neighbors": len(exact_neigh),
                "neighbor_vertices": exact_neigh,
                "killed_model_neighbor_colors": [colors[v] for v in exact_neigh],
                "sample_min_colors": cand["sample_min_colors"],
                "sample_rainbow_count": cand["sample_rainbow_count"],
                "sample_histogram": cand["sample_histogram"],
            }
            records.append(rec)
            print(json.dumps(rec), flush=True)
            if hasattr(solver, "set_phases"):
                solver.set_phases([v * 5 + colors[v] + 1 for v in range(len(colors))])

    # Every pair involving an added center was checked exactly against all prior points.
    checked_pairs = n0 * (n0 - 1) // 2
    for j in range(n0, len(cur_pts)):
        checked_pairs += j
    out = {
        "status": status,
        "classification": "A_CANDIDATE_REQUIRES_INDEPENDENT_CONFIRMATION" if status.startswith("A_CANDIDATE") else "C",
        "base_vertices": n0,
        "base_edges": len(base_edges),
        "vertices": len(cur_pts),
        "edges": len(cur_edges),
        "added_centers": len(cur_pts) - n0,
        "direction_vertices": a.direction_vertices,
        "unit_direction_count": len(dirs),
        "candidate_count": len(candidates),
        "validated_input_witnesses": len(models),
        "base_graph_file_sha256": hashlib.sha256(raw).hexdigest(),
        "semantic_pts_edges_sha256": semantic_sha(cur_pts, cur_edges),
        "all_added_center_pairs_exactly_checked": True,
        "unordered_pairs_covered_by_input_completion_plus_center_checks": checked_pairs,
        "records": records,
        "no_killer_or_iteration_limit_is_evidence": False,
    }
    write_json(a.out_dir / "PALETTE_CEGIS.json", out)
    write_json(a.out_dir / "SELECTED_GRAPH.json", {
        "pts": [pack(p) for p in cur_pts],
        "edges": [list(e) for e in sorted(cur_edges)],
        "construction": "palette-exhaustion center CEGIS",
        "all_saved_edges_exact_unit": True,
        "base_graph_was_induced_complete": bool(gd.get("induced_unit_edge_completion_pending") is False),
        "all_added_center_pairs_exactly_checked": True,
    })
    write_json(a.out_dir / "CANDIDATE_LIBRARY.json", {
        "candidates": [{k: (pack(v) if k == "point" else v) for k, v in c.items() if k != "selected"}
                       for c in candidates]
    })
    if final_colors is not None:
        assert valid_coloring(final_colors, len(cur_pts), sorted(cur_edges))
        (a.out_dir / "COLORING.txt").write_text("".join(map(str, final_colors)) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "records"}, indent=2))


if __name__ == "__main__":
    main()
