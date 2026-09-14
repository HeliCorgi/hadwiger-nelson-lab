#!/usr/bin/env python3
"""Adaptive component-wise large-neighborhood repair.

Start from endpoints of all seed conflicts. Solve each connected free component
with the outside frozen. Components that are SAT are committed immediately;
components that are UNSAT/UNKNOWN are expanded by one graph hop and retried.
Every reported whole-graph SAT coloring is validated on every exact edge.
Local UNSAT and budget exhaustion are never promoted to whole-graph evidence.
"""
from __future__ import annotations

import argparse, json
from pathlib import Path
from pysat.solvers import Cadical195

from hn_exact import K2, unit_modulus
from hn_unconditional_scan import valid_coloring, write_json
from hn_lns_sat_repair import load_coloring, local_cnf, extract


def components(free, adj):
    unseen = set(free)
    out = []
    while unseen:
        s = next(iter(unseen)); unseen.remove(s)
        stack = [s]; comp = []
        while stack:
            v = stack.pop(); comp.append(v)
            ns = adj[v] & unseen
            if ns:
                unseen.difference_update(ns); stack.extend(ns)
        out.append(set(comp))
    out.sort(key=len, reverse=True)
    return out


def solve_component(comp, edges, adj, colors, conflicts):
    verts, clauses = local_cnf(comp, edges, adj, colors)
    with Cadical195(bootstrap_with=clauses) as s:
        s.conf_budget(conflicts)
        s.set_phases([i * 5 + colors[v] + 1 for i, v in enumerate(verts)])
        ans = s.solve_limited()
        if ans is True:
            full = extract(s.get_model(), verts, colors)
            return 'SAT', full, len(clauses)
        return ('UNSAT' if ans is False else 'UNKNOWN'), None, len(clauses)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--graph', type=Path, required=True)
    ap.add_argument('--seed-coloring', type=Path, required=True)
    ap.add_argument('--out-dir', type=Path, required=True)
    ap.add_argument('--rounds', type=int, default=4)
    ap.add_argument('--conflicts', type=int, default=5_000_000)
    a = ap.parse_args(); a.out_dir.mkdir(parents=True, exist_ok=True)

    d = json.loads(a.graph.read_text())
    pts = [K2(p['a'], p['b'], p['den']) for p in d['pts']]
    edges = sorted({tuple(map(int, e)) for e in d['edges']})
    n = len(pts)
    assert len(set(pts)) == n and all(unit_modulus(pts[u] - pts[v]) for u, v in edges)
    colors = load_coloring(a.seed_coloring, n)
    adj = [set() for _ in range(n)]
    for u, v in edges:
        adj[u].add(v); adj[v].add(u)

    initial_bad = [(u, v) for u, v in edges if colors[u] == colors[v]]
    free = {x for e in initial_bad for x in e}
    records = []

    for rnd in range(a.rounds):
        bad_before = [(u, v) for u, v in edges if colors[u] == colors[v]]
        if not bad_before:
            assert valid_coloring(colors, n, edges)
            break
        free |= {x for e in bad_before for x in e}
        comps = components(free, adj)
        next_free = set()
        rr = {'round': rnd, 'bad_before': len(bad_before), 'free_vertices': len(free),
              'components': len(comps), 'component_records': []}
        for ci, comp in enumerate(comps):
            status, candidate, nclauses = solve_component(comp, edges, adj, colors, a.conflicts)
            rec = {'component': ci, 'vertices': len(comp), 'status': status, 'clauses': nclauses}
            rr['component_records'].append(rec)
            if status == 'SAT':
                # Only vertices in this component differ from colors; boundary constraints
                # ensure all edges leaving the component remain proper.
                for v in comp:
                    colors[v] = candidate[v]
            else:
                next_free |= comp
                for v in comp:
                    next_free.update(adj[v])
        bad_after = [(u, v) for u, v in edges if colors[u] == colors[v]]
        rr['bad_after'] = len(bad_after)
        rr['next_free_vertices'] = len(next_free)
        records.append(rr)
        print(json.dumps({k:v for k,v in rr.items() if k!='component_records'}), flush=True)
        if not bad_after:
            assert valid_coloring(colors, n, edges)
            free = set(); break
        next_free |= {x for e in bad_after for x in e}
        if next_free == free and all(r['status'] == 'UNSAT' for r in rr['component_records']):
            # It will still expand on the next line only if neighbors add something.
            pass
        free = next_free

    bad_final = [(u, v) for u, v in edges if colors[u] == colors[v]]
    if not bad_final:
        assert valid_coloring(colors, n, edges)
        out = {'status': 'SAT', 'classification': 'NOT_A', 'vertices': n, 'edges': len(edges),
               'initial_conflicts': len(initial_bad), 'final_conflicts': 0,
               'records': records, 'all_edges_validated': True, 'colors': colors}
        (a.out_dir / 'COLORING.txt').write_text(''.join(map(str, colors)) + '\n')
    else:
        out = {'status': 'NO_REPAIR_WITHIN_BUDGET', 'classification': None,
               'vertices': n, 'edges': len(edges), 'initial_conflicts': len(initial_bad),
               'final_conflicts': len(bad_final), 'records': records,
               'local_failure_is_whole_graph_evidence': False}
    write_json(a.out_dir / 'ADAPTIVE_LNS.json', out)
    print(json.dumps({k:v for k,v in out.items() if k not in ('colors','records')}, indent=2))

if __name__ == '__main__':
    main()
