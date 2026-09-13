#!/usr/bin/env python3
"""Rebuild Cycle 4/6 from the pinned Cycle-3 exact graph, add the entire
Cycle-7 top-200 exact candidate pool, and decide ordinary 5-colorability.

Float arithmetic proposes/filters possible unit incidences only. Every retained
point and every saved edge is checked exactly in K2. No C88/quotient/palette or
color-equality assumption is used.
"""
from __future__ import annotations
import argparse, hashlib, itertools, json, math, time
from collections import defaultdict, Counter
from pathlib import Path
import numpy as np
import sympy as sp
from scipy.spatial import cKDTree
from pysat.solvers import Cadical195, Glucose4
from hn_exact import K2, Z0, unit_modulus

SCALE=1e7
_INV={}
def pack(z): return {'a':z.a,'b':z.b,'den':z.den}
def inverse(x):
    if x in _INV: return _INV[x]
    basis=[]
    for j in range(16):
        a=[0]*8; b=[0]*8; (a if j<8 else b)[j%8]=1; basis.append(K2(a,b))
    cols=[]
    for q in basis:
        p=x*q; cols.append([sp.Rational(v,p.den) for v in p.a+p.b])
    vals=sp.Matrix(16,16,lambda i,j:cols[j][i]).inv()[:,0]
    den=math.lcm(*(int(v.q) for v in vals)); ints=[int(v*den) for v in vals]
    r=K2(ints[:8],ints[8:],den); assert (r*x).is_one(); _INV[x]=r; return r
def circumcenter(a,b,c):
    u=b-a; v=c-a; det=u.conj()*v-v.conj()*u
    if det==K2(Z0): return None
    return a+(u*u.conj()*v-v*v.conj()*u)*inverse(det)
def xy_of(pts): return np.array([[p.emb().real,p.emb().imag] for p in pts],dtype=np.float64)

def simple_proposals(pts,min_contacts):
    xy=xy_of(pts); clusters=defaultdict(set); n=len(pts)
    for i in range(n):
        d=xy[i+1:]-xy[i]; r2=np.einsum('ij,ij->i',d,d)
        for jj in np.where((r2>1e-12)&(r2<=4+1e-10))[0]:
            j=i+1+int(jj); r=float(r2[jj]); mid=(xy[i]+xy[j])/2
            arm=math.sqrt(max(0.,1/r-.25))*np.array([-d[jj,1],d[jj,0]])
            for pos in (mid+arm,mid-arm):
                clusters[tuple(int(round(float(t)*SCALE)) for t in pos)].update((i,j))
    prop=sorted(((k,sorted(s)) for k,s in clusters.items() if len(s)>=min_contacts),
                key=lambda x:(-len(x[1]),x[0]))
    return xy,prop

def closure_round(pts,min_contacts,expected_new):
    xy,prop=simple_proposals(pts,min_contacts); known=set(pts); additions=[]
    for key,ns in prop:
        point=None
        for i,j,k in itertools.combinations(ns,3):
            a,b,c=xy[[i,j,k]]
            if abs(np.linalg.det(np.array([b-a,c-a])))<1e-9: continue
            point=circumcenter(pts[i],pts[j],pts[k]); break
        if point is None or point in known: continue
        if not all(unit_modulus(point-pts[v]) for v in ns): continue
        known.add(point); additions.append(point)
    assert len(additions)==expected_new,(len(additions),expected_new)
    return pts+additions, {'float_proposals':len(prop),'new_exact_points':len(additions)}

def pack_xy(q):
    ux=(q[:,0]&0xFFFFFFFF).astype(np.uint64); uy=(q[:,1]&0xFFFFFFFF).astype(np.uint64)
    return (ux<<np.uint64(32))|uy
def unpack_key(k):
    x=(k>>32)&0xFFFFFFFF; y=k&0xFFFFFFFF
    if x>=1<<31:x-=1<<32
    if y>=1<<31:y-=1<<32
    return x/SCALE,y/SCALE
