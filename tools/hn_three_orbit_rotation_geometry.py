#!/usr/bin/env python3
"""Geometry-only scan for one candidate C rotation in a three-orbit network."""
from __future__ import annotations
import argparse, json, random
from pathlib import Path

from hn_exact import K2, unit_modulus
from hn_closed_copy_assembly import build_ring, discover_exact_cross_edges
from hn_linked_closed_orbits import merge_transformed
from hn_linked_closed_orbits_fast import choose_pivots
from hn_three_orbit_network import rational_unit_rotation, merge_copy, inter_edges, owner_counts, pack
from hn_unconditional_scan import write_json


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--graph',type=Path,required=True)
    ap.add_argument('--out-dir',type=Path,required=True)
    ap.add_argument('--c-p',type=int,required=True)
    ap.add_argument('--c-q',type=int,required=True)
    ap.add_argument('--pivot-count',type=int,default=6)
    ap.add_argument('--seed',type=int,default=20260914)
    ap.add_argument('--float-tolerance',type=float,default=3e-7)
    a=ap.parse_args(); a.out_dir.mkdir(parents=True,exist_ok=True)

    d=json.loads(a.graph.read_text())
    bp=[K2(p['a'],p['b'],p['den']) for p in d['pts']]
    be=sorted({tuple(map(int,e)) for e in d['edges']})
    assert all(unit_modulus(bp[u]-bp[v]) for u,v in be)
    ring,inh,_=build_ring(bp,be,(95,101),3)
    ring_edges,_,_=discover_exact_cross_edges(ring,inh,a.float_tolerance); ring_edges=sorted(ring_edges)
    r1=rational_unit_rotation(1,3); r2=rational_unit_rotation(a.c_p,a.c_q)
    assert r1!=r2

    ab,ab_inherited,bmap,_=merge_transformed(ring,ring_edges,r1,0,911)
    ab_edges,_,_=discover_exact_cross_edges(ab,ab_inherited,a.float_tolerance); ab_edges=set(ab_edges)
    aset=set(range(len(ring))); bset=set(bmap)
    src,_=choose_pivots(len(ring),ring_edges,a.pivot_count,a.seed)
    deg=[0]*len(ab)
    for u,v in ab_edges: deg[u]+=1; deg[v]+=1
    def pick(owner,seed):
        ranked=sorted(owner,key=lambda v:(deg[v],-v),reverse=True)
        top=ranked[:max(1,a.pivot_count//2)]
        rng=random.Random(seed); rest=[v for v in owner if v not in set(top)]; rng.shuffle(rest)
        return (top+rest[:a.pivot_count-len(top)])[:a.pivot_count]
    dst_a=pick(aset,a.seed+1); dst_b=pick(bset,a.seed+2)

    records=[]
    for label,dsts in (('A',dst_a),('B',dst_b)):
        for dst in dsts:
            for s in src:
                union,transformed,cmap,cinherited,shift=merge_copy(ab,ring,ring_edges,r2,dst,s)
                cross,proposed=inter_edges(ab,transformed,cmap,a.float_tolerance)
                inherited=ab_edges|cinherited; new=cross-inherited
                ca,cb=owner_counts(new,set(cmap),aset,bset)
                records.append({'dst_owner':label,'dst_pivot':dst,'src_pivot':s,'vertices':len(union),
                                'added_cross_edges':len(new),'c_to_a_edges':ca,'c_to_b_edges':cb,
                                'couples_to_both':bool(ca and cb),'exact_proposals_checked':proposed,
                                'shift':pack(shift)})
    both=[r for r in records if r['couples_to_both']]
    pool=both if both else records
    selected=max(pool,key=lambda r:(min(r['c_to_a_edges'],r['c_to_b_edges']),
                                    r['c_to_a_edges']+r['c_to_b_edges'],r['added_cross_edges'],-r['vertices']))
    out={'c_parameter':[a.c_p,a.c_q],'c_rotation':pack(r2),'placements':len(records),
         'two_sided_placements':len(both),'max_min_two_sided_coupling':max((min(r['c_to_a_edges'],r['c_to_b_edges']) for r in both),default=0),
         'max_total_two_sided_coupling':max((r['c_to_a_edges']+r['c_to_b_edges'] for r in both),default=0),
         'max_added_cross_edges':max(r['added_cross_edges'] for r in records),'selected':selected}
    write_json(a.out_dir/'SUMMARY.json',out)
    write_json(a.out_dir/'SCREEN.json',{'records':records})
    print(json.dumps(out,indent=2))

if __name__=='__main__': main()
