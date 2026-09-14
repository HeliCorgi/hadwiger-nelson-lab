#!/usr/bin/env python3
"""Exact MaxSAT analysis of three-color escape valves in a center list CSP.

Base colors induce an allowed list L_i on each center: colors not used by its
exact base neighbors. Center-center unit edges require unequal colors. For each
3-color palette T, minimize the number of centers assigned outside T. A positive
optimum measures how many escape valves a list-coloring needs for that fixed base
coloring; it is not evidence about the full graph because the base may recolor.
"""
from __future__ import annotations
import argparse,json
from itertools import combinations
from pathlib import Path
from pysat.formula import WCNF
from pysat.examples.rc2 import RC2


def solve(lists,edges,T):
    n=len(lists); w=WCNF()
    def var(i,c): return i*5+c+1
    for i,L in enumerate(lists):
        xs=[var(i,c) for c in L]; assert xs
        w.append(xs)
        for a,b in combinations(xs,2): w.append([-a,-b])
        for c in range(5):
            if c not in L: w.append([-var(i,c)])
    for u,v in edges:
        for c in range(5): w.append([-var(u,c),-var(v,c)])
    for i,L in enumerate(lists):
        for c in L:
            if c not in T: w.append([-var(i,c)],weight=1)
    with RC2(w,solver='g4') as rc:
        model=rc.compute(); cost=int(rc.cost)
    pos={x for x in model if x>0}; colors=[]
    for i,L in enumerate(lists):
        q=[c for c in L if var(i,c) in pos]; assert len(q)==1; colors.append(q[0])
    assert all(colors[u]!=colors[v] for u,v in edges)
    outside=[i for i,c in enumerate(colors) if c not in T]
    assert len(outside)==cost
    return cost,colors,outside


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--library',type=Path,required=True)
    ap.add_argument('--base-coloring',type=Path,required=True); ap.add_argument('--base-vertices',type=int,required=True)
    ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    lib=json.loads(a.library.read_text()); cands=lib['candidates']; edges=[tuple(map(int,e)) for e in lib['center_edges']]
    s=a.base_coloring.read_text().strip(); assert len(s)>=a.base_vertices and all(ch in '01234' for ch in s[:a.base_vertices])
    base=list(map(int,s[:a.base_vertices])); lists=[]
    for cand in cands:
        used={base[v] for v in cand['base_neighbors']}; L=sorted(set(range(5))-used); assert L; lists.append(L)
    results=[]
    for T in combinations(range(5),3):
        cost,colors,outside=solve(lists,edges,set(T))
        results.append({'palette':list(T),'min_outside_centers':cost,'outside_centers':outside,'center_colors':colors})
        print(json.dumps({'palette':T,'min_outside_centers':cost,'outside_centers':outside}),flush=True)
    results.sort(key=lambda r:(r['min_outside_centers'],r['palette']))
    out={'status':'EXACT_FIXED_BASE_LIST_ESCAPE_ANALYSIS','centers':len(cands),'center_edges':len(edges),
         'list_size_histogram':{str(k):sum(len(L)==k for L in lists) for k in sorted(set(map(len,lists)))},
         'best_palette':results[0]['palette'],'minimum_escape_valves':results[0]['min_outside_centers'],
         'results':results,'fixed_base_only_not_global_evidence':True}
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k!='results'},indent=2))

if __name__=='__main__': main()
