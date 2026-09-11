#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import json
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

from pysat.formula import CNF
from pysat.solvers import Cadical195, Glucose4

K = 5
P, Q = 217, 490
UPSTREAM_SHA = "d1e80998bda337d9fa721f2e96d203ae54e97fc8"


def load_verts(path: Path):
    d = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(d, dict):
        d = d["verts"]
    return list(map(int, d))


def partitions_rgs(n: int, max_blocks: int = 5):
    if n == 0:
        yield ()
        return
    a = [0] * n
    def rec(i: int, mx: int):
        if i == n:
            yield tuple(a)
            return
        hi = min(mx + 1, max_blocks - 1)
        for x in range(hi + 1):
            a[i] = x
            yield from rec(i + 1, max(mx, x))
    yield from rec(1, 0)


def projection_states(solver, support_idx):
    out = []
    for st in partitions_rgs(len(support_idx)):
        assumptions = [i * K + st[j] + 1 for j, i in enumerate(support_idx)]
        if solver.solve(assumptions=assumptions):
            out.append("".join(map(str, st)))
    return out


def partition_blocks(state: str, support_vertices):
    blocks = defaultdict(list)
    for lab, v in zip(state, support_vertices):
        blocks[lab].append(v)
    return [blocks[k] for k in sorted(blocks)]


