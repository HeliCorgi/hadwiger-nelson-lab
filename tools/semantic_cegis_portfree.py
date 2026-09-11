#!/usr/bin/env python3
"""
Hybrid, resumable CEGIS for the remaining port-free support-4 semantic interface.

Pinned upstream: HeliCorgi/five-color-forcing-anatomy
commit d1e80998bda337d9fa721f2e96d203ae54e97fc8.

A = H* ∧ C88.
B = H* ∧ (c(217) != c(490)).

For a 4-set S of non-port vertices, compare only the equality partition on S.
If Mod(A)|S and Mod(B)|S are disjoint, the six equality atoms on S form a
semantic interface. Conversely, every equality-atom interface supported on
<=4 non-port vertices extends monotonically to a separating 4-set. Therefore
exhausting all 4-sets is complete for the port-free support<=4 question.

Candidate generation is hybrid:
  * a fast bitset/local-search layer proposes four-sets satisfying every known
    fooling-pair cut;
  * the exact SAT master is retained as the completeness backstop whenever the
    heuristic does not find a candidate.

Every oracle/master SAT call has a deterministic CaDiCaL decision budget. Calls
that exhaust the budget return UNKNOWN, are never converted into SAT/UNSAT facts,
and oracle-UNKNOWN supports are recorded for retry. The workflow also keeps an
outer wall-clock guard. The checkpoint stores newly found fooling pairs plus
safe search metadata; seed pairs are reloaded from the pinned upstream handoff.
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import random
import time
from pathlib import Path

import numpy as np
from pysat.card import CardEnc, EncType
from pysat.solvers import Cadical195

K = 5
P, Q = 217, 490
UPSTREAM_SHA = "d1e80998bda337d9fa721f2e96d203ae54e97fc8"


def log(msg: str) -> None:
    print(msg, flush=True)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def atomic_gzip_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8", compresslevel=6) as f:
        json.dump(obj, f, separators=(",", ":"))
    os.replace(tmp, path)


def build_system(data_dir: Path):
    g510 = load_json(data_dir / "g510_k2.json")
    e_full = [tuple(map(int, e)) for e in g510["edges"]]

    d = load_json(data_dir / "B5_MULTICORE.json")
    raw = d["cores"][0]
    if raw and isinstance(raw[0], int):
        hstar = [e_full[i] for i in raw]
    else:
        hstar = [tuple(map(int, e)) for e in raw]

    c88 = [
        tuple(map(int, p))
        for p in load_json(data_dir / "B5_P2_LEMMA.json")["C_min"]
    ]
    all_e = sorted({(min(u, v), max(u, v)) for (u, v) in hstar})
    verts = sorted(
        {x for e in all_e for x in e}
        | {x for e in c88 for x in e}
    )
    if len(verts) != 393:
        raise RuntimeError(f"expected 393 vertices, got {len(verts)}")
    if P not in verts or Q not in verts:
        raise RuntimeError("ports missing from system")
    return verts, all_e, c88


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


def decode_copy(model_pos, verts, vidx, base):
    out = {}
    for v in verts:
        for c in range(K):
            if base + vidx[v] * K + c + 1 in model_pos:
                out[v] = c
                break
        else:
            raise RuntimeError(f"no color decoded for vertex {v}")
    return out


def validate_coloring(arr, verts, edges, vidx, conditions=(), require_port_diff=False):
    if len(arr) != len(verts):
        return False
    if any(int(x) < 0 or int(x) >= K for x in arr):
        return False
    for u, v in edges:
        if arr[vidx[u]] == arr[vidx[v]]:
            return False
    for u, v in conditions:
        if arr[vidx[u]] != arr[vidx[v]]:
            return False
    if require_port_diff and arr[vidx[P]] == arr[vidx[Q]]:
        return False
    return True


def load_seed_pairs(data_dir: Path, verts, edges, c88, vidx):
    n = len(verts)
    seeds = []
    seen = set()

    def add(alpha, beta, source):
        av = np.asarray(alpha, dtype=np.int8)
        bv = np.asarray(beta, dtype=np.int8)
        if av.shape != (n,) or bv.shape != (n,):
            raise ValueError(f"{source}: wrong model length")
        if not validate_coloring(av, verts, edges, vidx, conditions=c88):
            raise ValueError(f"{source}: alpha is not an A model")
        if not validate_coloring(
            bv, verts, edges, vidx, require_port_diff=True
        ):
            raise ValueError(f"{source}: beta is not a B model")
        key = (av.tobytes(), bv.tobytes())
        if key not in seen:
            seen.add(key)
            seeds.append((av, bv, source))

    round1 = load_json(data_dir / "SEMANTIC_CEGIS_FINAL.json")
    if list(map(int, round1["verts"])) != verts:
        raise ValueError("round1 vertex order mismatch")
    for rec in round1["pair_library"]:
        add(rec["alpha"], rec["beta"], "round1")

    k4 = load_json(data_dir / "K4_CERTIFICATE.json")
    for rec in k4.get("survivor_witnesses", []):
        add(rec["alpha"], rec["beta"], "k4-survivor")

    return seeds


def budgeted_solve(solver, decision_budget: int):
    """Return (True/False/None, elapsed_wall_seconds).

    CaDiCaL 1.9.dev7 in PySAT does not expose a usable interrupt/clear-interrupt
    pair, but it does support decision budgets. Reaching the budget returns
    None (UNKNOWN). No caller may interpret None as UNSAT. The outer workflow
    timeout remains the independent hard wall-clock guard.
    """
    t0 = time.monotonic()
    if decision_budget <= 0:
        return None, 0.0

    solver.dec_budget(int(decision_budget))
    try:
        status = solver.solve_limited()
    finally:
        solver.dec_budget(-1)
    return status, time.monotonic() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, required=True)
    ap.add_argument("--checkpoint", type=Path, required=True)
    ap.add_argument("--result-dir", type=Path, required=True)
    ap.add_argument("--time-limit-sec", type=int, default=15000)
    ap.add_argument("--checkpoint-every", type=int, default=20)
    ap.add_argument("--query-decision-budget", type=int, default=2_000_000)
    ap.add_argument("--max-query-decision-budget", type=int, default=16_000_000)
    ap.add_argument("--fast-search-sec", type=float, default=20.0)
    ap.add_argument("--fast-restarts", type=int, default=48)
    args = ap.parse_args()

    t0 = time.monotonic()
    args.result_dir.mkdir(parents=True, exist_ok=True)

    final_path = args.result_dir / "FINAL.json"
    interface_path = args.result_dir / "INTERFACE.json"
    if final_path.exists() or interface_path.exists():
        log("terminal result already present; nothing to do")
        return 0

    verts, all_e, c88 = build_system(args.data_dir)
    n = len(verts)
    vidx = {v: i for i, v in enumerate(verts)}
    pi, qi = vidx[P], vidx[Q]
    nonports = [i for i in range(n) if i not in (pi, qi)]
    m = len(nonports)

    atoms = []
    atom_id = {}
    for ii, i in enumerate(nonports):
        for j in nonports[ii + 1:]:
            atom_id[(i, j)] = len(atoms)
            atoms.append((i, j))
    na = len(atoms)
    atom_i = np.asarray([p[0] for p in atoms], dtype=np.int32)
    atom_j = np.asarray([p[1] for p in atoms], dtype=np.int32)

    log(
        f"system n={n}, core_edges={len(all_e)}, C88={len(c88)}, "
        f"nonports={m}, port-free atoms={na}"
    )

    def cut_for_pair(av, bv):
        same_a = av[atom_i] == av[atom_j]
        same_b = bv[atom_i] == bv[atom_j]
        idx = np.flatnonzero(same_a != same_b)
        return idx.astype(int).tolist()

    new_pairs = []
    iterations = 0
    unresolved_records = []
    last_support_named = None
    stats = {
        "master_calls": 0,
        "master_unknown": 0,
        "oracle_calls": 0,
        "oracle_unknown": 0,
        "fast_candidates": 0,
        "max_master_sec": 0.0,
        "max_oracle_sec": 0.0,
    }
    if args.checkpoint.exists():
        with gzip.open(args.checkpoint, "rt", encoding="utf-8") as f:
            ck = json.load(f)
        if ck.get("upstream_sha") != UPSTREAM_SHA:
            raise RuntimeError("checkpoint upstream SHA mismatch")
        if ck.get("verts") != verts:
            raise RuntimeError("checkpoint vertex order mismatch")
        iterations = int(ck.get("iterations", 0))
        new_pairs = ck.get("new_pairs", [])
        unresolved_records = ck.get("unresolved_supports", [])
        last_support_named = ck.get("last_support")
        old_stats = ck.get("stats", {})
        for key in stats:
            if key in old_stats:
                stats[key] = old_stats[key]
        log(
            f"resume iterations={iterations}, new_pairs={len(new_pairs)}, "
            f"unresolved={len(unresolved_records)}"
        )

    if iterations != len(new_pairs):
        raise RuntimeError(
            f"checkpoint invariant failed: iterations={iterations}, "
            f"new_pairs={len(new_pairs)}"
        )

    seed_pairs = load_seed_pairs(args.data_dir, verts, all_e, c88, vidx)
    log(f"validated seed fooling pairs={len(seed_pairs)}")

    def Y(a):
        return a + 1

    z_of = {v_idx: na + rank + 1 for rank, v_idx in enumerate(nonports)}
    master = Cadical195()
    for a, (i, j) in enumerate(atoms):
        y = Y(a)
        zi, zj = z_of[i], z_of[j]
        master.add_clause([-y, zi])
        master.add_clause([-y, zj])
        master.add_clause([-zi, -zj, y])

    z_lits = [z_of[i] for i in nonports]
    card = CardEnc.equals(
        lits=z_lits,
        bound=4,
        top_id=max(z_lits),
        encoding=EncType.seqcounter,
    )
    for cl in card.clauses:
        master.add_clause(cl)

    BA, BB = 0, n * K
    oracle_base = coloring_cnf(verts, all_e, c88, vidx, BA)
    oracle_base += coloring_cnf(verts, all_e, [], vidx, BB)
    for c in range(K):
        oracle_base.append(
            [-(BB + pi * K + c + 1), -(BB + qi * K + c + 1)]
        )
    AUX0 = 2 * n * K

    def named_support(support):
        return [int(verts[i]) for i in sorted(support)]

    def support_key_from_named(support):
        return tuple(sorted(int(v) for v in support))

    unresolved = {}
    for rec in unresolved_records:
        key = support_key_from_named(rec["support"])
        unresolved[key] = {
            "support": list(key),
            "attempts": int(rec.get("attempts", 1)),
            "last_source": rec.get("last_source", "unknown"),
            "last_elapsed_sec": float(rec.get("last_elapsed_sec", 0.0)),
        }

    def record_timing(kind, status, elapsed):
        if kind == "master":
            stats["master_calls"] += 1
            stats["max_master_sec"] = max(float(stats["max_master_sec"]), elapsed)
            if status == "UNKNOWN":
                stats["master_unknown"] += 1
        elif kind == "oracle":
            stats["oracle_calls"] += 1
            stats["max_oracle_sec"] = max(float(stats["max_oracle_sec"]), elapsed)
            if status == "UNKNOWN":
                stats["oracle_unknown"] += 1

    def mark_unresolved(support, source, elapsed):
        ns = named_support(support)
        key = tuple(ns)
        rec = unresolved.get(key)
        if rec is None:
            rec = {
                "support": ns,
                "attempts": 0,
                "last_source": source,
                "last_elapsed_sec": elapsed,
            }
            unresolved[key] = rec
        rec["attempts"] += 1
        rec["last_source"] = source
        rec["last_elapsed_sec"] = round(float(elapsed), 3)
        return rec

    def clear_unresolved(support):
        unresolved.pop(tuple(named_support(support)), None)

    def oracle_for_support(support, decision_budget):
        selected = []
        for a_pos in range(4):
            for b_pos in range(a_pos + 1, 4):
                i, j = support[a_pos], support[b_pos]
                if i > j:
                    i, j = j, i
                selected.append(atom_id[(i, j)])

        cls = list(oracle_base)
        nv = AUX0
        for a in selected:
            i, j = atoms[a]
            ea, eb = nv + 1, nv + 2
            nv += 2
            for c in range(K):
                ai = BA + i * K + c + 1
                aj = BA + j * K + c + 1
                bi = BB + i * K + c + 1
                bj = BB + j * K + c + 1
                cls.append([-ea, -ai, aj])
                cls.append([-ea, ai, -aj])
                cls.append([ea, -ai, -aj])
                cls.append([-eb, -bi, bj])
                cls.append([-eb, bi, -bj])
                cls.append([eb, -bi, -bj])
            cls.append([-ea, eb])
            cls.append([ea, -eb])

        with Cadical195(bootstrap_with=cls) as s:
            raw, elapsed = budgeted_solve(s, decision_budget)
            if raw is None:
                status = "UNKNOWN"
                record_timing("oracle", status, elapsed)
                return status, None, elapsed
            if raw is False:
                status = "UNSAT"
                record_timing("oracle", status, elapsed)
                return status, None, elapsed
            pos = {lit for lit in s.get_model() if lit > 0}
            status = "SAT"
            record_timing("oracle", status, elapsed)
            return (
                status,
                (
                    decode_copy(pos, verts, vidx, BA),
                    decode_copy(pos, verts, vidx, BB),
                ),
                elapsed,
            )

    known_cut_count = len(seed_pairs) + len(new_pairs)
    blocks = max(1, (known_cut_count + 63) // 64)
    packed_cover = np.zeros((na, blocks), dtype=np.uint64)
    empty_cut_witness = None
    replayed = 0

    def replay_pair(av, bv, source, cut_index):
        nonlocal empty_cut_witness, replayed
        cut = cut_for_pair(av, bv)
        if not cut:
            empty_cut_witness = {
                "source": source,
                "alpha": av.astype(int).tolist(),
                "beta": bv.astype(int).tolist(),
            }
            return False
        master.add_clause([Y(a) for a in cut])
        block = cut_index >> 6
        bit = np.uint64(1) << np.uint64(cut_index & 63)
        idx = np.asarray(cut, dtype=np.int32)
        packed_cover[idx, block] |= bit
        replayed += 1
        return True

    cut_index = 0
    for av, bv, source in seed_pairs:
        if not replay_pair(av, bv, source, cut_index):
            break
        cut_index += 1

    if empty_cut_witness is None:
        for rec in new_pairs:
            av = np.asarray(rec["alpha"], dtype=np.int8)
            bv = np.asarray(rec["beta"], dtype=np.int8)
            if not validate_coloring(av, verts, all_e, vidx, conditions=c88):
                raise ValueError("checkpoint alpha is not an A model")
            if not validate_coloring(
                bv, verts, all_e, vidx, require_port_diff=True
            ):
                raise ValueError("checkpoint beta is not a B model")
            if not replay_pair(av, bv, "checkpoint", cut_index):
                break
            cut_index += 1

    if cut_index != known_cut_count and empty_cut_witness is None:
        raise RuntimeError(
            f"cut replay mismatch: replayed={cut_index}, expected={known_cut_count}"
        )

    coverage = [
        int.from_bytes(packed_cover[a].tobytes(), "little")
        for a in range(na)
    ]
    del packed_cover

    edge_cov = [[0] * n for _ in range(n)]
    for a, (i, j) in enumerate(atoms):
        val = coverage[a]
        edge_cov[i][j] = val
        edge_cov[j][i] = val

    def save_checkpoint(status="RUNNING"):
        atomic_gzip_json(
            args.checkpoint,
            {
                "version": 3,
                "status": status,
                "upstream_sha": UPSTREAM_SHA,
                "verts": verts,
                "iterations": iterations,
                "new_pairs": new_pairs,
                "unresolved_supports": sorted(
                    unresolved.values(), key=lambda r: tuple(r["support"])
                ),
                "last_support": last_support_named,
                "stats": stats,
                "elapsed_sec_this_run": round(time.monotonic() - t0, 3),
            },
        )

    if empty_cut_witness is not None:
        result = {
            "status": "NO-PORT-FREE-INTERFACE-ANY-SUPPORT",
            "reason": (
                "A/B fooling pair has identical equality pattern on all "
                "391 non-port vertices"
            ),
            "upstream_sha": UPSTREAM_SHA,
            "verts": verts,
            "witness": empty_cut_witness,
        }
        final_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        save_checkpoint("FINAL-GLOBAL-FOOLING-PAIR")
        log("strong terminal result: global port-free fooling pair found")
        return 0

    log(
        f"replayed sound cuts={replayed}; fast bitsets ready; "
        f"unresolved={len(unresolved)}"
    )

    def support_mask(support):
        a, b, c, d = support
        return (
            edge_cov[a][b]
            | edge_cov[a][c]
            | edge_cov[a][d]
            | edge_cov[b][c]
            | edge_cov[b][d]
            | edge_cov[c][d]
        )

    def uncovered_count(support):
        return known_cut_count - support_mask(support).bit_count()

    def idx_support_from_named(named):
        if not named:
            return None
        try:
            out = sorted(vidx[int(v)] for v in named)
        except (KeyError, TypeError, ValueError):
            return None
        if len(out) != 4 or len(set(out)) != 4 or any(v not in nonports for v in out):
            return None
        return out

    last_support = idx_support_from_named(last_support_named)

    def fast_candidate(time_budget_sec):
        nonlocal last_support
        if time_budget_sec <= 0:
            return None, None, 0.0
        start = time.monotonic()
        deadline = start + time_budget_sec
        rng = random.Random(
            (known_cut_count + 1) * 1000003 + (iterations + 1) * 9176
        )
        deferred = set(unresolved)
        best_seen = None
        best_score = known_cut_count + 1

        starts = []
        if last_support is not None:
            starts.append(list(last_support))
        while len(starts) < args.fast_restarts:
            starts.append(sorted(rng.sample(nonports, 4)))

        for support in starts:
            if time.monotonic() >= deadline:
                break
            support = sorted(support)
            score = uncovered_count(support)
            if score < best_score:
                best_score, best_seen = score, list(support)

            for _step in range(10):
                if time.monotonic() >= deadline:
                    break
                key = tuple(named_support(support))
                if score == 0 and key not in deferred:
                    return support, score, time.monotonic() - start
                if score == 0:
                    pos = rng.randrange(4)
                    used = set(support)
                    choices = [v for v in nonports if v not in used]
                    support[pos] = rng.choice(choices)
                    support.sort()
                    score = uncovered_count(support)
                    continue

                move = None
                move_score = score
                positions = [0, 1, 2, 3]
                rng.shuffle(positions)
                for pos in positions:
                    base = [support[k] for k in range(4) if k != pos]
                    used = set(base)
                    for v in nonports:
                        if v in used:
                            continue
                        cand = sorted(base + [v])
                        cand_score = uncovered_count(cand)
                        if cand_score < move_score:
                            move_score = cand_score
                            move = cand
                            if cand_score == 0:
                                break
                    if move_score == 0:
                        break
                    if time.monotonic() >= deadline:
                        break

                if move is None:
                    break
                support = move
                score = move_score
                if score < best_score:
                    best_score, best_seen = score, list(support)

        return None, best_score if best_seen is not None else None, time.monotonic() - start

    def add_new_cut(cut):
        nonlocal known_cut_count
        bit = 1 << known_cut_count
        for a in cut:
            val = coverage[a] | bit
            coverage[a] = val
            i, j = atoms[a]
            edge_cov[i][j] = val
            edge_cov[j][i] = val
        known_cut_count += 1

    def remaining_time():
        return args.time_limit_sec - (time.monotonic() - t0)

    while True:
        if remaining_time() <= 5:
            save_checkpoint("TIME-SLICE-COMPLETE")
            log(
                f"time slice complete: iterations={iterations}, "
                f"new_pairs={len(new_pairs)}, unresolved={len(unresolved)}"
            )
            return 75

        fast_budget = min(args.fast_search_sec, max(0.0, remaining_time() - 5.0))
        support, best_miss, fast_elapsed = fast_candidate(fast_budget)
        source = "fast"
        if support is not None:
            stats["fast_candidates"] += 1
            log(
                f"fast candidate support={named_support(support)} "
                f"search_sec={fast_elapsed:.3f}"
            )
        else:
            log(
                f"fast search found no candidate in {fast_elapsed:.3f}s "
                f"best_uncovered={best_miss}; invoking exact master"
            )
            budget = args.query_decision_budget
            raw, master_elapsed = budgeted_solve(master, budget)
            master_status = "UNKNOWN" if raw is None else ("SAT" if raw else "UNSAT")
            record_timing("master", master_status, master_elapsed)
            log(
                f"master status={master_status} elapsed={master_elapsed:.3f}s "
                f"budget={budget} cuts={known_cut_count}"
            )
            if raw is None:
                save_checkpoint("MASTER-UNKNOWN")
                return 75
            if raw is False:
                result = {
                    "status": "NO-PORT-FREE-SEMANTIC-INTERFACE(support<=4)",
                    "proof_scope": (
                        "all equality-atom interfaces supported on at most four "
                        "vertices, excluding ports 217 and 490"
                    ),
                    "method": (
                        "hybrid exact 4-set CEGIS; terminal claim comes only "
                        "from the unmodified exact SAT master returning UNSAT"
                    ),
                    "upstream_sha": UPSTREAM_SHA,
                    "verts": verts,
                    "iterations": iterations,
                    "seed_pair_count": len(seed_pairs),
                    "new_pair_count": len(new_pairs),
                    "unresolved_support_count": len(unresolved),
                    "stats": stats,
                }
                final_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
                save_checkpoint("FINAL-NO-INTERFACE")
                log("MASTER UNSAT: complete port-free support<=4 negative")
                return 0

            pos = {lit for lit in master.get_model() if lit > 0}
            support = sorted(i for i in nonports if z_of[i] in pos)
            if len(support) != 4:
                raise RuntimeError(f"master returned support size {len(support)}")
            source = "master"

        last_support = list(support)
        last_support_named = named_support(support)

        key = tuple(last_support_named)
        previous_unknowns = unresolved.get(key, {}).get("attempts", 0)
        decision_budget = min(
            args.max_query_decision_budget,
            args.query_decision_budget * (2 ** min(previous_unknowns, 3)),
        )
        if remaining_time() <= 5:
            save_checkpoint("TIME-SLICE-COMPLETE")
            return 75

        oracle_status, payload, oracle_elapsed = oracle_for_support(
            support, decision_budget
        )
        log(
            f"oracle source={source} support={last_support_named} "
            f"status={oracle_status} elapsed={oracle_elapsed:.3f}s "
            f"decision_budget={decision_budget}"
        )

        if oracle_status == "UNKNOWN":
            rec = mark_unresolved(support, source, oracle_elapsed)
            save_checkpoint("ORACLE-UNKNOWN")
            log(
                f"deferred support={rec['support']} attempts={rec['attempts']} "
                f"(no blocking clause added)"
            )
            if source == "master":
                return 75
            continue

        clear_unresolved(support)

        if oracle_status == "UNSAT":
            named_atoms = []
            for a_pos in range(4):
                for b_pos in range(a_pos + 1, 4):
                    named_atoms.append(
                        [last_support_named[a_pos], last_support_named[b_pos]]
                    )
            result = {
                "status": "PORT-FREE-SUPPORT4-SEMANTIC-INTERFACE-FOUND",
                "upstream_sha": UPSTREAM_SHA,
                "support": last_support_named,
                "atoms_complete_graph": named_atoms,
                "iterations": iterations,
                "seed_pair_count": len(seed_pairs),
                "new_pair_count": len(new_pairs),
                "oracle_elapsed_sec": round(oracle_elapsed, 3),
                "stats": stats,
            }
            interface_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
            save_checkpoint("FINAL-INTERFACE")
            log(f"INTERFACE FOUND: support={last_support_named}")
            return 0

        alpha, beta = payload
        av = np.asarray([alpha[v] for v in verts], dtype=np.int8)
        bv = np.asarray([beta[v] for v in verts], dtype=np.int8)
        cut = cut_for_pair(av, bv)
        rec = {
            "alpha": av.astype(int).tolist(),
            "beta": bv.astype(int).tolist(),
        }

        if not cut:
            result = {
                "status": "NO-PORT-FREE-INTERFACE-ANY-SUPPORT",
                "reason": (
                    "oracle produced A/B pair with identical equality "
                    "pattern on all 391 non-port vertices"
                ),
                "upstream_sha": UPSTREAM_SHA,
                "verts": verts,
                "iterations": iterations,
                "witness": rec,
                "stats": stats,
            }
            final_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
            save_checkpoint("FINAL-GLOBAL-FOOLING-PAIR")
            log("strong terminal result: global port-free fooling pair")
            return 0

        new_pairs.append(rec)
        iterations += 1
        master.add_clause([Y(a) for a in cut])
        add_new_cut(cut)

        if iterations % args.checkpoint_every == 0:
            save_checkpoint()
        log(
            f"iter={iterations} source={source} support={last_support_named} "
            f"cut={len(cut)} total_cuts={known_cut_count} "
            f"unresolved={len(unresolved)}"
        )


if __name__ == "__main__":
    raise SystemExit(main())
