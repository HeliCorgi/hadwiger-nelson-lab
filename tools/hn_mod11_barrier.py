#!/usr/bin/env python3
"""Independent mod-11 five-color certificate for the old coordinate class.

No SAT, floating point or hn_exact import. K2 input is checked for membership
in Q(sqrt(5),sqrt(-3),sqrt(-11)); Cartesian coordinates then belong to
Z_(11)[sqrt(3),sqrt(5),sqrt(11)] when denominators pass the check.
The ring map sqrt(3)->5, sqrt(5)->4, sqrt(11)->0 preserves all unit edges.
The finite color table is Madore, arXiv:1509.07023, Lemma 4.5 (p.12).
All 726 edges of this 121-vertex table are verified, not assumed.
The separate valuation argument extends the obstruction to the whole real
field Q(sqrt(3),sqrt(5),sqrt(11)); this script certifies the integral inputs.
"""
from __future__ import annotations
import argparse
from collections import Counter
from itertools import combinations
import hashlib
import json
from math import gcd
from pathlib import Path
from time import perf_counter
import zipfile

TABLE = (
    (3,1,0,2,1,2,3,4,2,0,1),
    (1,2,1,0,4,1,2,3,4,3,2),
    (2,1,2,3,0,2,1,2,3,4,0),
    (0,2,3,1,3,4,0,4,1,3,4),
    (4,0,1,2,1,3,4,0,2,1,2),
    (3,4,0,1,2,1,3,4,1,2,1),
    (1,2,3,4,0,3,1,0,4,0,2),
    (2,1,4,3,4,0,2,3,0,3,4),
    (4,2,3,4,3,4,0,2,3,4,0),
    (0,4,1,2,1,0,4,0,2,3,2),
    (4,0,4,1,2,3,0,3,0,1,3),
)
# Basis mask: bit0=sqrt(3), bit1=sqrt(5), bit2=sqrt(11).
RAD = (1,3,5,15,11,33,55,165)
# Columns [1,sqrt(5),sqrt(-3),sqrt(-15)] in the zeta30 basis.
BASIS = (
    (1,-1,-1,-3), (0,0,0,-4), (0,2,0,2), (0,2,0,2),
    (0,0,0,4), (0,0,2,2), (0,0,0,0), (0,-2,0,-2),
)

def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)

def coeff4(v: list[int]) -> list[int]:
    """Return four times the coefficients in the smaller complex basis."""
    require(len(v)==8 and all(type(x) is int for x in v), 'bad K2 vector')
    c = [4*v[0]+2*v[2]+2*v[5]-v[1], 2*v[2]+v[1],
         2*v[5]+v[1], -v[1]]
    require(all(sum(b*q for b,q in zip(row,c))==4*w
                for row,w in zip(BASIS,v)), 'point is outside the audited subfield')
    return c

