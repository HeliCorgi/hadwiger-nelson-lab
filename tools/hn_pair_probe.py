#!/usr/bin/env python3
"""Focused unconditional same-color probe for one pair in an exact unit-edge graph.

The query asks whether a proper 5-coloring exists with the selected vertices
unequal. By color-name symmetry it is enough to fix u=0 and v=1. A SAT answer
is a directly checkable counterexample to forced equality. An UNSAT answer is
kept explicitly uncertified until independently checked/certified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from time import monotonic

from pysat.solvers import Cadical195, Glucose4

from hn_exact import K2, unit_modulus
from hn_unconditional_scan import color_cnf, valid_coloring, write_json

SOLVERS = {
    "cadical195": Cadical195,
    "glucose4": Glucose4,
}


def solve_with_budget(cls, clauses, assumptions, n, edges, conflicts):
    started = monotonic()
    with cls(bootstrap_with=clauses) as solver:
        solver.conf_budget(conflicts)
        answer = solver.solve_limited(assumptions=assumptions)
        model = None
        if answer is True:
            positive = set(solver.get_model())
            model = [next(c for c in range(5) if 5*v+c+1 in positive) for v in range(n)]
            assert valid_coloring(model, n, edges)
            assert all(lit in positive for lit in assumptions)
        return answer, model, round(monotonic() - started, 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--graph", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--pair", type=int, nargs=2, required=True, metavar=("U", "V"))
    ap.add_argument("--solver", choices=sorted(SOLVERS), required=True)
    ap.add_argument("--conflicts", type=int, default=5_000_000)
    ap.add_argument("--ordinary-conflicts", type=int, default=1_000_000)
    ap.add_argument("--expected-sha256")
    args = ap.parse_args()

    raw = args.graph.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if args.expected_sha256:
        assert sha == args.expected_sha256, (sha, args.expected_sha256)

    data = json.loads(raw)
    pts = [K2(p["a"], p["b"], p["den"]) for p in data["pts"]]
    edges = sorted(tuple(map(int, e)) for e in data["edges"])
    n = len(pts)
    u, v = args.pair
    assert 0 <= u < n and 0 <= v < n and u != v
    assert len(set(pts)) == n
    assert all(unit_modulus(pts[a] - pts[b]) for a, b in edges)
    pair_delta = pts[u] - pts[v]
    assert pts[u] != pts[v]

    clauses = color_cnf(n, edges)
    cls = SOLVERS[args.solver]

    ordinary, ordinary_model, ordinary_seconds = solve_with_budget(
        cls, clauses, [], n, edges, args.ordinary_conflicts
    )
    unequal_assumptions = [u*5 + 1, v*5 + 2]
    unequal, unequal_model, unequal_seconds = solve_with_budget(
        cls, clauses, unequal_assumptions, n, edges, args.conflicts
    )

    if unequal is True:
        status = "SAT_UNEQUAL_WITNESS"
        classification = "D_FOR_THIS_PAIR"
    elif unequal is False and ordinary is True:
        status = "FORCED_EQUAL_CANDIDATE_UNCERTIFIED"
        classification = "B_CANDIDATE_REQUIRES_INDEPENDENT_CHECK_OR_CERTIFICATE"
    elif ordinary is False:
        status = "GRAPH_5COLOR_UNSAT_CANDIDATE_UNCERTIFIED"
        classification = "A_CANDIDATE_REQUIRES_INDEPENDENT_CHECK_OR_CERTIFICATE"
    else:
        status = "UNKNOWN"
        classification = None

    result = {
        "status": status,
        "classification": classification,
        "solver": args.solver,
        "graph_sha256": sha,
        "vertices": n,
        "saved_unit_edges": len(edges),
        "all_saved_edges_exact_unit_distance": True,
        "distinct_exact_coordinates": True,
        "pair": [u, v],
        "pair_distinct_exact": True,
        "pair_is_unit_edge": unit_modulus(pair_delta),
        "pair_distance_float": abs(pair_delta.emb()),
        "ordinary_5color": "SAT" if ordinary is True else "UNSAT_UNCERTIFIED" if ordinary is False else "UNKNOWN",
        "ordinary_seconds": ordinary_seconds,
        "ordinary_conflict_budget": args.ordinary_conflicts,
        "ordinary_model": ordinary_model,
        "unequal_query": "SAT" if unequal is True else "UNSAT_UNCERTIFIED" if unequal is False else "UNKNOWN",
        "unequal_seconds": unequal_seconds,
        "unequal_conflict_budget": args.conflicts,
        "unequal_assumptions": {str(u): 0, str(v): 1},
        "unequal_model": unequal_model,
        "symmetry_note": "Any coloring with c(u)!=c(v) can be color-permuted to c(u)=0,c(v)=1.",
        "scope": "Only saved edges are used. SAT disproves forcing in this saved-edge graph; UNSAT would already imply forcing because every saved edge is an exact unit edge, even if additional unit edges were omitted.",
        "no_conditional_constraints": True,
        "distance_threshold": None,
    }
    write_json(args.out, result)
    print(json.dumps({k: result[k] for k in (
        "status", "classification", "solver", "graph_sha256", "vertices",
        "saved_unit_edges", "pair", "pair_distance_float", "ordinary_5color",
        "unequal_query", "ordinary_seconds", "unequal_seconds"
    )}, indent=2))


if __name__ == "__main__":
    main()
