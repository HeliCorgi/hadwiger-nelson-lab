#!/usr/bin/env python3
"""A direct geometric family: add unit-circle intersection points and real edges.

Float clustering proposes positions only. Each retained point is independently
reconstructed as the exact circumcenter of three original centers in K2; its
unit incidences are checked exactly. No coloring equality is an input constraint.
"""
from __future__ import annotations
import argparse
from collections import defaultdict, Counter
from fractions import Fraction
import hashlib
import itertools
import json
import math
from pathlib import Path
from time import monotonic
import numpy as np
import sympy as sp
from hn_exact import K2, E0, Z0, ONE, unit_modulus
from hn_unconditional_scan import write_json, scan


def inverse(x):
    basis=[]
    for j in range(16):
        a=[0]*8; b=[0]*8
        (a if j<8 else b)[j%8]=1
        basis.append(K2(a,b))
    cols=[]
    for b in basis:
        p=x*b
        cols.append([sp.Rational(v,p.den) for v in p.a+p.b])
    values=sp.Matrix(16,16,lambda i,j:cols[j][i]).inv()[:,0]
    den=math.lcm(*(int(v.q) for v in values))
    ints=[int(v*den) for v in values]
    result=K2(ints[:8],ints[8:],den)
    assert (result*x).is_one()
    return result


def circumcenter(a,b,c):
    u=b-a; v=c-a
    det=u.conj()*v-v.conj()*u
    if det==K2(Z0): return None
    return a+(u*u.conj()*v-v*v.conj()*u)*inverse(det)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--graph',type=Path,required=True)
    ap.add_argument('--out-dir',type=Path,required=True)
    ap.add_argument('--max-new',type=int,default=1000)
    ap.add_argument('--min-contacts',type=int,default=3)
    ap.add_argument('--scan-seconds',type=float,default=90)
    args=ap.parse_args()
    started=monotonic()
    original=json.loads(args.graph.read_text())
    pts=[K2(p['a'],p['b'],p['den']) for p in original['pts']]
    base_n=len(pts)
    known=set(pts)
    xy=np.array([[z.emb().real,z.emb().imag] for z in pts])
    clusters=defaultdict(set)
    for i in range(base_n):
        dx=xy[i+1:]-xy[i]
        rs=np.sum(dx*dx,axis=1)
        for jj in np.where((rs>1e-12)&(rs<=4+1e-10))[0]:
            j=int(jj+i+1); r=float(rs[jj])
            middle=(xy[i]+xy[j])/2
            arm=math.sqrt(max(0.,1/r-0.25))*np.array([-dx[jj,1],dx[jj,0]])
            for pos in (middle+arm,middle-arm):
                key=tuple(int(round(float(t)*1e7)) for t in pos)
                clusters[key].update((i,j))
    proposed=sorted(((key,sorted(vs)) for key,vs in clusters.items() if len(vs)>=args.min_contacts),
                    key=lambda p:(-len(p[1]),p[0]))
    write_json(args.out_dir/'PROPOSALS.json',{'base_vertices':base_n,'clusters':len(clusters),
        'min_contacts':args.min_contacts,'proposal_count':len(proposed),
        'contact_histogram':dict(Counter(len(v) for _,v in proposed)),
        'geometry_status':'float proposals only; not an exhaustive geometric classification'})
    print('Proposed',len(proposed),'clusters',flush=True)
    additions=[]
    for key,neighbors in proposed:
        point=None
        for i,j,k in itertools.combinations(neighbors,3):
            af,bf,cf=xy[[i,j,k]]
            if abs(np.linalg.det(np.array([bf-af,cf-af])))<1e-9: continue
            point=circumcenter(pts[i],pts[j],pts[k])
            break
        if point is None or point in known: continue
        if not all(unit_modulus(point-pts[v]) for v in neighbors): continue
        actual=[i for i in range(base_n) if unit_modulus(point-pts[i])]
        if len(actual)<args.min_contacts: continue
        known.add(point); pts.append(point)
        additions.append({'vertex':len(pts)-1,'base_unit_neighbors':actual,
                          'a':point.a,'b':point.b,'den':point.den})
        write_json(args.out_dir/'ADDITIONS.json',additions)
        print('Exact new point',len(additions),'contacts',len(actual),flush=True)
        if len(additions)>=args.max_new: break
    # Exact all-pairs graph. Slow but unambiguous for this bounded family.
    edges=[]
    for i in range(len(pts)):
        for j in range(i+1,len(pts)):
            if unit_modulus(pts[i]-pts[j]): edges.append((i,j))
        if i%100==0:
            write_json(args.out_dir/'BUILD_PROGRESS.json',{'checked_first_vertices':i+1,'vertices':len(pts),'unit_edges_so_far':len(edges)})
    graph={'pts':[{'a':p.a,'b':p.b,'den':p.den} for p in pts],'edges':edges,
           'construction':'one round of unit-circle intersection closure, exact circumcenters, selected by minimum contacts',
           'source_sha256':hashlib.sha256(args.graph.read_bytes()).hexdigest(),
           'new_vertices':len(additions),'min_contacts':args.min_contacts,
           'all_pairs_exactly_checked':len(pts)*(len(pts)-1)//2,
           'no_conditional_constraints':True,'distance_threshold':None}
    write_json(args.out_dir/'GRAPH.json',graph)
    result=scan(len(pts),edges,args.out_dir/'SCAN.json',seconds=args.scan_seconds)
    print(json.dumps({'classification':result['classification'],'status':result['status'],
                      'vertices':len(pts),'edges':len(edges),'new_vertices':len(additions),
                      'elapsed':round(monotonic()-started,2)},indent=2),flush=True)

if __name__=='__main__': main()
