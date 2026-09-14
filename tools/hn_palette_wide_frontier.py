#!/usr/bin/env python3
"""Build a wide counterexample-targeted palette frontier.

The bounded candidate language is p+d for every base vertex p and every exact
unit direction d obtained from an initial direction prefix.  For one validated
proper 5-coloring, retain all fresh candidates whose known p+d incidences:
  * already see all five colors (direct killers), or
  * see exactly four colors and participate in an exact unit edge to another
    fresh candidate forced to the same missing color.

All retained points are then exact-completed against the entire current graph
and against one another.  This kills only the supplied coloring; repair failure
or solver difficulty is not evidence of non-5-colorability.
"""
from __future__ import annotations
import argparse, hashlib, json
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

from hn_exact import K2, unit_modulus
from hn_palette_center_cegis import neg, pack, semantic_sha
from hn_unconditional_scan import valid_coloring, write_json


def load_graph(path):
    d=json.loads(Path(path).read_text())
    pts=[K2(p['a'],p['b'],p['den']) for p in d['pts']]
    edges=sorted({tuple(map(int,e)) for e in d['edges']})
    assert len(set(pts))==len(pts)
    assert all(unit_modulus(pts[u]-pts[v]) for u,v in edges)
    return d,pts,edges


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--graph',type=Path,required=True); ap.add_argument('--coloring',type=Path,required=True)
    ap.add_argument('--base-vertices',type=int,required=True); ap.add_argument('--direction-vertices',type=int,required=True)
    ap.add_argument('--out-dir',type=Path,required=True)
    a=ap.parse_args(); a.out_dir.mkdir(parents=True,exist_ok=True)
    gd,pts,edges=load_graph(a.graph); n=len(pts); n0=a.base_vertices
    s=a.coloring.read_text().strip(); assert len(s)==n and all(ch in '01234' for ch in s)
    colors=list(map(int,s)); assert valid_coloring(colors,n,edges)

    dirs=set()
    for u,v in edges:
        if u<a.direction_vertices and v<a.direction_vertices:
            d=pts[v]-pts[u]; dirs.add(d); dirs.add(neg(d))
    assert dirs and all(unit_modulus(d) for d in dirs)

    pointset=set(pts); masks={}
    for i,p in enumerate(pts[:n0]):
        bit=1<<colors[i]
        for d in dirs:
            x=p+d
            if x in pointset: continue
            masks[x]=masks.get(x,0)|bit
    hist=Counter(m.bit_count() for m in masks.values())
    direct=[]; forced=defaultdict(list)
    for x,m in masks.items():
        k=m.bit_count()
        if k==5: direct.append(x)
        elif k==4:
            miss=next(c for c in range(5) if not ((m>>c)&1))
            forced[miss].append(x)

    conflict_edges=[]; conflict_nodes=set()
    for c,xs in forced.items():
        for i,j in combinations(range(len(xs)),2):
            if unit_modulus(xs[i]-xs[j]):
                x,y=xs[i],xs[j]; conflict_edges.append((c,x,y)); conflict_nodes.add(x); conflict_nodes.add(y)

    selected=[]; kinds={}
    for x in direct:
        selected.append(x); kinds[x]='direct_killer'
    for x in conflict_nodes:
        if x not in kinds: selected.append(x); kinds[x]='forced_conflict_endpoint'
    assert selected
    del masks, forced

    fullpts=list(pts)+selected; fulledges=set(edges); exact_neigh=[]
    for i,x in enumerate(selected):
        vi=n+i; ns=[]
        for j,p in enumerate(pts):
            if unit_modulus(x-p): ns.append(j); fulledges.add((j,vi))
        exact_neigh.append(ns)
    sel_edges=[]
    for i,j in combinations(range(len(selected)),2):
        if unit_modulus(selected[i]-selected[j]):
            sel_edges.append((i,j)); fulledges.add((n+i,n+j))

    # Fixed-current-color seed: choose a locally minimum-conflict color for each
    # new center, then coordinate-descent including new-new edges.
    m=len(selected); cc=[]
    base_cost=[]
    for ns in exact_neigh:
        cnt=Counter(colors[v] for v in ns); row=[cnt[c] for c in range(5)]; base_cost.append(row)
        cc.append(min(range(5),key=lambda c:(row[c],c)))
    sadj=[[] for _ in range(m)]
    for i,j in sel_edges: sadj[i].append(j); sadj[j].append(i)
    for _ in range(30):
        changed=0
        for i in range(m):
            vals=[]
            for c in range(5): vals.append(base_cost[i][c]+sum(cc[j]==c for j in sadj[i]))
            best=min(range(5),key=lambda c:(vals[c],c))
            if best!=cc[i]: cc[i]=best; changed+=1
        if not changed: break
    seed=colors+cc
    bad=[(u,v) for u,v in fulledges if seed[u]==seed[v]]
    assert bad

    outgraph={'pts':[pack(p) for p in fullpts],'edges':[list(e) for e in sorted(fulledges)],
      'construction':'wide counterexample-targeted palette frontier',
      'base_graph_induced_complete':bool(gd.get('induced_unit_edge_completion_pending') is False),
      'all_added_center_pairs_exactly_checked':True,'induced_unit_edge_completion_pending':False,
      'all_saved_edges_exact_unit':True}
    write_json(a.out_dir/'GRAPH.json',outgraph); (a.out_dir/'SEED.txt').write_text(''.join(map(str,seed))+'\n')
    loc={x:i for i,x in enumerate(selected)}
    out={'status':'BUILT_WIDE_FRONTIER','classification':None,'input_vertices':n,'input_edges':len(edges),
      'base_vertices':n0,'direction_vertices':a.direction_vertices,'unit_direction_count':len(dirs),
      'fresh_candidate_count':sum(hist.values()),'known_color_count_histogram':dict(sorted(hist.items())),
      'fresh_direct_killers':len(direct),'fresh_forced_conflict_edges':len(conflict_edges),
      'fresh_forced_conflict_endpoints':len(conflict_nodes),'selected_fresh_centers':m,
      'selected_internal_edges':len(sel_edges),'vertices':len(fullpts),'edges':len(fulledges),
      'seed_conflicts':len(bad),'semantic_pts_edges_sha256':semantic_sha(fullpts,fulledges),
      'all_added_center_relations_exactly_checked':True,'repair_failure_is_evidence':False,
      'conflict_edges':[{'forced_color':c,'u_local':loc[x],'v_local':loc[y]} for c,x,y in conflict_edges]}
    write_json(a.out_dir/'WIDE_FRONTIER.json',out)
    print(json.dumps({k:v for k,v in out.items() if k!='conflict_edges'},indent=2))

if __name__=='__main__': main()
