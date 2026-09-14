#!/usr/bin/env python3
"""Large-neighborhood SAT repair for a near proper 5-coloring.

All vertices outside a graph-distance neighborhood of the seed conflicts are fixed
to their seed colors. Only the free neighborhood is encoded. A SAT result is
expanded to the full graph and validated on every supplied edge. UNSAT only means
that particular frozen-boundary neighborhood cannot repair the seed; it is not a
whole-graph UNSAT claim. UNKNOWN/timeout is non-evidence.
"""
from __future__ import annotations

import argparse, json, random
from pathlib import Path
from pysat.solvers import Cadical195, Glucose4

from hn_exact import K2, unit_modulus
from hn_unconditional_scan import valid_coloring, write_json


def load_coloring(path: Path, n: int):
    s = path.read_text().strip()
    if len(s) == n and all(ch in '01234' for ch in s):
        return [int(ch) for ch in s]
    d = json.loads(path.read_text())
    for k in ('colors', 'coloring'):
        if isinstance(d, dict) and k in d:
            c = list(map(int, d[k]))
            if len(c) == n:
                return c
    raise ValueError('no usable coloring')


def local_cnf(free, edges, adj, seed):
    verts = sorted(free)
    pos = {v: i for i, v in enumerate(verts)}
    clauses = []
    def var(v, c):
        return pos[v] * 5 + c + 1
    for v in verts:
        clauses.append([var(v, c) for c in range(5)])
        for a in range(5):
            for b in range(a + 1, 5):
                clauses.append([-var(v, a), -var(v, b)])
        forbidden = {seed[w] for w in adj[v] if w not in free}
        for c in forbidden:
            clauses.append([-var(v, c)])
    for u, v in edges:
        if u in free and v in free:
            for c in range(5):
                clauses.append([-var(u, c), -var(v, c)])
    return verts, clauses


def extract(model, verts, seed):
    pos = {x for x in model if x > 0}
    colors = list(seed)
    for i, v in enumerate(verts):
        base = i * 5 + 1
        choices = [c for c in range(5) if base + c in pos]
        if len(choices) != 1:
            raise AssertionError((v, choices))
        colors[v] = choices[0]
    return colors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--graph', type=Path, required=True)
    ap.add_argument('--seed-coloring', type=Path, required=True)
    ap.add_argument('--out-dir', type=Path, required=True)
    ap.add_argument('--radius', type=int, required=True)
    ap.add_argument('--conflicts', type=int, default=8_000_000)
    ap.add_argument('--attempts', type=int, default=3)
    ap.add_argument('--seed', type=int, default=20260914)
    a = ap.parse_args(); a.out_dir.mkdir(parents=True, exist_ok=True)

    d = json.loads(a.graph.read_text())
    pts = [K2(p['a'], p['b'], p['den']) for p in d['pts']]
    edges = sorted({tuple(map(int, e)) for e in d['edges']})
    n = len(pts)
    assert len(set(pts)) == n
    assert all(unit_modulus(pts[u] - pts[v]) for u, v in edges)
    seed = load_coloring(a.seed_coloring, n)
    assert all(0 <= c < 5 for c in seed)

    bad = [(u, v) for u, v in edges if seed[u] == seed[v]]
    if not bad:
        assert valid_coloring(seed, n, edges)
        out = {'status': 'SAT', 'classification': 'NOT_A', 'radius': a.radius,
               'vertices': n, 'edges': len(edges), 'seed_conflicts': 0,
               'free_vertices': 0, 'all_edges_validated': True, 'colors': seed}
        write_json(a.out_dir / 'LNS.json', out)
        (a.out_dir / 'COLORING.txt').write_text(''.join(map(str, seed)) + '\n')
        return

    adj = [set() for _ in range(n)]
    for u, v in edges:
        adj[u].add(v); adj[v].add(u)
    free = {x for e in bad for x in e}
    for _ in range(a.radius):
        free |= {w for v in list(free) for w in adj[v]}
    verts, clauses = local_cnf(free, edges, adj, seed)
    internal = sum(1 for u, v in edges if u in free and v in free)
    boundary = sum(1 for u, v in edges if (u in free) ^ (v in free))

    rng = random.Random(a.seed + a.radius)
    records = []
    result = None
    for attempt in range(a.attempts):
        phases = []
        for i, v in enumerate(verts):
            # Mostly preserve the near-coloring; perturb phase preference slightly.
            c = seed[v] if attempt == 0 or rng.random() < 0.8 else rng.randrange(5)
            phases.append(i * 5 + c + 1)
        with Cadical195(bootstrap_with=clauses) as s:
            s.conf_budget(a.conflicts)
            s.set_phases(phases)
            ans = s.solve_limited()
            records.append({'attempt': attempt,
                            'cadical195': 'SAT' if ans is True else 'UNSAT' if ans is False else 'UNKNOWN'})
            if ans is True:
                colors = extract(s.get_model(), verts, seed)
                assert valid_coloring(colors, n, edges)
                result = colors
                break
            if ans is False:
                # Independent confirmation only for the frozen-boundary local problem.
                with Glucose4(bootstrap_with=clauses) as g:
                    g.conf_budget(a.conflicts * 2)
                    gg = g.solve_limited()
                records[-1]['glucose4'] = 'SAT' if gg is True else 'UNSAT' if gg is False else 'UNKNOWN'
                if gg is True:
                    # Different solver found a repair despite CaDiCaL's result; validate it.
                    with Glucose4(bootstrap_with=clauses) as g2:
                        if g2.solve():
                            colors = extract(g2.get_model(), verts, seed)
                            assert valid_coloring(colors, n, edges)
                            result = colors
                break

    if result is not None:
        out = {'status': 'SAT', 'classification': 'NOT_A', 'radius': a.radius,
               'vertices': n, 'edges': len(edges), 'seed_conflicts': len(bad),
               'conflict_endpoint_vertices': len({x for e in bad for x in e}),
               'free_vertices': len(free), 'internal_edges': internal, 'boundary_edges': boundary,
               'local_clauses': len(clauses), 'records': records,
               'all_edges_validated': True, 'colors': result}
        (a.out_dir / 'COLORING.txt').write_text(''.join(map(str, result)) + '\n')
    else:
        out = {'status': 'NO_REPAIR_WITHIN_BUDGET', 'classification': None, 'radius': a.radius,
               'vertices': n, 'edges': len(edges), 'seed_conflicts': len(bad),
               'conflict_endpoint_vertices': len({x for e in bad for x in e}),
               'free_vertices': len(free), 'internal_edges': internal, 'boundary_edges': boundary,
               'local_clauses': len(clauses), 'records': records,
               'local_failure_is_whole_graph_evidence': False}
    write_json(a.out_dir / 'LNS.json', out)
    print(json.dumps({k: v for k, v in out.items() if k != 'colors'}, indent=2))

if __name__ == '__main__':
    main()
