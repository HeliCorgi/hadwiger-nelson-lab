#!/usr/bin/env python3
"""Independently reconstruct the final port-free support-4 difference-cut library.

This module deliberately does not import exact_fourset_master.py or its monotone
wrapper.  It reloads the pinned graph data and every saved A/B fooling pair,
validates the colorings directly, rebuilds the 391-vertex equality-difference
cuts, deduplicates exact cuts in first-occurrence order, and emits a compact
binary edge-mask library for a separate C++ exhaustive verifier.

The binary format is intentionally simple and checker-oriented:

    8 bytes magic: b'HN4MSK01'
    uint32 little-endian: vertex_count, atom_count, unique_cut_count, edge_bytes
    repeated unique_cut_count times:
        uint32 little-endian cut_edge_count
        edge_bytes bytes, little-endian bit mask over lexicographic u<v atoms

The script also reproduces the historical cut-library digest only as a cross-
check.  The subsequent exhaustive search uses a different decomposition and
never reads the producing master's state or root order.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import struct
from pathlib import Path

import numpy as np

K = 5
P, Q = 217, 490
UPSTREAM_SHA = "d1e80998bda337d9fa721f2e96d203ae54e97fc8"
MAGIC = b"HN4MSK01"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_system(data_dir: Path):
    g510 = load_json(data_dir / "g510_k2.json")
    all_edges = [tuple(map(int, e)) for e in g510["edges"]]

    cores = load_json(data_dir / "B5_MULTICORE.json")["cores"]
    raw = cores[0]
    if raw and isinstance(raw[0], int):
        hstar = [all_edges[i] for i in raw]
    else:
        hstar = [tuple(map(int, e)) for e in raw]

    c88 = [
        tuple(map(int, e))
        for e in load_json(data_dir / "B5_P2_LEMMA.json")["C_min"]
    ]
    edges = sorted({(min(u, v), max(u, v)) for u, v in hstar})
    verts = sorted({v for e in edges for v in e} | {v for e in c88 for v in e})
    if len(verts) != 393:
        raise RuntimeError(f"expected 393 vertices, got {len(verts)}")
    if P not in verts or Q not in verts:
        raise RuntimeError("ports missing")
    return verts, edges, c88


def validate_model(arr, n, edge_i, edge_j, *, cond_i=None, cond_j=None,
                   pi=None, qi=None, label="model") -> np.ndarray:
    x = np.asarray(arr, dtype=np.int8)
    if x.shape != (n,):
        raise ValueError(f"{label}: wrong length {x.shape}")
    if np.any(x < 0) or np.any(x >= K):
        raise ValueError(f"{label}: color outside 0..4")
    if np.any(x[edge_i] == x[edge_j]):
        raise ValueError(f"{label}: improper H* edge")
    if cond_i is not None and np.any(x[cond_i] != x[cond_j]):
        raise ValueError(f"{label}: violates C88 equality")
    if pi is not None and qi is not None and x[pi] == x[qi]:
        raise ValueError(f"{label}: violates port disequality")
    return x


def load_pairs(data_dir: Path, checkpoint: Path, verts, edges, c88):
    n = len(verts)
    vidx = {v: i for i, v in enumerate(verts)}
    pi, qi = vidx[P], vidx[Q]
    edge_i = np.asarray([vidx[u] for u, _ in edges], dtype=np.int32)
    edge_j = np.asarray([vidx[v] for _, v in edges], dtype=np.int32)
    cond_i = np.asarray([vidx[u] for u, _ in c88], dtype=np.int32)
    cond_j = np.asarray([vidx[v] for _, v in c88], dtype=np.int32)

    records = []
    seen_seed_pairs = set()

    def add(alpha, beta, source, dedup_seed):
        a = validate_model(
            alpha, n, edge_i, edge_j,
            cond_i=cond_i, cond_j=cond_j, label=source + ":A"
        )
        b = validate_model(
            beta, n, edge_i, edge_j,
            pi=pi, qi=qi, label=source + ":B"
        )
        key = (a.tobytes(), b.tobytes())
        if dedup_seed and key in seen_seed_pairs:
            return
        if dedup_seed:
            seen_seed_pairs.add(key)
        records.append((a, b, source))

    round1 = load_json(data_dir / "SEMANTIC_CEGIS_FINAL.json")
    if list(map(int, round1["verts"])) != verts:
        raise RuntimeError("SEMANTIC_CEGIS_FINAL vertex order mismatch")
    for i, rec in enumerate(round1["pair_library"]):
        add(rec["alpha"], rec["beta"], f"round1:{i}", True)

    k4 = load_json(data_dir / "K4_CERTIFICATE.json")
    for i, rec in enumerate(k4.get("survivor_witnesses", [])):
        add(rec["alpha"], rec["beta"], f"k4:{i}", True)

    seed_count = len(records)
    if seed_count != 872:
        raise RuntimeError(f"expected 872 seed pairs, got {seed_count}")

    with gzip.open(checkpoint, "rt", encoding="utf-8") as f:
        ck = json.load(f)
    if ck.get("upstream_sha") != UPSTREAM_SHA:
        raise RuntimeError("checkpoint upstream SHA mismatch")
    if ck.get("verts") != verts:
        raise RuntimeError("checkpoint vertex order mismatch")
    new_pairs = ck.get("new_pairs", [])
    iterations = int(ck.get("iterations", -1))
    if iterations != len(new_pairs):
        raise RuntimeError("checkpoint iterations/new_pairs invariant failed")

    # Preserve every recorded lab pair, including exact duplicate model pairs.
    # Deduplication belongs to the difference-cut stage, not pair validation.
    for i, rec in enumerate(new_pairs):
        add(rec["alpha"], rec["beta"], f"checkpoint:{i}", False)

    return records, seed_count, iterations, ck.get("status")


def reconstruct(records, verts):
    vidx = {v: i for i, v in enumerate(verts)}
    nonport_full = [i for i in range(len(verts)) if i not in (vidx[P], vidx[Q])]
    nonport_ids = [verts[i] for i in nonport_full]
    m = len(nonport_full)
    if m != 391:
        raise RuntimeError(f"expected 391 nonports, got {m}")

    atom_u = []
    atom_v = []
    for u in range(m):
        for v in range(u + 1, m):
            atom_u.append(u)
            atom_v.append(v)
    atom_u = np.asarray(atom_u, dtype=np.int16)
    atom_v = np.asarray(atom_v, dtype=np.int16)
    if len(atom_u) != 76245:
        raise RuntimeError("atom count mismatch")

    full_u = np.asarray([nonport_full[u] for u in atom_u], dtype=np.int32)
    full_v = np.asarray([nonport_full[v] for v in atom_v], dtype=np.int32)
    edge_bytes = (len(atom_u) + 7) // 8

    unique = []
    seen = set()
    duplicate_count = 0
    empty_source = None

    for i, (a, b, source) in enumerate(records):
        diff = ((a[full_u] == a[full_v]) != (b[full_u] == b[full_v]))
        size = int(np.count_nonzero(diff))
        if size == 0:
            empty_source = source
            break
        raw = np.packbits(diff, bitorder="little").tobytes()
        if len(raw) < edge_bytes:
            raw += b"\0" * (edge_bytes - len(raw))
        elif len(raw) > edge_bytes:
            raw = raw[:edge_bytes]
        if raw in seen:
            duplicate_count += 1
            continue
        seen.add(raw)
        unique.append((raw, size, source))
        if (i + 1) % 500 == 0:
            print(
                f"reconstruct pairs={i+1}/{len(records)} "
                f"unique={len(unique)} duplicates={duplicate_count}",
                flush=True,
            )

    h = hashlib.sha256()
    h.update(UPSTREAM_SHA.encode("ascii"))
    h.update(b"\0exact-fourset-cut-library-v1\0")
    h.update(json.dumps(nonport_ids, separators=(",", ":")).encode("ascii"))
    for raw, _size, _source in unique:
        h.update(raw)

    return {
        "nonport_ids": nonport_ids,
        "atom_count": len(atom_u),
        "edge_bytes": edge_bytes,
        "unique": unique,
        "duplicate_count": duplicate_count,
        "empty_source": empty_source,
        "digest": h.hexdigest(),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, required=True)
    ap.add_argument("--checkpoint", type=Path, required=True)
    ap.add_argument("--output-bin", type=Path, required=True)
    ap.add_argument("--output-json", type=Path, required=True)
    ap.add_argument("--expected-full", type=int)
    ap.add_argument("--expected-unique", type=int)
    ap.add_argument("--expected-digest")
    args = ap.parse_args()

    verts, edges, c88 = build_system(args.data_dir)
    records, seed_count, iterations, ck_status = load_pairs(
        args.data_dir, args.checkpoint, verts, edges, c88
    )
    rec = reconstruct(records, verts)

    if rec["empty_source"] is not None:
        raise RuntimeError(f"unexpected empty difference cut: {rec['empty_source']}")

    full = len(records)
    unique_count = len(rec["unique"])
    if args.expected_full is not None and full != args.expected_full:
        raise RuntimeError(f"full pair count mismatch: {full} != {args.expected_full}")
    if args.expected_unique is not None and unique_count != args.expected_unique:
        raise RuntimeError(
            f"unique cut count mismatch: {unique_count} != {args.expected_unique}"
        )
    if args.expected_digest is not None and rec["digest"] != args.expected_digest:
        raise RuntimeError(
            f"cut digest mismatch: {rec['digest']} != {args.expected_digest}"
        )

    args.output_bin.parent.mkdir(parents=True, exist_ok=True)
    with args.output_bin.open("wb") as f:
        f.write(MAGIC)
        f.write(struct.pack(
            "<IIII", len(rec["nonport_ids"]), rec["atom_count"],
            unique_count, rec["edge_bytes"]
        ))
        for raw, size, _source in rec["unique"]:
            f.write(struct.pack("<I", size))
            f.write(raw)

    sizes = [size for _raw, size, _source in rec["unique"]]
    meta = {
        "status": "INDEPENDENT-CUT-RECONSTRUCTION-OK",
        "upstream_sha": UPSTREAM_SHA,
        "checkpoint_status": ck_status,
        "seed_pair_count": seed_count,
        "lab_pair_count": iterations,
        "full_pair_count": full,
        "unique_cut_count": unique_count,
        "duplicate_cut_count": rec["duplicate_count"],
        "nonport_vertex_count": len(rec["nonport_ids"]),
        "atom_count": rec["atom_count"],
        "edge_bytes": rec["edge_bytes"],
        "cut_size_min": min(sizes),
        "cut_size_max": max(sizes),
        "cut_library_sha256": rec["digest"],
        "binary_sha256": hashlib.sha256(args.output_bin.read_bytes()).hexdigest(),
        "method": "independent direct model validation and difference-mask reconstruction",
        "does_not_import_producing_master": True,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(meta, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