def cartesian(p: dict) -> tuple[tuple[int,...],tuple[int,...],int]:
    require(type(p['den']) is int and p['den']>0, 'bad denominator')
    a,b = coeff4(p['a']), coeff4(p['b'])
    x = [a[0],0,a[1],0,0,-b[2],0,-b[3]]
    y = [0,a[2],0,a[3],b[0],0,b[1],0]
    den = 4*p['den']
    g = den
    for q in x+y:
        g=gcd(g,q)
    x,y,den = tuple(q//g for q in x),tuple(q//g for q in y),den//g
    require(den%11!=0, 'denominator needs valuation handling; direct map not applicable')
    return x,y,den

def residue(p) -> tuple[int,int]:
    x,y,den = p
    values=(1,5,4,20,0,0,0,0)
    inv=pow(den,-1,11)
    return (sum(q*v for q,v in zip(x,values))*inv%11,
            sum(q*v for q,v in zip(y,values))*inv%11)

def square(v: list[int]) -> list[int]:
    out=[0]*8
    nz=[(i,q) for i,q in enumerate(v) if q]
    for i,a in nz:
        out[0]+=a*a*RAD[i]
    for (i,a),(j,b) in combinations(nz,2):
        out[i^j]+=2*a*b*RAD[i&j]
    return out

def unit_distance(p,q) -> bool:
    x,y,d=p; xx,yy,e=q
    sx=square([a*e-b*d for a,b in zip(x,xx)])
    sy=square([a*e-b*d for a,b in zip(y,yy)])
    norm=[a+b for a,b in zip(sx,sy)]
    return norm[0]==(d*e)**2 and all(t==0 for t in norm[1:])

def check_table() -> int:
    require(len(TABLE)==11 and all(len(row)==11 for row in TABLE), 'bad table shape')
    require(all(type(c) is int and 0<=c<5 for row in TABLE for c in row), 'bad table colors')
    pts=[(i,j) for i in range(11) for j in range(11)]
    count=0
    for (x,y),(xx,yy) in combinations(pts,2):
        if ((x-xx)**2+(y-yy)**2)%11==1:
            require(TABLE[x][y]!=TABLE[xx][yy], 'invalid finite-field color table')
            count+=1
    require(count==726, 'unexpected finite-field graph edge count')
    return count

def read_graph(path: Path) -> dict:
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            return json.loads(archive.read('GRAPH.json'))
    return json.loads(path.read_text())

def audit(graph: dict, check_geometry: bool=True):
    started=perf_counter()
    finite_edges=check_table()
    pts=[cartesian(p) for p in graph['pts']]
    n=len(pts)
    require(len(set(pts))==n, 'duplicate exact Cartesian points')
    edges=[tuple(e) for e in graph['edges']]
    require(all(len(e)==2 and all(type(i) is int for i in e)
                and 0<=e[0]<e[1]<n for e in edges), 'invalid edge indexing')
    require(len(set(edges))==len(edges), 'duplicate saved edge')
    red=[residue(p) for p in pts]
    colors=[TABLE[x][y] for x,y in red]
    for u,v in edges:
        if check_geometry:
            require(unit_distance(pts[u],pts[v]), 'non-unit saved geometric edge')
        x,y=red[u]; xx,yy=red[v]
        require(((x-xx)**2+(y-yy)**2)%11==1, 'edge not preserved by reduction')
        require(colors[u]!=colors[v], 'monochromatic saved edge')
    text=''.join(map(str,colors))+'\n'
    semantic={'pts':graph['pts'],'edges':[list(e) for e in sorted(edges)]}
    small_ring=True
    for _,_,den in pts:
        for p in (2,3,5):
            while den%p==0:
                den//=p
        small_ring &= den==1
    info={
        'status':'EXPLICIT_MOD11_5_COLORING', 'classification':'NOT_A',
        'vertices':n, 'edges':len(edges), 'all_points_checked_in_subfield':True,
        'all_denominators_coprime_to_11':True,
        'all_points_in_Z_1over30_sqrt3_sqrt5_sqrt11':small_ring,
        'finite_field_vertices':121, 'finite_field_edges_checked':finite_edges,
        'residue_classes_used':len(set(red)), 'all_saved_edges_preserved_mod11':True,
        'all_saved_edges_checked_exactly_independent_multiquadratic':check_geometry,
        'monochromatic_edges':0, 'class_sizes':dict(sorted(Counter(colors).items())),
        'semantic_pts_edges_sha256':hashlib.sha256(json.dumps(semantic,sort_keys=True,
                                        separators=(',',':')).encode()).hexdigest(),
        'coloring_txt_sha256':hashlib.sha256(text.encode()).hexdigest(),
        'elapsed_seconds':round(perf_counter()-started,6),
        'scope':'The ring-map proof protects all true unit pairs in the checked ring; '
                'only saved edges are individually enumerated here. '
                'No claim about arbitrary ambient K2 points or a forced-equal B pair.',
    }
    return info,text

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--graph',type=Path,required=True)
    ap.add_argument('--out-dir',type=Path,required=True)
    a=ap.parse_args()
    info,text=audit(read_graph(a.graph))
    a.out_dir.mkdir(parents=True,exist_ok=True)
    (a.out_dir/'MOD11_AUDIT.json').write_text(json.dumps(info,indent=2)+'\n')
    (a.out_dir/'COLORING.txt').write_text(text)
    print(json.dumps(info,indent=2))

if __name__=='__main__':
    main()
