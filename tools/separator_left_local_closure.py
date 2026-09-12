#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path

from pysat.solvers import Cadical195

from separator_interface import P, Q, UPSTREAM_SHA, build, components_without, min_vertex_cut

K = 5
S_EXPECTED = [0, 6, 8, 9, 10, 266]
TARGETS = [(5, 6), (0, 10), (8, 9)]


class DSU:
    def __init__(self, xs):
        self.p = {x: x for x in xs}
    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x
    def union(self, a, b):
        a, b = self.find(a), self.find(b)
        if a == b:
            return False
        if a > b:
            a, b = b, a
        self.p[b] = a
        return True
    def classes(self):
        out = {}
        for x in sorted(self.p):
            out.setdefault(self.find(x), []).append(x)
        return [out[r] for r in sorted(out)]


def three_colorable(vertices, edges):
    vs = sorted(vertices)
    idx = {v: i for i, v in enumerate(vs)}
    def X(v, c): return idx[v] * 3 + c + 1
    cls = []
    for v in vs:
        lits = [X(v, c) for c in range(3)]
        cls.append(lits)
        for a, b in combinations(lits, 2):
            cls.append([-a, -b])
    V = set(vs)
    for u, v in edges:
        if u in V and v in V:
            for c in range(3):
                cls.append([-X(u, c), -X(v, c)])
    with Cadical195(bootstrap_with=cls) as sol:
        return sol.solve()


def find_k4(vertices, edges):
    E = set(edges)
    for q in combinations(sorted(vertices), 4):
        if all((min(a, b), max(a, b)) in E for a, b in combinations(q, 2)):
            return list(q)
    return None


def contracted_graph(nodes, edges, dsu):
    cls = dsu.classes()
    root_to_id = {dsu.find(c[0]): i for i, c in enumerate(cls)}
    node_to_id = {v: root_to_id[dsu.find(v)] for v in nodes}
    ce = set()
    for u, v in edges:
        if u not in node_to_id or v not in node_to_id:
            continue
        a, b = node_to_id[u], node_to_id[v]
        if a == b:
            raise RuntimeError(('internal edge after sound equality contraction', cls[a], u, v))
        ce.add((min(a, b), max(a, b)))
    adj = [set() for _ in cls]
    for a, b in ce:
        adj[a].add(b)
        adj[b].add(a)
    return cls, sorted(ce), adj


def one_round(nodes, edges, dsu):
    classes, ce, adj = contracted_graph(nodes, edges, dsu)
    E = set(ce)
    witnesses = []
    for a, b in combinations(range(len(classes)), 2):
        if (a, b) in E:
            continue
        common = sorted(adj[a] & adj[b])
        if len(common) < 4:
            continue
        k4 = find_k4(common, E)
        if k4 is not None:
            non3 = True
        else:
            non3 = not three_colorable(common, E)
        if not non3:
            continue
        witnesses.append({
            'class_ids': [a, b],
            'left_class': classes[a],
            'right_class': classes[b],
            'common_neighbor_class_ids': common,
            'common_neighbor_classes': [classes[x] for x in common],
            'k4_witness_class_ids': k4,
            'k4_witness_classes': [classes[x] for x in k4] if k4 is not None else None,
        })
    return witnesses


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
    left = sorted(set(pc) | set(S))
    dsu = DSU(left)

    rounds = []
    while True:
        ws = one_round(left, E, dsu)
        if not ws:
            break
        before = len(dsu.classes())
        merges = 0
        for w in ws:
            if dsu.union(w['left_class'][0], w['right_class'][0]):
                merges += 1
        after = len(dsu.classes())
        rounds.append({
            'round': len(rounds) + 1,
            'classes_before': before,
            'witness_count': len(ws),
            'actual_merges': merges,
            'classes_after': after,
            'witnesses': ws,
        })
        if merges == 0:
            raise RuntimeError('witness round produced no new merge')

    final_classes, final_edges, _ = contracted_graph(left, E, dsu)
    target_status = []
    for u, v in TARGETS:
        target_status.append({
            'pair': [u, v],
            'proved_by_closure': dsu.find(u) == dsu.find(v),
            'final_class': next(c for c in final_classes if u in c),
        })

    rep = {
        'upstream_sha': UPSTREAM_SHA,
        'separator_qnodes': S,
        'p_qnode': p,
        'left_bag_size': len(left),
        'rule': 'In a proper 5-coloring, two nonadjacent quotient vertices/classes are forced equal if their common-neighborhood graph is not 3-colorable. Already proved equal classes are contracted and the rule is iterated to closure.',
        'round_count': len(rounds),
        'rounds': rounds,
        'final_class_count': len(final_classes),
        'final_classes': final_classes,
        'final_contracted_edge_count': len(final_edges),
        'targets': target_status,
        'all_targets_proved_by_closure': all(x['proved_by_closure'] for x in target_status),
        'interpretation': 'Every merge is justified by the same graph-theoretic common-neighborhood lemma, applied after contracting equalities proved in earlier rounds. If a target pair ends in one class, this supplies a human-checkable local-lemma chain rather than a direct SAT boundary-table argument.'
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(rep, indent=2) + '\n')
    print(json.dumps({
        'round_count': rep['round_count'],
        'round_sizes': [{'round': r['round'], 'witnesses': r['witness_count'], 'merges': r['actual_merges'], 'classes_after': r['classes_after']} for r in rounds],
        'targets': target_status,
        'all_targets_proved_by_closure': rep['all_targets_proved_by_closure'],
    }, indent=2))


if __name__ == '__main__':
    main()
