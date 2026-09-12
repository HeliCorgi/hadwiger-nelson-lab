#!/usr/bin/env python3
"""Direct same-color forcing scan on actual unit-distance graphs, never quotients.

Every saved coloring is checked on every edge. Its equality classes refine the
remaining possible forced-equality classes; singletons exhaust ALL point pairs.
Timeout/conflict-budget UNKNOWN does not establish any forcing statement.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import hashlib
import itertools
import json
import random
from pathlib import Path
from time import monotonic
from pysat.solvers import Cadical195
from hn_exact import K2, unit_modulus


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, indent=2) + '\n')
    tmp.replace(path)


def color_cnf(n, edges, k=5):
    clauses = []
    for v in range(n):
        vs = [v*k+c+1 for c in range(k)]
        clauses.append(vs)
        clauses.extend([[-a,-b] for a,b in itertools.combinations(vs,2)])
    clauses.extend([[-(u*k+c+1),-(v*k+c+1)] for u,v in edges for c in range(k)])
    return clauses


def valid_coloring(colors, n, edges):
    return len(colors)==n and all(type(c) is int and 0<=c<5 for c in colors) and all(colors[u]!=colors[v] for u,v in edges)


def refine(blocks, colors):
    result=[]
    for block in blocks:
        parts=defaultdict(list)
        for v in block:
            parts[colors[v]].append(v)
        result.extend(parts.values())
    return result


def pairs_left(blocks):
    return sum(len(b)*(len(b)-1)//2 for b in blocks)


def scan(n, edges, out, seed_models=(), seconds=90, conflict_budget=200000):
    started=monotonic()
    blocks=[list(range(n))]
    witnesses=[]
    records=[]
    pending=[]
    rng=random.Random(20260913)
    def accept(colors, origin):
        nonlocal blocks
        assert valid_coloring(colors,n,edges)
        new=refine(blocks,colors)
        if pairs_left(new)<pairs_left(blocks):
            blocks=new
            witnesses.append(colors)
            records.append({'origin':origin,'remaining_pairs':pairs_left(blocks)})
            save('ACTIVE')
    def save(status):
        data={'status':status,'classification':'D' if status=='NO_FORCED_EQUAL_PAIR' else 'C' if status=='CANDIDATE_UNVERIFIED' else None,
              'vertices':n,'edges':len(edges),'colorings':witnesses,'progress':records,
              'remaining_blocks':[b for b in blocks if len(b)>1],'remaining_pairs':pairs_left(blocks),
              'unchecked_candidates':pending,'seconds':round(monotonic()-started,3),
              'no_conditional_constraints':True,'distance_threshold':None}
        write_json(out,data)
        return data
    save('ACTIVE')
    # Greedy use of already available real proper colorings; every one validated.
    candidates=[]
    for color in seed_models:
        color=list(map(int,color))
        assert valid_coloring(color,n,edges)
        candidates.append(color)
    while candidates and pairs_left(blocks):
        best=min(range(len(candidates)), key=lambda i:pairs_left(refine(blocks,candidates[i])))
        color=candidates.pop(best)
        if pairs_left(refine(blocks,color))==pairs_left(blocks):
            break
        accept(color,'validated_saved_model')
    if not pairs_left(blocks):
        return save('NO_FORCED_EQUAL_PAIR')
    with Cadical195(bootstrap_with=color_cnf(n,edges)) as solver:
        while pairs_left(blocks) and monotonic()-started<seconds:
            block=max(blocks,key=len)
            u,v=block[:2]
            # WLOG colors of one tested unequal pair are 0 and 1. No other
            # symmetry fixing is used, so this represents every unequal model.
            solver.conf_budget(conflict_budget)
            # Phases only guide SAT search; they do not constrain the formula.
            solver.set_phases([i*5+rng.randrange(5)+1 for i in range(n)])
            sat=solver.solve_limited(assumptions=[u*5+1,v*5+2])
            if sat is None:
                pending.append({'pair':[u,v],'status':'UNKNOWN'})
                return save('UNKNOWN')
            if sat is False:
                pending.append({'pair':[u,v],'status':'INEQUALITY_UNSAT_REQUIRES_INDEPENDENT_CHECK'})
                return save('CANDIDATE_UNVERIFIED')
            positive=set(solver.get_model())
            color=[next(c for c in range(5) if i*5+c+1 in positive) for i in range(n)]
            assert color[u]!=color[v]
            accept(color,'unconditional_inequality_SAT')
    return save('NO_FORCED_EQUAL_PAIR' if not pairs_left(blocks) else 'UNKNOWN')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--graph',type=Path,required=True)
    ap.add_argument('--seed-models',type=Path)
    ap.add_argument('--out-dir',type=Path,required=True)
    ap.add_argument('--seconds',type=float,default=90)
    args=ap.parse_args()
    if not __debug__: raise SystemExit('Run without -O')
    data=json.loads(args.graph.read_text())
    pts=[K2(p['a'],p['b'],p['den']) for p in data['pts']]
    edges=sorted(tuple(e) for e in data['edges'])
    assert len(set(pts))==len(pts)
    assert all(unit_modulus(pts[u]-pts[v]) for u,v in edges)
    # All-pairs exact test ensures the D conclusion includes the full induced
    # unit-distance graph, and hence all of its subgraphs.
    exact=[(u,v) for u in range(len(pts)) for v in range(u+1,len(pts)) if unit_modulus(pts[u]-pts[v])]
    assert exact==edges
    write_json(args.out_dir/'GEOMETRY.json',{'graph_sha256':hashlib.sha256(args.graph.read_bytes()).hexdigest(),
        'vertices':len(pts),'edges':len(edges),'distinct_exact_points':True,'all_pairs_exactly_checked':len(pts)*(len(pts)-1)//2,
        'induced_unit_edges_exactly_match':True,'field':'Q(zeta30,sqrt(-11))','distance_threshold':None})
    seeds=[] if not args.seed_models else json.loads(args.seed_models.read_text())['models'].values()
    result=scan(len(pts),edges,args.out_dir/'SCAN.json',seeds,args.seconds)
    print(json.dumps({k:v for k,v in result.items() if k not in ('colorings','progress','remaining_blocks')},indent=2))

if __name__=='__main__': main()
