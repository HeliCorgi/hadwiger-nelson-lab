#!/usr/bin/env python3
"""Build a three-closed-orbit unconditional network with two distinct rotations.

Orbit A is the exact order-3 closed G510 ring. Orbit B uses the already tested
r(1/3)=(-1+3*sqrt(-11))/10 placement (dst,src)=(0,911). Orbit C uses the distinct
r(1/2)=(-7+4*sqrt(-11))/15 rotation. We search C pivot placements and explicitly
prefer candidates with literal exact unit edges from C to BOTH A and B.

Float geometry only proposes distance-1 pairs. Every admitted edge is exact-checked.
The selected point set is still marked pending all-pairs exact completion.
"""
from __future__ import annotations

import argparse, hashlib, json, random
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree
from pysat.solvers import Cadical195, Glucose4

from hn_exact import K2, Z0, unit_modulus, zpow
from hn_closed_copy_assembly import build_ring, discover_exact_cross_edges, sample_models, signature_stats
from hn_linked_closed_orbits import merge_transformed, solve_limited, pack
from hn_linked_closed_orbits_fast import choose_pivots
from hn_unconditional_scan import color_cnf, write_json


def rational_unit_rotation(p: int, q: int) -> K2:
    """Cayley parametrization in Q(sqrt(-11)); t=p/q."""
    if q == 0:
        raise ValueError('q=0')
    a=Z0[:]; b=Z0[:]
    a[0]=q*q-11*p*p
    b[0]=2*p*q
    r=K2(a,b,q*q+11*p*p)
    assert unit_modulus(r)
    assert all(r!=zpow(k) for k in range(30))
    return r


def merge_copy(existing, ring, ring_edges, rotation, dst, src):
    shift=existing[dst]-rotation*ring[src]
    transformed=[rotation*p+shift for p in ring]
    index={p:i for i,p in enumerate(existing)}
    union=list(existing); cmap=[]
    for q in transformed:
        j=index.get(q)
        if j is None:
            j=len(union); index[q]=j; union.append(q)
        cmap.append(j)
    inherited=set()
    for u,v in ring_edges:
        x,y=cmap[u],cmap[v]
        if x!=y: inherited.add((min(x,y),max(x,y)))
    assert cmap[src]==dst
    return union, transformed, cmap, inherited, shift


def inter_edges(existing, transformed, cmap, tol):
    xy1=np.asarray([[p.emb().real,p.emb().imag] for p in existing],dtype=np.float64)
    xy2=np.asarray([[p.emb().real,p.emb().imag] for p in transformed],dtype=np.float64)
    tree=cKDTree(xy1)
    added=set(); proposed=0
    lo=(1.0-tol)**2
    for j,q in enumerate(xy2):
        for i in tree.query_ball_point(q,1.0+tol):
            d=xy1[i]-q
            if d[0]*d[0]+d[1]*d[1] < lo:
                continue
            proposed+=1
            gj=cmap[j]
            if i==gj:
                continue
            e=(i,gj) if i<gj else (gj,i)
            if unit_modulus(existing[i]-transformed[j]):
                added.add(e)
    return added, proposed


