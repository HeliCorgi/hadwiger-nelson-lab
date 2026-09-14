#!/usr/bin/env python3
"""Geometry-only scan for an 8-orbit commuting cube.

T1=r(1/3) and T2=r(1/5) use the exact common center determined by the
established A->B placement. A caller supplies a distinct T3=r(p/q). All eight
Boolean products of T1,T2,T3 are applied about that same center. Floating point
only proposes unit pairs; every saved edge is exact-validated.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from hn_exact import K2,ONE,Z0,unit_modulus
from hn_closed_copy_assembly import build_ring,discover_exact_cross_edges
from hn_linked_closed_orbits import pack
from hn_three_orbit_network import rational_unit_rotation
from hn_unconditional_scan import write_json


def inv_subfield(x:K2)->K2:
    assert all(v==0 for v in x.a[1:]+x.b[1:])
    aa,bb=x.a[0],x.b[0]
    a=Z0[:]; b=Z0[:]
    a[0]=x.den*aa; b[0]=-x.den*bb
    y=K2(a,b,aa*aa+11*bb*bb)
    assert (x*y).is_one()
    return y


def transform(points,r,c):
    return [r*p+(ONE-r)*c for p in points]


def between_count(edges,s1,s2):
    out=set()
    for u,v in edges:
        if (u in s1 and v in s2) or (v in s1 and u in s2): out.add((u,v))
    return len(out)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--graph',type=Path,required=True)
    ap.add_argument('--out-dir',type=Path,required=True)
    ap.add_argument('--p',type=int,required=True); ap.add_argument('--q',type=int,required=True)
    ap.add_argument('--float-tolerance',type=float,default=3e-7)
    a=ap.parse_args(); a.out_dir.mkdir(parents=True,exist_ok=True)
    d=json.loads(a.graph.read_text()); bp=[K2(x['a'],x['b'],x['den']) for x in d['pts']]; be=sorted({tuple(map(int,e)) for e in d['edges']})
    ring,inh,_=build_ring(bp,be,(95,101),3); re,_,_=discover_exact_cross_edges(ring,inh,a.float_tolerance); re=sorted(re)
    r1=rational_unit_rotation(1,3); r2=rational_unit_rotation(1,5); r3=rational_unit_rotation(a.p,a.q)
    assert r3!=r1 and r3!=r2
    s1=ring[0]-r1*ring[911]; center=inv_subfield(ONE-r1)*s1
    assert r1*center+s1==center
    rots=[ONE,r1,r2,r1*r2,r3,r1*r3,r2*r3,r1*r2*r3]
    labels=['000','100','010','110','001','101','011','111']
    index={}; pts=[]; maps={}; inherited=set()
    for lab,r in zip(labels,rots):
        cp=transform(ring,r,center); m=[]
        for p in cp:
            j=index.get(p)
            if j is None: j=len(pts); index[p]=j; pts.append(p)
            m.append(j)
        maps[lab]=m
        for u,v in re:
            x,y=m[u],m[v]
            if x!=y: inherited.add((min(x,y),max(x,y)))
    edges,added,proposal=discover_exact_cross_edges(pts,inherited,a.float_tolerance)
    assert all(unit_modulus(pts[u]-pts[v]) for u,v in edges)
    sets={k:set(v) for k,v in maps.items()}
    base_t3=between_count(added,sets['000'],sets['001'])
    pair_counts={}
    for i,x in enumerate(labels):
        for y in labels[i+1:]:
            n=between_count(added,sets[x],sets[y])
            if n: pair_counts[x+'-'+y]=n
    out={'parameter':[a.p,a.q],'rotation':pack(r3),'vertices':len(pts),'inherited_edges':len(inherited),'added_cross_edges':len(added),'screen_edges':len(edges),'base_t3_cross_edges':base_t3,'nonzero_copy_pair_counts':pair_counts,'proposal':proposal,'center':pack(center),'all_saved_edges_exact_unit':True,'completion_pending':True}
    write_json(a.out_dir/'SUMMARY.json',out)
    write_json(a.out_dir/'SELECTED_GRAPH.json',{'pts':[pack(p) for p in pts],'edges':[list(e) for e in sorted(edges)],'cube_parameter':[a.p,a.q],'all_saved_edges_exact_unit':True,'induced_unit_edge_completion_pending':True})
    print(json.dumps(out,indent=2))

if __name__=='__main__': main()