def circle_keys(xy,pairs):
    a=xy[pairs[:,0]]; b=xy[pairs[:,1]]; d=b-a; r2=np.einsum('ij,ij->i',d,d)
    good=(r2>1e-14)&(r2<=4.00000004); pairs=pairs[good]; a=a[good]; b=b[good]; d=d[good]; r2=r2[good]
    mid=(a+b)*.5; h=np.sqrt(np.maximum(0.,1/r2-.25)); arm=np.column_stack((-d[:,1],d[:,0]))*h[:,None]
    for pos in (mid+arm,mid-arm): yield pack_xy(np.rint(pos*SCALE).astype(np.int64)),pairs

def cycle7_candidates(base_pts,min_contacts=5):
    xy=xy_of(base_pts); tree=cKDTree(xy); pairs=tree.query_pairs(r=2.00000001,output_type='ndarray')
    chunks=[]; step=500000
    for s in range(0,len(pairs),step):
        for kk,_ in circle_keys(xy,pairs[s:s+step]): chunks.append(kk)
    keys=np.concatenate(chunks); keys.sort(); min_mult=min_contacts*(min_contacts-1)//2
    changes=np.r_[True,keys[1:]!=keys[:-1],True]; bd=np.flatnonzero(changes); counts=np.diff(bd); starts=bd[:-1]; keep=counts>=min_mult
    high=np.array(keys[starts[keep]],dtype=np.uint64); hc=np.array(counts[keep],dtype=np.int64)
    approx=np.array([unpack_key(int(k)) for k in high],dtype=np.float64); nearest,_=tree.query(approx,k=1,workers=-1); newish=nearest>=2e-6
    high=high[newish]; hc=hc[newish]; approx=approx[newish]
    order=np.argsort(high); sorted_high=high[order]; key_to_idx={int(k):i for i,k in enumerate(high.tolist())}; nsets=[set() for _ in range(len(high))]
    for s in range(0,len(pairs),step):
        p0=pairs[s:s+step]
        for kk,p in circle_keys(xy,p0):
            si=np.searchsorted(sorted_high,kk); rows0=np.flatnonzero(si<len(sorted_high))
            if not len(rows0): continue
            rows=rows0[sorted_high[si[rows0]]==kk[rows0]]
            for row in rows:
                idx=key_to_idx[int(kk[row])]; u,v=map(int,p[row]); nsets[idx].add(u); nsets[idx].add(v)
    prop=[]
    for i,s in enumerate(nsets):
        if len(s)>=min_contacts: prop.append({'key':int(high[i]),'mult':int(hc[i]),'xy':approx[i].tolist(),'ns':sorted(s)})
    prop.sort(key=lambda c:(-len(c['ns']),-c['mult'],c['key']))
    seen=set(); known=set(base_pts); exact=[]
    for c in prop:
        z=complex(c['xy'][0],c['xy'][1]); point=None; tried=0
        for i,j,k in itertools.combinations(c['ns'],3):
            a,b,d=xy[[i,j,k]]
            if abs(np.linalg.det(np.array([b-a,d-a])))<1e-9: continue
            q=circumcenter(base_pts[i],base_pts[j],base_pts[k]); tried+=1
            if q is not None and abs(q.emb()-z)<=2e-5: point=q; break
            if tried>=24: break
        if point is None or point in known or point in seen: continue
        ex=[v for v in c['ns'] if unit_modulus(point-base_pts[v])]
        if len(ex)<min_contacts: continue
        seen.add(point); exact.append(point)
    return exact, {'pairs_le_2':int(len(pairs)),'float_proposals':len(prop),'exact_candidates':len(exact)}

def induced_edges(pts):
    xy=xy_of(pts); edges=[]; approx_candidates=0
    for i in range(len(pts)):
        d=xy[i+1:]-xy[i]; r2=np.einsum('ij,ij->i',d,d); idx=np.where(np.abs(r2-1.0)<1e-7)[0]; approx_candidates+=len(idx)
        for jj in idx:
            j=i+1+int(jj)
            if unit_modulus(pts[i]-pts[j]): edges.append((i,j))
    assert len(edges)==approx_candidates, 'float filter admitted non-unit candidates; inspect tolerance'
    return edges

