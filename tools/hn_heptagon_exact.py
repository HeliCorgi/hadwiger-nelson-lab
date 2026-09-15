#!/usr/bin/env python3
"""Exact Haugland 2608.04542v2 reconstruction in Q(zeta42,sqrt(5)).

Complex coordinates (a+b*sqrt(5))/den with 12-coefficient integral vectors.
No floating point is used. All unordered pairs are tested with necessary modular
norm filters followed by exact norm arithmetic. Filters cannot omit a unit edge:
the two evaluation maps respect Phi42 and sqrt(5)^2=5, and denominators are
checked invertible. Paper appendix path data have CC BY 4.0 attribution.
"""
from __future__ import annotations
import argparse, hashlib, json
from itertools import combinations
from math import gcd
from pathlib import Path
from time import monotonic

N=12
# Phi42 = X^12+X^11-X^9-X^8+X^6-X^4-X^3+X+1.
PHI=(1,1,0,-1,-1,0,1,0,-1,-1,0,1,1)
ZERO=(0,)*N

def reduce(v):
    v=list(v)+[0]*max(0,N-len(v))
    for d in range(len(v)-1,N-1,-1):
        c=v[d]
        if c:
            for j in range(N): v[d-N+j]-=c*PHI[j]
    return tuple(v[:N])

POW=[reduce([0]*j+[1]) for j in range(42)]

def mul(a,b):
    v=[0]*(2*N-1)
    for i,x in enumerate(a):
        if x:
            for j,y in enumerate(b):
                if y: v[i+j]+=x*y
    return reduce(v)

def conj(a):
    out=[0]*N
    for i,c in enumerate(a):
        if c:
            for j,v in enumerate(POW[-i%42]): out[j]+=c*v
    return tuple(out)

