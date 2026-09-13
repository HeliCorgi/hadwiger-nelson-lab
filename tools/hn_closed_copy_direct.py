#!/usr/bin/env python3
"""Build one exact closed-copy ring candidate for subsequent all-pairs completion."""
import argparse, json
from pathlib import Path
from hn_exact import K2
from hn_closed_copy_assembly import build_ring, discover_exact_cross_edges, pack
from hn_unconditional_scan import write_json

ap=argparse.ArgumentParser()
ap.add_argument('--graph',type=Path,required=True)
ap.add_argument('--out-dir',type=Path,required=True)
ap.add_argument('--order',type=int,required=True)
ap.add_argument('--anchor',required=True,help='u,v')
ap.add_argument('--float-tolerance',type=float,default=3e-7)
a=ap.parse_args(); a.out_dir.mkdir(parents=True,exist_ok=True)
d=json.loads(a.graph.read_text()); pts=[K2(p['a'],p['b'],p['den']) for p in d['pts']]
edges=[tuple(map(int,e)) for e in d['edges']]; u,v=map(int,a.anchor.split(','))
q,inherited,_=build_ring(pts,edges,(u,v),a.order)
screen,added,meta=discover_exact_cross_edges(q,inherited,a.float_tolerance)
out={'pts':[pack(p) for p in q],'edges':[list(e) for e in sorted(screen)],
     'construction':f'closed cyclic order-{a.order} ring, anchor ({u},{v})',
     'order':a.order,'anchor':[u,v],'no_conditional_constraints':True,
     'all_saved_edges_exact_unit':True,'induced_unit_edge_completion_pending':True}
write_json(a.out_dir/'SELECTED_GRAPH.json',out)
write_json(a.out_dir/'SCREEN.json',{'vertices':len(q),'inherited_edges':len(inherited),
    'added_exact_cross_edges':len(added),'screen_edges':len(screen),**meta})
print((a.out_dir/'SCREEN.json').read_text())
