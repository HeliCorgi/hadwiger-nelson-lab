#!/usr/bin/env python3
"""Positive-only affine copy restrictions; no negative HN conclusion is valid here."""
from __future__ import annotations
from itertools import combinations

class NoAffineModel(ValueError):
    """The extra template restriction is inconsistent, not the original graph."""

class AffineDSU:
    def __init__(self, n: int, k: int = 5):
        self.k=k; self.parent=list(range(n)); self.scale=[1]*n; self.shift=[0]*n
        self.dom=[set(range(k)) for _ in range(n)]
    def find(self, x):
        path=[]; cur=x
        while self.parent[cur]!=cur:
            path.append(cur); cur=self.parent[cur]
        a,b=1,0
        for v in reversed(path):
            a,b=self.scale[v]*a%self.k,(self.scale[v]*b+self.shift[v])%self.k
            self.parent[v]=cur; self.scale[v]=a; self.shift[v]=b
        return cur,a,b
    def restrict(self,x,values):
        r,a,b=self.find(x); self.dom[r]&={v for v in range(self.k) if (a*v+b)%self.k in values}
        if not self.dom[r]:raise NoAffineModel('empty root domain')
    def merge(self,x,y,a,b):
        """Enforce X[x] = a*X[y]+b modulo k."""
        k=self.k; rx,sx,tx=self.find(x); ry,sy,ty=self.find(y)
        if rx==ry:
            coeff=(sx-a*sy)%k; rhs=(a*ty+b-tx)%k
            self.dom[rx]&={v for v in range(k) if coeff*v%k==rhs}
            if not self.dom[rx]:raise NoAffineModel('inconsistent affine overlap')
        else:
            aa=a*sy*pow(sx,-1,k)%k; bb=(a*ty+b-tx)*pow(sx,-1,k)%k
            self.dom[ry]&={v for v in range(k) if (aa*v+bb)%k in self.dom[rx]}
            if not self.dom[ry]:raise NoAffineModel('inconsistent merged domains')
            self.parent[rx]=ry; self.scale[rx]=aa; self.shift[rx]=bb

def encode(n,edges,copies,slopes,offsets,k=5,source_pins=()):
    if not copies or len(copies)!=len(slopes) or len(copies)!=len(offsets):raise ValueError('bad copies')
    if any(type(a)!=int or not 0<a<k for a in slopes):raise ValueError('bad slopes')
    if any(type(b)!=int or not 0<=b<k for b in offsets):raise ValueError('bad offsets')
    size=len(copies[0]); d=AffineDSU(size,k); seen={}
    for cp,a,b in zip(copies,slopes,offsets):
        if len(cp)!=size or len(set(cp))!=size:raise ValueError('noninjective copy')
        for i,v in enumerate(cp):
            if type(v)!=int or not 0<=v<n:raise ValueError('bad vertex')
            if v in seen:
                j,s,t=seen[v]; d.merge(i,j,s*pow(a,-1,k)%k,(t-b)*pow(a,-1,k)%k)
            else: seen[v]=(i,a,b)
    if len(seen)!=n:raise ValueError('copies do not cover graph')
    for i,c in source_pins:d.restrict(i,{c})
    roots={}; recipe=[]
    for v in range(n):
        i,a,b=seen[v];r,s,t=d.find(i)
        if r not in roots:roots[r]=len(roots)
        recipe.append((roots[r],a*s%k,(a*t+b)%k))
    var=lambda r,c:r*k+c+1
    clauses=[]
    for r,idx in roots.items():
        row=[var(idx,c) for c in range(k)];clauses.append(row)
        clauses.extend([[-a,-b] for a,b in combinations(row,2)])
        clauses.extend([[-var(idx,c)] for c in range(k) if c not in d.dom[r]])
    constraints=set(); units=set()
    for u,v in edges:
        if not 0<=u<v<n:raise ValueError('bad edge')
        ra,sa,ta=recipe[u]; rb,sb,tb=recipe[v]
        if ra==rb:
            bad=[c for c in range(k) if (sa*c+ta-sb*c-tb)%k==0]
            if len(bad)==k:raise NoAffineModel('edge collapsed by affine restriction')
            units.update(-var(ra,c) for c in bad); continue
        if ra>rb:ra,rb,sa,sb,ta,tb=rb,ra,sb,sa,tb,ta
        constraints.add((ra,rb,sa*pow(sb,-1,k)%k,(ta-tb)*pow(sb,-1,k)%k))
    clauses.extend([[v] for v in sorted(units)])
    for ra,rb,a,b in sorted(constraints):
        clauses.extend([[-var(ra,c),-var(rb,(a*c+b)%k)] for c in range(k)])
    return clauses,recipe,len(roots)

def lift(model,recipe,roots,k=5):
    pos={v for v in model if v>0};xs=[]
    for r in range(roots):
        row=[c for c in range(k) if r*k+c+1 in pos]
        if len(row)!=1:raise ValueError('not one-hot')
        xs.append(row[0])
    return [(a*xs[r]+b)%k for r,a,b in recipe]

def rhombus_templates(case,t):
    if case not in ('u','fork') or t not in range(1,5):raise ValueError('bad case/t')
    slope=[1,t,4,(-t)%5];offset=[0,1,(1+t)%5,t]
    shifts=[0,1] if case=='u' else [0,1,t]
    return slope*len(shifts),[(b+c)%5 for c in shifts for b in offset]
