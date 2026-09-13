#!/usr/bin/env python3
"""Link two already-closed G510 copy orbits by an asymmetric exact rotation.

This is the construction-level continuation after the order-3 and order-6 single
rings were both closed D. Orbit A is a closed finite zeta30 ring. Orbit B is an
exact isometric copy of the same closed ring, but rotated by a non-root K2 unit
and translated so one chosen pivot of B coincides with one pivot of A.

Initial asymmetric rotation:
    r = (-1 + 3*sqrt(-11)) / 10.
Its exact norm is (1 + 99)/100 = 1, and it is checked against all zeta30 roots.

Float geometry is proposal/ranking only. Every edge admitted to SAT is checked by
exact K2 arithmetic. The selected point set must still receive all-pairs exact
completion before any final D/B conclusion.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
from time import monotonic

import numpy as np
from scipy.spatial import cKDTree
from pysat.solvers import Cadical195, Glucose4

from hn_exact import K2, Z0, unit_modulus, zpow
from hn_closed_copy_assembly import build_ring, discover_exact_cross_edges, sample_models, signature_stats
from hn_unconditional_scan import color_cnf, valid_coloring, write_json


def pack(z): return {'a':z.a,'b':z.b,'den':z.den}


def asymmetric_rotation():
    a=Z0[:]; b=Z0[:]
    a[0]=-1; b[0]=3
    r=K2(a,b,10)
    assert r.den==10
    assert unit_modulus(r)
    assert all(r!=zpow(k) for k in range(30))
    return r


def merge_transformed(points, edges, rotation, dst_pivot, src_pivot):
    """Union first orbit with rotated second orbit, identifying chosen pivots."""
    index={p:i for i,p in enumerate(points)}
    out=list(points)
    cmap=[]
    shift=points[dst_pivot]-rotation*points[src_pivot]
    for p in points:
        q=rotation*p+shift
        j=index.get(q)
        if j is None:
            j=len(out); index[q]=j; out.append(q)
        cmap.append(j)
    inherited=set(edges)
    for u,v in edges:
        x,y=cmap[u],cmap[v]
        if x!=y: inherited.add((min(x,y),max(x,y)))
    assert cmap[src_pivot]==dst_pivot
    return out,inherited,cmap,shift


def choose_pivots(n, edges, count, seed):
    deg=[0]*n
    for u,v in edges: deg[u]+=1; deg[v]+=1
    ranked=sorted(range(n),key=lambda v:(deg[v],-v),reverse=True)
    chosen=ranked[:max(1,count//2)]
    rng=random.Random(seed)
    rest=[v for v in range(n) if v not in set(chosen)]
    rng.shuffle(rest)
    chosen.extend(rest[:max(0,count-len(chosen))])
    return chosen[:count],deg


def solve_limited(clauses,n,edges,conflicts,seed):
    rng=random.Random(seed)
    with Cadical195(bootstrap_with=clauses) as s:
        s.conf_budget(conflicts)
        s.set_phases([v*5+rng.randrange(5)+1 for v in range(n)])
        ans=s.solve_limited()
        if ans is not True: return ans,None
        pos=set(x for x in s.get_model() if x>0)
        c=[next(k for k in range(5) if v*5+k+1 in pos) for v in range(n)]
        assert valid_coloring(c,n,edges)
        return True,c


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--graph',type=Path,required=True)
    ap.add_argument('--out-dir',type=Path,required=True)
    ap.add_argument('--ring-order',type=int,default=3)
    ap.add_argument('--ring-anchor',default='95,101')
    ap.add_argument('--pivot-count',type=int,default=10)
    ap.add_argument('--geometry-keep',type=int,default=6)
    ap.add_argument('--sample-models',type=int,default=8)
    ap.add_argument('--conflicts',type=int,default=800000)
    ap.add_argument('--float-tolerance',type=float,default=3e-7)
    ap.add_argument('--seed',type=int,default=20260914)
    a=ap.parse_args(); a.out_dir.mkdir(parents=True,exist_ok=True)
    started=monotonic()

    raw=a.graph.read_bytes(); d=json.loads(raw)
    base_pts=[K2(p['a'],p['b'],p['den']) for p in d['pts']]
    base_edges=sorted({tuple(map(int,e)) for e in d['edges']})
    assert len(set(base_pts))==len(base_pts)
    assert all(unit_modulus(base_pts[u]-base_pts[v]) for u,v in base_edges)
    anchor=tuple(map(int,a.ring_anchor.split(',')))
    ring_pts,ring_inherited,_=build_ring(base_pts,base_edges,anchor,a.ring_order)
    ring_edges,ring_added,_=discover_exact_cross_edges(ring_pts,ring_inherited,a.float_tolerance)
    ring_edges=sorted(ring_edges)

    r=asymmetric_rotation()
    pivots,deg=choose_pivots(len(ring_pts),ring_edges,a.pivot_count,a.seed)
    write_json(a.out_dir/'ROTATION.json',{
        'rotation':pack(r),'approx_xy':[r.emb().real,r.emb().imag],
        'exact_unit_modulus':True,'zeta30_root':False,
        'construction':'(-1+3*sqrt(-11))/10'})

    geometry=[]
    for dst in pivots:
        for src in pivots:
            pts,inh,_map,shift=merge_transformed(ring_pts,ring_edges,r,dst,src)
            edges,added,proposal=discover_exact_cross_edges(pts,inh,a.float_tolerance)
            rec={'dst_pivot':dst,'src_pivot':src,'dst_degree':deg[dst],'src_degree':deg[src],
                 'vertices':len(pts),'inherited_edges':len(inh),'added_cross_edges':len(added),
                 'screen_edges':len(edges),'shift':pack(shift),**proposal,
                 'all_screen_edges_exact_unit':True,'screen_induced_complete':False}
            geometry.append(rec)
            print(json.dumps({'stage':'geometry',**{k:v for k,v in rec.items() if k!='shift'}},sort_keys=True),flush=True)
    geometry.sort(key=lambda x:(x['added_cross_edges'],-x['vertices']),reverse=True)
    write_json(a.out_dir/'GEOMETRY_SCREEN.json',{'rotation':pack(r),'pivots':pivots,'records':geometry})

    evaluated=[]; selected_graph=None; selected=None
    for idx,rec0 in enumerate(geometry[:a.geometry_keep]):
        pts,inh,_map,shift=merge_transformed(ring_pts,ring_edges,r,rec0['dst_pivot'],rec0['src_pivot'])
        edges,added,_=discover_exact_cross_edges(pts,inh,a.float_tolerance)
        edge_list=sorted(edges); n=len(pts); clauses=color_cnf(n,edge_list)
        sat,model=solve_limited(clauses,n,edge_list,a.conflicts,a.seed+idx)
        rec=dict(rec0)
        rec['cadical195']='SAT' if sat is True else 'UNSAT' if sat is False else 'UNKNOWN'
        if sat is False:
            with Glucose4(bootstrap_with=clauses) as gs:
                gs.conf_budget(a.conflicts*2); g=gs.solve_limited()
            rec['glucose4']='SAT' if g is True else 'UNSAT' if g is False else 'UNKNOWN'
            if g is False:
                rec['classification']='A_CANDIDATE_EXACT_SUBGRAPH_DUAL_UNSAT'
                selected=rec
                selected_graph={'pts':[pack(p) for p in pts],'edges':[list(e) for e in edge_list]}
                evaluated.append(rec); break
        elif sat is True:
            models=sample_models(n,edge_list,a.sample_models,max(100000,a.conflicts//2),a.seed+1000+idx,first_model=model)
            rec['signature_stats']=signature_stats(models,n)
            rec['classification']='SAT_SCREENING_CANDIDATE'
        else:
            rec['classification']='SCREENING_UNKNOWN'
        evaluated.append(rec)
        print(json.dumps({'stage':'sat',**{k:v for k,v in rec.items() if k!='shift'}},sort_keys=True),flush=True)

    if selected_graph is None:
        satrows=[x for x in evaluated if x.get('cadical195')=='SAT']
        if satrows:
            selected=max(satrows,key=lambda x:(
                float((x.get('signature_stats') or {}).get('remaining_pair_ratio',-1)),
                int((x.get('signature_stats') or {}).get('max_signature_block',-1)),
                x['added_cross_edges']))
        else:
            selected=geometry[0]
        pts,inh,_map,shift=merge_transformed(ring_pts,ring_edges,r,selected['dst_pivot'],selected['src_pivot'])
        edges,_,_=discover_exact_cross_edges(pts,inh,a.float_tolerance)
        selected_graph={'pts':[pack(p) for p in pts],'edges':[list(e) for e in sorted(edges)]}

    selected_graph.update({
        'construction':'two linked closed G510 orbits; asymmetric exact K2 rotation; screening edge set pending all-pairs exact completion',
        'base_graph_sha256':hashlib.sha256(raw).hexdigest(),
        'ring_order':a.ring_order,'ring_anchor':list(anchor),
        'link_rotation':pack(r),'link_dst_pivot':selected['dst_pivot'],'link_src_pivot':selected['src_pivot'],
        'no_conditional_constraints':True,'all_saved_edges_exact_unit':True,
        'induced_unit_edge_completion_pending':True})
    write_json(a.out_dir/'EVALUATED.json',{'records':evaluated})
    write_json(a.out_dir/'SELECTED.json',{'selection':selected})
    write_json(a.out_dir/'SELECTED_GRAPH.json',selected_graph)
    print(json.dumps({'selected':{k:v for k,v in selected.items() if k!='shift'},
                      'elapsed_seconds':round(monotonic()-started,3)},indent=2))

if __name__=='__main__': main()
