#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path

from pysat.solvers import Cadical195, Glucose4

from separator_interface import P, Q, UPSTREAM_SHA, build, components_without, min_vertex_cut

K = 5
PAIRS = [(5, 6), (0, 10), (8, 9)]
S_EXPECTED = [0, 6, 8, 9, 10, 266]
TRACKED = [5] + S_EXPECTED


def activation_cnf(nodes, edges):
    ns = sorted(nodes)
    idx = {v: i for i, v in enumerate(ns)}
    color_n = len(ns) * K
    def X(v, c): return idx[v] * K + c + 1
    def A(v): return color_n + idx[v] + 1
    cls = []
    for v in ns:
        cls.append([-A(v)] + [X(v, c) for c in range(K)])
        for a, b in combinations(range(K), 2):
            cls.append([-A(v), -X(v, a), -X(v, b)])
    V = set(ns)
    for u, v in edges:
        if u in V and v in V:
            for c in range(K):
                cls.append([-A(u), -A(v), -X(u, c), -X(v, c)])
    return ns, cls, X, A


def direct_cnf(nodes, edges, pair=None):
    ns = sorted(nodes)
    idx = {v: i for i, v in enumerate(ns)}
    def X(v, c): return idx[v] * K + c + 1
    cls = []
    for v in ns:
        lits = [X(v, c) for c in range(K)]
        cls.append(lits)
        for a, b in combinations(lits, 2): cls.append([-a, -b])
    V = set(ns)
    for u, v in edges:
        if u in V and v in V:
            for c in range(K): cls.append([-X(u,c), -X(v,c)])
    if pair:
        u, v = pair
        for c in range(K): cls.append([-X(u,c), -X(v,c)])
    return cls


def verify(nodes, edges, pair):
    base = direct_cnf(nodes, edges)
    neq = direct_cnf(nodes, edges, pair)
    out = {}
    for name, Solver in [('Cadical195', Cadical195), ('Glucose4', Glucose4)]:
        with Solver(bootstrap_with=base) as s: base_sat = s.solve()
        with Solver(bootstrap_with=neq) as s: neq_sat = s.solve()
        out[name] = {'base_sat': base_sat, 'neq_sat': neq_sat}
    out['verified_forced_equal'] = all(x['base_sat'] and not x['neq_sat'] for x in out.values() if isinstance(x, dict))
    return out


def minimize_with_solver(ns, cls, X, A, pair, start):
    u, v = pair
    extra = [[-X(u,c), -X(v,c)] for c in range(K)]
    sol = Cadical195(bootstrap_with=cls + extra)
    try:
        active = set(start) | {u, v}
        universe = set(ns)
        for x in sorted(active - {u, v}):
            trial = active - {x}
            ass = [A(z) if z in trial else -A(z) for z in ns]
            if not sol.solve(assumptions=ass):
                active = trial
        for x in sorted(active - {u, v}):
            trial = active - {x}
            ass = [A(z) if z in trial else -A(z) for z in ns]
            if not sol.solve(assumptions=ass):
                raise RuntimeError((pair, x, 'not inclusion-minimal'))
        return sorted(active)
    finally:
        sol.delete()


def extract_pair_core(ns, cls, X, A, pair, edges):
    u, v = pair
    extra = [[-X(u,c), -X(v,c)] for c in range(K)]
    sol = Cadical195(bootstrap_with=cls + extra)
    try:
        ass = [A(z) for z in ns]
        sat = sol.solve(assumptions=ass)
        if sat:
            raise RuntimeError((pair, 'not forced equal in full left bag'))
        raw = sol.get_core()
        if raw is None:
            raise RuntimeError((pair, 'solver returned no assumption core'))
        inv = {A(z): z for z in ns}
        raw_vertices = sorted({inv[x] for x in raw if x > 0 and x in inv} | {u, v})
    finally:
        sol.delete()
    minimal = minimize_with_solver(ns, cls, X, A, pair, raw_vertices)
    V = set(minimal)
    es = [[a,b] for a,b in edges if a in V and b in V]
    return {
        'pair': list(pair),
        'raw_assumption_core_vertices': raw_vertices,
        'raw_assumption_core_size': len(raw_vertices),
        'minimal_vertices': minimal,
        'minimal_vertex_count': len(minimal),
        'minimal_edges': es,
        'minimal_edge_count': len(es),
        'verification': verify(minimal, edges, pair),
    }


