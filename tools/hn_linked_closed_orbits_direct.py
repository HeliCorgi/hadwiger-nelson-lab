#!/usr/bin/env python3
"""Rebuild one fixed asymmetric linked closed-orbit candidate exactly.

This avoids repeating the portfolio screen once a concrete pivot alignment has
already been selected. The saved edge set is exact but still receives the usual
all-pairs exact completion before any final classification.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

from hn_exact import K2, unit_modulus
from hn_closed_copy_assembly import build_ring, discover_exact_cross_edges
from hn_linked_closed_orbits import asymmetric_rotation, merge_transformed, pack
from hn_unconditional_scan import write_json


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--graph',type=Path,required=True)
    ap.add_argument('--out-dir',type=Path,required=True)
    ap.add_argument('--ring-order',type=int,default=3)
    ap.add_argument('--ring-anchor',default='95,101')
    ap.add_argument('--dst-pivot',type=int,required=True)
    ap.add_argument('--src-pivot',type=int,required=True)
    ap.add_argument('--float-tolerance',type=float,default=3e-7)
    a=ap.parse_args(); a.out_dir.mkdir(parents=True,exist_ok=True)

    raw=a.graph.read_bytes(); d=json.loads(raw)
    base_pts=[K2(p['a'],p['b'],p['den']) for p in d['pts']]
    base_edges=sorted({tuple(map(int,e)) for e in d['edges']})
    assert len(set(base_pts))==len(base_pts)
    assert all(unit_modulus(base_pts[u]-base_pts[v]) for u,v in base_edges)
    anchor=tuple(map(int,a.ring_anchor.split(',')))
    ring_pts,ring_inherited,_=build_ring(base_pts,base_edges,anchor,a.ring_order)
    ring_edges,_,_=discover_exact_cross_edges(ring_pts,ring_inherited,a.float_tolerance)
    ring_edges=sorted(ring_edges)

    r=asymmetric_rotation()
    pts,inh,_map,shift=merge_transformed(ring_pts,ring_edges,r,a.dst_pivot,a.src_pivot)
    edges,added,proposal=discover_exact_cross_edges(pts,inh,a.float_tolerance)
    edge_list=sorted(edges)
    assert all(unit_modulus(pts[u]-pts[v]) for u,v in edge_list)

    graph={
        'pts':[pack(p) for p in pts],
        'edges':[list(e) for e in edge_list],
        'construction':'fixed two linked closed G510 orbits; asymmetric exact K2 rotation; pending all-pairs exact completion',
        'base_graph_sha256':hashlib.sha256(raw).hexdigest(),
        'ring_order':a.ring_order,'ring_anchor':list(anchor),
        'link_rotation':pack(r),'link_dst_pivot':a.dst_pivot,'link_src_pivot':a.src_pivot,
        'no_conditional_constraints':True,'all_saved_edges_exact_unit':True,
        'induced_unit_edge_completion_pending':True,
    }
    meta={
        'dst_pivot':a.dst_pivot,'src_pivot':a.src_pivot,
        'vertices':len(pts),'inherited_edges':len(inh),'added_cross_edges':len(added),
        'screen_edges':len(edge_list),'shift':pack(shift),**proposal,
        'all_screen_edges_exact_unit':True,
    }
    write_json(a.out_dir/'SELECTED.json',{'selection':meta})
    write_json(a.out_dir/'ROTATION.json',{'rotation':pack(r),'exact_unit_modulus':True,'zeta30_root':False})
    write_json(a.out_dir/'SELECTED_GRAPH.json',graph)
    print(json.dumps(meta,indent=2))

if __name__=='__main__': main()
