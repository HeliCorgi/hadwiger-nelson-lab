#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import json
from collections import Counter
from itertools import combinations
from pathlib import Path

from pysat.formula import CNF
from pysat.solvers import Cadical195, Glucose4

K = 5
P, R, Q = 217, 489, 490
UPSTREAM_SHA = "d1e80998bda337d9fa721f2e96d203ae54e97fc8"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def build_system(data_dir: Path):
    g510 = load_json(data_dir / "g510_k2.json")
    e_full = [tuple(map(int, e)) for e in g510["edges"]]
    raw = load_json(data_dir / "B5_MULTICORE.json")["cores"][0]
    if raw and isinstance(raw[0], int):
        hstar = [e_full[i] for i in raw]
    else:
        hstar = [tuple(map(int, e)) for e in raw]
    c88 = [tuple(map(int, e)) for e in load_json(data_dir / "B5_P2_LEMMA.json")["C_min"]]
    edges = sorted({(min(u, v), max(u, v)) for u, v in hstar})
    verts = sorted({x for e in edges for x in e} | {x for e in c88 for x in e})
    if len(verts) != 393:
        raise RuntimeError(f"expected 393 vertices, got {len(verts)}")
    return verts, edges, c88


class DSU:
    def __init__(self, xs):
        self.p = {x: x for x in xs}
    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x
    def union(self, a, b):
        a, b = self.find(a), self.find(b)
        if a != b:
            if a > b:
                a, b = b, a
            self.p[b] = a


def color_sat(nodes, edges, k, extra_edges=()):
    order = sorted(nodes)
    pos = {v: i for i, v in enumerate(order)}
    cls = []
    for v in order:
        lits = [pos[v] * k + c + 1 for c in range(k)]
        cls.append(lits)
        for a, b in combinations(lits, 2):
            cls.append([-a, -b])
    for u, v in set(edges) | set(extra_edges):
        if u not in pos or v not in pos:
            continue
        for c in range(k):
            cls.append([-(pos[u] * k + c + 1), -(pos[v] * k + c + 1)])
    with Cadical195(bootstrap_with=cls) as s:
        return s.solve()


def max_clique(nodes, edges):
    adj = {v: set() for v in nodes}
    for u, v in edges:
        if u in adj and v in adj:
            adj[u].add(v)
            adj[v].add(u)
    best = []
    def bk(r, p, x):
        nonlocal best
        if len(r) + len(p) <= len(best):
            return
        if not p and not x:
            if len(r) > len(best):
                best = list(r)
            return
        pivot = max(p | x, key=lambda v: len(adj[v] & p), default=None)
        cand = list(p - (adj[pivot] if pivot is not None else set()))
        for v in cand:
            bk(r | {v}, p & adj[v], x & adj[v])
            p.remove(v)
            x.add(v)
    bk(set(), set(nodes), set())
    return sorted(best)


def shrink_non3(nodes, edges):
    active = set(nodes)
    changed = True
    while changed:
        changed = False
        for v in sorted(active):
            trial = active - {v}
            te = [(a, b) for a, b in edges if a in trial and b in trial]
            if trial and not color_sat(trial, te, 3):
                active = trial
                changed = True
    return sorted(active)


