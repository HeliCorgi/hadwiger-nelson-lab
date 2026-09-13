#!/usr/bin/env python3
"""Probe a graph whose induced unit-edge set was completed by an exact all-pairs tool.

The script does not infer geometry completeness itself. It validates every supplied
edge as literal unit distance, solves ordinary 5-colorability, samples diverse proper
colorings, and then attacks any remaining same-color signature blocks with direct
pair-inequality SAT. UNKNOWN is never promoted to evidence.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import random
from time import monotonic

from pysat.solvers import Cadical195, Glucose4
from hn_exact import K2, unit_modulus
from hn_unconditional_scan import color_cnf, valid_coloring, write_json


def colors_from_model(model, n):
    pos = set(x for x in model if x > 0)
    return [next(c for c in range(5) if v * 5 + c + 1 in pos) for v in range(n)]


def canonical(colors):
    mp = {}
    nxt = 0
    out = []
    for c in colors:
        if c not in mp:
            mp[c] = nxt
            nxt += 1
        out.append(mp[c])
    return tuple(out)


def refine(blocks, colors):
    out = []
    for block in blocks:
        buckets = defaultdict(list)
        for v in block:
            buckets[colors[v]].append(v)
        out.extend(buckets.values())
    return out


def pairs_left(blocks):
    return sum(len(b) * (len(b) - 1) // 2 for b in blocks)


def solve_limited(cls, clauses, conflicts, assumptions=(), phases=None):
    with cls(bootstrap_with=clauses) as solver:
        solver.conf_budget(conflicts)
        if phases is not None:
            solver.set_phases(phases)
        ans = solver.solve_limited(assumptions=list(assumptions))
        return ans, None if ans is not True else solver.get_model()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--graph", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--sample-models", type=int, default=64)
    ap.add_argument("--pair-seconds", type=float, default=1200)
    ap.add_argument("--conflicts", type=int, default=1_000_000)
    ap.add_argument("--seed", type=int, default=20260914)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    started = monotonic()

    raw = args.graph.read_bytes()
    data = json.loads(raw)
    pts = [K2(p["a"], p["b"], p["den"]) for p in data["pts"]]
    edges = sorted({tuple(map(int, e)) for e in data["edges"]})
    n = len(pts)
    assert len(set(pts)) == n
    assert all(0 <= u < v < n for u, v in edges)
    assert all(unit_modulus(pts[u] - pts[v]) for u, v in edges)
    clauses = color_cnf(n, edges)

    ca, model = solve_limited(Cadical195, clauses, args.conflicts)
    result = {"graph_sha256": hashlib.sha256(raw).hexdigest(), "vertices": n, "edges": len(edges),
              "all_saved_edges_exact_unit": True, "no_conditional_constraints": True,
              "cadical195": "SAT" if ca is True else "UNSAT" if ca is False else "UNKNOWN"}
    if ca is False:
        gl, _ = solve_limited(Glucose4, clauses, args.conflicts * 2)
        result["glucose4"] = "SAT" if gl is True else "UNSAT" if gl is False else "UNKNOWN"
        result["classification"] = "A_CANDIDATE_REQUIRES_CERTIFICATE" if gl is False else "C"
        result["status"] = "FIVE_COLOR_DUAL_UNSAT" if gl is False else "SOLVER_DISAGREEMENT_OR_UNKNOWN"
        write_json(args.out_dir / "PROBE.json", result)
        print(json.dumps(result, indent=2))
        return
    if ca is None:
        result.update({"classification": "C", "status": "FIVE_COLOR_UNKNOWN"})
        write_json(args.out_dir / "PROBE.json", result)
        print(json.dumps(result, indent=2))
        return

    first = colors_from_model(model, n)
    assert valid_coloring(first, n, edges)
    blocks = [list(range(n))]
    models = []
    seen = set()
    progress = []

    def accept(c, origin):
        nonlocal blocks
        can = canonical(c)
        if can in seen:
            return False
        seen.add(can)
        models.append(c)
        blocks = refine(blocks, c)
        progress.append({"origin": origin, "models": len(models), "remaining_pairs": pairs_left(blocks),
                         "max_block": max(map(len, blocks), default=0)})
        return True

    accept(first, "initial_sat")
    rng = random.Random(args.seed)
    with Cadical195(bootstrap_with=clauses) as sampler:
        attempts = 0
        while len(models) < args.sample_models and attempts < max(100, 10 * args.sample_models):
            attempts += 1
            sampler.conf_budget(max(100_000, args.conflicts // 2))
            sampler.set_phases([v * 5 + rng.randrange(5) + 1 for v in range(n)])
            ans = sampler.solve_limited()
            if ans is not True:
                if ans is False:
                    break
                continue
            c = colors_from_model(sampler.get_model(), n)
            assert valid_coloring(c, n, edges)
            sampler.add_clause([-(v * 5 + c[v] + 1) for v in range(n)])
            accept(c, "sampled_sat")
            if not pairs_left(blocks):
                break

    pair_records = []
    deadline = monotonic() + args.pair_seconds
    if pairs_left(blocks):
        with Cadical195(bootstrap_with=clauses) as solver:
            while pairs_left(blocks) and monotonic() < deadline:
                block = max((b for b in blocks if len(b) > 1), key=len)
                u, v = block[0], block[1]
                solver.conf_budget(args.conflicts)
                solver.set_phases([x * 5 + rng.randrange(5) + 1 for x in range(n)])
                ans = solver.solve_limited(assumptions=[u * 5 + 1, v * 5 + 2])
                if ans is None:
                    pair_records.append({"pair": [u, v], "cadical195": "UNKNOWN"})
                    break
                if ans is False:
                    gl, _ = solve_limited(Glucose4, clauses, args.conflicts * 2,
                                          assumptions=[u * 5 + 1, v * 5 + 2])
                    pair_records.append({"pair": [u, v], "cadical195": "UNSAT",
                                         "glucose4": "UNSAT" if gl is False else "SAT" if gl is True else "UNKNOWN"})
                    if gl is False:
                        result.update({"classification": "B_CANDIDATE_REQUIRES_INDEPENDENT_CONFIRMATION",
                                       "status": "DUAL_UNSAT_PAIR", "forced_equal_pair_candidate": [u, v]})
                    break
                c = colors_from_model(solver.get_model(), n)
                assert c[u] != c[v] and valid_coloring(c, n, edges)
                before = pairs_left(blocks)
                accept(c, "pair_inequality_sat")
                after = pairs_left(blocks)
                assert after < before
                pair_records.append({"pair": [u, v], "cadical195": "SAT",
                                     "remaining_pairs": after})

    remaining = pairs_left(blocks)
    if "classification" not in result:
        if remaining == 0:
            result.update({"classification": "D", "status": "SAT_NO_FORCED_EQUAL_PAIR"})
        else:
            result.update({"classification": "C", "status": "SAT_B_UNRESOLVED"})
    result.update({"proper_5color_witnesses": len(models), "remaining_unseparated_pairs": remaining,
                   "remaining_blocks": [b for b in blocks if len(b) > 1],
                   "pair_queries": pair_records, "seconds": round(monotonic() - started, 3)})

    (args.out_dir / "COLORINGS.txt").write_text("\n".join("".join(map(str, c)) for c in models) + "\n")
    write_json(args.out_dir / "PROGRESS.json", {"progress": progress})
    write_json(args.out_dir / "PROBE.json", result)
    compact = {k: v for k, v in result.items() if k not in ("remaining_blocks", "pair_queries")}
    print(json.dumps(compact, indent=2))


if __name__ == "__main__":
    main()
