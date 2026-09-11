#!/usr/bin/env python3
"""Independently check a four-set candidate against the exact A/B semantic oracle.

A = H* plus C88 equality conditions.
B = H* plus c(217) != c(490).

For the supplied four vertices, build two complete 5-coloring copies and require
that all six pair-equality observables agree between A and B.  SAT therefore
produces an explicit A/B fooling pair for this support; UNSAT means the four-set
is a genuine semantic-interface candidate and should be certificate-checked.

The same CNF is solved by both CaDiCaL195 and Glucose4.  Solver agreement is
required before a terminal SAT/UNSAT status is written.
"""
from __future__ import annotations

import argparse
import json
import time
from itertools import combinations
from pathlib import Path

from pysat.solvers import Cadical195, Glucose4

K = 5
P, Q = 217, 490
UPSTREAM_SHA = "d1e80998bda337d9fa721f2e96d203ae54e97fc8"
DEFAULT_SUPPORT = [26, 316, 398, 409]


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_system(data_dir: Path):
    g510 = load_json(data_dir / "g510_k2.json")
    e_full = [tuple(map(int, e)) for e in g510["edges"]]
    raw = load_json(data_dir / "B5_MULTICORE.json")["cores"][0]
    if raw and isinstance(raw[0], int):
        hstar = [e_full[i] for i in raw]
    else:
        hstar = [tuple(map(int, e)) for e in raw]
    c88 = [tuple(map(int, p)) for p in load_json(data_dir / "B5_P2_LEMMA.json")["C_min"]]
    edges = sorted({(min(u, v), max(u, v)) for u, v in hstar})
    verts = sorted({x for e in edges for x in e} | {x for e in c88 for x in e})
    if len(verts) != 393:
        raise RuntimeError(f"expected 393 vertices, got {len(verts)}")
    return verts, edges, c88


def coloring_cnf(verts, edges, conds, vidx, base):
    def cv(v, c):
        return base + vidx[v] * K + c + 1

    cls = []
    for v in verts:
        cls.append([cv(v, c) for c in range(K)])
        for c1 in range(K):
            for c2 in range(c1 + 1, K):
                cls.append([-cv(v, c1), -cv(v, c2)])
    for u, v in edges:
        for c in range(K):
            cls.append([-cv(u, c), -cv(v, c)])
    for u, v in conds:
        for c in range(K):
            cls.append([-cv(u, c), cv(v, c)])
            cls.append([cv(u, c), -cv(v, c)])
    return cls


def decode(model, verts, vidx, base):
    pos = {x for x in model if x > 0}
    out = {}
    for v in verts:
        hits = [c for c in range(K) if base + vidx[v] * K + c + 1 in pos]
        if len(hits) != 1:
            raise RuntimeError(f"bad one-hot decode for {v}: {hits}")
        out[v] = hits[0]
    return out


def validate(coloring, verts, edges, conds=(), require_port_diff=False):
    for u, v in edges:
        if coloring[u] == coloring[v]:
            return False
    for u, v in conds:
        if coloring[u] != coloring[v]:
            return False
    if require_port_diff and coloring[P] == coloring[Q]:
        return False
    return True


def equality_pattern(coloring, support):
    return [int(coloring[u] == coloring[v]) for u, v in combinations(support, 2)]


def build_oracle(data_dir: Path, support):
    verts, edges, c88 = build_system(data_dir)
    vidx = {v: i for i, v in enumerate(verts)}
    if len(support) != 4 or len(set(support)) != 4:
        raise ValueError("support must contain four distinct vertices")
    if any(v not in vidx for v in support):
        raise ValueError("support contains a vertex outside the 393-vertex system")
    if P in support or Q in support:
        raise ValueError("support must be port-free")

    n = len(verts)
    BA, BB = 0, n * K
    clauses = coloring_cnf(verts, edges, c88, vidx, BA)
    clauses += coloring_cnf(verts, edges, [], vidx, BB)
    pi, qi = vidx[P], vidx[Q]
    for c in range(K):
        clauses.append([-(BB + pi * K + c + 1), -(BB + qi * K + c + 1)])

    nv = 2 * n * K
    eq_vars = []
    support_pairs = list(combinations(support, 2))
    for u, v in support_pairs:
        i, j = vidx[u], vidx[v]
        ea, eb = nv + 1, nv + 2
        nv += 2
        eq_vars.append((u, v, ea, eb))
        for c in range(K):
            ai = BA + i * K + c + 1
            aj = BA + j * K + c + 1
            bi = BB + i * K + c + 1
            bj = BB + j * K + c + 1
            # e=true iff the pair has equal colors (using one-hot coloring).
            clauses.append([-ea, -ai, aj])
            clauses.append([-ea, ai, -aj])
            clauses.append([ea, -ai, -aj])
            clauses.append([-eb, -bi, bj])
            clauses.append([-eb, bi, -bj])
            clauses.append([eb, -bi, -bj])
        # A and B must induce the same equality observable on this pair.
        clauses.append([-ea, eb])
        clauses.append([ea, -eb])

    meta = {
        "verts": verts,
        "edges": edges,
        "c88": c88,
        "vidx": vidx,
        "BA": BA,
        "BB": BB,
        "support_pairs": support_pairs,
        "eq_vars": eq_vars,
        "max_var": nv,
    }
    return clauses, meta


