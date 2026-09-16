#!/usr/bin/env python3
"""Independent all-pairs geometry audit; no search arithmetic or SAT imports.

Uses SymPy's integer polynomial ring, independently generates Phi210, and uses
prime filters distinct from construction. Exact positive color vectors are
validated against the complete original graph. Does not certify UNSAT traces.
"""
from __future__ import annotations
import argparse,gzip,hashlib,json
from pathlib import Path
from math import gcd,isqrt
import numpy as np
import sympy as s
from sympy.polys.rings import ring
from sympy.polys.domains import ZZ


def load(p):
    p=Path(p);raw=p.read_bytes();return json.loads(gzip.decompress(raw) if p.suffix=='.gz' else raw)

def digest(g):return hashlib.sha256(json.dumps({k:g[k] for k in ('pts','edges')},sort_keys=True,separators=(',',':')).encode()).hexdigest()

def audit(g,colorings=(),k=5):
    R,z=ring('z',ZZ);x=s.Symbol('x');cs=list(reversed([int(a) for a in s.Poly(s.cyclotomic_poly(210,x),x).all_coeffs()]));degree=len(cs)-1
    phi=sum((a*z**i for i,a in enumerate(cs)),R.zero)
    if degree!=48:raise ValueError('wrong degree')
    powers=[z**i%phi for i in range(210)]
    def unpack(q):
        v=q['coeffs'];d=q['den']
        if len(v)!=degree or type(d)!=int or d<=0 or any(type(a)!=int for a in v):raise ValueError('invalid coordinate')
        h=d
        for a in v:h=gcd(h,a)
        if h!=1:raise ValueError('noncanonical coordinate')
        return sum((a*z**i for i,a in enumerate(v)),R.zero),d
    points=[(unpack(p['a']),unpack(p['b'])) for p in g['pts']]
    if any(len(e)!=2 or any(type(v)!=int for v in e) or not 0<=e[0]<e[1]<len(points) for e in g['edges']):raise ValueError('invalid edge indexing')
    if len(set(points))!=len(points):raise ValueError('duplicate point')
    # All prime divisors ramifying in Q(zeta210) lie over 2,3,5,7. Since
    # Q(sqrt(-11)) ramifies at 11 it is not a subfield; (1,w) is independent.
    maps=[]
    for p in range(1051,20000,210):
        if any(p%q==0 for q in range(2,isqrt(p)+1)):continue
        w=next((i for i in range(1,p) if i*i%p==(-11)%p),None)
        if w is None:continue
        r=next(i for i in range(2,p) if pow(i,210,p)==1 and all(pow(i,210//q,p)!=1 for q in (2,3,5,7)))
        if sum(a*pow(r,j,p) for j,a in enumerate(cs))%p:raise ValueError('bad independent filter')
        maps.append((p,w,r))
        if len(maps)==2:break
    def red(q,p,r):
        poly,d=q
        return sum(int(a)*pow(r,m[0],p) for m,a in poly.items())*pow(d,-1,p)%p
    residues=np.array([[( (red(a,p,r)+w*red(b,p,r))%p,(red(a,p,pow(r,-1,p))-w*red(b,p,pow(r,-1,p)))%p) for p,w,r in maps] for a,b in points],dtype=np.int64)
    def minus(a,b):
        v,d=a;u,e=b
        return (v*e-u*d),d*e
    def bar(q):return sum((a*powers[-m[0]%210] for m,a in q.items()),R.zero)%phi
    cache={}
    def isunit(i,j):
        (a,da),(b,db)=points[i];(c,dc),(d,dd)=points[j]
        aa,ad=minus((a,da),(c,dc));bb,bd=minus((b,db),(d,dd))
        aa*=bd;bb*=ad;den=ad*bd
        key=(aa,bb,den)
        if key not in cache:
            abar,bbar=bar(aa),bar(bb)
            cache[key]=((aa*abar+11*bb*bbar-den*den)%phi==R.zero and (bb*abar-aa*bbar)%phi==R.zero)
        return cache[key]
    edges=[];survivors=0
    for i in range(len(points)-1):
        js=np.arange(i+1,len(points))
        for t,(p,_,_) in enumerate(maps):
            js=js[((residues[js,t,0]-residues[i,t,0])*(residues[js,t,1]-residues[i,t,1]))%p==1]
        for j in js:
            survivors+=1
            if isunit(i,int(j)):edges.append([i,int(j)])
    if edges!=g['edges']:raise ValueError('saved edges are not exact induced unit-distance graph')
    for c in colorings:
        if len(c)!=len(points) or any(type(a)!=int or not 0<=a<k for a in c):raise ValueError('invalid coloring')
        if any(c[u]==c[v] for u,v in edges):raise ValueError('invalid coloring edge')
    return {'status':'PASS','graph_sha256':digest(g),'vertices':len(points),'edges':len(edges),'all_pairs':len(points)*(len(points)-1)//2,'survivors':survivors,'separate_filter_primes':[p for p,*_ in maps],'models_checked':len(colorings),'search_arithmetic_imported':False,'SAT_imported':False,'float_geometry':False}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);args=ap.parse_args()
    r=load(args.run/'SUMMARY.json');g=load(args.run/'CURRENT.json.gz')
    models=r['current_colorings'];k=r['k']
    if r['discovery'] and r['discovery'].get('k_plus_one_model'):
        models=[r['discovery']['k_plus_one_model']];k+=1
    result=audit(g,models,k)
    if result['graph_sha256']!=r['current_graph_sha256']:raise ValueError('wrong summary hash')
    (args.run/'INDEPENDENT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
