#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import deque
from itertools import combinations
from pathlib import Path

from pysat.solvers import Cadical195, Glucose4

from separator_interface import P, Q, UPSTREAM_SHA, build, components_without, min_vertex_cut

K = 5
S_EXPECTED = [0, 6, 8, 9, 10, 266]
TARGETS = [(5, 6), (0, 10), (8, 9)]
ANCHORS = [5, 0, 8]


def make_cnf(nodes, edges):
    ns = sorted(nodes)
    idx = {v: i for i, v in enumerate(ns)}
    cls = []

    def X(v, c):
        return idx[v] * K + c + 1

    for v in ns:
        lits = [X(v, c) for c in range(K)]
        cls.append(lits)
        for a, b in combinations(lits, 2):
            cls.append([-a, -b])
    V = set(ns)
    for u, v in edges:
        if u in V and v in V:
            for c in range(K):
                cls.append([-X(u, c), -X(v, c)])
    return ns, cls, X


def forced_equal_class(Solver, clauses, X, ns, anchor):
    out = []
    with Solver(bootstrap_with=clauses) as sol:
        if not sol.solve(assumptions=[X(anchor, 0)]):
            raise RuntimeError((anchor, 'anchor color fixation unexpectedly UNSAT'))
        for v in ns:
            if v == anchor:
                out.append(v)
                continue
            can_differ = any(sol.solve(assumptions=[X(anchor, 0), X(v, c)]) for c in range(1, K))
            if not can_differ:
                out.append(v)
    return sorted(out)


def three_colorable(vertices, edge_set):
    vs = sorted(vertices)
    idx = {v: i for i, v in enumerate(vs)}
    cls = []

    def Y(v, c):
        return idx[v] * 3 + c + 1

    for v in vs:
        lits = [Y(v, c) for c in range(3)]
        cls.append(lits)
        for a, b in combinations(lits, 2):
            cls.append([-a, -b])
    V = set(vs)
    for u, v in edge_set:
        if u in V and v in V:
            for c in range(3):
                cls.append([-Y(u, c), -Y(v, c)])
    with Cadical195(bootstrap_with=cls) as sol:
        return sol.solve()


def find_k4(vertices, edge_set):
    V = sorted(vertices)
    E = set(edge_set)
    for q in combinations(V, 4):
        if all((min(a, b), max(a, b)) in E for a, b in combinations(q, 2)):
            return list(q)
    return None


def local_forcing_edges(eq_class, left, edges):
    E = {(min(u, v), max(u, v)) for u, v in edges if u in left and v in left}
    adj = {v: set() for v in left}
    for u, v in E:
        adj[u].add(v)
        adj[v].add(u)
    rows = []
    for u, v in combinations(sorted(eq_class), 2):
        common = sorted(adj[u] & adj[v])
        non3 = not three_colorable(common, E)
        if non3:
            rows.append({
                'pair': [u, v],
                'common_neighborhood_size': len(common),
                'common_neighbors': common,
                'k4_witness': find_k4(common, E),
            })
    return rows


def shortest_path(edges, s, t):
    adj = {}
    for row in edges:
        u, v = row['pair']
        adj.setdefault(u, []).append(v)
        adj.setdefault(v, []).append(u)
    q = deque([s])
    prev = {s: None}
    while q:
        u = q.popleft()
        if u == t:
            break
        for v in sorted(adj.get(u, [])):
            if v not in prev:
                prev[v] = u
                q.append(v)
    if t not in prev:
        return None
    path = []
    x = t
    while x is not None:
        path.append(x)
        x = prev[x]
    return list(reversed(path))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data-dir', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()

    C, R, vq, E = build(args.data_dir)
    n = len(R)
    p, q = vq[P], vq[Q]
    val, S = min_vertex_cut(n, E, p, q)
    if p != 5 or S != S_EXPECTED:
        raise RuntimeError((p, q, val, S))
    cc = components_without(n, E, S)
    pc = next(x for x in cc if p in x)
    left = set(pc) | set(S)
    ns, clauses, X = make_cnf(left, E)

    classes = {}
    for anchor in ANCHORS:
        ca = forced_equal_class(Cadical195, clauses, X, ns, anchor)
        gl = forced_equal_class(Glucose4, clauses, X, ns, anchor)
        if ca != gl:
            raise RuntimeError(('solver disagreement', anchor, ca, gl))
        classes[str(anchor)] = ca

    target_reports = []
    for u, v in TARGETS:
        eq = classes[str(u)]
        if v not in eq:
            raise RuntimeError(('target missing from equality class', u, v))
        local = local_forcing_edges(eq, left, E)
        path = shortest_path(local, u, v)
        target_reports.append({
            'target_pair': [u, v],
            'equality_class': eq,
            'equality_class_size': len(eq),
            'local_common_neighborhood_forcing_edges': local,
            'local_forcing_edge_count': len(local),
            'shortest_local_forcing_path': path,
            'target_explained_by_local_chain': path is not None,
        })

    unique_classes = []
    seen = set()
    for a in ANCHORS:
        key = tuple(classes[str(a)])
        if key not in seen:
            seen.add(key)
            unique_classes.append(list(key))

    rep = {
        'upstream_sha': UPSTREAM_SHA,
        'separator_qnodes': S,
        'p_qnode': p,
        'left_bag_size': len(left),
        'target_pairs': [list(x) for x in TARGETS],
        'solver_crosscheck': 'Cadical195 and Glucose4 produced identical equality classes',
        'anchor_equality_classes': classes,
        'unique_target_equality_classes': unique_classes,
        'targets': target_reports,
        'interpretation': 'Forced equality is an equivalence relation across all proper 5-colorings of the left bag. Each target anchor class is reconstructed exactly with two solvers. Inside each class, pairs whose common-neighborhood graph is not 3-colorable give short graph-theoretic equality lemmas; shortest paths test whether the target equality factors through such local lemmas.'
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(rep, indent=2) + '\n')
    print(json.dumps({
        'class_sizes': {a: len(v) for a, v in classes.items()},
        'targets': [
            {
                'pair': x['target_pair'],
                'class_size': x['equality_class_size'],
                'local_edges': x['local_forcing_edge_count'],
                'path': x['shortest_local_forcing_path'],
            }
            for x in target_reports
        ]
    }, indent=2))


if __name__ == '__main__':
    main()
