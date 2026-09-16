#!/usr/bin/env python3
"""Independent induced-geometry audit: SymPy polynomial arithmetic, new primes.

Does not import hn_cyclotomic210. Residue screens use 631 and 1051, rather
than the construction's 211 and 421. All surviving differences are evaluated
exactly modulo the independently generated cyclotomic polynomial Phi_210.
"""
from __future__ import annotations
import argparse,gzip,hashlib,json,math,time
from functools import lru_cache
from pathlib import Path
import numpy as np
import sympy as sp
from sympy.polys.rings import ring
from sympy.polys.domains import QQ

R,z=ring('z',QQ); phi=R.from_expr(sp.cyclotomic_poly(210,sp.Symbol('z')))
powers=[(z**i)%phi for i in range(210)]
PRIMES=(631,1051)

def normalize(coeffs,den):
    if type(den)!=int or den<=0 or len(coeffs)!=48 or any(type(c)!=int for c in coeffs):raise ValueError('invalid algebraic coordinate')
    d=den
    for c in coeffs:d=math.gcd(d,c)
    return tuple(c//d for c in coeffs),den//d

@lru_cache(maxsize=300000)
def norm(coeffs,den):
    f=R.from_dict({(i,):QQ(c,den) for i,c in enumerate(coeffs) if c})
    bar=R.zero
    for i,c in enumerate(coeffs):
        if c:bar+=powers[(-i)%210]*QQ(c,den)
    return (f*bar)%phi

def audit(g):
    start=time.monotonic();pts=[normalize(p['coeffs'],p['den']) for p in g['pts']]
    if len(set(pts))!=len(pts):raise ValueError('coincident points')
    n=len(pts);edges=[tuple(e) for e in g['edges']]
    if edges!=sorted(set(edges)) or any(not 0<=a<b<n for a,b in edges):raise ValueError('noncanonical edges')
    targets=set(edges);found=set();red=[]
    for p in PRIMES:
        if not sp.isprime(p):raise AssertionError('not prime')
        root=next(r for r in range(2,p) if pow(r,210,p)==1 and all(pow(r,210//q,p)!=1 for q in (2,3,5,7)))
        if sum(int(c)*pow(root,m[0],p) for m,c in phi.items())%p:raise AssertionError('bad field map')
        forward=[pow(root,i,p) for i in range(48)];backward=[pow(root,-i,p) for i in range(48)]
        vals=[]
        for coeffs,den in pts:
            inv=pow(den,-1,p)
            vals.append((sum(a*b for a,b in zip(coeffs,forward))*inv%p,sum(a*b for a,b in zip(coeffs,backward))*inv%p))
        red.append(np.asarray(vals,dtype=np.int64))
    survivors=0
    for a in range(n-1):
        js=np.arange(a+1,n)
        for p,t in zip(PRIMES,red):js=js[((t[js,0]-t[a,0])*(t[js,1]-t[a,1]))%p==1]
        x,d=pts[a]
        for b0 in js:
            b=int(b0);y,e=pts[b];survivors+=1
            coeffs,den=normalize([xx*e-yy*d for xx,yy in zip(x,y)],d*e)
            if norm(coeffs,den)==R.one:found.add((a,b))
    if found!=targets:raise ValueError(f'edge mismatch: omitted={len(found-targets)}, nonunit={len(targets-found)}')
    return {'status':'PASS','vertices':n,'unit_edges':len(found),
      'all_unordered_pairs':n*(n-1)//2,'exact_filter_survivors':survivors,
      'filter_primes':list(PRIMES),'independent_polynomial':'sympy.cyclotomic_poly(210)',
      'arithmetic':'SymPy QQ polynomial remainder; no geometry-kernel imports',
      'point_distinctness_checked':True,'induced_completeness_checked':True,
      'seconds':round(time.monotonic()-start,3),'sympy_version':sp.__version__}

def read_graph(p):
    raw=gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes()
    return json.loads(raw),hashlib.sha256(raw).hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--graph',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();g,sha=read_graph(a.graph);r=audit(g);r['graph_file_sha256']=sha
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)
if __name__=='__main__':main()
