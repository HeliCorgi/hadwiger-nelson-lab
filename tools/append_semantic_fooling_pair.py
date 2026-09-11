#!/usr/bin/env python3
"""Append a validated SAT semantic-oracle witness to the v3 CEGIS checkpoint."""
from __future__ import annotations

import argparse
import gzip
import json
import os
from pathlib import Path

import numpy as np

K = 5
P, Q = 217, 490
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
    c88 = [tuple(map(int, p)) for p in load_json(data_dir / "B5_P2_LEMMA.json")["C_min"]]
    edges = sorted({(min(u, v), max(u, v)) for u, v in hstar})
    verts = sorted({x for e in edges for x in e} | {x for e in c88 for x in e})
    return verts, edges, c88


def validate(arr, verts, edges, vidx, conditions=(), require_port_diff=False):
    a = np.asarray(arr, dtype=np.int8)
    if a.shape != (len(verts),) or np.any(a < 0) or np.any(a >= K):
        return False
    for u, v in edges:
        if a[vidx[u]] == a[vidx[v]]:
            return False
    for u, v in conditions:
        if a[vidx[u]] != a[vidx[v]]:
            return False
    if require_port_diff and a[vidx[P]] == a[vidx[Q]]:
        return False
    return True


def atomic_gzip_json(path: Path, obj):
    tmp = path.with_name(path.name + ".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8", compresslevel=6) as f:
        json.dump(obj, f, separators=(",", ":"))
    os.replace(tmp, path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, required=True)
    ap.add_argument("--checkpoint", type=Path, required=True)
    ap.add_argument("--oracle-result", type=Path, required=True)
    args = ap.parse_args()

    result = load_json(args.oracle_result)
    if result.get("status") != "SAT-FOOLING-PAIR":
        raise RuntimeError(f"oracle result is not SAT-FOOLING-PAIR: {result.get('status')}")
    if result.get("upstream_sha") != UPSTREAM_SHA:
        raise RuntimeError("oracle upstream SHA mismatch")
    if not all(x.get("sat") is True for x in result.get("solvers", {}).values()):
        raise RuntimeError("not all recorded solvers returned SAT")
    witness = result.get("canonical_witness") or {}
    alpha = witness.get("alpha")
    beta = witness.get("beta")
    vertex_order = witness.get("vertex_order")

    verts, edges, c88 = build_system(args.data_dir)
    vidx = {v: i for i, v in enumerate(verts)}
    if vertex_order != verts:
        raise RuntimeError("oracle witness vertex order mismatch")
    if not validate(alpha, verts, edges, vidx, conditions=c88):
        raise RuntimeError("oracle alpha witness failed A validation")
    if not validate(beta, verts, edges, vidx, require_port_diff=True):
        raise RuntimeError("oracle beta witness failed B validation")

    with gzip.open(args.checkpoint, "rt", encoding="utf-8") as f:
        ck = json.load(f)
    if ck.get("version") != 3 or ck.get("upstream_sha") != UPSTREAM_SHA or ck.get("verts") != verts:
        raise RuntimeError("checkpoint metadata mismatch")
    pairs = ck.setdefault("new_pairs", [])
    if int(ck.get("iterations", -1)) != len(pairs):
        raise RuntimeError("checkpoint iterations/new_pairs invariant failed")

    key = (tuple(alpha), tuple(beta))
    for rec in pairs:
        if (tuple(rec["alpha"]), tuple(rec["beta"])) == key:
            print("witness already present; no append")
            return 0

    pairs.append({"alpha": alpha, "beta": beta})
    ck["iterations"] = len(pairs)
    ck["status"] = "RUNNING-AFTER-EXACT-MASTER-CUT"
    ck["last_support"] = result.get("support")
    ck["unresolved_supports"] = []
    ck.setdefault("stats", {})
    ck["exact_master_loop"] = {
        "last_support": result.get("support"),
        "last_equality_pattern": result.get("equality_pattern"),
        "last_new_cut_edge_count": result.get("new_cut_edge_count"),
        "last_oracle_solvers": result.get("solvers"),
    }
    atomic_gzip_json(args.checkpoint, ck)
    print(f"appended validated fooling pair; lab iterations={len(pairs)} total cuts={len(pairs)+872}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
