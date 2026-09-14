#!/usr/bin/env python3
"""Geometry census for coupled palette-exhaustion centers.

Generates the same exact candidate-center language as hn_palette_center_cegis,
then studies the *center graph* instead of greedily killing one coloring at a
time.  Center-center unit edges force their missing colors to differ. Shared
base neighbors measure where several missing-color variables act on the same
base vertices.

This is geometry/diagnostic output only; it makes no chromatic claim.
"""
from __future__ import annotations
import argparse,json
from collections import Counter,deque
from itertools import combinations
from pathlib import Path
from hn_exact import K2,unit_modulus
from hn_palette_center_cegis import load_graph,load_models,unit_directions,build_candidates,pack
from hn_unconditional_scan import write_json


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--graph',type=Path,required=True)
    ap.add_argument('--witnesses',type=Path,default=None)
    ap.add_argument('--direction-vertices',type=int,default=1192)
    ap.add_argument('--candidate-count',type=int,default=400)
    ap.add_argument('--out-dir',type=Path,required=True)
    a=ap.parse_args(); a.out_dir.mkdir(parents=True,exist_ok=True)
    raw,gd,pts,edges=load_graph(a.graph); n=len(pts)
    models=load_models(a.witnesses,n,edges)
    dirs=unit_directions(pts,edges,a.direction_vertices)
    cs=build_candidates(pts,dirs,a.candidate_count,models)
    m=len(cs); cpts=[c['point'] for c in cs]; nsets=[set(c['base_neighbors']) for c in cs]

    cedges=[]; edge_records=[]; deg=[0]*m
    for i,j in combinations(range(m),2):
        if unit_modulus(cpts[i]-cpts[j]):
            cedges.append((i,j));deg[i]+=1;deg[j]+=1
            sh=sorted(nsets[i]&nsets[j])
            edge_records.append({'u':i,'v':j,'shared_base_neighbors':sh,'shared_count':len(sh)})

    # All-pair overlap census (not only unit-adjacent centers).
    overlaps=[]
    for i,j in combinations(range(m),2):
        k=len(nsets[i]&nsets[j])
        if k: overlaps.append((k,i,j))
    overlaps.sort(reverse=True)

    adj=[set() for _ in range(m)]
    for i,j in cedges: adj[i].add(j);adj[j].add(i)
    comps=[];seen=set()
    for s in range(m):
        if s in seen: continue
        q=[s];seen.add(s);vs=[]
        while q:
            u=q.pop();vs.append(u)
            for v in adj[u]:
                if v not in seen:seen.add(v);q.append(v)
        es=sum(len(adj[v]) for v in vs)//2
        comps.append({'vertices':sorted(vs),'size':len(vs),'edges':es,'max_degree':max((deg[v] for v in vs),default=0)})
    comps.sort(key=lambda z:(-z['edges'],-z['size']))

    triangles=[]
    for i in range(m):
        for j in sorted(v for v in adj[i] if v>i):
            for k in sorted(v for v in (adj[i]&adj[j]) if v>j):
                triangles.append([i,j,k])

    # Actual center-center-base triangles: each unit center edge may share up to
    # two base unit-neighbors geometrically.
    base_triangles=[]
    for r in edge_records:
        for v in r['shared_base_neighbors']:
            base_triangles.append([r['u'],r['v'],v])

    top_vertices=sorted(range(m),key=lambda i:(-deg[i],-cs[i]['exact_base_neighbors'],-(cs[i]['sample_rainbow_count'] or 0),i))[:40]
    out={
      'vertices_base':n,'edges_base':len(edges),'candidate_count':m,'direction_count':len(dirs),
      'center_center_unit_edges':len(cedges),'center_edge_degree_histogram':dict(sorted(Counter(deg).items())),
      'max_center_degree':max(deg,default=0),'center_components':comps[:20],
      'center_triangles':triangles[:500],'center_triangle_count':len(triangles),
      'center_center_base_triangle_count':len(base_triangles),'center_center_base_triangles':base_triangles[:1000],
      'top_unit_edges_by_shared_neighbors':sorted(edge_records,key=lambda r:(-r['shared_count'],r['u'],r['v']))[:200],
      'max_any_pair_shared_base_neighbors':overlaps[0][0] if overlaps else 0,
      'top_any_pair_overlaps':[{'shared_count':k,'u':i,'v':j,'unit_center_edge':j in adj[i],'shared_base_neighbors':sorted(nsets[i]&nsets[j])} for k,i,j in overlaps[:200]],
      'top_center_vertices':[{'index':i,'center_degree':deg[i],'base_degree':cs[i]['exact_base_neighbors'],'sample_min_colors':cs[i]['sample_min_colors'],'sample_rainbow_count':cs[i]['sample_rainbow_count'],'point':pack(cpts[i])} for i in top_vertices],
      'all_center_edges_exact_unit':True,'all_base_neighbor_sets_exact':True,'classification':None,
    }
    write_json(a.out_dir/'CENTER_GEOMETRY.json',out)
    write_json(a.out_dir/'CENTER_LIBRARY.json',{'candidates':[{**{k:(pack(v) if k=='point' else v) for k,v in c.items()},'center_degree':deg[i]} for i,c in enumerate(cs)],'center_edges':[list(e) for e in cedges]})
    print(json.dumps({k:v for k,v in out.items() if k not in ('center_components','center_triangles','center_center_base_triangles','top_unit_edges_by_shared_neighbors','top_any_pair_overlaps','top_center_vertices')},indent=2))
    print('top components',json.dumps(comps[:5]))
    print('top shared unit edges',json.dumps(out['top_unit_edges_by_shared_neighbors'][:10]))

if __name__=='__main__': main()