def mine_supports(proof, nverts: int, min_size: int, max_size: int):
    counts = Counter()
    late_counts = Counter()
    vertex_counts = Counter()
    pair_counts = Counter()
    additions = []
    for line_no, line in enumerate(proof):
        t = line.strip()
        if not t or t.startswith("d "):
            continue
        lits = []
        for tok in t.split():
            x = int(tok)
            if x == 0:
                break
            if 1 <= abs(x) <= nverts * K:
                lits.append(x)
        supp = tuple(sorted({(abs(x) - 1) // K for x in lits}))
        if not supp:
            continue
        additions.append((line_no, supp))
        for v in supp:
            vertex_counts[v] += 1
        if len(supp) <= 12:
            for u, v in combinations(supp, 2):
                pair_counts[(u, v)] += 1
        if min_size <= len(supp) <= max_size:
            counts[supp] += 1
    cutoff = int(len(proof) * 0.8)
    for line_no, supp in additions:
        if line_no >= cutoff and min_size <= len(supp) <= max_size:
            late_counts[supp] += 1
    return counts, late_counts, vertex_counts, pair_counts


def select_candidates(counts, late_counts, verts, pidx, qidx, per_size, min_size, max_size):
    selected = []
    for size in range(min_size, max_size + 1):
        pool = [s for s in counts if len(s) == size and not (pidx in s and qidx in s)]
        pool.sort(key=lambda s: (-late_counts[s], -counts[s], s))
        # Preserve both port-free and one-port candidates, because a one-port
        # symmetric relation can still be geometrically meaningful while the
        # direct two-port equality is deliberately excluded.
        pf = [s for s in pool if pidx not in s and qidx not in s]
        op = [s for s in pool if (pidx in s) ^ (qidx in s)]
        quota_pf = max(1, (per_size * 3) // 4)
        quota_op = per_size - quota_pf
        chosen = pf[:quota_pf] + op[:quota_op]
        if len(chosen) < per_size:
            used = set(chosen)
            chosen += [s for s in pool if s not in used][:per_size - len(chosen)]
        for s in chosen:
            selected.append({
                "support": s,
                "size": size,
                "proof_occurrences": counts[s],
                "late_occurrences": late_counts[s],
                "port_free": pidx not in s and qidx not in s,
                "one_port": (pidx in s) ^ (qidx in s),
            })
    return selected


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--min-size", type=int, default=4)
    ap.add_argument("--max-size", type=int, default=6)
    ap.add_argument("--per-size", type=int, default=180)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    a = CNF(from_file=str(args.data_dir / "A.cnf"))
    b = CNF(from_file=str(args.data_dir / "B.cnf"))
    verts = load_verts(args.data_dir / "verts.json")
    vidx = {v: i for i, v in enumerate(verts)}
    pidx, qidx = vidx[P], vidx[Q]

    with Glucose4(bootstrap_with=a.clauses + b.clauses, with_proof=True) as s:
        if s.solve():
            raise RuntimeError("A+B unexpectedly SAT")
        proof = s.get_proof() or []
        stats = s.accum_stats()

    with gzip.open(args.out_dir / "p2_glucose4.drup.gz", "wt", encoding="utf-8") as f:
        for line in proof:
            f.write(line.rstrip() + "\n")

    counts, late_counts, vertex_counts, pair_counts = mine_supports(
        proof, len(verts), args.min_size, args.max_size
    )
    candidates = select_candidates(
        counts, late_counts, verts, pidx, qidx,
        args.per_size, args.min_size, args.max_size
    )

    evaluated = []
    separators = []
    with Cadical195(bootstrap_with=a.clauses) as sa, Cadical195(bootstrap_with=b.clauses) as sb:
        for rank, meta in enumerate(candidates):
            supp = meta["support"]
            ast = projection_states(sa, supp)
            bst = projection_states(sb, supp)
            aset, bset = set(ast), set(bst)
            overlap = sorted(aset & bset)
            sv = [verts[i] for i in supp]
            rec = {
                "rank": rank,
                "support_indices": list(supp),
                "support_vertices": sv,
                "size": meta["size"],
                "proof_occurrences": meta["proof_occurrences"],
                "late_occurrences": meta["late_occurrences"],
                "port_free": meta["port_free"],
                "one_port": meta["one_port"],
                "A_state_count": len(ast),
                "B_state_count": len(bst),
                "overlap_count": len(overlap),
                "overlap_states": overlap,
                "A_only_count": len(aset - bset),
                "B_only_count": len(bset - aset),
            }
            if not overlap:
                rec["interpolant_A_states"] = ast
                rec["interpolant_A_partitions"] = [partition_blocks(st, sv) for st in ast]
                separators.append(rec)
            evaluated.append(rec)

    evaluated.sort(key=lambda r: (
        r["overlap_count"],
        r["size"],
        -r["late_occurrences"],
        -r["proof_occurrences"],
    ))
    separators.sort(key=lambda r: (r["size"], len(r.get("interpolant_A_states", []))))

    by_size = {}
    for size in range(args.min_size, args.max_size + 1):
        rs = [r for r in evaluated if r["size"] == size]
        by_size[str(size)] = {
            "evaluated": len(rs),
            "min_overlap": min((r["overlap_count"] for r in rs), default=None),
            "zero_overlap": sum(r["overlap_count"] == 0 for r in rs),
            "best": rs[:10],
        }

    report = {
        "upstream_sha": UPSTREAM_SHA,
        "solver": "Glucose4 DRUP -> exact Cadical195 partition projection",
        "proof_lines": len(proof),
        "solver_stats": stats,
        "support_range": [args.min_size, args.max_size],
        "per_size_target": args.per_size,
        "unique_mined_supports_by_size": {
            str(k): sum(1 for s in counts if len(s) == k)
            for k in range(args.min_size, args.max_size + 1)
        },
        "evaluated_count": len(evaluated),
        "separator_count": len(separators),
        "separators": separators,
        "by_size": by_size,
        "best_overall": evaluated[:50],
        "top_proof_vertices": [
            {"vertex": verts[i], "index": i, "count": c}
            for i, c in vertex_counts.most_common(30)
        ],
        "top_proof_pairs": [
            {"vertices": [verts[i], verts[j]], "indices": [i, j], "count": c}
            for (i, j), c in pair_counts.most_common(50)
        ],
        "interpretation": (
            "A/B state sets use canonical restricted-growth strings, so the test "
            "is invariant under permutation of the five color names. Zero overlap "
            "is an exact color-symmetric semantic interpolant on that support."
        ),
    }
    (args.out_dir / "deep_interpolant.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    summary = {
        "proof_lines": len(proof),
        "evaluated_count": len(evaluated),
        "separator_count": len(separators),
        "by_size": {
            k: {q: v for q, v in d.items() if q != "best"}
            for k, d in by_size.items()
        },
        "best_overall": evaluated[:10],
    }
    (args.out_dir / "DEEP_SUMMARY.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
