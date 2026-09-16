"""Exact geometry for bounded counterexample-guided unit-distance experiments.

K = Q(zeta210), L = K(sqrt(-11)). 11 is a new ramified prime, so sqrt(-11)
is not in K. Coordinates are (a + b*w), w^2=-11, bar(w)=-w.
All claimed unit edges use exact integer polynomial arithmetic; residue tests
are necessary filters only. No floating point geometry or tolerance is used.
"""
from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache
from math import gcd, isqrt

D=48
PHI=(1,-1,1,0,0,1,-1,2,-1,1,0,0,1,-1,1,-1,1,-1,0,0,-1,0,-1,0,-1,0,-1,0,-1,0,0,-1,1,-1,1,-1,1,0,0,1,-1,2,-1,1,0,0,1,-1,1)
TAIL=tuple((i,v) for i,v in enumerate(PHI[:-1]) if v)

def reduce_poly(v):
    v=list(v)+[0]*max(0,D-len(v))
    for i in range(len(v)-1,D-1,-1):
        if v[i]:
            a=v[i]
            for j,b in TAIL:v[i-D+j]-=a*b
    return tuple(v[:D])
POW=tuple(reduce_poly([0]*i+[1]) for i in range(210))

@dataclass(frozen=True)
class K:
    v: tuple[int,...]=(0,)*D
    den: int=1
    def __post_init__(self):
        if len(self.v)!=D or type(self.den)!=int or self.den==0 or any(type(x)!=int for x in self.v):
            raise ValueError('invalid exact field element')
        g=abs(self.den)
        for x in self.v:g=gcd(g,x)
        if self.den<0:g=-g
        object.__setattr__(self,'v',tuple(x//g for x in self.v));object.__setattr__(self,'den',self.den//g)
    def __add__(self,o):return K(tuple(a*o.den+b*self.den for a,b in zip(self.v,o.v)),self.den*o.den)
    def __neg__(self):return K(tuple(-a for a in self.v),self.den)
    def __sub__(self,o):return self+-o
    def __mul__(self,o):
        v=[0]*(2*D-1)
        for i,a in enumerate(self.v):
            if a:
                for j,b in enumerate(o.v):
                    if b:v[i+j]+=a*b
        return K(reduce_poly(v),self.den*o.den)
    def conjugate(self):
        v=[0]*D
        for i,a in enumerate(self.v):
            if a:
                for j,b in enumerate(POW[-i%210]):v[j]+=a*b
        return K(tuple(v),self.den)
    def pack(self):return {'coeffs':list(self.v),'den':self.den}
    @classmethod
    def unpack(cls,v):return cls(tuple(v['coeffs']),v['den'])

def rational(n,d=1):return K((n,)+(0,)*(D-1),d)
def root(k):return K(POW[k%210])
ZERO=K();ONE=rational(1);RAD=rational(11)
SQRT5=ONE+rational(2)*(root(42)+root(-42))

@dataclass(frozen=True)
class P:
    a: K=ZERO
    b: K=ZERO
    def __add__(self,o):return P(self.a+o.a,self.b+o.b)
    def __neg__(self):return P(-self.a,-self.b)
    def __sub__(self,o):return self+-o
    def __mul__(self,o):return P(self.a*o.a-RAD*self.b*o.b,self.a*o.b+self.b*o.a)
    def conjugate(self):return P(self.a.conjugate(),-self.b.conjugate())
    def pack(self):return {'a':self.a.pack(),'b':self.b.pack()}
    @classmethod
    def unpack(cls,p):return cls(K.unpack(p['a']),K.unpack(p['b']))
    def key(self):return self.a.den,self.a.v,self.b.den,self.b.v

ORIGIN=P();UNIT=P(ONE);ESCAPE=P(rational(5,6),rational(1,6))

@lru_cache(maxsize=200000)
def unit(z):
    return z*z.conjugate()==UNIT

def heptagon(p):
    if len(p['a'])!=12 or len(p['b'])!=12:raise ValueError('bad source basis')
    aa=[0]*D;bb=[0]*D
    for i,(a,b) in enumerate(zip(p['a'],p['b'])):
        for j,c in enumerate(POW[5*i]):aa[j]+=a*c;bb[j]+=b*c
    return P(K(tuple(aa),p['den'])+K(tuple(bb),p['den'])*SQRT5)

def _prime(n):
    return n>=2 and all(n%d for d in range(2,isqrt(n)+1))

@lru_cache(maxsize=1)
def maps():
    found=[]
    for p in range(211,30000,210):
        if not _prime(p):continue
        w=next((i for i in range(1,p) if i*i%p==(-11)%p),None)
        if w is None:continue
        r=next(r for r in range(2,p) if pow(r,210,p)==1 and all(pow(r,210//q,p)!=1 for q in (2,3,5,7)))
        if sum(a*pow(r,j,p) for j,a in enumerate(PHI))%p:raise ValueError('bad residue root')
        found.append((p,w,tuple(pow(r,j,p) for j in range(D)),tuple(pow(r,-j,p) for j in range(D))))
        if len(found)==2:return tuple(found)
    raise RuntimeError('no filter primes')

def residues(z):
    ans=[]
    for p,w,f,b in maps():
        ia=pow(z.a.den,-1,p);ib=pow(z.b.den,-1,p)
        af=sum(x*y for x,y in zip(z.a.v,f))*ia;ab=sum(x*y for x,y in zip(z.a.v,b))*ia
        bf=sum(x*y for x,y in zip(z.b.v,f))*ib;bb=sum(x*y for x,y in zip(z.b.v,b))*ib
        ans.append(((af+w*bf)%p,(ab-w*bb)%p))
    return ans

def complete(points):
    import numpy as np
    if len(set(points))!=len(points):raise ValueError('duplicate points')
    red=np.array([residues(p) for p in points],dtype=np.int64);edges=[];survivors=0
    for i in range(len(points)-1):
        js=np.arange(i+1,len(points))
        for k,(p,_,_,_) in enumerate(maps()):
            js=js[((red[js,k,0]-red[i,k,0])*(red[js,k,1]-red[i,k,1]))%p==1]
        for j in js:
            j=int(j);survivors+=1
            if unit(points[j]-points[i]):edges.append([i,j])
    return edges,{'all_pairs':len(points)*(len(points)-1)//2,'survivors':survivors,
                  'filter_primes':[p for p,*_ in maps()],'exact_survivors':True,'float_geometry':False}