def minimize_shared(ns, cls, X, A, starts):
    active = set().union(*[set(x) for x in starts]) | set(TRACKED)
    solvers = []
    for u,v in PAIRS:
        extra=[[-X(u,c),-X(v,c)] for c in range(K)]
        solvers.append(Cadical195(bootstrap_with=cls+extra))
    try:
        for x in sorted(active - set(TRACKED)):
            trial=active-{x}
            ass=[A(z) if z in trial else -A(z) for z in ns]
            if all(not s.solve(assumptions=ass) for s in solvers):
                active=trial
        critical=[]
        for x in sorted(active-set(TRACKED)):
            trial=active-{x}
            ass=[A(z) if z in trial else -A(z) for z in ns]
            broken=[]
            for pair,s in zip(PAIRS,solvers):
                if s.solve(assumptions=ass): broken.append(list(pair))
            if not broken: raise RuntimeError((x,'shared core not minimal'))
            critical.append({'vertex':x,'equalities_broken_if_deleted':broken})
    finally:
        for s in solvers: s.delete()
    V=set(active)
    es=[[a,b] for a,b in edges_global if a in V and b in V]
    checks={f'{u}-{v}':verify(active,edges_global,(u,v)) for u,v in PAIRS}
    return sorted(active), es, critical, checks


def contracted_graph(edges):
    classes=[[5,6],[0,10],[8,9],[266]]
    ci={v:i for i,c in enumerate(classes) for v in c}
    ce=set(); direct=[]; T=set(TRACKED)
    for u,v in edges:
        if u in T and v in T:
            direct.append([u,v]); a,b=ci[u],ci[v]
            if a!=b: ce.add((min(a,b),max(a,b)))
    all6=set(combinations(range(4),2)); missing=sorted(all6-ce)
    return {'classes':classes,'direct_edges':sorted(direct),'contracted_edges':[list(x) for x in sorted(ce)],'missing_edges':[list(x) for x in missing],'is_K4_minus_one_edge':len(ce)==5 and len(missing)==1}


def main():
    global edges_global
    ap=argparse.ArgumentParser(); ap.add_argument('--data-dir',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    C,R,vq,E=build(a.data_dir); edges_global=E; n=len(R); p,q=vq[P],vq[Q]; val,S=min_vertex_cut(n,E,p,q)
    if p!=5 or S!=S_EXPECTED: raise RuntimeError((p,q,S))
    cc=components_without(n,E,S); pc=next(x for x in cc if p in x); left=set(pc)|set(S)
    ns,cls,X,A=activation_cnf(left,E)
    pair_cores=[extract_pair_core(ns,cls,X,A,pair,E) for pair in PAIRS]
    shared_nodes,shared_edges,critical,checks=minimize_shared(ns,cls,X,A,[x['minimal_vertices'] for x in pair_cores])
    rep={
      'upstream_sha':UPSTREAM_SHA,'separator_qnodes':S,'left_bag_size':len(left),'forced_equal_pairs':[list(x) for x in PAIRS],
      'pair_cores':pair_cores,
      'shared_core':{'vertices':shared_nodes,'vertex_count':len(shared_nodes),'edges':shared_edges,'edge_count':len(shared_edges),'deletion_criticality':critical,'verification':checks,'original_components':{str(v):C[R[v]] for v in shared_nodes}},
      'tracked_contracted_graph':contracted_graph(E),
      'interpretation':'CaDiCaL assumption cores identify sufficient active-vertex sets for each forced equality. Each core is then deletion-minimized as an induced subgraph and independently rechecked with Glucose4. The union is deletion-minimized for all three equalities while retaining p plus all six separator nodes. Contracting the three equalities on those tracked nodes gives K4 minus one edge, which explains exactly the two p-side boundary states.'
    }
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(rep,indent=2)+'\n')
    print(json.dumps({'pair_core_sizes':{f"{x['pair'][0]}-{x['pair'][1]}":x['minimal_vertex_count'] for x in pair_cores},'raw_core_sizes':{f"{x['pair'][0]}-{x['pair'][1]}":x['raw_assumption_core_size'] for x in pair_cores},'shared_core_size':len(shared_nodes),'shared_core_edges':len(shared_edges),'tracked_contraction':rep['tracked_contracted_graph']},indent=2))

if __name__=='__main__': main()
