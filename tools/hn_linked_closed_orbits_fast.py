#!/usr/bin/env python3
"""Fast geometry selector for the asymmetric two-closed-orbit construction.

Equivalent geometry to hn_linked_closed_orbits.py, but when evaluating a pivot
alignment it searches only first-orbit vs transformed-second-orbit pairs. Internal
ring edges are already exact and unchanged by isometry, so re-running a KDTree on
the whole union is unnecessary for ranking inter-orbit coupling.
"""
from __future__ import annotations
import argparse, hashlib, json, random
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from hn_exact import K2, Z0, unit_modulus, zpow
from hn_closed_copy_assembly import build_ring, discover_exact_cross_edges
from hn_unconditional_scan import write_json


def pack(z): return {'a':z.a,'b':z.b,'den':z.den}

def rotation():
    a=Z0[:]; b=Z0[:]; a[0]=-1; b[0]=3
    r=K2(a,b,10)
    assert unit_modulus(r) and all(r!=zpow(k) for k in range(30))
    return r

def choose_pivots(n,edges,count,seed):
    deg=[0]*n
    for u,v in edges: deg[u]+=1; deg[v]+=1
    ranked=sorted(range(n),key=lambda v:(deg[v],-v),reverse=True)
    out=ranked[:max(1,count//2)]
    rng=random.Random(seed); rest=[v for v in range(n) if v not in set(out)]; rng.shuffle(rest)
    out.extend(rest[:count-len(out)])
    return out,deg

def inter_edges(first,second,map_second,tol):
    xy1=np.asarray([[p.emb().real,p.emb().imag] for p in first])
    xy2=np.asarray([[p.emb().real,p.emb().imag] for p in second])
    tree=cKDTree(xy1)
    added=set(); proposed=0
    for j,q in enumerate(xy2):
        cand=tree.query_ball_point(q,1.0+tol)
        for i in cand:
            d=xy1[i]-q
            if d[0]*d[0]+d[1]*d[1] < (1.0-tol)**2: continue
            proposed+=1
            gj=map_second[j]
            if i==gj: continue
            e=(i,gj) if i<gj else (gj,i)
            if unit_modulus(first[i]-second[j]): added.add(e)
    return added,proposed

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--graph',type=Path,required=True); ap.add_argument('--out-dir',type=Path,required=True)
    ap.add_argument('--ring-order',type=int,default=3); ap.add_argument('--ring-anchor',default='95,101')
    ap.add_argument('--pivot-count',type=int,default=8); ap.add_argument('--float-tolerance',type=float,default=3e-7)
    ap.add_argument('--seed',type=int,default=20260914)
    a=ap.parse_args(); a.out_dir.mkdir(parents=True,exist_ok=True)
    raw=a.graph.read_bytes(); d=json.loads(raw)
    bp=[K2(p['a'],p['b'],p['den']) for p in d['pts']]; be=sorted({tuple(e) for e in d['edges']})
    anchor=tuple(map(int,a.ring_anchor.split(',')))
    ring,inh,_=build_ring(bp,be,anchor,a.ring_order)
    ring_edges,_,_=discover_exact_cross_edges(ring,inh,a.float_tolerance); ring_edges=sorted(ring_edges)
    r=rotation(); pivots,deg=choose_pivots(len(ring),ring_edges,a.pivot_count,a.seed)
    records=[]; best=None; best_payload=None
    for dst in pivots:
        for src in pivots:
            shift=ring[dst]-r*ring[src]
            second=[r*p+shift for p in ring]
            idx={p:i for i,p in enumerate(ring)}; union=list(ring); cmap=[]
            for q in second:
                gi=idx.get(q)
                if gi is None: gi=len(union); idx[q]=gi; union.append(q)
                cmap.append(gi)
            added,proposed=inter_edges(union,second,cmap,a.float_tolerance)
            # Internal edges of B under cmap.
            inherited=set(ring_edges)
            for u,v in ring_edges:
                x,y=cmap[u],cmap[v]
                if x!=y: inherited.add((min(x,y),max(x,y)))
            # inter_edges may include edges already internal/shared; count only new union edges.
            cross=added-inherited
            rec={'dst_pivot':dst,'src_pivot':src,'dst_degree':deg[dst],'src_degree':deg[src],
                 'vertices':len(union),'inherited_edges':len(inherited),'added_cross_edges':len(cross),
                 'exact_proposals_checked':proposed,'shift':pack(shift)}
            records.append(rec)
            key=(len(cross),-len(union),deg[dst]+deg[src])
            if best is None or key>best:
                best=key; best_payload=(rec,union,inherited|cross)
            print(json.dumps({k:v for k,v in rec.items() if k!='shift'},sort_keys=True),flush=True)
    rec,pts,edges=best_payload
    graph={'pts':[pack(p) for p in pts],'edges':[list(e) for e in sorted(edges)],
           'construction':'two linked closed G510 orbits; optimized geometry selection; asymmetric exact rotation; pending all-pairs completion',
           'base_graph_sha256':hashlib.sha256(raw).hexdigest(),'ring_order':a.ring_order,'ring_anchor':list(anchor),
           'link_rotation':pack(r),'link_dst_pivot':rec['dst_pivot'],'link_src_pivot':rec['src_pivot'],
           'no_conditional_constraints':True,'all_saved_edges_exact_unit':True,'induced_unit_edge_completion_pending':True}
    write_json(a.out_dir/'ROTATION.json',{'rotation':pack(r),'approx_xy':[r.emb().real,r.emb().imag],'exact_unit_modulus':True,'zeta30_root':False})
    write_json(a.out_dir/'GEOMETRY_SCREEN.json',{'records':records})
    write_json(a.out_dir/'SELECTED.json',{'selection':rec})
    write_json(a.out_dir/'SELECTED_GRAPH.json',graph)
    print(json.dumps({'selection':{k:v for k,v in rec.items() if k!='shift'}},indent=2))
if __name__=='__main__': main()
