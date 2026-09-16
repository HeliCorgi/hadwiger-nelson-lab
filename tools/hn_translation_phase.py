#!/usr/bin/env python3
"""Positive-only cyclic copy gluing. Its UNSAT is NEVER an original-graph claim."""
from itertools import combinations

class NoPhaseModel(ValueError):
    pass

class DSU:
    """pot[x] is color(x)-color(parent[x]) modulo k."""
    def __init__(self,n,k=5):
        self.p=list(range(n));self.pot=[0]*n;self.k=k
    def find(self,x):
        cur=x;total=0;path=[]
        while self.p[cur]!=cur:
            path.append((cur,total));total+=self.pot[cur];cur=self.p[cur]
        for v,before in path:
            self.p[v]=cur;self.pot[v]=(total-before)%self.k
        return cur,total%self.k
    def merge(self,a,b,d):
        ra,wa=self.find(a);rb,wb=self.find(b)
        if ra==rb:
            if (wa-wb-d)%self.k:raise NoPhaseModel('inconsistent overlap equations')
        else:
            self.p[ra]=rb;self.pot[ra]=(d-wa+wb)%self.k

def encode(n,edges,copies,phases,k=5):
    """Impose C(copy_t[i])=X_i+phases[t]. Return CNF and lifting recipe."""
    if not copies or len(copies)!=len(phases):raise ValueError('bad copies/phases')
    size=len(copies[0]);d=DSU(size,k);seen={}
    for cp,phase in zip(copies,phases):
        if len(cp)!=size or len(set(cp))!=size:raise ValueError('copy is not injective')
        for i,v in enumerate(cp):
            if not 0<=v<n:raise ValueError('bad vertex index')
            if v in seen:
                j,old=seen[v];d.merge(i,j,old-phase)
            else:seen[v]=(i,phase)
    if set(seen)!=set(range(n)):raise ValueError('copies do not cover graph')
    root_ids={};recipe=[]
    for v in range(n):
        i,phase=seen[v];root,w=d.find(i)
        if root not in root_ids:root_ids[root]=len(root_ids)
        recipe.append((root_ids[root],(w+phase)%k))
    var=lambda r,c:r*k+c+1
    clauses=[]
    for r in range(len(root_ids)):
        row=[var(r,c) for c in range(k)];clauses.append(row)
        clauses.extend([[-a,-b] for a,b in combinations(row,2)])
    constraints=set()
    for a,b in edges:
        if not 0<=a<b<n:raise ValueError('bad original edge')
        ra,wa=recipe[a];rb,wb=recipe[b]
        if ra==rb:
            if wa==wb:raise NoPhaseModel('phase identification collapses an edge')
            continue
        if ra>rb:ra,rb,wa,wb=rb,ra,wb,wa
        constraints.add((ra,rb,(wa-wb)%k))
    for ra,rb,delta in sorted(constraints):
        clauses.extend([[-var(ra,c),-var(rb,(c+delta)%k)] for c in range(k)])
    if root_ids:clauses.append([var(0,0)]) # global cyclic color shift only
    return clauses,recipe,len(root_ids)

def lift(model,recipe,roots,k=5):
    positive={x for x in model if x>0};colors=[]
    for r in range(roots):
        row=[c for c in range(k) if r*k+c+1 in positive]
        if len(row)!=1:raise ValueError('model is not one-hot')
        colors.append(row[0])
    return [(colors[r]+w)%k for r,w in recipe]
