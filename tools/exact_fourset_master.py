#!/usr/bin/env python3
"""Exact specialized master for the port-free support-4 semantic search.

This program consumes the validated A/B fooling-pair library stored in the
semantic CEGIS checkpoint and decides the purely combinatorial master problem:

    does some four-set of the 391 non-port vertices contain an edge from every
    accumulated difference graph?

Each fooling pair (alpha,beta) defines a difference graph D_t whose edge uv is
present iff [alpha(u)=alpha(v)] != [beta(u)=beta(v)].  Any equality-based
separator supported on four vertices must contain at least one edge of every
D_t.  Therefore exact exhaustion of this master is already a complete negative
for port-free equality interfaces of support <= 4 for the pinned system.

The search does not use SAT.  It branches on edges of an uncovered difference
graph:

  * choose the sparsest difference graph as a root pivot;
  * every solution must contain one of its edges, so enumerate those root edges;
  * from a selected pair, choose another uncovered cut and branch on all ways
    an edge of that cut can fit into the two remaining vertex slots;
  * from a selected triple, choose an uncovered cut and branch only on fourth
    vertices adjacent to the triple in that cut;
  * at four vertices, check the six edge-coverage bitsets exactly.

Heuristics affect only branch order.  They never remove a logically possible
branch.  Root-edge canonicalization assigns every four-set to the earliest
pivot edge that it contains, avoiding duplicate work without changing the
answer.

A time slice may stop with exit code 75.  Progress is checkpointed only between
fully exhausted root-edge branches; a timed-out root branch is retried from its
start on the next invocation.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import random
import statistics
import time
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Callable, Optional

import numpy as np

K = 5
P, Q = 217, 490
UPSTREAM_SHA = "d1e80998bda337d9fa721f2e96d203ae54e97fc8"
STATE_VERSION = 1
EXIT_SLICE_COMPLETE = 75


def log(msg: str) -> None:
    print(msg, flush=True)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def atomic_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")
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
    edges = sorted({(min(u, v), max(u, v)) for (u, v) in hstar})
    verts = sorted({x for e in edges for x in e} | {x for e in c88 for x in e})
    if len(verts) != 393:
        raise RuntimeError(f"expected 393 vertices, got {len(verts)}")
    if P not in verts or Q not in verts:
        raise RuntimeError("ports missing from system")
    return verts, edges, c88


def coloring_valid(arr: np.ndarray, edge_i, edge_j, cond_i=(), cond_j=(),
                   pi: Optional[int] = None, qi: Optional[int] = None) -> bool:
    if arr.ndim != 1:
        return False
    if np.any(arr < 0) or np.any(arr >= K):
        return False
    if np.any(arr[edge_i] == arr[edge_j]):
        return False
    if len(cond_i) and np.any(arr[cond_i] != arr[cond_j]):
        return False
    if pi is not None and qi is not None and arr[pi] == arr[qi]:
        return False
    return True


@dataclass
class PairRecord:
    alpha: np.ndarray
    beta: np.ndarray
    source: str


def load_pair_library(data_dir: Path, checkpoint: Path, verts, edges, c88):
    n = len(verts)
    vidx = {v: i for i, v in enumerate(verts)}
    pi, qi = vidx[P], vidx[Q]
    edge_i = np.asarray([vidx[u] for u, _ in edges], dtype=np.int32)
    edge_j = np.asarray([vidx[v] for _, v in edges], dtype=np.int32)
    cond_i = np.asarray([vidx[u] for u, _ in c88], dtype=np.int32)
    cond_j = np.asarray([vidx[v] for _, v in c88], dtype=np.int32)

    out: list[PairRecord] = []
    seen_pairs = set()

    def add(alpha, beta, source, dedup_pair=True):
        av = np.asarray(alpha, dtype=np.int8)
        bv = np.asarray(beta, dtype=np.int8)
        if av.shape != (n,) or bv.shape != (n,):
            raise ValueError(f"{source}: wrong model length")
        if not coloring_valid(av, edge_i, edge_j, cond_i, cond_j):
            raise ValueError(f"{source}: alpha is not a valid A model")
        if not coloring_valid(bv, edge_i, edge_j, pi=pi, qi=qi):
            raise ValueError(f"{source}: beta is not a valid B model")
        key = (av.tobytes(), bv.tobytes())
        if dedup_pair and key in seen_pairs:
            return
        seen_pairs.add(key)
        out.append(PairRecord(av, bv, source))

    round1 = load_json(data_dir / "SEMANTIC_CEGIS_FINAL.json")
    if list(map(int, round1["verts"])) != verts:
        raise ValueError("round1 vertex order mismatch")
    for i, rec in enumerate(round1["pair_library"]):
        add(rec["alpha"], rec["beta"], f"round1:{i}")

    k4 = load_json(data_dir / "K4_CERTIFICATE.json")
    for i, rec in enumerate(k4.get("survivor_witnesses", [])):
        add(rec["alpha"], rec["beta"], f"k4-survivor:{i}")

    seed_count = len(out)
    if seed_count != 872:
        raise RuntimeError(f"expected 872 validated seed pairs, got {seed_count}")

    with gzip.open(checkpoint, "rt", encoding="utf-8") as f:
        ck = json.load(f)
    if ck.get("upstream_sha") != UPSTREAM_SHA:
        raise RuntimeError("checkpoint upstream SHA mismatch")
    if ck.get("verts") != verts:
        raise RuntimeError("checkpoint vertex order mismatch")
    new_pairs = ck.get("new_pairs", [])
    iterations = int(ck.get("iterations", -1))
    if iterations != len(new_pairs):
        raise RuntimeError(
            f"checkpoint invariant failed: iterations={iterations}, new_pairs={len(new_pairs)}"
        )
    for i, rec in enumerate(new_pairs):
        # Preserve every recorded checkpoint pair so pair counts match it. Exact
        # duplicate difference graphs are collapsed later because they are
        # logically redundant master constraints.
        add(rec["alpha"], rec["beta"], f"checkpoint:{i}", dedup_pair=False)

    return out, seed_count, iterations, ck.get("status", "UNKNOWN")


@dataclass
class CutLibrary:
    nonport_vertex_ids: list[int]
    atoms: list[tuple[int, int]]
    atom_id: list[list[int]]
    edge_cov: list[list[int]]
    vertex_cut_mask: list[int]
    cut_edge_masks: list[int]
    cut_sizes: list[int]
    cut_sources: list[str]
    all_cuts_mask: int
    digest: str
    full_pair_count: int
    duplicate_cut_count: int
    empty_cut_source: Optional[str]


def build_cut_library(pair_records: list[PairRecord], verts: list[int]) -> CutLibrary:
    n = len(verts)
    vidx = {v: i for i, v in enumerate(verts)}
    pi, qi = vidx[P], vidx[Q]
    nonport_full = [i for i in range(n) if i not in (pi, qi)]
    nonport_vertex_ids = [int(verts[i]) for i in nonport_full]
    m = len(nonport_full)
    if m != 391:
        raise RuntimeError(f"expected 391 nonports, got {m}")

    atoms: list[tuple[int, int]] = []
    atom_id = [[-1] * m for _ in range(m)]
    atom_i_full = []
    atom_j_full = []
    for u in range(m):
        for v in range(u + 1, m):
            a = len(atoms)
            atoms.append((u, v))
            atom_id[u][v] = atom_id[v][u] = a
            atom_i_full.append(nonport_full[u])
            atom_j_full.append(nonport_full[v])
    atom_i_full = np.asarray(atom_i_full, dtype=np.int32)
    atom_j_full = np.asarray(atom_j_full, dtype=np.int32)
    na = len(atoms)
    if na != 76245:
        raise RuntimeError(f"expected 76245 atoms, got {na}")

    # First pass: build combinatorial cuts and collapse exact duplicate
    # difference graphs. Duplicate cuts are logically redundant.
    unique_records: list[PairRecord] = []
    cut_edge_masks: list[int] = []
    cut_sizes: list[int] = []
    cut_sources: list[str] = []
    seen_cut_masks: dict[int, int] = {}
    duplicate_cut_count = 0
    empty_cut_source = None

    for idx, rec in enumerate(pair_records):
        same_a = rec.alpha[atom_i_full] == rec.alpha[atom_j_full]
        same_b = rec.beta[atom_i_full] == rec.beta[atom_j_full]
        diff = same_a != same_b
        size = int(np.count_nonzero(diff))
        if size == 0:
            empty_cut_source = rec.source
            break
        edge_mask = int.from_bytes(
            np.packbits(diff, bitorder="little").tobytes(), "little"
        )
        if edge_mask in seen_cut_masks:
            duplicate_cut_count += 1
            continue
        seen_cut_masks[edge_mask] = len(cut_edge_masks)
        unique_records.append(rec)
        cut_edge_masks.append(edge_mask)
        cut_sizes.append(size)
        cut_sources.append(rec.source)
        if (idx + 1) % 500 == 0:
            log(
                f"cut pass 1: pairs={idx + 1}/{len(pair_records)} "
                f"unique={len(cut_edge_masks)} duplicates={duplicate_cut_count}"
            )

    if empty_cut_source is not None:
        return CutLibrary(
            nonport_vertex_ids, atoms, atom_id, [], [], cut_edge_masks,
            cut_sizes, cut_sources, 0, "", len(pair_records),
            duplicate_cut_count, empty_cut_source,
        )

    kcuts = len(unique_records)
    blocks = max(1, (kcuts + 63) // 64)
    packed = np.zeros((na, blocks), dtype=np.uint64)

    # Second vectorized pass builds, for every vertex pair uv, the bitset of
    # difference-graph cuts containing uv.
    for t, rec in enumerate(unique_records):
        same_a = rec.alpha[atom_i_full] == rec.alpha[atom_j_full]
        same_b = rec.beta[atom_i_full] == rec.beta[atom_j_full]
        idxs = np.flatnonzero(same_a != same_b).astype(np.int32)
        if len(idxs) != cut_sizes[t]:
            raise RuntimeError("cut size changed between construction passes")
        block = t >> 6
        bit = np.uint64(1) << np.uint64(t & 63)
        packed[idxs, block] |= bit
        if (t + 1) % 500 == 0:
            log(f"cut pass 2: {t + 1}/{kcuts}")

    coverage = [int.from_bytes(packed[a].tobytes(), "little") for a in range(na)]
    del packed

    edge_cov = [[0] * m for _ in range(m)]
    for a, (u, v) in enumerate(atoms):
        x = coverage[a]
        edge_cov[u][v] = x
        edge_cov[v][u] = x

    vertex_cut_mask = [0] * m
    for u in range(m):
        x = 0
        for v in range(m):
            x |= edge_cov[u][v]
        vertex_cut_mask[u] = x

    h = hashlib.sha256()
    h.update(UPSTREAM_SHA.encode("ascii"))
    h.update(b"\0exact-fourset-cut-library-v1\0")
    h.update(json.dumps(nonport_vertex_ids, separators=(",", ":")).encode("ascii"))
    edge_bytes = (na + 7) // 8
    for mask in cut_edge_masks:
        h.update(mask.to_bytes(edge_bytes, "little"))
    digest = h.hexdigest()

    return CutLibrary(
        nonport_vertex_ids=nonport_vertex_ids,
        atoms=atoms,
        atom_id=atom_id,
        edge_cov=edge_cov,
        vertex_cut_mask=vertex_cut_mask,
        cut_edge_masks=cut_edge_masks,
        cut_sizes=cut_sizes,
        cut_sources=cut_sources,
        all_cuts_mask=(1 << kcuts) - 1,
        digest=digest,
        full_pair_count=len(pair_records),
        duplicate_cut_count=duplicate_cut_count,
        empty_cut_source=None,
    )


class SliceTimeout(RuntimeError):
    pass


class ExactFourSetSearch:
    def __init__(self, lib: CutLibrary, lookahead_cuts: int = 32,
                 deadline: Optional[float] = None):
        self.lib = lib
        self.m = len(lib.nonport_vertex_ids)
        self.lookahead_cuts = max(1, int(lookahead_cuts))
        self.deadline = deadline
        self.cut_order = sorted(
            range(len(lib.cut_sizes)), key=lambda t: (lib.cut_sizes[t], t)
        )
        if not self.cut_order:
            raise RuntimeError("empty cut library")
        self.pivot_cut = self.cut_order[0]
        pivot_atoms = self._decode_cut_atoms(self.pivot_cut)
        # Stronger root edges first; this changes only discovery order.
        pivot_atoms.sort(
            key=lambda a: (
                -lib.edge_cov[lib.atoms[a][0]][lib.atoms[a][1]].bit_count(),
                a,
            )
        )
        self.pivot_atoms = pivot_atoms
        self.pivot_rank = {a: r for r, a in enumerate(pivot_atoms)}
        self._decoded_cache: dict[int, list[int]] = {self.pivot_cut: list(pivot_atoms)}
        self._ops = 0
        self.stats = {
            "root_edges_completed_this_process": 0,
            "pair_states": 0,
            "triple_states": 0,
            "quad_leaves": 0,
            "canonical_prunes": 0,
            "triple_incident_prunes": 0,
            "triple_branch_vertices": 0,
        }

    def _tick(self, n: int = 1) -> None:
        self._ops += n
        if self.deadline is not None and (self._ops & 2047) == 0:
            if time.monotonic() >= self.deadline:
                raise SliceTimeout

    def _decode_cut_atoms(self, t: int) -> list[int]:
        cached = getattr(self, "_decoded_cache", {}).get(t)
        if cached is not None:
            return cached
        mask = self.lib.cut_edge_masks[t]
        out = []
        while mask:
            lsb = mask & -mask
            out.append(lsb.bit_length() - 1)
            mask ^= lsb
        if hasattr(self, "_decoded_cache"):
            # Keep only a modest cache; selected cuts tend to repeat across roots.
            if len(self._decoded_cache) >= 128:
                for key in list(self._decoded_cache):
                    if key != self.pivot_cut:
                        self._decoded_cache.pop(key)
                        break
            self._decoded_cache[t] = out
        return out

    def _support_cov(self, support: tuple[int, ...]) -> int:
        cov = 0
        for u, v in combinations(support, 2):
            cov |= self.lib.edge_cov[u][v]
        return cov

    def _first_uncovered_cut(self, cov: int) -> Optional[int]:
        for t in self.cut_order:
            if not (cov >> t) & 1:
                return t
        return None

    def _canonical_for_root(self, support: tuple[int, ...], root_rank: int) -> bool:
        for u, v in combinations(support, 2):
            a = self.lib.atom_id[u][v]
            pr = self.pivot_rank.get(a)
            if pr is not None and pr < root_rank:
                self.stats["canonical_prunes"] += 1
                return False
        return True

    def _complete_candidate(self, support: tuple[int, ...]) -> tuple[int, int, int, int]:
        out = list(support)
        for v in range(self.m):
            if v not in out:
                out.append(v)
                if len(out) == 4:
                    break
        if len(out) != 4:
            raise RuntimeError("could not complete support to four vertices")
        out.sort()
        return tuple(out)  # type: ignore[return-value]

    def _triple_extension_vertices(self, triple: tuple[int, int, int], cov: int):
        # If some cut has no edge incident to any of the three selected vertices,
        # one remaining vertex cannot possibly hit it: every new K4 edge is
        # incident to the triple.
        incident = (
            self.lib.vertex_cut_mask[triple[0]]
            | self.lib.vertex_cut_mask[triple[1]]
            | self.lib.vertex_cut_mask[triple[2]]
        )
        if incident != self.lib.all_cuts_mask:
            self.stats["triple_incident_prunes"] += 1
            return None, []

        best_t = None
        best_vs = None
        considered = 0
        for t in self.cut_order:
            if (cov >> t) & 1:
                continue
            bit = 1 << t
            vs = []
            s0, s1, s2 = triple
            for v in range(self.m):
                if v == s0 or v == s1 or v == s2:
                    continue
                if (
                    (self.lib.edge_cov[s0][v] & bit)
                    or (self.lib.edge_cov[s1][v] & bit)
                    or (self.lib.edge_cov[s2][v] & bit)
                ):
                    vs.append(v)
            if best_vs is None or len(vs) < len(best_vs):
                best_t, best_vs = t, vs
                if not vs:
                    break
            considered += 1
            if considered >= self.lookahead_cuts:
                break
            self._tick()
        return best_t, (best_vs or [])

    def _search_triple(self, triple: tuple[int, int, int], cov: int,
                       root_rank: int) -> Optional[tuple[int, int, int, int]]:
        self.stats["triple_states"] += 1
        self._tick()
        if cov == self.lib.all_cuts_mask:
            return self._complete_candidate(triple)

        _t, vertices = self._triple_extension_vertices(triple, cov)
        if not vertices:
            return None

        self.stats["triple_branch_vertices"] += len(vertices)
        a, b, c = triple
        # Try the strongest actual extensions first. This is branch ordering only.
        vertices.sort(
            key=lambda d: -(
                cov
                | self.lib.edge_cov[a][d]
                | self.lib.edge_cov[b][d]
                | self.lib.edge_cov[c][d]
            ).bit_count()
        )
        for d in vertices:
            quad = tuple(sorted((a, b, c, d)))
            if not self._canonical_for_root(quad, root_rank):
                continue
            self.stats["quad_leaves"] += 1
            cov4 = (
                cov
                | self.lib.edge_cov[a][d]
                | self.lib.edge_cov[b][d]
                | self.lib.edge_cov[c][d]
            )
            if cov4 == self.lib.all_cuts_mask:
                return quad  # type: ignore[return-value]
            self._tick()
        return None

    def _search_root_edge(self, root_rank: int) -> Optional[tuple[int, int, int, int]]:
        root_atom = self.pivot_atoms[root_rank]
        a, b = self.lib.atoms[root_atom]
        pair = (a, b)
        cov = self.lib.edge_cov[a][b]
        self.stats["pair_states"] += 1
        if cov == self.lib.all_cuts_mask:
            return self._complete_candidate(pair)

        t = self._first_uncovered_cut(cov)
        if t is None:
            return self._complete_candidate(pair)

        triple_vertices = set()
        # Every completion must contain an edge of this uncovered cut. With two
        # slots left, an edge touching the root pair creates a triple branch;
        # a disjoint edge determines the full four-set immediately.
        for atom in self._decode_cut_atoms(t):
            u, v = self.lib.atoms[atom]
            if u == a or u == b:
                if v != a and v != b:
                    triple_vertices.add(v)
            elif v == a or v == b:
                triple_vertices.add(u)
            else:
                quad = tuple(sorted((a, b, u, v)))
                if len(set(quad)) != 4:
                    continue
                if not self._canonical_for_root(quad, root_rank):
                    continue
                self.stats["quad_leaves"] += 1
                if self._support_cov(quad) == self.lib.all_cuts_mask:
                    return quad  # type: ignore[return-value]
            self._tick()

        # Stronger triples first.
        triples = []
        for c in triple_vertices:
            triple = tuple(sorted((a, b, c)))
            if not self._canonical_for_root(triple, root_rank):
                continue
            cov3 = cov | self.lib.edge_cov[a][c] | self.lib.edge_cov[b][c]
            triples.append((cov3.bit_count(), triple, cov3))
        triples.sort(reverse=True, key=lambda x: x[0])
        for _score, triple, cov3 in triples:
            ans = self._search_triple(triple, cov3, root_rank)
            if ans is not None:
                return ans
        return None

    def search(self, start_root_rank: int = 0,
               on_root_complete: Optional[Callable[[int], None]] = None):
        if start_root_rank < 0 or start_root_rank > len(self.pivot_atoms):
            raise ValueError("invalid start root rank")
        for r in range(start_root_rank, len(self.pivot_atoms)):
            self._tick()
            atom = self.pivot_atoms[r]
            u, v = self.lib.atoms[atom]
            ans = self._search_root_edge(r)
            if ans is not None:
                return {
                    "status": "CANDIDATE",
                    "support_positions": list(ans),
                    "root_rank": r,
                    "root_edge_positions": [u, v],
                    "next_root_rank": r,
                }
            self.stats["root_edges_completed_this_process"] += 1
            if on_root_complete is not None:
                on_root_complete(r + 1)
            if r < 10 or (r + 1) % 25 == 0:
                log(
                    f"exact master root {r + 1}/{len(self.pivot_atoms)} complete; "
                    f"triples={self.stats['triple_states']} quads={self.stats['quad_leaves']}"
                )
        return {
            "status": "EXHAUSTED",
            "support_positions": None,
            "root_rank": len(self.pivot_atoms),
            "next_root_rank": len(self.pivot_atoms),
        }


def library_summary(lib: CutLibrary, checkpoint_iterations: int,
                    checkpoint_status: str, seed_count: int):
    if lib.empty_cut_source is not None:
        return {
            "upstream_sha": UPSTREAM_SHA,
            "checkpoint_iterations": checkpoint_iterations,
            "checkpoint_status": checkpoint_status,
            "seed_pair_count": seed_count,
            "full_pair_count": lib.full_pair_count,
            "empty_cut_source": lib.empty_cut_source,
        }
    sizes = lib.cut_sizes
    return {
        "upstream_sha": UPSTREAM_SHA,
        "checkpoint_iterations": checkpoint_iterations,
        "checkpoint_status": checkpoint_status,
        "seed_pair_count": seed_count,
        "lab_pair_count": checkpoint_iterations,
        "full_pair_count": lib.full_pair_count,
        "unique_cut_count": len(sizes),
        "duplicate_cut_count": lib.duplicate_cut_count,
        "cut_library_sha256": lib.digest,
        "nonport_vertex_count": len(lib.nonport_vertex_ids),
        "atom_count": len(lib.atoms),
        "cut_size_min": min(sizes),
        "cut_size_max": max(sizes),
        "cut_size_median": statistics.median(sizes),
        "cut_size_mean": statistics.fmean(sizes),
    }


def run_self_test() -> None:
    """Cross-check the exact branching search against brute force on random toys."""
    rng = random.Random(0x484E36)
    trials = 0
    for m in range(5, 10):
        atoms = list(combinations(range(m), 2))
        aid = [[-1] * m for _ in range(m)]
        for i, (u, v) in enumerate(atoms):
            aid[u][v] = aid[v][u] = i
        for _ in range(80):
            edge_sets = []
            for _j in range(rng.randint(1, 12)):
                p = rng.uniform(0.05, 0.75)
                cut = {i for i in range(len(atoms)) if rng.random() < p}
                if not cut:
                    cut.add(rng.randrange(len(atoms)))
                edge_sets.append(cut)

            kcuts = len(edge_sets)
            edge_cov = [[0] * m for _ in range(m)]
            cut_masks = []
            cut_sizes = []
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
            lib = CutLibrary(
                nonport_vertex_ids=list(range(m)), atoms=atoms, atom_id=aid,
                edge_cov=edge_cov, vertex_cut_mask=vmask,
                cut_edge_masks=cut_masks, cut_sizes=cut_sizes,
                cut_sources=[f"toy:{i}" for i in range(kcuts)],
                all_cuts_mask=(1 << kcuts) - 1, digest="toy",
                full_pair_count=kcuts, duplicate_cut_count=0,
                empty_cut_source=None,
            )

            brute = None
            for s in combinations(range(m), 4):
                cov = 0
                for u, v in combinations(s, 2):
                    cov |= edge_cov[u][v]
                if cov == lib.all_cuts_mask:
                    brute = s
                    break
            exact = ExactFourSetSearch(lib, lookahead_cuts=8).search()
            found = exact["status"] == "CANDIDATE"
            if (brute is None) == found:
                raise AssertionError(
                    f"self-test mismatch m={m}: brute={brute}, exact={exact}"
                )
            trials += 1
    print(f"self-test OK: {trials} randomized instances matched brute force")


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
    library_path = result_dir / "LIBRARY.json"
    candidate_path = result_dir / "CANDIDATE.json"
    final_path = result_dir / "FINAL.json"

    verts, edges, c88 = build_system(args.data_dir)
    pairs, seed_count, iterations, checkpoint_status = load_pair_library(
        args.data_dir, args.checkpoint, verts, edges, c88
    )
    log(
        f"validated pair library: seeds={seed_count}, lab={iterations}, "
        f"total={len(pairs)}, checkpoint_status={checkpoint_status}"
    )

    t_build = time.monotonic()
    lib = build_cut_library(pairs, verts)
    summary = library_summary(lib, iterations, checkpoint_status, seed_count)
    atomic_json(library_path, summary)
    log(f"cut library built in {time.monotonic() - t_build:.1f}s")

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
        log(f"terminal global empty cut from {lib.empty_cut_source}")
        return 0

    search = ExactFourSetSearch(
        lib,
        lookahead_cuts=args.lookahead_cuts,
        deadline=(time.monotonic() + args.time_limit_sec) if args.time_limit_sec > 0 else None,
    )
    pivot_atom = search.pivot_atoms[0]
    pu, pv = lib.atoms[pivot_atom]
    pivot_info = {
        "pivot_cut_index": search.pivot_cut,
        "pivot_cut_source": lib.cut_sources[search.pivot_cut],
        "pivot_cut_size": lib.cut_sizes[search.pivot_cut],
        "pivot_root_edge_count": len(search.pivot_atoms),
        "first_pivot_edge_positions": [pu, pv],
        "first_pivot_edge_vertices": [
            lib.nonport_vertex_ids[pu], lib.nonport_vertex_ids[pv]
        ],
    }
    summary.update(pivot_info)
    atomic_json(library_path, summary)
    log(
        f"unique cuts={summary['unique_cut_count']} duplicates={summary['duplicate_cut_count']} "
        f"cut-size min/median/max={summary['cut_size_min']}/"
        f"{summary['cut_size_median']}/{summary['cut_size_max']}"
    )
    log(
        f"pivot cut={search.pivot_cut} source={lib.cut_sources[search.pivot_cut]} "
        f"edges={len(search.pivot_atoms)}"
    )

    start_root_rank = 0
    previous = {}
    if state_path.exists():
        previous = load_json(state_path)
        checks = {
            "version": STATE_VERSION,
            "upstream_sha": UPSTREAM_SHA,
            "checkpoint_iterations": iterations,
            "full_pair_count": lib.full_pair_count,
            "unique_cut_count": len(lib.cut_sizes),
            "cut_library_sha256": lib.digest,
            "pivot_cut_index": search.pivot_cut,
            "pivot_root_edge_count": len(search.pivot_atoms),
        }
        for key, expected in checks.items():
            if previous.get(key) != expected:
                raise RuntimeError(
                    f"state mismatch for {key}: {previous.get(key)!r} != {expected!r}"
                )
        start_root_rank = int(previous.get("next_root_rank", 0))
        log(f"resume exact master at pivot root rank {start_root_rank}")

    base_state = {
        "version": STATE_VERSION,
        **summary,
        "method": "exact edge-branching four-set master",
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
    except SliceTimeout:
        # The current root edge was not certified complete; retry it next time.
        base_state["status"] = "TIME-SLICE-COMPLETE"
        base_state["last_process_stats"] = dict(search.stats)
        atomic_json(state_path, base_state)
        log(
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
        base_state["next_root_rank"] = result["root_rank"]
        atomic_json(state_path, base_state)
        log(f"candidate found: support={named}")
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
            "The algorithm is exhaustive: every four-set hits the pivot cut, is assigned "
            "to its earliest pivot edge, and every subsequent uncovered cut is branched "
            "over all edges that can fit in the remaining vertex slots. Promote this to a "
            "public mathematical claim only after an independent implementation rechecks it."
        ),
    }
    atomic_json(final_path, out)
    base_state.update(out)
    base_state["next_root_rank"] = len(search.pivot_atoms)
    atomic_json(state_path, base_state)
    log("EXACT MASTER EXHAUSTED: independent verification required before promotion")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