def cnf5(n,edges):
    clauses=[]
    for v in range(n):
        xs=[v*5+c+1 for c in range(5)]; clauses.append(xs)
        for a in range(5):
            for b in range(a+1,5): clauses.append([-xs[a],-xs[b]])
    for u,v in edges:
        for c in range(5): clauses.append([-(u*5+c+1),-(v*5+c+1)])
    clauses.append([1])
    return clauses
def model_colors(model,n):
    pos=set(x for x in model if x>0); return [next(c for c in range(5) if v*5+c+1 in pos) for v in range(n)]
def valid(colors,edges): return all(colors[u]!=colors[v] for u,v in edges)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--cycle3',type=Path,required=True); ap.add_argument('--out-dir',type=Path,required=True); args=ap.parse_args(); out=args.out_dir; out.mkdir(parents=True,exist_ok=True); t=time.time()
    d=json.loads(args.cycle3.read_text()); pts=[K2(p['a'],p['b'],p['den']) for p in d['pts']]; assert len(pts)==760 and len(d['edges'])==4280
    cycle4,m4=closure_round(pts,3,1752); assert len(cycle4)==2512
    cycle6,m6=closure_round(cycle4,3,6403); assert len(cycle6)==8915
    cands,mc=cycle7_candidates(cycle6,5); assert len(cands)==13556,(len(cands),13556)
    final_pts=cycle6+cands[:200]; edges=induced_edges(final_pts); base_edges=sum(u<8915 and v<8915 for u,v in edges)
    assert base_edges==78063,(base_edges,78063); assert len(edges)==81068,(len(edges),81068)
    rebuild={'cycle3_vertices':760,'cycle3_edges':4280,'cycle4_vertices':2512,'cycle4':m4,'cycle6_vertices':8915,'cycle6_edges':base_edges,'cycle6':m6,'cycle7_candidates':mc,'top200_vertices':len(final_pts),'top200_edges':len(edges),'all_edges_exact_unit':True,'elapsed_before_sat':round(time.time()-t,3)}
    (out/'REBUILD.json').write_text(json.dumps(rebuild,indent=2))
    graph={'pts':[pack(p) for p in final_pts],'edges':[list(e) for e in edges],'construction':'Cycle6 plus all top-200 Cycle7 exact candidates','no_conditional_constraints':True}
    (out/'GRAPH.json').write_text(json.dumps(graph,separators=(',',':')))
    clauses=cnf5(len(final_pts),edges); sat_started=time.time()
    with Cadical195(bootstrap_with=clauses) as s:
        ans=s.solve(); model=s.get_model() if ans else None
    verdict={'cadical195':'SAT' if ans else 'UNSAT','sat_seconds':round(time.time()-sat_started,3)}
    if ans:
        colors=model_colors(model,len(final_pts)); assert valid(colors,edges); (out/'COLORING.txt').write_text(''.join(map(str,colors))+'\n'); verdict.update({'classification':'D','proper_5_coloring_verified':True,'conclusion':'Entire top-200 Cycle7 candidate family remains 5-colorable.'})
    else:
        with Glucose4(bootstrap_with=clauses) as s: g=s.solve()
        verdict.update({'glucose4':'SAT' if g else 'UNSAT','classification':'A_CANDIDATE' if not g else 'C','conclusion':'UNSAT requires proof certificate and independent exact audit.'})
    verdict['graph_sha256']=hashlib.sha256((out/'GRAPH.json').read_bytes()).hexdigest(); verdict['vertices']=len(final_pts); verdict['edges']=len(edges); verdict['total_seconds']=round(time.time()-t,3)
    (out/'VERDICT.json').write_text(json.dumps(verdict,indent=2)); print(json.dumps({**rebuild,**verdict},indent=2),flush=True)
if __name__=='__main__':main()
