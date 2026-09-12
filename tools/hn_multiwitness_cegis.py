#!/usr/bin/env python3
"""Cycle-7 unconditional multi-witness CEGIS over exact unit-distance points.

Goal: stop chasing one 5-coloring at a time.  Starting from a verified exact
unit-distance graph and many proper 5-colorings, propose new *actual planar
points* which are unit distance from at least ``min_contacts`` old points.
A candidate kills a witness if its unit-neighbor colors already use all five
colors.  Greedy max-coverage chooses a small batch that kills many witnesses at
once.  The enlarged literal unit-distance graph is then solved unconditionally.

Floating point is used only to cluster/propose circle-intersection locations.
Every selected point is reconstructed in K2 from three old exact centers, every
edge added to the graph is checked by exact ``unit_modulus``, and SAT never sees
C88, quotient equalities, palette assumptions, or any other conditional input.

Scope: the candidate pool is one circle-intersection round over the supplied
base points, with a quantized float clustering heuristic.  Failure to find a
forcing graph is D only for this tested family; it is not an exhaustive theorem
about all unit-distance constructions.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import itertools
import json
import math
from pathlib import Path
import random
import tempfile
from time import monotonic

import numpy as np
import sympy as sp
from scipy.spatial import cKDTree
from pysat.solvers import Cadical195, Glucose4

from hn_exact import K2, Z0, unit_modulus
from hn_unconditional_scan import color_cnf, valid_coloring, write_json


def pack_point(z: K2) -> dict:
    return {"a": z.a, "b": z.b, "den": z.den}


def inverse(x: K2) -> K2:
    basis = []
    for j in range(16):
        a = [0] * 8
        b = [0] * 8
        (a if j < 8 else b)[j % 8] = 1
        basis.append(K2(a, b))
    cols = []
    for bb in basis:
        p = x * bb
        cols.append([sp.Rational(v, p.den) for v in p.a + p.b])
    values = sp.Matrix(16, 16, lambda i, j: cols[j][i]).inv()[:, 0]
    den = math.lcm(*(int(v.q) for v in values))
    ints = [int(v * den) for v in values]
    result = K2(ints[:8], ints[8:], den)
    assert (result * x).is_one()
    return result


def circumcenter(a: K2, b: K2, c: K2) -> K2 | None:
    u = b - a
    v = c - a
    det = u.conj() * v - v.conj() * u
    if det == K2(Z0):
        return None
    return a + (u * u.conj() * v - v * v.conj() * u) * inverse(det)


def _pack_xy(q: np.ndarray) -> np.ndarray:
    ux = (q[:, 0] & 0xFFFFFFFF).astype(np.uint64)
    uy = (q[:, 1] & 0xFFFFFFFF).astype(np.uint64)
    return (ux << np.uint64(32)) | uy


def _unpack_key(key: int, scale: float) -> tuple[float, float]:
    x = (key >> 32) & 0xFFFFFFFF
    y = key & 0xFFFFFFFF
    if x >= 1 << 31:
        x -= 1 << 32
    if y >= 1 << 31:
        y -= 1 << 32
    return x / scale, y / scale


def circle_keys_for_pairs(xy: np.ndarray, pairs: np.ndarray, scale: float):
    a = xy[pairs[:, 0]]
    b = xy[pairs[:, 1]]
    d = b - a
    r2 = np.einsum("ij,ij->i", d, d)
    good = (r2 > 1e-14) & (r2 <= 4.00000004)
    pairs = pairs[good]
    a = a[good]
    b = b[good]
    d = d[good]
    r2 = r2[good]
    middle = (a + b) * 0.5
    h = np.sqrt(np.maximum(0.0, 1.0 / r2 - 0.25))
    arm = np.column_stack((-d[:, 1], d[:, 0])) * h[:, None]
    for pos in (middle + arm, middle - arm):
        q = np.rint(pos * scale).astype(np.int64)
        yield _pack_xy(q), pairs


def propose_candidates(base_pts, xy, min_contacts, scale, tmp_dir, progress):
    started = monotonic()
    tree = cKDTree(xy)
    pairs = tree.query_pairs(r=2.00000001, output_type="ndarray")
    progress("pair_enumeration", {"pairs_with_float_distance_le_2": int(len(pairs))})

    total = 2 * len(pairs)
    key_path = Path(tmp_dir) / "intersection_keys.u64"
    keys_mm = np.memmap(key_path, dtype=np.uint64, mode="w+", shape=(total,))
    chunk = 500_000
    off = 0
    for s in range(0, len(pairs), chunk):
        p = pairs[s:s + chunk]
        for kk, _ in circle_keys_for_pairs(xy, p, scale):
            keys_mm[off:off + len(kk)] = kk
            off += len(kk)
    keys_mm.flush()
    keys = np.asarray(keys_mm[:off])
    keys.sort()

    min_mult = min_contacts * (min_contacts - 1) // 2
    arr = np.asarray(keys)
    changes = np.r_[True, arr[1:] != arr[:-1], True]
    boundaries = np.flatnonzero(changes)
    counts = np.diff(boundaries)
    starts = boundaries[:-1]
    keep = counts >= min_mult
    high_keys = np.array(arr[starts[keep]], dtype=np.uint64)
    high_counts = np.array(counts[keep], dtype=np.int64)

    approx_xy = np.array([_unpack_key(int(k), scale) for k in high_keys], dtype=np.float64)
    nearest, _ = tree.query(approx_xy, k=1, workers=-1)
    newish = nearest >= 2e-6
    high_keys = high_keys[newish]
    high_counts = high_counts[newish]
    approx_xy = approx_xy[newish]

    order = np.argsort(high_keys)
    sorted_high = high_keys[order]
    key_to_idx = {int(k): i for i, k in enumerate(high_keys.tolist())}
    neighbor_sets = [set() for _ in range(len(high_keys))]
    hit_occurrences = 0
    for s in range(0, len(pairs), chunk):
        p0 = pairs[s:s + chunk]
        for kk, p in circle_keys_for_pairs(xy, p0, scale):
            si = np.searchsorted(sorted_high, kk)
            in_range = si < len(sorted_high)
            rows0 = np.flatnonzero(in_range)
            if not len(rows0):
                continue
            rows = rows0[sorted_high[si[rows0]] == kk[rows0]]
            for row in rows:
                idx = key_to_idx[int(kk[row])]
                u, v = map(int, p[row])
                neighbor_sets[idx].add(u)
                neighbor_sets[idx].add(v)
                hit_occurrences += 1

    proposed = []
    for i, ns in enumerate(neighbor_sets):
        if len(ns) >= min_contacts:
            proposed.append({
                "key": int(high_keys[i]),
                "multiplicity": int(high_counts[i]),
                "approx_xy": approx_xy[i].tolist(),
                "approx_neighbors": sorted(ns),
            })
    proposed.sort(key=lambda c: (-len(c["approx_neighbors"]), -c["multiplicity"], c["key"]))
    progress("float_proposals", {
        "high_multiplicity_newish_keys": int(len(high_keys)),
        "proposal_count_with_enough_distinct_centers": len(proposed),
        "hit_occurrences": int(hit_occurrences),
        "contact_histogram": dict(Counter(len(c["approx_neighbors"]) for c in proposed)),
        "elapsed_seconds": round(monotonic() - started, 3),
    })
    try:
        del keys_mm
        key_path.unlink(missing_ok=True)
    except Exception:
        pass
    return proposed


def exactify_candidates(proposed, base_pts, xy, min_contacts, progress):
    started = monotonic()
    known = set(base_pts)
    exact = []
    seen = set()
    for row_no, c in enumerate(proposed):
        ns = c["approx_neighbors"]
        approx = complex(c["approx_xy"][0], c["approx_xy"][1])
        point = None
        tried = 0
        for i, j, k in itertools.combinations(ns, 3):
            af, bf, cf = xy[[i, j, k]]
            if abs(np.linalg.det(np.array([bf - af, cf - af]))) < 1e-9:
                continue
            q = circumcenter(base_pts[i], base_pts[j], base_pts[k])
            tried += 1
            if q is not None and abs(q.emb() - approx) <= 2e-5:
                point = q
                break
            if tried >= 24:
                break
        if point is None or point in known or point in seen:
            continue
        exact_neighbors = [v for v in ns if unit_modulus(point - base_pts[v])]
        if len(exact_neighbors) < min_contacts:
            continue
        seen.add(point)
        exact.append({
            "point": point,
            "base_neighbors_hint_exact": sorted(exact_neighbors),
            "approx_xy": c["approx_xy"],
            "multiplicity": c["multiplicity"],
            "key": c["key"],
            "extra_neighbors": [],
        })
        if len(exact) % 1000 == 0:
            progress("exactify_progress", {"processed": row_no + 1, "exact_candidates": len(exact)})
    progress("exact_candidates", {
        "exact_candidate_count": len(exact),
        "elapsed_seconds": round(monotonic() - started, 3),
    })
    return exact


def load_colorings(path: Path, n: int, edges):
    rows = []
    for line_no, line in enumerate(path.read_text().splitlines(), 1):
        s = line.strip()
        if not s:
            continue
        if len(s) != n or any(ch not in "01234" for ch in s):
            raise ValueError(f"bad coloring line {line_no}")
        rows.append([ord(ch) - 48 for ch in s])
    colors = np.asarray(rows, dtype=np.uint8)
    if len(colors) == 0:
        raise ValueError("no witness colorings")
    eu = np.asarray([e[0] for e in edges], dtype=np.int64)
    ev = np.asarray([e[1] for e in edges], dtype=np.int64)
    for s in range(0, len(colors), 64):
        block = colors[s:s + 64]
        if np.any(block[:, eu] == block[:, ev]):
            raise ValueError(f"input witness coloring invalid in block starting {s}")
    return colors


def kill_mask(candidate, colors: np.ndarray) -> int:
    neighbors = candidate["base_neighbors_hint_exact"] + candidate["extra_neighbors"]
    if len(neighbors) < 5:
        return 0
    vals = colors[:, neighbors]
    used = np.bitwise_or.reduce((1 << vals).astype(np.uint8), axis=1)
    hit = np.flatnonzero(used == 31)
    mask = 0
    for i in hit.tolist():
        mask |= 1 << i
    return mask


def greedy_cover(candidates, active_indices, colors, max_batch):
    masks = {}
    for idx in active_indices:
        m = kill_mask(candidates[idx], colors)
        if m:
            masks[idx] = m
    uncovered = (1 << len(colors)) - 1
    chosen = []
    while uncovered and len(chosen) < max_batch and masks:
        best_idx = None
        best_gain = 0
        best_total = 0
        for idx, mask in masks.items():
            gain = (mask & uncovered).bit_count()
            total = mask.bit_count()
            if (gain, total, -idx) > (best_gain, best_total, -(best_idx if best_idx is not None else 10**18)):
                best_idx, best_gain, best_total = idx, gain, total
        if best_idx is None or best_gain == 0:
            break
        chosen.append({"candidate_index": best_idx, "gain": best_gain, "total_kills": best_total})
        uncovered &= ~masks[best_idx]
        masks.pop(best_idx, None)
    return chosen, uncovered.bit_count(), len(masks)


def full_base_neighbors(point, base_pts):
    return [i for i, p in enumerate(base_pts) if unit_modulus(point - p)]


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


def solve_limited(cls, clauses, n, edges, conflicts, assumptions=()):
    with cls(bootstrap_with=clauses) as solver:
        solver.conf_budget(conflicts)
        ans = solver.solve_limited(assumptions=list(assumptions))
        if ans is not True:
            return ans, None
        positive = set(solver.get_model())
        colors = [next(c for c in range(5) if v * 5 + c + 1 in positive) for v in range(n)]
        assert valid_coloring(colors, n, edges)
        return True, colors


def sample_models(n, edges, target, conflicts, seed):
    clauses = color_cnf(n, edges)
    rng = random.Random(seed)
    raw_seen = set()
    canonical_seen = set()
    models = []
    with Cadical195(bootstrap_with=clauses) as solver:
        attempts = 0
        while len(models) < target and attempts < max(30, target * 12):
            attempts += 1
            solver.conf_budget(conflicts)
            solver.set_phases([v * 5 + rng.randrange(5) + 1 for v in range(n)])
            ans = solver.solve_limited()
            if ans is None or ans is False:
                break
            positive = set(solver.get_model())
            colors = tuple(next(c for c in range(5) if v * 5 + c + 1 in positive) for v in range(n))
            assert valid_coloring(colors, n, edges)
            if colors not in raw_seen:
                raw_seen.add(colors)
                can = canonical_coloring(colors)
                if can not in canonical_seen:
                    canonical_seen.add(can)
                    models.append(list(colors))
                solver.add_clause([-(v * 5 + colors[v] + 1) for v in range(n)])
    return models, attempts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--graph", type=Path, required=True)
    ap.add_argument("--colorings", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--min-contacts", type=int, default=5)
    ap.add_argument("--cluster-scale", type=float, default=1e7)
    ap.add_argument("--max-rounds", type=int, default=8)
    ap.add_argument("--max-batch", type=int, default=16)
    ap.add_argument("--models-per-round", type=int, default=16)
    ap.add_argument("--conflicts", type=int, default=5_000_000)
    ap.add_argument("--seed", type=int, default=20260913)
    ap.add_argument("--expected-graph-sha256")
    ap.add_argument("--expected-colorings-sha256")
    args = ap.parse_args()

    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    started = monotonic()
    events = []

    def progress(kind, data):
        event = {"event": kind, "elapsed_seconds": round(monotonic() - started, 3), **data}
        events.append(event)
        write_json(out / "PROGRESS.json", {"events": events})
        print(json.dumps(event, sort_keys=True), flush=True)

    graph_bytes = args.graph.read_bytes()
    color_bytes = args.colorings.read_bytes()
    graph_sha = hashlib.sha256(graph_bytes).hexdigest()
    colors_sha = hashlib.sha256(color_bytes).hexdigest()
    if args.expected_graph_sha256:
        assert graph_sha == args.expected_graph_sha256, (graph_sha, args.expected_graph_sha256)
    if args.expected_colorings_sha256:
        assert colors_sha == args.expected_colorings_sha256, (colors_sha, args.expected_colorings_sha256)

    data = json.loads(graph_bytes)
    base_pts = [K2(p["a"], p["b"], p["den"]) for p in data["pts"]]
    base_n = len(base_pts)
    base_edges = sorted({tuple(map(int, e)) for e in data["edges"]})
    assert len(set(base_pts)) == base_n
    assert all(unit_modulus(base_pts[u] - base_pts[v]) for u, v in base_edges)
    initial_colors = load_colorings(args.colorings, base_n, base_edges)
    progress("input_verified", {
        "base_vertices": base_n,
        "base_edges": len(base_edges),
        "initial_witnesses": int(len(initial_colors)),
        "graph_sha256": graph_sha,
        "colorings_sha256": colors_sha,
        "all_saved_edges_exact_unit": True,
        "all_input_colorings_proper": True,
    })

    xy = np.array([[z.emb().real, z.emb().imag] for z in base_pts], dtype=np.float64)
    with tempfile.TemporaryDirectory(prefix="hn-cycle7-") as td:
        proposed = propose_candidates(base_pts, xy, args.min_contacts, args.cluster_scale, td, progress)
    candidates = exactify_candidates(proposed, base_pts, xy, args.min_contacts, progress)
    if not candidates:
        result = {"status": "NO_EXACT_CANDIDATES", "classification": "D", "scope": "tested candidate family only"}
        write_json(out / "FINAL.json", result)
        return

    current_pts = list(base_pts)
    current_edges = list(base_edges)
    selected_candidate_indices = []
    remaining = set(range(len(candidates)))
    active_colors = initial_colors
    round_records = []
    final_status = "MAX_ROUNDS_REACHED"
    final_classification = "C"

    for round_no in range(args.max_rounds):
        if round_no > 0:
            for idx in remaining:
                c = candidates[idx]
                c["extra_neighbors"] = [
                    base_n + j for j, old_idx in enumerate(selected_candidate_indices)
                    if unit_modulus(c["point"] - candidates[old_idx]["point"])
                ]

        chosen, uncovered, positive_candidates = greedy_cover(candidates, sorted(remaining), active_colors, args.max_batch)
        if not chosen:
            final_status = "NO_POSITIVE_COVERAGE_CANDIDATE"
            final_classification = "D"
            round_records.append({
                "round": round_no,
                "active_witnesses": int(len(active_colors)),
                "chosen": [],
                "uncovered_witnesses": int(uncovered),
                "positive_candidates": int(positive_candidates),
            })
            break

        selected_this_round = []
        for item in chosen:
            idx = item["candidate_index"]
            c = candidates[idx]
            point = c["point"]
            base_neighbors = full_base_neighbors(point, base_pts)
            global_v = len(current_pts)
            assert point not in set(current_pts)
            edges_added = []
            for u in base_neighbors:
                current_edges.append((u, global_v))
                edges_added.append((u, global_v))
            for old_v in range(base_n, len(current_pts)):
                if unit_modulus(point - current_pts[old_v]):
                    current_edges.append((old_v, global_v))
                    edges_added.append((old_v, global_v))
            current_pts.append(point)
            selected_candidate_indices.append(idx)
            remaining.remove(idx)
            selected_this_round.append({
                **item,
                "global_vertex": global_v,
                "point": pack_point(point),
                "base_unit_neighbors": base_neighbors,
                "edges_added": [list(e) for e in edges_added],
            })

        current_edges = sorted(set(current_edges))
        n = len(current_pts)
        clauses = color_cnf(n, current_edges)
        ca_ans, ca_model = solve_limited(Cadical195, clauses, n, current_edges, args.conflicts)
        round_record = {
            "round": round_no,
            "active_witnesses": int(len(active_colors)),
            "chosen": selected_this_round,
            "uncovered_witnesses_before_sat": int(uncovered),
            "vertices_after": n,
            "edges_after": len(current_edges),
            "cadical195": "SAT" if ca_ans is True else "UNSAT" if ca_ans is False else "UNKNOWN",
        }
        progress("round_sat", {k: v for k, v in round_record.items() if k != "chosen"})

        if ca_ans is False:
            gl_ans, _ = solve_limited(Glucose4, clauses, n, current_edges, args.conflicts)
            round_record["glucose4"] = "SAT" if gl_ans is True else "UNSAT" if gl_ans is False else "UNKNOWN"
            round_records.append(round_record)
            if gl_ans is False:
                final_status = "FIVE_COLOR_UNSAT_DUAL_SOLVER"
                final_classification = "A_CANDIDATE_REQUIRES_CERTIFICATE"
            else:
                final_status = "CADICAL_UNSAT_NOT_CONFIRMED"
                final_classification = "C"
            break
        if ca_ans is None:
            round_records.append(round_record)
            final_status = "SAT_QUERY_UNKNOWN"
            final_classification = "C"
            break

        write_json(out / f"ROUND_{round_no:02d}_SAT_WITNESS.json", {"colors": ca_model})
        models, attempts = sample_models(n, current_edges, args.models_per_round, args.conflicts, args.seed + round_no + 1)
        if not models:
            models = [ca_model]
        active_colors = np.asarray(models, dtype=np.uint8)
        round_record["sampled_models"] = len(models)
        round_record["sampling_attempts"] = attempts
        round_records.append(round_record)
        final_status = "SAT_CONTINUE"
        final_classification = "C"
        write_json(out / "ROUNDS.json", round_records)

    graph_out = {
        "pts": [pack_point(p) for p in current_pts],
        "edges": [list(e) for e in current_edges],
        "construction": "Cycle 7 multi-witness max-coverage CEGIS over one new circle-intersection round from Cycle 6",
        "base_graph_sha256": graph_sha,
        "base_vertices": base_n,
        "new_vertices": len(current_pts) - base_n,
        "no_conditional_constraints": True,
        "distance_threshold": None,
    }
    write_json(out / "GRAPH.json", graph_out)
    write_json(out / "SELECTION.json", {
        "selected_candidate_indices": selected_candidate_indices,
        "rounds": round_records,
        "candidate_pool": {
            "float_proposals": len(proposed),
            "exact_candidates": len(candidates),
            "remaining_exact_candidates": len(remaining),
        },
    })
    final = {
        "status": final_status,
        "classification": final_classification,
        "base_vertices": base_n,
        "final_vertices": len(current_pts),
        "final_edges": len(current_edges),
        "selected_new_points": len(current_pts) - base_n,
        "rounds_completed": len(round_records),
        "initial_witnesses": int(len(initial_colors)),
        "all_added_edges_exact_unit_distance": True,
        "no_conditional_constraints": True,
        "candidate_family_scope": "one float-clustered circle-intersection round over supplied base points; retained selected points and edges exact",
        "elapsed_seconds": round(monotonic() - started, 3),
    }
    write_json(out / "FINAL.json", final)
    print(json.dumps(final, indent=2), flush=True)


if __name__ == "__main__":
    main()
