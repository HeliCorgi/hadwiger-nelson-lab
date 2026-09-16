#!/usr/bin/env python3
"""Independent exact geometry and saved-witness verification.

Uses SymPy's independently generated Phi_210, integer polynomial arithmetic,
and all-pairs necessary modular filters; never imports the synthesis arithmetic
or any SAT solver. Input is an extracted candidate artifact directory. No
UNSAT claim is accepted by this verifier. Rerunning a DRAT proof needs drat-trim.
"""
from __future__ import annotations
import argparse,gzip,hashlib,json
from functools import lru_cache
from math import gcd
from pathlib import Path
from time import monotonic


def verify(directory: Path, five_bundle: Path | None = None) -> dict:
    import numpy as np
    import sympy as sp
    from sympy.polys.rings import ring
    from sympy.polys.domains import ZZ
    started=monotonic();path=directory/'GRAPH.json';raw=path.read_bytes();g=json.loads(raw)
    R,z=ring('z',ZZ);poly=R.from_expr(sp.cyclotomic_poly(210,sp.Symbol('z')))
    assert poly.degree()==48 and (z**210)%poly==1
    conjugates=[z**((-i)%210)%poly for i in range(48)]
    pts=[]
    for p in g['pts']:
        cs=tuple(p['coeffs']);d=p['den']
        assert len(cs)==48 and type(d) is int and d>0 and all(type(c) is int for c in cs)
        assert gcd(d,*cs)==1
        pts.append((cs,d))
    n=len(pts);assert len(set(pts))==n
    edges=[tuple(e) for e in g['edges']];es=set(edges)
    assert len(es)==len(edges) and all(type(u) is int and type(v) is int and 0<=u<v<n for u,v in es)

    @lru_cache(None)
    def norm(cs,d):
        p=R.from_dict({(i,):c for i,c in enumerate(cs) if c})
        pc=sum((c*conjugates[i] for i,c in enumerate(cs) if c),R.zero)
        return (p*pc)%poly==d*d

    def is_unit(i,j):
        (a,d),(b,e)=pts[i],pts[j];den=d*e
        cs=tuple(x*e-y*d for x,y in zip(a,b));div=gcd(den,*cs)
        return norm(tuple(x//div for x in cs),den//div)

    primes=(211,421);red=[]
    for p in primes:
        root=next(r for r in range(2,p) if pow(r,210,p)==1 and all(pow(r,210//q,p)!=1 for q in (2,3,5,7)))
        assert sum(int(c)*pow(root,k[0],p) for k,c in poly.items())%p==0
        f=[pow(root,i,p) for i in range(48)];b=[pow(root,-i,p) for i in range(48)]
        values=[]
        for cs,d in pts:
            inv=pow(d,-1,p)
            values.append([sum(c*v for c,v in zip(cs,f))*inv%p,sum(c*v for c,v in zip(cs,b))*inv%p])
        red.append(np.array(values,dtype=np.int64))
    found=set();survivors=0
    for i in range(n-1):
        js=np.arange(i+1,n,dtype=np.int64)
        for p,rr in zip(primes,red):
            js=js[((rr[js,0]-rr[i,0])*(rr[js,1]-rr[i,1]))%p==1]
        for j0 in js:
            j=int(j0);survivors+=1
            if is_unit(i,j):found.add((i,j))
    assert found==es,'saved graph is not the complete unit-distance graph on the points'
    witness=[];statuses=[]
    for rp in sorted((directory/'probes').glob('*/*/RESULT.json')):
        r=json.loads(rp.read_text());statuses.append({'path':str(rp.relative_to(directory)),'status':r['status']})
        if r['status']!='SAT':continue
        assert r['graph_file_sha256']==hashlib.sha256(raw).hexdigest()
        cp=rp.parent/'COLORING.txt';cb=cp.read_bytes();s=cb.decode().strip();k=r['colors']
        assert len(s)==n and all(c in '0123456789' and int(c)<k for c in s)
        colors=list(map(int,s));assert all(colors[u]!=colors[v] for u,v in edges)
        assert all(colors[v]==c for v,c in r['pins'])
        if 'coloring_sha256' in r:assert r['coloring_sha256']==hashlib.sha256(cb).hexdigest()
        witness.append({'path':str(cp.relative_to(directory)),'colors':k,'pins':r['pins'],
            'sha256':hashlib.sha256(cb).hexdigest(),'all_edges_and_pins_validated':True})
    if five_bundle is not None:
        bundle=json.loads(gzip.decompress(five_bundle.read_bytes()))
        matches=[(key,case) for key,case in bundle.items() if case['graph_sha256']==hashlib.sha256(raw).hexdigest()]
        assert len(matches)==1,'bundle must contain exactly one matching graph'
        key,case=matches[0];assert case['vertices']==n and case['edges']==len(edges)
        assert case['five_colorings']
        for solver,entry in sorted(case['five_colorings'].items()):
            cb=entry['text'].encode();s=entry['text'].strip()
            assert hashlib.sha256(cb).hexdigest()==entry['sha256']
            assert len(s)==n and all(c in '01234' for c in s)
            colors=list(map(int,s));assert all(colors[u]!=colors[v] for u,v in edges)
            witness.append({'path':five_bundle.name+'::'+key+'::'+solver,'colors':5,
                'sha256':entry['sha256'],'all_edges_validated':True,
                'terminal_relation':'equal' if colors[g['ports']['a']]==colors[g['ports']['b']] else 'different'})
    return {'status':'PASS','vertices':n,'edges':len(edges),'graph_file_sha256':hashlib.sha256(raw).hexdigest(),
        'all_unordered_pairs_checked':n*(n-1)//2,'modular_filter_survivors':survivors,
        'exact_norm_cache':norm.cache_info()._asdict(),'induced_unit_edge_set_equal':True,
        'engine':'SymPy polynomial ring ZZ[z]/Phi210; no hn_cyclotomic210 import',
        'sympy_version':sp.__version__,'numpy_version':np.__version__,'float_used':False,
        'witnesses_verified':witness,'solver_statuses_recorded_without_promoting_negatives':statuses,
        'elapsed_seconds':round(monotonic()-started,3)}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--five-bundle',type=Path)
    a=p.parse_args();r=verify(a.candidate,a.five_bundle)
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))

if __name__=='__main__':main()
