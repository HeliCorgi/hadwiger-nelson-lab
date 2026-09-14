#!/usr/bin/env python3
"""Analyze fresh centers as missing-color list constraints around a validated coloring.

The existing graph is a base graph followed by already selected palette centers.
A larger CENTER_LIBRARY may contain those centers plus fresh ones.  Centers are
matched by exact serialized K2 coordinates, not by unstable library indices.

For each fresh center x, the allowed colors under the fixed existing coloring are
  {0..4} minus colors on exact base neighbors minus colors on existing center
  neighbors.
An empty list means x alone kills this *fixed coloring*.  This is a CEGIS fact,
not evidence that the augmented graph is not 5-colorable.
"""
from __future__ import annotations
import argparse,json
from collections import Counter
from pathlib import Path


def pkey(p): return (tuple(p['a']),tuple(p['b']),int(p['den']))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--library',type=Path,required=True)
    ap.add_argument('--existing-graph',type=Path,required=True)
    ap.add_argument('--coloring',type=Path,required=True)
    ap.add_argument('--base-vertices',type=int,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args()
    lib=json.loads(a.library.read_text()); cands=lib['candidates']; edges=[tuple(map(int,e)) for e in lib['center_edges']]
    gd=json.loads(a.existing_graph.read_text()); pts=gd['pts']; nall=len(pts); n0=a.base_vertices
    assert 0<n0<=nall
    s=a.coloring.read_text().strip(); assert len(s)==nall and all(ch in '01234' for ch in s)
    col=[int(ch) for ch in s]

    bykey={pkey(c['point']):i for i,c in enumerate(cands)}
    graph_center_to_lib={gv:bykey[pkey(pts[gv])] for gv in range(n0,nall) if pkey(pts[gv]) in bykey}
    lib_to_graph={li:gv for gv,li in graph_center_to_lib.items()}
    existing=set(lib_to_graph)
    adj=[set() for _ in cands]
    for u,v in edges:adj[u].add(v);adj[v].add(u)

    recs=[];empty=[]
    for i,c in enumerate(cands):
        if i in existing:continue
        bns=list(map(int,c['base_neighbors']))
        used_base={col[v] for v in bns}
        exn=sorted(adj[i]&existing)
        used_existing={col[lib_to_graph[j]] for j in exn}
        missing_base=sorted(set(range(5))-used_base)
        allowed=sorted(set(missing_base)-used_existing)
        r={'index':i,'base_degree':len(bns),'center_degree':len(adj[i]),
           'base_palette_size':len(used_base),'missing_base':missing_base,
           'existing_center_neighbors':exn,'existing_center_neighbor_count':len(exn),
           'existing_neighbor_colors':sorted(used_existing),'allowed_colors':allowed,
           'allowed_size':len(allowed),'point':c['point']}
        recs.append(r)
        if not allowed:empty.append(i)

    emptyset=set(empty); closure=set(empty)
    for i in empty:closure|=adj[i]
    fresh_closure=closure-existing
    cross=sum(1 for u,v in edges if (u in fresh_closure and v in existing) or (v in fresh_closure and u in existing))
    induced=sum(1 for u,v in edges if u in fresh_closure and v in fresh_closure)
    hist=Counter(r['allowed_size'] for r in recs)
    ranked=sorted(recs,key=lambda r:(r['allowed_size'],-r['existing_center_neighbor_count'],-r['center_degree'],-r['base_degree'],r['index']))
    out={'candidate_count':len(cands),'base_vertices':n0,'existing_graph_vertices':nall,
         'existing_graph_centers':nall-n0,'existing_centers_matched_in_library':len(existing),
         'unmatched_existing_centers':(nall-n0)-len(existing),'fresh_candidates':len(recs),
         'fresh_allowed_size_histogram':dict(sorted(hist.items())),
         'single_center_fixed_coloring_killers':len(empty),'single_center_killer_indices':sorted(empty),
         'killer_one_hop_fresh_closure_count':len(fresh_closure),'killer_one_hop_fresh_closure_indices':sorted(fresh_closure),
         'killer_closure_induced_center_edges':induced,'killer_closure_cross_edges_to_existing':cross,
         'top_fresh_candidates':ranked[:300],
         'fixed_coloring_kill_is_global_chromatic_evidence':False}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k not in ('single_center_killer_indices','killer_one_hop_fresh_closure_indices','top_fresh_candidates')},indent=2))
    print('top candidates',json.dumps(ranked[:30]))

if __name__=='__main__':main()
