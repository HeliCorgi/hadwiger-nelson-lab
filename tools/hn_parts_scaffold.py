#!/usr/bin/env python3
"""Exact Parts 2010.12656v2 G16/G31 two-distance scaffold; NOT an HN A.

Positive real roots r=sqrt(5), t^2=(5-r)/8, s^2=(97-19*r)/1000.
The eight basis elements are r^i t^j s^k (i,j,k in {0,1}).
Fractions certify geometry without floats. Exhaustive coloring search on the
small graphs independently certifies the relation and six-chromatic result.
"""
from __future__ import annotations
import argparse, hashlib, json
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path

ZERO=(F(0),)*8

def pairmul(x,y): return (x[0]*y[0]+5*x[1]*y[1],x[0]*y[1]+x[1]*y[0])

def product(i,j):
    c=(F(5 if i&j&1 else 1),F(0)); mask=i^j
    if i&j&2: c=pairmul(c,(F(5,8),F(-1,8)))
    if i&j&4: c=pairmul(c,(F(97,1000),F(-19,1000)))
    if mask&1: c=pairmul(c,(F(0),F(1)))
    return [(mask&6,c[0]),((mask&6)|1,c[1])]

PROD=[[product(i,j) for j in range(8)] for i in range(8)]

class A:
    __slots__=('v',)
    def __init__(self,v=ZERO):
        if isinstance(v,(int,F)): v=(F(v),)+ZERO[1:]
        self.v=tuple(map(F,v)); assert len(self.v)==8
    def __hash__(self): return hash(self.v)
    def __eq__(self,o): return isinstance(o,A) and self.v==o.v
    def __add__(self,o): return A([x+y for x,y in zip(self.v,o.v)])
    def __neg__(self): return A([-x for x in self.v])
    def __sub__(self,o): return self+-o
    def __mul__(self,o):
        v=list(ZERO)
        for i,x in enumerate(self.v):
            if x:
                for j,y in enumerate(o.v):
                    if y:
                        for k,c in PROD[i][j]:
                            if c: v[k]+=x*y*c
        return A(v)
    def pack(self): return [[x.numerator,x.denominator] for x in self.v]

def atom(i):
    v=list(ZERO); v[i]=F(1); return A(v)

O=A(); ONE=A(1); R=atom(1); T=atom(2); S=atom(4); PHI=(ONE+R)*A(F(1,2)); PHI2=PHI*PHI

def norm(p,q):
    x=p[0]-q[0]; y=p[1]-q[1]; return x*x+y*y

def add(p,q): return p[0]+q[0],p[1]+q[1]

E1=[(1,2),(1,3),(2,4),(2,5),(3,4),(3,6),(4,7),(4,8),(5,6),(5,8),(5,9),(6,7),(6,10),(7,9),(7,12),(7,13),(8,10),(8,11),(8,13),(9,11),(10,12),(11,12),(11,14),(12,15),(13,14),(13,15),(14,16),(15,16)]
EP=[(1,5),(1,6),(2,3),(2,6),(2,7),(2,9),(3,5),(3,8),(3,10),(4,9),(4,10),(4,11),(4,12),(5,13),(6,13),(7,10),(7,14),(8,9),(8,15),(9,13),(9,14),(10,13),(10,15),(11,15),(11,16),(12,14),(12,16),(14,15)]

def complete(pts):
    e1=[]; ep=[]
    assert len(set(pts))==len(pts)
    for i,j in combinations(range(len(pts)),2):
        d=norm(pts[i],pts[j])
        if d==ONE: e1.append((i,j))
        if d==PHI2: ep.append((i,j))
    return e1,ep

def enumerate_colorings(n,edges,k,pins,limit=None):
    adj=[set() for _ in range(n)]
    for u,v in edges: adj[u].add(v); adj[v].add(u)
    col=[-1]*n
    for v,c in pins.items(): col[v]=c
    assert all(col[u]<0 or col[v]<0 or col[u]!=col[v] for u,v in edges)
    models=[]; nodes=0
    def rec():
        nonlocal nodes
        nodes+=1
        if limit is not None and len(models)>=limit: return
        free=[v for v in range(n) if col[v]<0]
        if not free: models.append(col[:]); return
        v=max(free,key=lambda v:(len({col[w] for w in adj[v] if col[w]>=0}),len(adj[v]),-v))
        used={col[w] for w in adj[v]}
        for c in range(k):
            if c not in used: col[v]=c; rec(); col[v]=-1
    rec()
    assert all(all(c[u]!=c[v] for u,v in edges) for c in models)
    return models,nodes