def owner_counts(edges, cset, aset, bset):
    ca=set(); cb=set()
    for u,v in edges:
        uc=u in cset; vc=v in cset
        if uc==vc:
            continue
        c=u if uc else v
        x=v if uc else u
        e=(min(c,x),max(c,x))
        if x in aset: ca.add(e)
        if x in bset: cb.add(e)
    return len(ca),len(cb)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--graph',type=Path,required=True)
    ap.add_argument('--out-dir',type=Path,required=True)
    ap.add_argument('--ring-order',type=int,default=3)
    ap.add_argument('--ring-anchor',default='95,101')
    ap.add_argument('--b-dst',type=int,default=0)
    ap.add_argument('--b-src',type=int,default=911)
    ap.add_argument('--pivot-count',type=int,default=6)
    ap.add_argument('--geometry-keep',type=int,default=6)
    ap.add_argument('--sample-models',type=int,default=6)
    ap.add_argument('--conflicts',type=int,default=500000)
    ap.add_argument('--float-tolerance',type=float,default=3e-7)
    ap.add_argument('--seed',type=int,default=20260914)
    a=ap.parse_args(); a.out_dir.mkdir(parents=True,exist_ok=True)

    raw=a.graph.read_bytes(); d=json.loads(raw)
    bp=[K2(p['a'],p['b'],p['den']) for p in d['pts']]
    be=sorted({tuple(map(int,e)) for e in d['edges']})
    assert len(set(bp))==len(bp) and all(unit_modulus(bp[u]-bp[v]) for u,v in be)
    anchor=tuple(map(int,a.ring_anchor.split(',')))
    ring,inh,_=build_ring(bp,be,anchor,a.ring_order)
    ring_edges,_,_=discover_exact_cross_edges(ring,inh,a.float_tolerance)
    ring_edges=sorted(ring_edges)

    r1=rational_unit_rotation(1,3)
    r2=rational_unit_rotation(1,2)
    # Build fixed A+B control geometry.
    ab,ab_inherited,bmap,bshift=merge_transformed(ring,ring_edges,r1,a.b_dst,a.b_src)
    ab_edges,_,_=discover_exact_cross_edges(ab,ab_inherited,a.float_tolerance)
    ab_edges=set(ab_edges)
    aset=set(range(len(ring)))
    bset=set(bmap)

    # Source pivots in C come from the ring portfolio. Destination pivots are drawn
    # separately from A and B so the search is not biased to a single orbit.
    src_pivots,_=choose_pivots(len(ring),ring_edges,a.pivot_count,a.seed)
    deg_ab=[0]*len(ab)
    for u,v in ab_edges: deg_ab[u]+=1; deg_ab[v]+=1
    def pick(owner,seed):
        ranked=sorted(owner,key=lambda x:(deg_ab[x],-x),reverse=True)
        top=ranked[:max(1,a.pivot_count//2)]
        rng=random.Random(seed); rest=[x for x in owner if x not in set(top)]; rng.shuffle(rest)
        return (top+rest[:a.pivot_count-len(top)])[:a.pivot_count]
    dst_a=pick(aset,a.seed+11)
    dst_b=pick(bset,a.seed+12)
    destinations=[]
    for owner,label in ((dst_a,'A'),(dst_b,'B')):
        for v in owner:
            if (v,label) not in destinations: destinations.append((v,label))

    records=[]; payload={}
    for dst,label in destinations:
        for src in src_pivots:
            union,transformed,cmap,cinherited,shift=merge_copy(ab,ring,ring_edges,r2,dst,src)
            cross,proposed=inter_edges(ab,transformed,cmap,a.float_tolerance)
            inherited=set(ab_edges)|cinherited
            newcross=cross-inherited
            cset=set(cmap)
            ca,cb=owner_counts(newcross,cset,aset,bset)
            edges=inherited|newcross
            rec={
                'dst_pivot':dst,'dst_owner':label,'src_pivot':src,
                'vertices':len(union),'inherited_edges':len(inherited),
                'added_cross_edges':len(newcross),'c_to_a_edges':ca,'c_to_b_edges':cb,
                'couples_to_both':bool(ca and cb),'exact_proposals_checked':proposed,
                'shift':pack(shift),
            }
            records.append(rec)
            payload[(dst,src)]=(union,edges)
            print(json.dumps({k:v for k,v in rec.items() if k!='shift'},sort_keys=True),flush=True)

    # Geometry ranking: require two-sided coupling when available, then maximize the
    # weaker side before total coupling. This explicitly rejects a strong one-sided leaf.
    both=[r for r in records if r['couples_to_both']]
    pool=both if both else records
    pool=sorted(pool,key=lambda r:(min(r['c_to_a_edges'],r['c_to_b_edges']),
                                   r['c_to_a_edges']+r['c_to_b_edges'],
                                   r['added_cross_edges'],-r['vertices']),reverse=True)
    write_json(a.out_dir/'GEOMETRY_SCREEN.json',{
        'rotations':{'B':pack(r1),'C':pack(r2)},'src_pivots':src_pivots,
        'dst_a':dst_a,'dst_b':dst_b,'records':records})

    evaluated=[]; selected=None; selected_graph=None
    for idx,rec0 in enumerate(pool[:a.geometry_keep]):
        pts,edges=payload[(rec0['dst_pivot'],rec0['src_pivot'])]
        edge_list=sorted(edges); n=len(pts); clauses=color_cnf(n,edge_list)
        sat,model=solve_limited(clauses,n,edge_list,a.conflicts,a.seed+100+idx)
        rec=dict(rec0)
        rec['cadical195']='SAT' if sat is True else 'UNSAT' if sat is False else 'UNKNOWN'
        if sat is False:
            with Glucose4(bootstrap_with=clauses) as gs:
                gs.conf_budget(a.conflicts*2); g=gs.solve_limited()
            rec['glucose4']='UNSAT' if g is False else 'SAT' if g is True else 'UNKNOWN'
            if g is False:
                rec['classification']='A_CANDIDATE_EXACT_SUBGRAPH_DUAL_UNSAT'
                selected=rec; selected_graph=(pts,edge_list); evaluated.append(rec); break
        elif sat is True:
            models=sample_models(n,edge_list,a.sample_models,max(100000,a.conflicts//2),a.seed+1000+idx,first_model=model)
            rec['signature_stats']=signature_stats(models,n)
            rec['classification']='SAT_SCREENING_CANDIDATE'
        else:
            rec['classification']='SCREENING_UNKNOWN'
        evaluated.append(rec)
        print(json.dumps({k:v for k,v in rec.items() if k!='shift'},sort_keys=True),flush=True)

    if selected_graph is None:
        sats=[r for r in evaluated if r.get('cadical195')=='SAT']
        if sats:
            # More sampled same-signature pairs = more promising for B/global rigidity.
            selected=max(sats,key=lambda r:(
                float((r.get('signature_stats') or {}).get('remaining_pair_ratio',-1)),
                int((r.get('signature_stats') or {}).get('max_signature_block',-1)),
                min(r['c_to_a_edges'],r['c_to_b_edges']),r['added_cross_edges']))
        else:
            selected=pool[0]
        selected_graph=payload[(selected['dst_pivot'],selected['src_pivot'])]
        selected_graph=(selected_graph[0],sorted(selected_graph[1]))

    pts,edge_list=selected_graph
    graph={
        'pts':[pack(p) for p in pts],'edges':[list(e) for e in edge_list],
        'construction':'three closed G510 orbits; B uses r(1/3), C uses r(1/2); pending all-pairs exact completion',
        'base_graph_sha256':hashlib.sha256(raw).hexdigest(),
        'ring_order':a.ring_order,'ring_anchor':list(anchor),
        'b_rotation':pack(r1),'b_dst_pivot':a.b_dst,'b_src_pivot':a.b_src,'b_shift':pack(bshift),
        'c_rotation':pack(r2),'c_dst_pivot':selected['dst_pivot'],'c_src_pivot':selected['src_pivot'],
        'no_conditional_constraints':True,'all_saved_edges_exact_unit':True,
        'induced_unit_edge_completion_pending':True,
    }
    assert all(unit_modulus(pts[u]-pts[v]) for u,v in edge_list)
    write_json(a.out_dir/'ROTATIONS.json',{
        'B':{'rotation':pack(r1),'parameter':'1/3','exact_unit_modulus':True,'zeta30_root':False},
        'C':{'rotation':pack(r2),'parameter':'1/2','exact_unit_modulus':True,'zeta30_root':False}})
    write_json(a.out_dir/'EVALUATED.json',{'records':evaluated})
    write_json(a.out_dir/'SELECTED.json',{'selection':selected})
    write_json(a.out_dir/'SELECTED_GRAPH.json',graph)
    print(json.dumps({'selected':{k:v for k,v in selected.items() if k!='shift'}},indent=2))

if __name__=='__main__': main()
