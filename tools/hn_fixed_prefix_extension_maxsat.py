#!/usr/bin/env python3
"""Exact weighted MaxSAT for extending a fixed proper prefix coloring.

Vertices [0,prefix) have fixed colors. Suffix vertices must be properly colored
among themselves; every suffix-prefix monochromatic edge costs one. RC2 finds
the exact minimum number of unavoidable conflicts with the fixed prefix. The
result is a near-coloring seed for unrestricted repair only; positive optimum is
not evidence that the whole graph is non-5-colorable because prefix colors may
change.
"""
from __future__ import annotations
import argparse,json
from collections import Counter
from itertools import combinations
from pathlib import Path
from pysat.formula import WCNF
from pysat.examples.rc2 import RC2
from hn_exact import K2,unit_modulus
from hn_unconditional_scan import valid_coloring,write_json


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--graph',type=Path,required=True)
    ap.add_argument('--prefix-coloring',type=Path,required=True); ap.add_argument('--prefix',type=int,required=True)
    ap.add_argument('--out-dir',type=Path,required=True); a=ap.parse_args(); a.out_dir.mkdir(parents=True,exist_ok=True)
    d=json.loads(a.graph.read_text()); pts=[K2(p['a'],p['b'],p['den']) for p in d['pts']]
    edges=sorted({tuple(map(int,e)) for e in d['edges']}); n=len(pts); p=a.prefix; assert 0<p<n
    assert len(set(pts))==n and all(unit_modulus(pts[u]-pts[v]) for u,v in edges)
    s=a.prefix_coloring.read_text().strip(); assert len(s)>=p and all(ch in '01234' for ch in s[:p])
    base=list(map(int,s[:p])); prefix_edges=[(u,v) for u,v in edges if v<p]
    assert valid_coloring(base,p,prefix_edges)
    m=n-p; w=WCNF()
    def var(i,c): return i*5+c+1
    for i in range(m):
        xs=[var(i,c) for c in range(5)]; w.append(xs)
        for x,y in combinations(xs,2): w.append([-x,-y])
    cross=[]; suffix=[]
    for u,v in edges:
        if u<p<=v: cross.append((u,v-p)); w.append([-var(v-p,base[u])],weight=1)
        elif p<=u<v:
            i,j=u-p,v-p; suffix.append((i,j))
            for c in range(5): w.append([-var(i,c),-var(j,c)])
    with RC2(w,solver='g4') as rc:
        model=rc.compute(); opt=int(rc.cost)
    pos={x for x in model if x>0}; cc=[]
    for i in range(m):
        q=[c for c in range(5) if var(i,c) in pos]; assert len(q)==1; cc.append(q[0])
    seed=base+cc; bad=[(u,v) for u,v in edges if seed[u]==seed[v]]
    assert len(bad)==opt and all(u<p<=v for u,v in bad)
    (a.out_dir/'SEED.txt').write_text(''.join(map(str,seed))+'\n')
    out={'status':'OPTIMUM','vertices':n,'edges':len(edges),'prefix_vertices':p,'suffix_vertices':m,
         'cross_edges':len(cross),'suffix_edges':len(suffix),'optimum_fixed_prefix_conflicts':opt,
         'bad_edges':[list(e) for e in bad],'positive_optimum_is_evidence':False}
    write_json(a.out_dir/'MAXSAT.json',out)
    print(json.dumps({k:v for k,v in out.items() if k!='bad_edges'},indent=2))

if __name__=='__main__': main()
