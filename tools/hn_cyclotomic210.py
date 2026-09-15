#!/usr/bin/env python3
"""Exact complex arithmetic in Q(zeta210); no floating-point geometry.

Necessary residue filters evaluate Phi210 at primitive 210th roots in F211
and F421. BOTH zeta and its inverse are evaluated: conjugation must not be
silently replaced by the identity. Noninvertible denominators are rejected.
"""
from __future__ import annotations
from math import gcd
from dataclasses import dataclass

D = 48
PHI = (1,-1,1,0,0,1,-1,2,-1,1,0,0,1,-1,1,-1,1,-1,0,0,-1,0,-1,0,-1,
       0,-1,0,-1,0,0,-1,1,-1,1,-1,1,0,0,1,-1,2,-1,1,0,0,1,-1,1)
TAIL = tuple((j,a) for j,a in enumerate(PHI[:-1]) if a)
ZERO = (0,) * D

def reduce_poly(coeffs):
    v = list(coeffs) + [0] * max(0, D-len(coeffs))
    for i in range(len(v)-1, D-1, -1):
        c = v[i]
        if c:
            for j,a in TAIL:
                v[i-D+j] -= c*a
    return tuple(v[:D])

POW = tuple(reduce_poly([0]*i+[1]) for i in range(210))

def multiply(a,b):
    v = [0]*(2*D-1)
    aa = [(i,x) for i,x in enumerate(a) if x]
    bb = [(j,y) for j,y in enumerate(b) if y]
    for i,x in aa:
        for j,y in bb:
            v[i+j] += x*y
    return reduce_poly(v)

@dataclass(frozen=True, slots=True)
class C:
    coeffs: tuple[int,...] = ZERO
    den: int = 1
    def __post_init__(self):
        if self.den == 0 or len(self.coeffs) != D:
            raise ValueError('invalid cyclotomic element')
        g = abs(self.den)
        for x in self.coeffs:
            if not isinstance(x,int): raise TypeError('integer coefficients required')
            g = gcd(g,x)
        if self.den < 0: g = -g
        object.__setattr__(self,'coeffs',tuple(x//g for x in self.coeffs))
        object.__setattr__(self,'den',self.den//g)
    def __add__(self,o):
        g = gcd(self.den,o.den); a = o.den//g; b = self.den//g
        return C(tuple(a*x+b*y for x,y in zip(self.coeffs,o.coeffs)),self.den*a)
    def __neg__(self): return C(tuple(-x for x in self.coeffs),self.den)
    def __sub__(self,o): return self+-o
    def __mul__(self,o): return C(multiply(self.coeffs,o.coeffs),self.den*o.den)
    def conjugate(self):
        v=[0]*D
        for i,x in enumerate(self.coeffs):
            if x:
                for j,y in enumerate(POW[-i%210]):
                    v[j]+=x*y
        return C(tuple(v),self.den)
    def rotate(self,k):
        v=[0]*D
        for i,x in enumerate(self.coeffs):
            if x:
                for j,y in enumerate(POW[(i+k)%210]):
                    v[j]+=x*y
        return C(tuple(v),self.den)
    def pack(self): return {'coeffs':list(self.coeffs),'den':self.den}
    def key(self): return self.den,self.coeffs
    @classmethod
    def unpack(cls,d): return cls(tuple(d['coeffs']),d['den'])

ONE=C(POW[0]); ORIGIN=C()
def zp(k): return C(POW[k%210])
SQRT5=ONE+(zp(42)+zp(-42)) * C(tuple([2]+[0]*(D-1)))
U=zp(21)
GOLD=U+U.conjugate()

def unit(z): return z*z.conjugate()==ONE

def from_heptagon(p):
    """Embed (a(zeta42)+b(zeta42)*sqrt5)/den, zeta42=zeta210^5."""
    a=[0]*D; b=[0]*D
    if len(p['a'])!=12 or len(p['b'])!=12: raise ValueError('expected degree-24 input')
    for i,(aa,bb) in enumerate(zip(p['a'],p['b'])):
        for j,x in enumerate(POW[5*i]):
            a[j]+=aa*x; b[j]+=bb*x
    return C(tuple(a),p['den'])+C(tuple(b),p['den'])*SQRT5

def maps():
    out=[]
    for p in (211,421):
        r=next(r for r in range(2,p) if pow(r,210,p)==1 and
               all(pow(r,210//q,p)!=1 for q in (2,3,5,7)))
        assert sum(a*pow(r,j,p) for j,a in enumerate(PHI))%p==0
        out.append((p,tuple(pow(r,j,p) for j in range(D)),
                    tuple(pow(r,-j,p) for j in range(D))))
    return tuple(out)
MAPS=maps()

def residues(z):
    out=[]
    for p,forward,backward in MAPS:
        inv=pow(z.den,-1,p)
        out.append((sum(x*y for x,y in zip(z.coeffs,forward))*inv%p,
                    sum(x*y for x,y in zip(z.coeffs,backward))*inv%p))
    return out

def complete(points):
    """All pairs: vectorized int64 necessary filters, exact integer survivors.

    Modular residues are 0..420; multiplying differences is <421^2, so the
    NumPy int64 operations cannot overflow. No edge can fail a necessary filter.
    """
    import numpy as np
    if len(set(points))!=len(points): raise ValueError('duplicate vertices')
    red=np.asarray([residues(x) for x in points],dtype=np.int64)
    edges=[]; survivors=0
    for i in range(len(points)-1):
        js=np.arange(i+1,len(points))
        for k,(p,_,_) in enumerate(MAPS):
            ok=((red[js,k,0]-red[i,k,0])*(red[js,k,1]-red[i,k,1]))%p==1
            js=js[ok]
        for j0 in js:
            j=int(j0); survivors+=1
            if unit(points[i]-points[j]): edges.append([i,j])
    return edges, {'all_unordered_pairs':len(points)*(len(points)-1)//2,
          'necessary_filter_survivors':survivors,'unit_edges':len(edges),
          'filter_primes':[x[0] for x in MAPS],'induced_complete':True,
          'float_used':False,'int64_filter_product_abs_bound':421**2,
          'exact_survivor_arithmetic':'unbounded Python integers'}

def selftest():
    assert len(PHI)==D+1 and reduce_poly(PHI)==ZERO
    assert zp(210)==ONE and zp(105)==-ONE
    assert SQRT5*SQRT5==C(tuple([5]+[0]*(D-1)))
    assert GOLD*GOLD==GOLD+ONE
    assert unit(U) and unit(GOLD-U) and GOLD==U+U.conjugate()
    assert all(unit(zp(i)) for i in range(210))
    for z in (U,GOLD,SQRT5,zp(5),zp(21)+zp(5)):
        assert z.conjugate().conjugate()==z
        for (a,b),(aa,bb) in zip(residues(z),residues(z.conjugate())):
            assert (a,b)==(bb,aa)
    v=ORIGIN
    for i,c in enumerate((1,1,0,-1,-1,0,1,0,-1,-1,0,1,1)):
        if c: v=v+C(tuple(c*x for x in POW[5*i]))
    assert v==ORIGIN
    rh=[ORIGIN,U,GOLD,U.conjugate()]
    ee,audit=complete(rh)
    assert ee==[[0,1],[0,3],[1,2],[2,3]]
    assert audit['all_unordered_pairs']==6
    return {'status':'PASS','degree':D,'field':'Q(zeta210)',
            'identities':'Phi210, Phi42 embedding, sqrt5, phi, conjugation, all roots unit, rhombus'}

if __name__=='__main__':
    import json
    print(json.dumps(selftest()))
