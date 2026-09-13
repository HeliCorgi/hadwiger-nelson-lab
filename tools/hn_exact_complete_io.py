#!/usr/bin/env python3
"""Small I/O wrapper around hn_exact_completion.cpp for selected point sets."""
import argparse, hashlib, json
from pathlib import Path

ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='cmd',required=True)
p=sub.add_parser('prepare'); p.add_argument('--graph',type=Path,required=True); p.add_argument('--out',type=Path,required=True)
p=sub.add_parser('finish'); p.add_argument('--graph',type=Path,required=True); p.add_argument('--edges',type=Path,required=True); p.add_argument('--out-dir',type=Path,required=True)
a=ap.parse_args()
if a.cmd=='prepare':
    g=json.loads(a.graph.read_text()); a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open('w') as f:
        print(len(g['pts']),file=f)
        for p in g['pts']: print(p['den'],*p['a'],*p['b'],file=f)
else:
    a.out_dir.mkdir(parents=True,exist_ok=True); s=json.loads(a.graph.read_text())
    exact=[list(map(int,x.split())) for x in a.edges.read_text().splitlines() if x.strip()]
    old={tuple(e) for e in s['edges']}; full={tuple(e) for e in exact}; assert old<=full
    s['edges']=exact; s['induced_unit_edge_completion_pending']=False
    s['all_pairs_exactly_checked']=len(s['pts'])*(len(s['pts'])-1)//2
    s['construction']=s.get('construction','closed cyclic multi-copy')+'; exact all-pairs induced completion'
    path=a.out_dir/'COMPLETED_GRAPH.json'; path.write_text(json.dumps(s,separators=(',',':'))+'\n')
    geo={'vertices':len(s['pts']),'screen_edges':len(old),'exact_induced_edges':len(exact),
         'new_edges_from_exact_completion':len(full-old),'all_pairs_exactly_checked':s['all_pairs_exactly_checked'],
         'float_prefilter_used_for_final_completion':False,'screen_edges_subset_of_exact_completion':True,
         'graph_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    (a.out_dir/'GEOMETRY.json').write_text(json.dumps(geo,indent=2)+'\n'); print(json.dumps(geo,indent=2))