class E:
    __slots__=('a','b','den')
    def __init__(self,a=ZERO,b=ZERO,den=1):
        if den==0: raise ValueError('zero denominator')
        if isinstance(a,int): a=(a,)+(0,)*(N-1)
        if len(a)!=N or len(b)!=N: raise ValueError('wrong basis size')
        g=abs(den)
        for v in (*a,*b): g=gcd(g,v)
        if den<0: g=-g
        self.a=tuple(v//g for v in a); self.b=tuple(v//g for v in b); self.den=den//g
    def __hash__(self): return hash((self.a,self.b,self.den))
    def __eq__(self,o): return isinstance(o,E) and (self.a,self.b,self.den)==(o.a,o.b,o.den)
    def __add__(self,o):
        return E(tuple(x*o.den+y*self.den for x,y in zip(self.a,o.a)),
                 tuple(x*o.den+y*self.den for x,y in zip(self.b,o.b)),self.den*o.den)
    def __neg__(self): return E(tuple(-v for v in self.a),tuple(-v for v in self.b),self.den)
    def __sub__(self,o): return self+-o
    def __mul__(self,o):
        aa=mul(self.a,o.a); bb=mul(self.b,o.b)
        ab=mul(self.a,o.b); ba=mul(self.b,o.a)
        return E(tuple(x+5*y for x,y in zip(aa,bb)),tuple(x+y for x,y in zip(ab,ba)),self.den*o.den)
    def conjugate(self): return E(conj(self.a),conj(self.b),self.den)
    def pack(self): return {'a':list(self.a),'b':list(self.b),'den':self.den}
    def key(self): return self.den,self.a,self.b
    @classmethod
    def unpack(cls,p): return cls(p['a'],p['b'],p['den'])

ONE=E(1); ORIGIN=E(); SQM3=E(tuple(2*x-y for x,y in zip(POW[7],POW[0])))

def zp(j): return E(POW[j%42])

def unit(p): return p*p.conjugate()==ONE

def evaluation_setup(p):
    root=next(r for r in range(2,p) if pow(r,42,p)==1 and all(pow(r,42//q,p)!=1 for q in (2,3,7)))
    h=next(r for r in range(p) if r*r%p==5)
    if sum(c*pow(root,j,p) for j,c in enumerate(PHI))%p: raise AssertionError('bad map')
    return p,root,h

MAPS=[evaluation_setup(p) for p in (421,1009)]

def residues(x):
    out=[]
    for p,r,h in MAPS:
        inv=pow(x.den,-1,p)
        v=sum((a+h*b)*pow(r,i,p) for i,(a,b) in enumerate(zip(x.a,x.b)))*inv%p
        vc=sum((a+h*b)*pow(r,-i,p) for i,(a,b) in enumerate(zip(x.a,x.b)))*inv%p
        out.append((v,vc))
    return out

def complete(pts):
    red=[residues(x) for x in pts]; edges=[]; passed=0
    for i,j in combinations(range(len(pts)),2):
        if any((red[i][k][0]-red[j][k][0])*(red[i][k][1]-red[j][k][1])%p!=1
               for k,(p,_,_) in enumerate(MAPS)): continue
        passed+=1
        if unit(pts[i]-pts[j]): edges.append([i,j])
    return edges,{'all_unordered_pairs':len(pts)*(len(pts)-1)//2,
                  'passed_necessary_modular_filters':passed,'exact_unit_edges':len(edges),
                  'filter_primes':[x[0] for x in MAPS],'floating_point_used':False,
                  'induced_complete':True}

def directions():
    # u1 = Q0-R0, derived modulo Phi42 from Section 2 / Table 1.
    u1=E((2,1,3,0,-2,1,5,1,1,-6,-4,4),den=7)
    us=[v for j in range(42) for v in (zp(j),u1*zp(j))]
    assert len(set(us))==84 and all(unit(v) for v in us)
    assert all(us[(j+42)%84]==-us[j] for j in range(84))
    return us

def save(name,pts,expected,ports,out):
    pts=sorted(set(pts),key=E.key); assert len(pts)==expected[0],(name,len(pts))
    edges,info=complete(pts); assert len(edges)==expected[1],(name,len(edges))
    loc={p:i for i,p in enumerate(pts)}
    graph={'field':'Q(zeta42,sqrt5)','basis_degree':24,'cyclotomic_polynomial':list(PHI),
           'pts':[p.pack() for p in pts],'edges':edges,
           'ports':{k:loc[v] for k,v in ports.items()},'audit':info}
    semantic={'pts':graph['pts'],'edges':edges}
    info['semantic_pts_edges_sha256']=hashlib.sha256(json.dumps(semantic,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    (out/(name+'.json')).write_text(json.dumps(graph,separators=(',',':'))+'\n')
    print(json.dumps({'graph':name,'vertices':len(pts),**info}),flush=True)
    return pts,info

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--paths',type=Path,required=True); ap.add_argument('--out-dir',type=Path,required=True)
    a=ap.parse_args(); a.out_dir.mkdir(parents=True,exist_ok=True); started=monotonic()
    us=directions()
    h0=[E(v,den=7) for v in [
        (-2,-3,0,5,-1,0,-1,0,3,4,0,1),
        (-3,0,2,5,0,-4,0,3,6,0,-5,-1),
        (-5,-1,-1,5,2,-5,-5,2,5,6,-1,-5)]]
    hp=[zp(6*j)*p for p in h0 for j in range(7)]
    h,rh=save('H21',hp,(21,42),{},a.out_dir)
    he,_=complete(h)
    hd={h[i]-h[j] for i,j in he}|{h[j]-h[i] for i,j in he}
    assert hd==set(us)
    pts={ORIGIN}; count=0
    for line in a.paths.read_text().splitlines():
        if not line.strip() or line.startswith('#'): continue
        row=list(map(int,line.split())); assert len(row) in (5,6) and all(0<=i<84 for i in row)
        p=ORIGIN
        for i in row: p=p+us[i]; pts.add(p)
        assert p==SQM3,('bad path',count,row)
        count+=1
    assert count==231
    g1,r1=save('G1',pts,(740,3985),{'A':ORIGIN,'B':SQM3},a.out_dir)
    # x(u2)=cos(pi/21) has degree 6, not a divisor of the old field degree 8.
    assert zp(1) in pts
    g2pts=[zp(-7)*p-ONE for p in g1]+[zp(7)*p+ONE for p in g1]
    ports={'left':-ONE,'middle':ORIGIN,'right':ONE,'upper_left':zp(7)-ONE,'upper_right':zp(7)}
    g2,r2=save('G2',g2pts,(1066,6264),ports,a.out_dir)
    rotation=E(7,SQM3.a,8); assert unit(rotation)
    g3pts=g2+[rotation*(p+ONE)-ONE for p in g2]
    ports3={**ports,'rotated_right':rotation*(ONE+ONE)-ONE}
    g3,r3=save('G3',g3pts,(2131,12530),ports3,a.out_dir)
    report={'source':'https://arxiv.org/html/2608.04542v2','path_rows':count,
            'path_data_sha256':hashlib.sha256(a.paths.read_bytes()).hexdigest(),
            'unit_directions':len(us),'graphs':{'H21':rh,'G1':r1,'G2':r2,'G3':r3},
            'old_field_escape':{'actual_point':'u2=zeta42 in G1',
                'x_minpoly_ascending':[1,16,32,-48,-96,32,64],
                'degree':6,'reason':'6 does not divide the old real field degree 8'},
            'claim':'Exact reproduction of known geometry only; chromatic tests are separate.',
            'elapsed_seconds':round(monotonic()-started,3)}
    (a.out_dir/'GEOMETRY.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__': main()
