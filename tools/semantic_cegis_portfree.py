#!/usr/bin/env python3
"""
Exact, resumable CEGIS for the remaining port-free support-4 semantic interface.

Pinned upstream: HeliCorgi/five-color-forcing-anatomy
commit d1e80998bda337d9fa721f2e96d203ae54e97fc8.

A = H* ∧ C88.
B = H* ∧ (c(217) != c(490)).

For a 4-set S of non-port vertices, compare only the equality partition on S.
If Mod(A)|S and Mod(B)|S are disjoint, the six equality atoms on S form a
semantic interface. Conversely, every equality-atom interface supported on
<=4 non-port vertices extends monotonically to a separating 4-set. Therefore
exhausting all 4-sets is complete for the port-free support<=4 question.

Master:
  choose exactly four non-port vertices z_i;
  y_ij <-> (z_i and z_j);
  for each known A/B fooling pair, require at least one y_ij on which their
  equality patterns differ.

Oracle:
  for the chosen 4-set, ask whether an A-model and B-model have the same
  complete equality pattern on all six pairs.
  SAT  -> add that fooling pair as a sound master cut.
  UNSAT -> genuine support-4 semantic interface.

The checkpoint stores only newly found fooling pairs. Seed pairs are reloaded
from the pinned upstream handoff each invocation.
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, required=True)
    ap.add_argument("--checkpoint", type=Path, required=True)
    ap.add_argument("--result-dir", type=Path, required=True)
    ap.add_argument("--time-limit-sec", type=int, default=15000)
    ap.add_argument("--checkpoint-every", type=int, default=20)
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

    # Pair atom universe among the 391 non-port vertices.
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

    # Master variable layout:
    # y_a = a+1, z_i = na + rank(i) + 1.
    def Y(a):
        return a + 1

    z_of = {v_idx: na + rank + 1 for rank, v_idx in enumerate(nonports)}
    master = Cadical195()

    # y_ij <-> (z_i & z_j)
    for a, (i, j) in enumerate(atoms):
        y = Y(a)
        zi, zj = z_of[i], z_of[j]
        master.add_clause([-y, zi])
        master.add_clause([-y, zj])
        master.add_clause([-zi, -zj, y])

    # Exactly four support vertices. Searching exactly four is complete for
    # support<=4 because separation is monotone under adding support vertices.
    z_lits = [z_of[i] for i in nonports]
    card = CardEnc.equals(
        lits=z_lits,
        bound=4,
        top_id=max(z_lits),
        encoding=EncType.seqcounter,
    )
    for cl in card.clauses:
        master.add_clause(cl)

    # Oracle base: A copy and B copy.
    BA, BB = 0, n * K
    oracle_base = coloring_cnf(verts, all_e, c88, vidx, BA)
    oracle_base += coloring_cnf(verts, all_e, [], vidx, BB)
    for c in range(K):
        oracle_base.append(
            [-(BB + pi * K + c + 1), -(BB + qi * K + c + 1)]
        )
    AUX0 = 2 * n * K

    def oracle_for_support(support):
        # Complete equality pattern on the 4-set = all six atoms.
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
            if not s.solve():
                return None
            pos = {lit for lit in s.get_model() if lit > 0}
            return (
                decode_copy(pos, verts, vidx, BA),
                decode_copy(pos, verts, vidx, BB),
            )

    def cut_for_pair(av, bv):
        same_a = av[atom_i] == av[atom_j]
        same_b = bv[atom_i] == bv[atom_j]
        idx = np.flatnonzero(same_a != same_b)
        return idx.astype(int).tolist()

    # Resume newly discovered pair library.
    new_pairs = []
    iterations = 0
    if args.checkpoint.exists():
        with gzip.open(args.checkpoint, "rt", encoding="utf-8") as f:
            ck = json.load(f)
        if ck.get("upstream_sha") != UPSTREAM_SHA:
            raise RuntimeError("checkpoint upstream SHA mismatch")
        if ck.get("verts") != verts:
            raise RuntimeError("checkpoint vertex order mismatch")
        iterations = int(ck.get("iterations", 0))
        new_pairs = ck.get("new_pairs", [])
        log(f"resume iterations={iterations}, new_pairs={len(new_pairs)}")

    seed_pairs = load_seed_pairs(args.data_dir, verts, all_e, c88, vidx)
    log(f"validated seed fooling pairs={len(seed_pairs)}")

    empty_cut_witness = None
    replayed = 0

    def replay_pair(av, bv, source):
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
        replayed += 1
        return True

    for av, bv, source in seed_pairs:
        if not replay_pair(av, bv, source):
            break

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
            if not replay_pair(av, bv, "checkpoint"):
                break

    def save_checkpoint(status="RUNNING"):
        atomic_gzip_json(
            args.checkpoint,
            {
                "version": 2,
                "status": status,
                "upstream_sha": UPSTREAM_SHA,
                "verts": verts,
                "iterations": iterations,
                "new_pairs": new_pairs,
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

    log(f"replayed sound cuts={replayed}")

    while True:
        elapsed = time.monotonic() - t0
        if elapsed >= args.time_limit_sec:
            save_checkpoint("TIME-SLICE-COMPLETE")
            log(
                f"time slice complete: iterations={iterations}, "
                f"new_pairs={len(new_pairs)}"
            )
            return 75

        iterations += 1
        if not master.solve():
            result = {
                "status": "NO-PORT-FREE-SEMANTIC-INTERFACE(support<=4)",
                "proof_scope": (
                    "all equality-atom interfaces supported on at most four "
                    "vertices, excluding ports 217 and 490"
                ),
                "method": (
                    "exact 4-set CEGIS; any <=3 separating support extends "
                    "monotonically to a separating 4-set"
                ),
                "upstream_sha": UPSTREAM_SHA,
                "verts": verts,
                "iterations": iterations,
                "seed_pair_count": len(seed_pairs),
                "new_pair_count": len(new_pairs),
            }
            final_path.write_text(
                json.dumps(result, indent=2), encoding="utf-8"
            )
            save_checkpoint("FINAL-NO-INTERFACE")
            log("MASTER UNSAT: complete port-free support<=4 negative")
            return 0

        pos = {lit for lit in master.get_model() if lit > 0}
        support = [i for i in nonports if z_of[i] in pos]
        if len(support) != 4:
            raise RuntimeError(f"master returned support size {len(support)}")

        r = oracle_for_support(support)
        if r is None:
            named_support = [int(verts[i]) for i in support]
            named_atoms = []
            for a_pos in range(4):
                for b_pos in range(a_pos + 1, 4):
                    named_atoms.append(
                        [named_support[a_pos], named_support[b_pos]]
                    )
            result = {
                "status": "PORT-FREE-SUPPORT4-SEMANTIC-INTERFACE-FOUND",
                "upstream_sha": UPSTREAM_SHA,
                "support": named_support,
                "atoms_complete_graph": named_atoms,
                "iterations": iterations,
                "seed_pair_count": len(seed_pairs),
                "new_pair_count": len(new_pairs),
            }
            interface_path.write_text(
                json.dumps(result, indent=2), encoding="utf-8"
            )
            save_checkpoint("FINAL-INTERFACE")
            log(f"INTERFACE FOUND: support={named_support}")
            return 0

        alpha, beta = r
        av = np.asarray([alpha[v] for v in verts], dtype=np.int8)
        bv = np.asarray([beta[v] for v in verts], dtype=np.int8)
        cut = cut_for_pair(av, bv)
        rec = {
            "alpha": av.astype(int).tolist(),
            "beta": bv.astype(int).tolist(),
        }
        new_pairs.append(rec)

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
            }
            final_path.write_text(
                json.dumps(result, indent=2), encoding="utf-8"
            )
            save_checkpoint("FINAL-GLOBAL-FOOLING-PAIR")
            log("strong terminal result: global port-free fooling pair")
            return 0

        master.add_clause([Y(a) for a in cut])

        if iterations % args.checkpoint_every == 0:
            save_checkpoint()
            log(
                f"iter={iterations} support="
                f"{[int(verts[i]) for i in support]} "
                f"cut={len(cut)} new_pairs={len(new_pairs)}"
            )


if __name__ == "__main__":
    raise SystemExit(main())