def solve_with(solver_cls, clauses):
    t0 = time.monotonic()
    with solver_cls(bootstrap_with=clauses) as s:
        sat = s.solve()
        elapsed = time.monotonic() - t0
        model = s.get_model() if sat else None
    return sat, model, elapsed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, required=True)
    ap.add_argument("--result", type=Path, required=True)
    ap.add_argument("--support", nargs=4, type=int, default=DEFAULT_SUPPORT)
    args = ap.parse_args()

    support = sorted(args.support)
    clauses, m = build_oracle(args.data_dir, support)

    ca_sat, ca_model, ca_sec = solve_with(Cadical195, clauses)
    gl_sat, gl_model, gl_sec = solve_with(Glucose4, clauses)
    if ca_sat != gl_sat:
        status = "SOLVER-DISAGREEMENT"
    else:
        status = "SAT-FOOLING-PAIR" if ca_sat else "UNSAT-INTERFACE-CANDIDATE"

    out = {
        "status": status,
        "upstream_sha": UPSTREAM_SHA,
        "support": support,
        "support_pairs": [list(x) for x in m["support_pairs"]],
        "cnf": {
            "variables": m["max_var"],
            "clauses": len(clauses),
        },
        "solvers": {
            "Cadical195": {"sat": ca_sat, "elapsed_sec": round(ca_sec, 6)},
            "Glucose4": {"sat": gl_sat, "elapsed_sec": round(gl_sec, 6)},
        },
    }

    if ca_sat and gl_sat:
        # Preserve one model from each solver, but use the CaDiCaL model as the
        # canonical fooling-pair witness and validate it directly.
        alpha = decode(ca_model, m["verts"], m["vidx"], m["BA"])
        beta = decode(ca_model, m["verts"], m["vidx"], m["BB"])
        if not validate(alpha, m["verts"], m["edges"], m["c88"]):
            raise RuntimeError("decoded A witness failed validation")
        if not validate(beta, m["verts"], m["edges"], require_port_diff=True):
            raise RuntimeError("decoded B witness failed validation")
        pa = equality_pattern(alpha, support)
        pb = equality_pattern(beta, support)
        if pa != pb:
            raise RuntimeError("oracle SAT model does not agree on support equality pattern")

        # Difference graph over all non-port vertices; support must contain no
        # difference edge because all six observables were tied.
        nonports = [v for v in m["verts"] if v not in (P, Q)]
        diff_edges = []
        for u, v in combinations(nonports, 2):
            if (alpha[u] == alpha[v]) != (beta[u] == beta[v]):
                diff_edges.append([u, v])
        support_pair_set = {tuple(x) for x in combinations(support, 2)}
        if any(tuple(e) in support_pair_set for e in diff_edges):
            raise RuntimeError("new fooling-pair cut unexpectedly hits the candidate support")

        out["equality_pattern"] = pa
        out["new_cut_edge_count"] = len(diff_edges)
        out["new_cut_hits_support"] = False
        out["canonical_witness"] = {
            "alpha": [alpha[v] for v in m["verts"]],
            "beta": [beta[v] for v in m["verts"]],
            "vertex_order": m["verts"],
        }

        # Cross-check the independently produced Glucose model too.
        ga = decode(gl_model, m["verts"], m["vidx"], m["BA"])
        gb = decode(gl_model, m["verts"], m["vidx"], m["BB"])
        out["glucose_witness_valid"] = bool(
            validate(ga, m["verts"], m["edges"], m["c88"])
            and validate(gb, m["verts"], m["edges"], require_port_diff=True)
            and equality_pattern(ga, support) == equality_pattern(gb, support)
        )

    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("status", "support", "cnf", "solvers")}, indent=2))
    if status == "SOLVER-DISAGREEMENT":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
