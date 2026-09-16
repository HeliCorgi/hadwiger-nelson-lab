#!/usr/bin/env python3
"""Check saved five-color witnesses without a SAT solver or geometry library.

The semantic hash binds point order and the complete saved edge list to the
separately audited geometry. This verifier does NOT itself prove unit distances.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
from pathlib import Path

DEFAULT = Path(__file__).resolve().parents[1] / 'results/interior-overlap-2026-09-16/G3_FIVE_COLORINGS.json.gz'

def load(path: Path) -> dict:
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)

def semantic(graph: dict) -> str:
    data = {key: graph[key] for key in ('pts', 'edges')}
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def verify(graph: dict, bundle: dict) -> dict:
    n = len(graph['pts'])
    edges = graph['edges']
    for edge in edges:
        if (not isinstance(edge, list) or len(edge) != 2 or
                any(type(v) is not int for v in edge) or not 0 <= edge[0] < edge[1] < n):
            raise ValueError('invalid edge')
    if len({tuple(e) for e in edges}) != len(edges):
        raise ValueError('duplicate edges')
    sha = semantic(graph)
    witnesses = [w for w in bundle['witnesses'] if w['semantic_sha256'] == sha]
    if not witnesses:
        raise ValueError('no witness bound to this exact graph')
    checked = []
    for w in witnesses:
        text = w['colors']
        if not isinstance(text, str) or len(text) != n or any(c not in '01234' for c in text):
            raise ValueError('invalid five-color vector')
        if hashlib.sha256((text + '\n').encode()).hexdigest() != w['coloring_sha256']:
            raise ValueError('coloring hash mismatch')
        if any(text[a] == text[b] for a, b in edges):
            raise ValueError('monochromatic original edge')
        checked.append({key: w[key] for key in ('case', 'solver', 'artifact_id', 'coloring_sha256')})
    return {'status': 'PASS', 'target_A': 'NOT_A', 'vertices': n, 'edges_checked_per_model': len(edges),
            'semantic_sha256': sha, 'witnesses_checked': checked,
            'geometry_reproved_by_this_tool': False, 'SAT_solver_used': False}

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--graph', type=Path, required=True)
    ap.add_argument('--bundle', type=Path, default=DEFAULT)
    ap.add_argument('--out', type=Path)
    a = ap.parse_args()
    result = verify(load(a.graph), load(a.bundle))
    text = json.dumps(result, indent=2) + '\n'
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(text)
    print(text, end='')

if __name__ == '__main__':
    main()