def quotient_analysis(data_dir: Path, out_dir: Path):
    verts, edges, c88 = build_system(data_dir)
    dsu = DSU(verts)
    for u, v in c88:
        dsu.union(u, v)
    comps = {}
    for v in verts:
        comps.setdefault(dsu.find(v), []).append(v)
    roots = sorted(comps, key=lambda r: min(comps[r]))
    qid = {r: i for i, r in enumerate(roots)}
    vq = {v: qid[dsu.find(v)] for v in verts}
    qedges = set()
    internal = []
    for u, v in edges:
        a, b = vq[u], vq[v]
        if a == b:
            internal.append((u, v))
        else:
            qedges.add((min(a, b), max(a, b)))
    if internal:
        raise RuntimeError(f"quotient has internal edges: {internal[:5]}")
    qnodes = set(range(len(roots)))
    adj = {v: set() for v in qnodes}
    for u, v in qedges:
        adj[u].add(v)
        adj[v].add(u)
    port_nodes = {str(x): vq[x] for x in (P, R, Q)}
    pairs = [(P, Q), (P, R), (R, Q)]
    pair_reports = []
    for a0, b0 in pairs:
        a, b = vq[a0], vq[b0]
        common = sorted(adj[a] & adj[b])
        cs = set(common)
        ce = [(u, v) for u, v in qedges if u in cs and v in cs]
        sat3 = color_sat(common, ce, 3) if common else True
        sat4 = color_sat(common, ce, 4) if common else True
        clique = max_clique(common, ce) if common else []
        core4 = shrink_non3(common, ce) if common and not sat3 else []
        pair_reports.append({
            "pair_original": [a0, b0],
            "pair_quotient": [a, b],
            "common_neighborhood_size": len(common),
            "common_neighborhood_edges": len(ce),
            "common_neighborhood_3_colorable": sat3,
            "common_neighborhood_4_colorable": sat4,
            "max_clique_size": len(clique),
            "max_clique_qnodes": clique,
            "max_clique_components": [comps[roots[x]] for x in clique],
            "vertex_minimal_non3_qnodes": core4,
            "vertex_minimal_non3_components": [comps[roots[x]] for x in core4],
        })
    q5 = color_sat(qnodes, qedges, 5)
    forced = {}
    for a0, b0 in pairs:
        a, b = vq[a0], vq[b0]
        forced[f"{a0}-{b0}"] = not color_sat(
            qnodes, qedges, 5, extra_edges=[(min(a, b), max(a, b))]
        )
    report = {
        "upstream_sha": UPSTREAM_SHA,
        "original_vertices": len(verts),
        "original_edges": len(edges),
        "c88_pairs": len(c88),
        "c88_support_vertices": len({x for e in c88 for x in e}),
        "c88_components_on_support_expected": 59,
        "quotient_vertices": len(qnodes),
        "quotient_edges": len(qedges),
        "quotient_5_colorable": q5,
        "port_nodes": port_nodes,
        "forced_equal_via_added_edge_unsat": forced,
        "pair_common_neighborhood_analysis": pair_reports,
        "component_sizes": sorted([len(vs) for vs in comps.values()], reverse=True),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "quotient_analysis.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    return report


def partitions_rgs(n, max_blocks=5):
    if n == 0:
        yield ()
        return
    a = [0] * n
    def rec(i, mx):
        if i == n:
            yield tuple(a)
            return
        for x in range(min(mx + 1, max_blocks - 1) + 1):
            a[i] = x
            yield from rec(i + 1, max(mx, x))
    a[0] = 0
    yield from rec(1, 0)


def projection_states(solver, support_idx, max_blocks=5):
    states = []
    for st in partitions_rgs(len(support_idx), max_blocks):
        assumptions = [i * K + st[j] + 1 for j, i in enumerate(support_idx)]
        if solver.solve(assumptions=assumptions):
            states.append("".join(map(str, st)))
    return states


def proof_analysis(data_dir: Path, out_dir: Path, max_candidates=300, max_support=6):
    a = CNF(from_file=str(data_dir / "A.cnf"))
    b = CNF(from_file=str(data_dir / "B.cnf"))
    verts = list(map(int, load_json(data_dir / "verts.json")))
    vidx = {v: i for i, v in enumerate(verts)}
    pidx, qidx = vidx[P], vidx[Q]
    clauses = a.clauses + b.clauses
    out_dir.mkdir(parents=True, exist_ok=True)
    with Glucose4(bootstrap_with=clauses, with_proof=True) as s:
        if s.solve():
            raise RuntimeError("A+B unexpectedly SAT")
        proof = s.get_proof() or []
        stats = s.accum_stats()
    with gzip.open(out_dir / "p2_glucose4.drup.gz", "wt", encoding="utf-8") as f:
        for line in proof:
            f.write(line.rstrip() + "\n")

    support_counter = Counter()
    vertex_counter = Counter()
    pair_counter = Counter()
    add_lines = 0
    del_lines = 0
    candidates = set()
    for line in proof:
        t = line.strip()
        if not t:
            continue
        isdel = t.startswith("d ")
        if isdel:
            del_lines += 1
            t = t[2:].strip()
        else:
            add_lines += 1
        lits = []
        for tok in t.split():
            x = int(tok)
            if x == 0:
                break
            lits.append(x)
        supp = sorted({(abs(x) - 1) // K for x in lits if 1 <= abs(x) <= len(verts) * K})
        if not isdel:
            for v in supp:
                vertex_counter[v] += 1
            for u, v in combinations(supp, 2):
                pair_counter[(u, v)] += 1
            if 2 <= len(supp) <= max_support:
                key = tuple(supp)
                support_counter[key] += 1
                candidates.add(key)

    ranked = sorted(candidates, key=lambda s: (len(s), -support_counter[s], s))[:max_candidates]
    topv = [v for v, _ in vertex_counter.most_common(20)]
    for k in (4, 5, 6):
        if k <= max_support:
            for comb in combinations(topv, min(k, len(topv))):
                ranked.append(tuple(sorted(comb)))
                if len(ranked) >= max_candidates * 2:
                    break
            if len(ranked) >= max_candidates * 2:
                break

    seen = set()
    ranked2 = []
    for s in ranked:
        if s in seen:
            continue
        seen.add(s)
        # Avoid the trivial interpolant E(217,490) / not-E(217,490).
        if pidx in s and qidx in s:
            continue
        ranked2.append(s)
        if len(ranked2) >= max_candidates:
            break

    with Cadical195(bootstrap_with=a.clauses) as sa, Cadical195(bootstrap_with=b.clauses) as sb:
        evaluated = []
        separators = []
        for supp in ranked2:
            ast = projection_states(sa, supp)
            bst = projection_states(sb, supp)
            ov = sorted(set(ast) & set(bst))
            rec = {
                "support_indices": list(supp),
                "support_vertices": [verts[i] for i in supp],
                "size": len(supp),
                "proof_occurrences": support_counter[supp],
                "A_states": ast,
                "B_states": bst,
                "overlap": ov,
                "overlap_count": len(ov),
                "port_free": pidx not in supp and qidx not in supp,
            }
            evaluated.append(rec)
            if not ov:
                separators.append(rec)
    evaluated.sort(key=lambda r: (r["overlap_count"], r["size"], -r["proof_occurrences"]))
    report = {
        "upstream_sha": UPSTREAM_SHA,
        "solver": "Glucose4(with_proof=True)",
        "proof_lines": len(proof),
        "proof_additions": add_lines,
        "proof_deletions": del_lines,
        "solver_stats": stats,
        "top_vertices": [
            {"vertex": verts[i], "index": i, "count": c}
            for i, c in vertex_counter.most_common(30)
        ],
        "top_pairs": [
            {"vertices": [verts[i], verts[j]], "indices": [i, j], "count": c}
            for (i, j), c in pair_counter.most_common(50)
        ],
        "candidate_policy": (
            "proof-clause supports <=6 plus top-vertex combinations; "
            "supports containing both 217 and 490 excluded"
        ),
        "evaluated_count": len(evaluated),
        "separator_count": len(separators),
        "separators": separators[:20],
        "best_candidates": evaluated[:50],
    }
    (out_dir / "proof_interpolant_probe.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--mode", choices=["quotient", "proof", "all"], default="all")
    ap.add_argument("--max-candidates", type=int, default=300)
    ap.add_argument("--max-support", type=int, default=6)
    args = ap.parse_args()
    summary = {"upstream_sha": UPSTREAM_SHA}
    if args.mode in ("quotient", "all"):
        summary["quotient"] = quotient_analysis(args.data_dir, args.out_dir)
    if args.mode in ("proof", "all"):
        p = proof_analysis(args.data_dir, args.out_dir, args.max_candidates, args.max_support)
        summary["proof"] = {
            k: p[k]
            for k in [
                "proof_lines", "proof_additions", "proof_deletions",
                "solver_stats", "evaluated_count", "separator_count",
            ]
        }
    (args.out_dir / "SUMMARY.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
