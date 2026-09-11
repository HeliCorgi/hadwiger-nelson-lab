#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from pysat.formula import CNF
from pysat.solvers import Cadical195, Glucose4

K = 5
UPSTREAM_SHA = "d1e80998bda337d9fa721f2e96d203ae54e97fc8"


def load_verts(path: Path):
    d = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(d, dict):
        d = d["verts"]
    return list(map(int, d))


def split_multiset(a_clauses, b_clauses):
    ca = Counter(tuple(c) for c in a_clauses)
    cb = Counter(tuple(c) for c in b_clauses)
    common = []
    aonly = []
    bonly = []
    keys = sorted(set(ca) | set(cb))
    for c in keys:
        nc = min(ca[c], cb[c])
        common.extend([c] * nc)
        aonly.extend([c] * (ca[c] - nc))
        bonly.extend([c] * (cb[c] - nc))
    return common, aonly, bonly


def write_dimacs(path: Path, clauses, nv: int):
    with path.open("w", encoding="utf-8") as f:
        f.write(f"p cnf {nv} {len(clauses)}\n")
        for c in clauses:
            f.write(" ".join(map(str, c)) + " 0\n")


def write_drup(path: Path, proof):
    with path.open("w", encoding="utf-8") as f:
        for line in proof:
            f.write(line.rstrip() + "\n")


def parse_lrat_dependency_cone(path: Path, n_input: int):
    deps = {}
    clauses = {}
    final_id = None
    deletion_lines = 0
    derived_lines = 0
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("c"):
                continue
            toks = s.split()
            try:
                cid = int(toks[0])
            except Exception:
                continue
            if len(toks) > 1 and toks[1] == "d":
                deletion_lines += 1
                continue
            derived_lines += 1
            vals = list(map(int, toks[1:]))
            if 0 not in vals:
                continue
            z = vals.index(0)
            clause = vals[:z]
            hints_raw = vals[z + 1:]
            hints = []
            for h in hints_raw:
                if h == 0:
                    continue
                # LRAT RAT segments may use negative IDs as separators/pivots;
                # abs() is a conservative dependency over-approximation.
                if abs(h) <= cid:
                    hints.append(abs(h))
            clauses[cid] = clause
            deps[cid] = sorted(set(hints))
            if not clause:
                final_id = cid
    if final_id is None:
        raise RuntimeError("no derived empty clause found in LRAT")
    used = set()
    stack = [final_id]
    while stack:
        cid = stack.pop()
        if cid in used:
            continue
        used.add(cid)
        if cid > n_input:
            stack.extend(deps.get(cid, ()))
    initial = sorted(i for i in used if 1 <= i <= n_input)
    learned = sorted(i for i in used if i > n_input)
    return {
        "final_clause_id": final_id,
        "used_ids": used,
        "initial_ids": initial,
        "learned_ids": learned,
        "derived_lines": derived_lines,
        "deletion_lines": deletion_lines,
        "deps": deps,
        "clauses": clauses,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--analyze-lrat", type=Path)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    a = CNF(from_file=str(args.data_dir / "A.cnf"))
    b = CNF(from_file=str(args.data_dir / "B.cnf"))
    verts = load_verts(args.data_dir / "verts.json")
    common, aonly, bonly = split_multiset(a.clauses, b.clauses)
    clauses = common + aonly + bonly
    nv = max(a.nv, b.nv)
    ranges = {
        "common": [1, len(common)],
        "A_only": [len(common) + 1, len(common) + len(aonly)],
        "B_only": [len(common) + len(aonly) + 1, len(clauses)],
    }
    meta = {
        "upstream_sha": UPSTREAM_SHA,
        "nv": nv,
        "common_clause_count": len(common),
        "A_only_clause_count": len(aonly),
        "B_only_clause_count": len(bonly),
        "total_clause_count": len(clauses),
        "clause_id_ranges": ranges,
    }

    combined_path = args.out_dir / "p2_partitioned.cnf"
    drup_path = args.out_dir / "p2_partitioned.drup"
    write_dimacs(combined_path, clauses, nv)
    with Glucose4(bootstrap_with=clauses, with_proof=True) as s:
        sat = s.solve()
        if sat:
            raise RuntimeError("partitioned A+B unexpectedly SAT")
        proof = s.get_proof() or []
        meta["glucose_stats"] = s.accum_stats()
    write_drup(drup_path, proof)
    meta["drup_lines"] = len(proof)

    # Independent SAT recheck before external proof conversion.
    with Cadical195(bootstrap_with=clauses) as s:
        meta["cadical_unsat_recheck"] = not s.solve()
    (args.out_dir / "PARTITION.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    if args.analyze_lrat:
        cone = parse_lrat_dependency_cone(args.analyze_lrat, len(clauses))
        c0, c1 = ranges["common"]
        a0, a1 = ranges["A_only"]
        b0, b1 = ranges["B_only"]
        def inrange(x, lo, hi):
            return lo <= x <= hi if lo <= hi else False
        common_ids = [x for x in cone["initial_ids"] if inrange(x, c0, c1)]
        a_ids = [x for x in cone["initial_ids"] if inrange(x, a0, a1)]
        b_ids = [x for x in cone["initial_ids"] if inrange(x, b0, b1)]
        used_initial_clauses = [clauses[i - 1] for i in cone["initial_ids"]]
        with Cadical195(bootstrap_with=used_initial_clauses) as s:
            cone_unsat = not s.solve()
        varset = sorted({abs(l) for c in used_initial_clauses for l in c})
        indices = sorted({(v - 1) // K for v in varset if 1 <= v <= len(verts) * K})
        report = {
            **meta,
            "lrat_path": str(args.analyze_lrat),
            "lrat_final_clause_id": cone["final_clause_id"],
            "lrat_derived_lines": cone["derived_lines"],
            "lrat_deletion_lines": cone["deletion_lines"],
            "dependency_cone_initial_count": len(cone["initial_ids"]),
            "dependency_cone_learned_count": len(cone["learned_ids"]),
            "dependency_cone_common_count": len(common_ids),
            "dependency_cone_A_only_count": len(a_ids),
            "dependency_cone_B_only_count": len(b_ids),
            "dependency_cone_initial_ids": cone["initial_ids"],
            "dependency_cone_A_only_ids": a_ids,
            "dependency_cone_B_only_ids": b_ids,
            "dependency_cone_unsat_recheck": cone_unsat,
            "dependency_cone_vertex_count": len(indices),
            "dependency_cone_vertices": [verts[i] for i in indices],
            "note": (
                "Cone dependency extraction treats absolute LRAT hint IDs as a "
                "conservative dependency relation; UNSAT is independently rechecked "
                "on the selected original clauses."
            ),
        }
        (args.out_dir / "LRAT_CONE.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps({
            k: report[k] for k in [
                "common_clause_count", "A_only_clause_count", "B_only_clause_count",
                "drup_lines", "dependency_cone_initial_count",
                "dependency_cone_learned_count", "dependency_cone_common_count",
                "dependency_cone_A_only_count", "dependency_cone_B_only_count",
                "dependency_cone_unsat_recheck", "dependency_cone_vertex_count",
            ]
        }, indent=2))
    else:
        print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
