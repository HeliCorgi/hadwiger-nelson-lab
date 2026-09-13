#!/usr/bin/env python3
"""Search exact two-anchor (edge-to-edge) links between closed rings.

For the asymmetric unit rotation r, an oriented source edge (c,d) of a closed
ring can be glued exactly onto an oriented destination edge (a,b) iff

    p_b - p_a = r * (p_d - p_c).

Then the translation t = p_a - r*p_c simultaneously identifies c->a and d->b.
This gives a two-shared-vertex linker instead of the one-pivot linker.
All matching is exact K2 arithmetic; no floating search is needed to find matches.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
from hn_exact import K2, Z0, unit_modulus, zpow
from hn_closed_copy_assembly import build_ring, discover_exact_cross_edges
from hn_unconditional_scan import write_json


def pack(z): return {'a':z.a,'b':z.b,'den':z.den}

def rotation():
    a=Z0[:]; b=Z0[:]; a[0]=-1; b[0]=3
    r=K2(a,b,10)
    assert unit_modulus(r) and all(r!=zpow(k) for k in range(30))
    return r

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--graph',type=Path,required=True)
    ap.add_argument('--out-dir',type=Path,required=True)
    ap.add_argument('--ring-order',type=int,default=3)
    ap.add_argument('--ring-anchor',default='95,101')
    ap.add_argument('--max-matches',type=int,default=500)
    a=ap.parse_args(); a.out_dir.mkdir(parents=True,exist_ok=True)
    d=json.loads(a.graph.read_text())
    bp=[K2(p['a'],p['b'],p['den']) for p in d['pts']]
    be=sorted({tuple(map(int,e)) for e in d['edges']})
    anchor=tuple(map(int,a.ring_anchor.split(',')))
    ring,inh,_=build_ring(bp,be,anchor,a.ring_order)
    edges,_,_=discover_exact_cross_edges(ring,inh,3e-7); edges=sorted(edges)
    r=rotation()
    dest={}
    for u,v in edges:
        dest.setdefault(ring[v]-ring[u],[]).append((u,v))
        dest.setdefault(ring[u]-ring[v],[]).append((v,u))
    matches=[]
    for c,dst in edges:
        for c0,d0 in ((c,dst),(dst,c)):
            td=r*(ring[d0]-ring[c0])
            for a0,b0 in dest.get(td,[]):
                shift=ring[a0]-r*ring[c0]
                assert r*ring[c0]+shift==ring[a0]
                assert r*ring[d0]+shift==ring[b0]
                matches.append({'dst_edge':[a0,b0],'src_edge':[c0,d0],'shift':pack(shift)})
                if len(matches)>=a.max_matches: break
            if len(matches)>=a.max_matches: break
        if len(matches)>=a.max_matches: break
    payload={'status':'FOUND_TWO_ANCHOR_MATCHES' if matches else 'NO_EDGE_TO_EDGE_MATCH',
             'ring_vertices':len(ring),'ring_edges':len(edges),
             'rotation':pack(r),'exact_unit_modulus':True,'zeta30_root':False,
             'matches_found':len(matches),'truncated_at':a.max_matches if len(matches)>=a.max_matches else None,
             'matches':matches,
             'scope_note':'Exact search over oriented unit edges of this closed ring only.'}
    write_json(a.out_dir/'TWO_ANCHOR_MATCHES.json',payload)
    lines=['# Exact two-anchor asymmetric link search','',
           f"- ring: **{len(ring)} vertices / {len(edges)} exact unit edges**",
           '- rotation: `(-1+3*sqrt(-11))/10`',
           f"- exact oriented edge-to-edge matches found: **{len(matches)}**",
           '', 'Matching condition is exact `p_b-p_a = r*(p_d-p_c)`; no float proposal is used.']
    (a.out_dir/'SUMMARY.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({k:v for k,v in payload.items() if k!='matches'},indent=2))
if __name__=='__main__': main()