def save(name,pts,edges,ephi,ports,out):
    graph={'pts':[{'x':x.pack(),'y':y.pack()} for x,y in pts],
           'field':'Q(r,t,s), r=sqrt5, t^2=(5-r)/8, s^2=(97-19r)/1000; positive roots',
           'edges':[list(e) for e in sorted(edges)],'phi_edges':[list(e) for e in ephi],
           'ports':ports,'scope':'Two distances {1,phi}; NOT a unit-distance graph or HN A witness.'}
    semantic={'pts':graph['pts'],'edges':graph['edges']}
    graph['semantic_pts_edges_sha256']=hashlib.sha256(json.dumps(semantic,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    (out/(name+'.json')).write_text(json.dumps(graph,indent=2)+'\n')
    return graph

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out-dir',type=Path,required=True)
    a=ap.parse_args(); out=a.out_dir; out.mkdir(parents=True,exist_ok=True)
    assert R*R==A(5) and T*T==(A(5)-R)*A(F(1,8))
    assert S*S==(A(97)-R*A(19))*A(F(1,1000))
    gs=[(PHI*A(F(1,2)),T),(-PHI*A(F(1,2)),T),(A(F(1,2)),PHI2*T),(A(F(-1,2)),PHI2*T)]
    # Vertex numbering of Parts Figure 2, reconstructed as subset sums.
    masks=[0,1,2,3,4,8,9,6,5,10,7,11,12,13,14,15]
    pts=[]
    for mask in masks:
        p=(O,O)
        for i,g in enumerate(gs):
            if mask>>i&1: p=add(p,g)
        pts.append(p)
    unit,long=complete(pts)
    assert unit==[(i-1,j-1) for i,j in E1]
    assert long==[(i-1,j-1) for i,j in EP]
    edges=sorted(unit+long)
    models,nodes=enumerate_colorings(16,edges,5,{0:0,1:1,2:2,4:3,5:4})
    assert models and all(c[0]==c[15] for c in models)
    c=(A(95)+R)*A(F(1,100))
    assert c*c+S*S==ONE
    rot=[(c*x-S*y,S*x+c*y) for x,y in pts]
    assert rot[0]==pts[0] and set(rot)&set(pts)=={pts[0]}
    assert norm(pts[15],rot[15])==ONE
    both=pts+rot[1:]; u31,p31=complete(both); all31=sorted(u31+p31)
    six,nn=enumerate_colorings(31,all31,6,{0:0,1:1,2:2,4:3,5:4},1)
    assert six
    five,n5=enumerate_colorings(31,all31,5,{0:0,1:1,2:2,4:3,5:4})
    assert not five
    three,_=enumerate_colorings(31,u31,3,{0:0,1:1},1)
    assert three
    cycle=[0,1,4,5,2]
    assert all(tuple(sorted((cycle[i],cycle[(i+1)%5]))) in u31 for i in range(5))
    g16=save('PARTS_G16',pts,edges,long,{'left':0,'right':15},out)
    g31=save('PARTS_G31',both,all31,p31,{'center':0,'tip1':15,'tip2':30},out)
    (out/'G31_6COLORING.txt').write_text(''.join(map(str,six[0]))+'\n')
    (out/'G31_UNIT_ONLY_3COLORING.txt').write_text(''.join(map(str,three[0]))+'\n')
    (out/'G16_MODELS.json').write_text(json.dumps({'models':models})+'\n')
    report={'source':'https://arxiv.org/abs/2010.12656v2','G16_vertices':16,
        'G16_unit_edges':len(unit),'G16_phi_edges':len(long),
        'G16_complete_canonical_5colorings':len(models),'G16_enum_nodes':nodes,
        'G16_terminals_forced_equal_in_5colors':True,
        'G31_vertices':31,'G31_unit_edges':len(u31),'G31_phi_edges':len(p31),
        'G31_5colorings':len(five),'G31_5color_refutation_nodes':n5,
        'G31_6coloring_validated':True,'G31_chromatic_number':6,
        'G31_unit_only_chromatic_number':3,'G31_unit_only_odd_cycle':cycle,
        'unit_distance_A':False,'all_pairs_exact_checked':True,
        'G16_sha256':g16['semantic_pts_edges_sha256'],'G31_sha256':g31['semantic_pts_edges_sha256'],
        'scope':'Known two-distance result reproduced, not a new HN bound; phi edges are unresolved virtual constraints.'}
    (out/'PARTS_SUMMARY.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report,indent=2))

if __name__=='__main__': main()
