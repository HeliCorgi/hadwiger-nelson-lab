#!/usr/bin/env python3
"""Analyze fresh palette-center frontiers against validated escape colorings.

This is a diagnostic/selection tool only.  It matches centers from an existing
constructed graph to a larger CENTER_LIBRARY by their exact K2 coordinates,
then finds *fresh* candidate centers whose exact base neighborhoods use all five
colors in one or more supplied proper base colorings.  It also reports exact
center-center unit coupling to the existing layer and among fresh killers.

No absence of killers, low density, or repair difficulty is chromatic evidence.
"""
from __future__ import annotations
import argparse,json
from collections import Counter
from pathlib import Path


def pkey(p):
    return (tuple(p['a']),tuple(p['b']),int(p['den']))


def load_coloring(path: Path, n: int):
    s=path.read_text().strip()
    assert len(s)>=n and all(ch in '01234' for ch in s[:n])
    return [int(ch) for ch in s[:n]]


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--library',type=Path,required=True)
    ap.add_argument('--existing-graph',type=Path,required=True,
                    help='graph whose points after base_vertices are existing centers')
    ap.add_argument('--base-vertices',type=int,required=True)
    ap.add_argument('--coloring',type=Path,action='append',required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args()

    lib=json.loads(a.library.read_text())
    cands=lib['candidates']; cedges=[tuple(map(int,e)) for e in lib['center_edges']]
    m=len(cands); assert m>0
    gd=json.loads(a.existing_graph.read_text()); pts=gd['pts']
    assert 0<a.base_vertices<=len(pts)
    existing_keys={pkey(p) for p in pts[a.base_vertices:]}
    index_by_key={pkey(c['point']):i for i,c in enumerate(cands)}
    existing_indices=sorted(index_by_key[k] for k in existing_keys if k in index_by_key)
    unmatched_existing=len(existing_keys)-len(existing_indices)
    existing=set(existing_indices)

    colors=[load_coloring(p,a.base_vertices) for p in a.coloring]
    adj=[set() for _ in range(m)]
    for u,v in cedges: adj[u].add(v);adj[v].add(u)

    records=[]; killer_sets=[]
    for ci,c in enumerate(cands):
        if ci in existing: continue
        ns=list(map(int,c['base_neighbors']))
        ks=[]; sizes=[]
        for col in colors:
            z=len({col[v] for v in ns}); sizes.append(z); ks.append(z==5)
        rec={
          'index':ci,'base_degree':len(ns),'center_degree':len(adj[ci]),
          'palette_sizes':sizes,'kills':ks,'kill_count':sum(ks),
          'existing_center_neighbors':sorted(adj[ci]&existing),
          'existing_center_neighbor_count':len(adj[ci]&existing),
          'point':c['point'],
        }
        records.append(rec)
    for j in range(len(colors)):
        killer_sets.append({r['index'] for r in records if r['kills'][j]})

    primary=killer_sets[0]
    closure=set(primary)
    for i in primary: closure |= adj[i]
    new_closure=closure-existing
    induced_edges=[(u,v) for u,v in cedges if u in new_closure and v in new_closure]
    cross_edges=[(u,v) for u,v in cedges if (u in new_closure and v in existing) or (v in new_closure and u in existing)]

    seen=set(); comps=[]
    for s in new_closure:
        if s in seen: continue
        stack=[s];seen.add(s);vs=[]
        while stack:
            u=stack.pop();vs.append(u)
            for v in adj[u]&new_closure:
                if v not in seen:seen.add(v);stack.append(v)
        es=sum(len(adj[v]&new_closure) for v in vs)//2
        comps.append({'size':len(vs),'edges':es,'vertices':sorted(vs)})
    comps.sort(key=lambda z:(-z['edges'],-z['size']))

    ranked=sorted(records,key=lambda r:(-r['kill_count'],-r['existing_center_neighbor_count'],-r['center_degree'],-r['base_degree'],r['index']))
    out={
      'candidate_count':m,'base_vertices':a.base_vertices,'escape_colorings':len(colors),
      'existing_center_points':len(existing_keys),'existing_centers_matched_in_library':len(existing_indices),
      'unmatched_existing_centers':unmatched_existing,'fresh_candidates':len(records),
      'killer_counts':[len(s) for s in killer_sets],
      'killers_all_escapes':len(set.intersection(*killer_sets)) if killer_sets else 0,
      'primary_killers':sorted(primary),'primary_killer_count':len(primary),
      'primary_killers_adjacent_to_existing':sum(1 for i in primary if adj[i]&existing),
      'primary_killer_existing_cross_edges':sum(len(adj[i]&existing) for i in primary),
      'primary_one_hop_closure_new_count':len(new_closure),
      'primary_one_hop_closure_new_indices':sorted(new_closure),
      'primary_one_hop_induced_center_edges':len(induced_edges),
      'primary_one_hop_cross_edges_to_existing':len(cross_edges),
      'primary_one_hop_components':comps[:50],
      'top_fresh_candidates':ranked[:200],
      'absence_or_density_is_evidence':False,
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k not in ('primary_one_hop_components','top_fresh_candidates','primary_killers','primary_one_hop_closure_new_indices')},indent=2))
    print('top components',json.dumps(comps[:10]))
    print('top candidates',json.dumps(ranked[:20]))

if __name__=='__main__': main()
