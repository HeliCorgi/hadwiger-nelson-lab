#!/usr/bin/env python3
"""Monotone-resumable exact support-4 master.

This is a compatibility wrapper around exact_fourset_master.py. The original
master can resume only when the cut-library hash is unchanged. In CEGIS the
library grows monotonically: every SAT semantic-oracle witness appends one
additional difference-graph cut. A root branch proved empty for an old cut
library stays empty after more cuts are added, provided the root partition
(pivot cut and pivot-edge order) is held fixed.

State v2 therefore stores a hash of a separately persisted fixed root order and
allows resume across a verified prefix extension of the unique-cut library.
The candidate's own root is retried; only earlier fully exhausted roots are
reused. If any compatibility check fails, the search safely falls back to a
fresh root partition at rank zero.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import time
from itertools import combinations
from pathlib import Path
from typing import Optional

import exact_fourset_master as base

STATE_VERSION = 2
ROOT_ORDER_VERSION = 1
EXIT_SLICE_COMPLETE = base.EXIT_SLICE_COMPLETE


def atomic_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def cut_prefix_digest(lib: base.CutLibrary, count: int) -> str:
    if count < 0 or count > len(lib.cut_edge_masks):
        return ""
    h = hashlib.sha256()
    h.update(base.UPSTREAM_SHA.encode("ascii"))
    h.update(b"\0exact-fourset-cut-library-v1\0")
    h.update(json.dumps(lib.nonport_vertex_ids, separators=(",", ":")).encode("ascii"))
    edge_bytes = (len(lib.atoms) + 7) // 8
    for mask in lib.cut_edge_masks[:count]:
        h.update(mask.to_bytes(edge_bytes, "little"))
    return h.hexdigest()


def root_order_digest(pivot_cut: int, atoms: list[int]) -> str:
    h = hashlib.sha256()
    h.update(b"exact-fourset-fixed-root-order-v1\0")
    h.update(str(int(pivot_cut)).encode("ascii"))
    h.update(b"\0")
    for atom in atoms:
        h.update(int(atom).to_bytes(4, "little", signed=False))
    return h.hexdigest()


def decode_cut_atoms(lib: base.CutLibrary, cut_index: int) -> list[int]:
    mask = lib.cut_edge_masks[cut_index]
    out: list[int] = []
    while mask:
        lsb = mask & -mask
        out.append(lsb.bit_length() - 1)
        mask ^= lsb
    return out


class FixedRootSearch(base.ExactFourSetSearch):
    """Original exact search with an optionally frozen root partition."""

    def __init__(
        self,
        lib: base.CutLibrary,
        lookahead_cuts: int = 32,
        deadline: Optional[float] = None,
        fixed_pivot_cut: Optional[int] = None,
        fixed_pivot_atoms: Optional[list[int]] = None,
    ):
        super().__init__(lib, lookahead_cuts=lookahead_cuts, deadline=deadline)
        if fixed_pivot_cut is None:
            if fixed_pivot_atoms is not None:
                raise ValueError("fixed_pivot_atoms requires fixed_pivot_cut")
            return

        t = int(fixed_pivot_cut)
        if t < 0 or t >= len(lib.cut_edge_masks):
            raise ValueError("fixed pivot cut is outside current cut library")
        actual = decode_cut_atoms(lib, t)
        if fixed_pivot_atoms is None:
            # Used only for a v1 state with the exact same library. Reproduce
            # the old deterministic strength ordering under that same library.
            order = list(actual)
            order.sort(
                key=lambda a: (
                    -lib.edge_cov[lib.atoms[a][0]][lib.atoms[a][1]].bit_count(),
                    a,
                )
            )
        else:
            order = [int(a) for a in fixed_pivot_atoms]
            if len(order) != len(actual) or len(set(order)) != len(order):
                raise ValueError("fixed pivot order has wrong length or duplicates")
            if set(order) != set(actual):
                raise ValueError("fixed pivot order is not exactly the pivot cut")

        self.pivot_cut = t
        self.pivot_atoms = order
        self.pivot_rank = {a: r for r, a in enumerate(order)}
        self._decoded_cache[t] = list(order)


def load_root_order(path: Path, expected_sha: str) -> tuple[int, list[int]]:
    d = base.load_json(path)
    if int(d.get("version", -1)) != ROOT_ORDER_VERSION:
        raise ValueError("root-order version mismatch")
    pivot = int(d["pivot_cut_index"])
    atoms = [int(a) for a in d["pivot_atom_order"]]
    got = root_order_digest(pivot, atoms)
    if d.get("sha256") != got or got != expected_sha:
        raise ValueError("root-order digest mismatch")
    return pivot, atoms


def save_root_order(path: Path, pivot_cut: int, atoms: list[int]) -> str:
    digest = root_order_digest(pivot_cut, atoms)
    atomic_json(
        path,
        {
            "version": ROOT_ORDER_VERSION,
            "pivot_cut_index": int(pivot_cut),
            "pivot_atom_order": [int(a) for a in atoms],
            "sha256": digest,
        },
    )
    return digest


def choose_resume(
    lib: base.CutLibrary,
    previous: dict,
    root_order_path: Path,
) -> tuple[int, Optional[int], Optional[list[int]], str]:
    """Choose an auditable, sound resume mode.

    Cross-library resume is accepted only for a cryptographically verified
    prefix extension of the old ordered unique-cut library.
    """
    if not previous:
        return 0, None, None, "fresh-no-state"
    if previous.get("upstream_sha") != base.UPSTREAM_SHA:
        return 0, None, None, "fresh-upstream-mismatch"

    try:
        old_n = int(previous["unique_cut_count"])
        old_digest = str(previous["cut_library_sha256"])
        old_pivot = int(previous["pivot_cut_index"])
        old_root_count = int(previous["pivot_root_edge_count"])
        start = int(previous.get("next_root_rank", 0))
    except (KeyError, TypeError, ValueError):
        return 0, None, None, "fresh-incomplete-state"

    if old_n > len(lib.cut_edge_masks):
        return 0, None, None, "fresh-cut-count-regressed"
    if cut_prefix_digest(lib, old_n) != old_digest:
        return 0, None, None, "fresh-nonprefix-library"
    if not (0 <= start <= old_root_count):
        return 0, None, None, "fresh-invalid-root-rank"

    version = int(previous.get("version", 1))
    same_library = old_n == len(lib.cut_edge_masks) and old_digest == lib.digest

    if version >= STATE_VERSION:
        try:
            pivot, atoms = load_root_order(
                root_order_path, str(previous["root_order_sha256"])
            )
        except (OSError, KeyError, TypeError, ValueError) as exc:
            base.log(f"monotone resume rejected: {exc}")
            return 0, None, None, "fresh-root-order-invalid"
        if pivot != old_pivot or len(atoms) != old_root_count:
            return 0, None, None, "fresh-root-partition-mismatch"
        mode = "resume-same-library-v2" if same_library else "resume-monotone-prefix-v2"
        return start, pivot, atoms, mode

    # State v1 did not persist the root order. It is safe to upgrade only if
    # the library itself is unchanged, because the old deterministic ordering
    # can then be reproduced exactly.
    if version == 1 and same_library:
        return start, old_pivot, None, "resume-same-library-v1-upgrade"

    return 0, None, None, "fresh-v1-cannot-cross-library"


def _toy_lib(m: int, edge_sets: list[set[int]]) -> base.CutLibrary:
    atoms = list(combinations(range(m), 2))
    aid = [[-1] * m for _ in range(m)]
    for i, (u, v) in enumerate(atoms):
        aid[u][v] = aid[v][u] = i
    edge_cov = [[0] * m for _ in range(m)]
    cut_masks: list[int] = []
    cut_sizes: list[int] = []
    for t, cut in enumerate(edge_sets):
        em = 0
        for a in cut:
            u, v = atoms[a]
            edge_cov[u][v] |= 1 << t
            edge_cov[v][u] |= 1 << t
            em |= 1 << a
        cut_masks.append(em)
        cut_sizes.append(len(cut))
    vmask = []
    for u in range(m):
        x = 0
        for v in range(m):
            x |= edge_cov[u][v]
        vmask.append(x)
    return base.CutLibrary(
        nonport_vertex_ids=list(range(m)), atoms=atoms, atom_id=aid,
        edge_cov=edge_cov, vertex_cut_mask=vmask,
        cut_edge_masks=cut_masks, cut_sizes=cut_sizes,
        cut_sources=[f"toy:{i}" for i in range(len(edge_sets))],
        all_cuts_mask=(1 << len(edge_sets)) - 1,
        digest=f"toy-{len(edge_sets)}", full_pair_count=len(edge_sets),
        duplicate_cut_count=0, empty_cut_source=None,
    )


def _brute_exists(lib: base.CutLibrary) -> bool:
    for support in combinations(range(len(lib.nonport_vertex_ids)), 4):
        cov = 0
        for u, v in combinations(support, 2):
            cov |= lib.edge_cov[u][v]
        if cov == lib.all_cuts_mask:
            return True
    return False


def run_self_test() -> None:
    base.run_self_test()
    rng = random.Random(0x4D4F4E4F)
    checked = 0
    skipped_positive = 0
    for _ in range(120):
        m = rng.randint(7, 10)
        atoms = list(combinations(range(m), 2))
        cuts: list[set[int]] = []
        for _j in range(rng.randint(3, 12)):
            p = rng.uniform(0.08, 0.65)
            cut = {a for a in range(len(atoms)) if rng.random() < p}
            if not cut:
                cut.add(rng.randrange(len(atoms)))
            cuts.append(cut)
        old = _toy_lib(m, cuts)
        old_search = FixedRootSearch(old, lookahead_cuts=8)
        old_result = old_search.search()
        if old_result["status"] != "CANDIDATE":
            continue
        support = set(old_result["support_positions"])
        outside_atoms = [
            a for a, (u, v) in enumerate(atoms)
            if u not in support and v not in support
        ]
        if not outside_atoms:
            continue
        # New cut blocks the old candidate. Earlier completed root branches
        # remain impossible by monotonicity, so retry only the candidate root.
        new = _toy_lib(m, cuts + [{rng.choice(outside_atoms)}])
        resumed = FixedRootSearch(
            new,
            lookahead_cuts=8,
            fixed_pivot_cut=old_search.pivot_cut,
            fixed_pivot_atoms=list(old_search.pivot_atoms),
        ).search(start_root_rank=int(old_result["root_rank"]))
        found = resumed["status"] == "CANDIDATE"
        brute = _brute_exists(new)
        if found != brute:
            raise AssertionError(
                f"monotone-resume mismatch: root={old_result['root_rank']} "
                f"found={found} brute={brute}"
            )
        checked += 1
        if int(old_result["root_rank"]) > 0:
            skipped_positive += 1
    if checked < 20 or skipped_positive < 1:
        raise AssertionError(
            f"insufficient monotone-resume coverage: checked={checked}, "
            f"positive-skips={skipped_positive}"
        )
    print(
        f"monotone-resume self-test OK: {checked} extensions matched brute force; "
        f"{skipped_positive} reused at least one completed root"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path)
    ap.add_argument("--checkpoint", type=Path)
    ap.add_argument("--result-dir", type=Path, default=Path("results/exact-fourset-master"))
    ap.add_argument("--state", type=Path)
    ap.add_argument("--time-limit-sec", type=int, default=14_400)
    ap.add_argument("--lookahead-cuts", type=int, default=32)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        run_self_test()
        return 0
    if args.data_dir is None or args.checkpoint is None:
        ap.error("--data-dir and --checkpoint are required unless --self-test is used")

    result_dir = args.result_dir
    result_dir.mkdir(parents=True, exist_ok=True)
    state_path = args.state or (result_dir / "STATE.json")
    root_order_path = result_dir / "ROOT_ORDER.json"
    library_path = result_dir / "LIBRARY.json"
    candidate_path = result_dir / "CANDIDATE.json"
    final_path = result_dir / "FINAL.json"

    verts, edges, c88 = base.build_system(args.data_dir)
    pairs, seed_count, iterations, checkpoint_status = base.load_pair_library(
        args.data_dir, args.checkpoint, verts, edges, c88
    )
    base.log(
        f"validated pair library: seeds={seed_count}, lab={iterations}, "
        f"total={len(pairs)}, checkpoint_status={checkpoint_status}"
    )

    t_build = time.monotonic()
    lib = base.build_cut_library(pairs, verts)
    summary = base.library_summary(lib, iterations, checkpoint_status, seed_count)
    atomic_json(library_path, summary)
    base.log(f"cut library built in {time.monotonic() - t_build:.1f}s")

    if lib.empty_cut_source is not None:
        result = {
            **summary,
            "status": "GLOBAL-EMPTY-DIFFERENCE-CUT",
            "statement": (
                "A validated A/B fooling pair has identical equality pattern on all "
                "391 non-port vertices; no port-free equality interface of any support exists."
            ),
        }
        atomic_json(final_path, result)
        atomic_json(state_path, {**result, "version": STATE_VERSION})
        base.log(f"terminal global empty cut from {lib.empty_cut_source}")
        return 0

    previous = base.load_json(state_path) if state_path.exists() else {}
    start_root_rank, fixed_pivot, fixed_atoms, resume_mode = choose_resume(
        lib, previous, root_order_path
    )

    search = FixedRootSearch(
        lib,
        lookahead_cuts=args.lookahead_cuts,
        deadline=(time.monotonic() + args.time_limit_sec) if args.time_limit_sec > 0 else None,
        fixed_pivot_cut=fixed_pivot,
        fixed_pivot_atoms=fixed_atoms,
    )

    # A v1 exact-library upgrade must reproduce the old root partition before
    # accepting its completed-prefix rank.
    if resume_mode == "resume-same-library-v1-upgrade":
        if (
            search.pivot_cut != int(previous["pivot_cut_index"])
            or len(search.pivot_atoms) != int(previous["pivot_root_edge_count"])
        ):
            base.log("v1 upgrade root partition mismatch; restarting at root zero")
            search = FixedRootSearch(
                lib,
                lookahead_cuts=args.lookahead_cuts,
                deadline=(time.monotonic() + args.time_limit_sec) if args.time_limit_sec > 0 else None,
            )
            start_root_rank = 0
            resume_mode = "fresh-v1-root-partition-mismatch"

    root_sha = save_root_order(root_order_path, search.pivot_cut, list(search.pivot_atoms))
    pivot_atom = search.pivot_atoms[0]
    pu, pv = lib.atoms[pivot_atom]
    pivot_info = {
        "pivot_cut_index": search.pivot_cut,
        "pivot_cut_source": lib.cut_sources[search.pivot_cut],
        "pivot_cut_size": lib.cut_sizes[search.pivot_cut],
        "pivot_root_edge_count": len(search.pivot_atoms),
        "first_pivot_edge_positions": [pu, pv],
        "first_pivot_edge_vertices": [lib.nonport_vertex_ids[pu], lib.nonport_vertex_ids[pv]],
        "root_order_sha256": root_sha,
        "resume_mode": resume_mode,
    }
    summary.update(pivot_info)
    atomic_json(library_path, summary)
    base.log(
        f"unique cuts={summary['unique_cut_count']} duplicates={summary['duplicate_cut_count']} "
        f"cut-size min/median/max={summary['cut_size_min']}/"
        f"{summary['cut_size_median']}/{summary['cut_size_max']}"
    )
    base.log(
        f"pivot cut={search.pivot_cut} source={lib.cut_sources[search.pivot_cut]} "
        f"edges={len(search.pivot_atoms)} resume_mode={resume_mode} "
        f"start_root_rank={start_root_rank}"
    )

    # Only stale outputs are removed. STATE and ROOT_ORDER are the resumable
    # exact-search prefix and must survive CEGIS cut additions.
    candidate_path.unlink(missing_ok=True)
    final_path.unlink(missing_ok=True)

    base_state = {
        "version": STATE_VERSION,
        **summary,
        "method": "exact edge-branching four-set master with monotone cut-extension resume",
        "next_root_rank": start_root_rank,
        "status": "RUNNING",
    }

    def root_complete(next_rank: int) -> None:
        base_state["next_root_rank"] = next_rank
        base_state["status"] = "RUNNING"
        base_state["last_process_stats"] = dict(search.stats)
        atomic_json(state_path, base_state)

    try:
        result = search.search(start_root_rank=start_root_rank, on_root_complete=root_complete)
    except base.SliceTimeout:
        base_state["status"] = "TIME-SLICE-COMPLETE"
        base_state["last_process_stats"] = dict(search.stats)
        atomic_json(state_path, base_state)
        base.log(
            f"time slice complete; next_root_rank={base_state['next_root_rank']} "
            f"of {len(search.pivot_atoms)}"
        )
        return EXIT_SLICE_COMPLETE

    if result["status"] == "CANDIDATE":
        pos = result["support_positions"]
        named = [lib.nonport_vertex_ids[i] for i in pos]
        cov = search._support_cov(tuple(pos))
        if cov != lib.all_cuts_mask:
            raise RuntimeError("internal error: reported candidate does not cover all cuts")
        out = {
            **summary,
            "status": "FOURSET-CANDIDATE",
            "support_positions": pos,
            "support_vertices": named,
            "root_rank": result["root_rank"],
            "root_edge_positions": result["root_edge_positions"],
            "covers_all_unique_cuts": True,
            "search_stats": search.stats,
            "next_step": (
                "Send this support to the exact A/B semantic oracle. Oracle SAT adds "
                "another sound fooling-pair cut; oracle UNSAT yields a support-4 interface candidate."
            ),
        }
        atomic_json(candidate_path, out)
        base_state.update(out)
        # Candidate root is deliberately not certified complete. If the oracle
        # adds a cut, monotone resume retries exactly this root.
        base_state["next_root_rank"] = result["root_rank"]
        atomic_json(state_path, base_state)
        base.log(f"candidate found: support={named} root_rank={result['root_rank']}")
        return 0

    if result["status"] != "EXHAUSTED":
        raise RuntimeError(f"unexpected search result: {result}")

    out = {
        **summary,
        "status": "EXACT-MASTER-EXHAUSTED-REQUIRES-INDEPENDENT-VERIFY",
        "statement": (
            "No four-set of the 391 non-port vertices hits every validated unique "
            "difference-graph cut in this library."
        ),
        "implication_if_independently_verified": (
            "For the pinned A/B system, no port-free equality semantic interface "
            "supported on at most four vertices exists."
        ),
        "search_stats": search.stats,
        "completed_pivot_root_edges": len(search.pivot_atoms),
        "proof_note": (
            "Every four-set hits the fixed pivot cut and is assigned to its earliest "
            "fixed pivot edge. Completed roots from an older prefix cut library remain "
            "impossible after additional cuts are appended. Independent verification "
            "is still required before theorem promotion."
        ),
    }
    atomic_json(final_path, out)
    base_state.update(out)
    base_state["next_root_rank"] = len(search.pivot_atoms)
    atomic_json(state_path, base_state)
    base.log("EXACT MASTER EXHAUSTED: independent verification required before promotion")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
