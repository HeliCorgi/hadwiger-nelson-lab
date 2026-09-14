#!/usr/bin/env python3
"""Exact SAT probe for the chromatic number of a center-center graph.

Input CENTER_LIBRARY edges have already been certified as literal unit-distance
relations by the geometry census.  This tool is diagnostic: it tests ordinary
k-colorability of the center graph itself.  A 4-chromatic center graph is not an
HN witness, but can provide a stronger missing-color/list-coloring coupling core.
"""
from __future__ import annotations
import argparse,json
from itertools import combinations
from pathlib import Path
from pysat.solvers import Cadical195


def cnf(n,edges,k):
    out=[]
    def x(v,c): return v*k+c+1
    for v in range(n):
        xs=[x(v,c) for c in range(k)];out.append(xs)
        for a,b in combinations(xs,2):out.append([-a,-b])
    for u,v in edges:
        for c in range(k):out.append([-x(u,c),-x(v,c)])
    # Global color symmetry: any nonempty graph coloring can rename the first
    # vertex's color to 0.  For an empty graph this is also harmless.
    if n: out.append([x(0,0)])
    return out


def solve(n,edges,k):
    with Cadical195(bootstrap_with=cnf(n,edges,k)) as s:
        ans=s.solve()
        if not ans:return False,None
        pos={z for z in s.get_model() if z>0}; col=[]
        for v in range(n):
            cs=[c for c in range(k) if v*k+c+1 in pos]
            assert len(cs)==1;col.append(cs[0])
        assert all(col[u]!=col[v] for u,v in edges)
        return True,col


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--library',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();d=json.loads(a.library.read_text());n=len(d['candidates']);edges=sorted({tuple(map(int,e)) for e in d['center_edges']})
    assert all(0<=u<v<n for u,v in edges)
    res=[];chi_upper=None;best=None
    for k in (2,3,4,5):
        sat,col=solve(n,edges,k);res.append({'k':k,'sat':sat})
        if sat:
            chi_upper=k;best=col;break
    chi_lower=1
    for r in res:
        if not r['sat']:chi_lower=max(chi_lower,r['k']+1)
    out={'vertices':n,'edges':len(edges),'tests':res,'chromatic_lower_bound':chi_lower,'chromatic_upper_bound':chi_upper,
         'classification':None,'ordinary_center_graph_coloring_is_not_an_HN_claim':True}
    if best is not None:
        out['validated_coloring']=best
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k!='validated_coloring'},indent=2))

if __name__=='__main__':main()
