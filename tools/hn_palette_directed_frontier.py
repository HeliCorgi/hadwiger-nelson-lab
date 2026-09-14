#!/usr/bin/env python3
"""Counterexample-directed palette-center scan over the full p+d language.

Unlike top-K center censuses, this scans every point p plus every exact unit
direction d from the chosen direction dictionary.  For a validated base
5-coloring, the generating incidences are themselves certified unit edges.  If
those known incidences already contain all five colors, x=p+d is guaranteed to
kill that fixed coloring, even before discovering any additional unit neighbors.

A bounded pool of such guaranteed killers is then scored by exact unit coupling
to the existing palette centers and to other killers.  Selected fresh centers
are exact-completed against every base vertex, and a combined CENTER_LIBRARY
(existing centers + fresh centers) is emitted with all center-center pairs
checked exactly.

This is CEGIS selection only.  Killing one coloring is never global chromatic
evidence.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from hn_exact import K2,unit_modulus
from hn_palette_center_cegis import load_graph,unit_directions,pack
from hn_unconditional_scan import valid_coloring,write_json


def load_col(path,n,edges):
    s=path.read_text().strip(); assert len(s)>=n and all(ch in '01234' for ch in s[:n])
    c=[int(ch) for ch in s[:n]]; assert valid_coloring(c,n,edges); return c


def load_pts(d): return [K2(p['a'],p['b'],p['den']) for p in d['pts']]


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--base-graph',type=Path,required=True)
    ap.add_argument('--existing-graph',type=Path,required=True)
    ap.add_argument('--coloring',type=Path,required=True)
    ap.add_argument('--direction-vertices',type=int,default=1192)
    ap.add_argument('--pool-limit',type=int,default=1200)
    ap.add_argument('--select-count',type=int,default=160)
    ap.add_argument('--out-dir',type=Path,required=True)
    a=ap.parse_args();a.out_dir.mkdir(parents=True,exist_ok=True)

    _,gd,bpts,bedges=load_graph(a.base_graph);n0=len(bpts);col=load_col(a.coloring,n0,bedges)
    exd=json.loads(a.existing_graph.read_text()); epts=load_pts(exd);eedges={tuple(map(int,e)) for e in exd['edges']}
    assert epts[:n0]==bpts and len(epts)>n0
    existing_centers=epts[n0:]; all_existing=set(epts)
    assert all(unit_modulus(epts[u]-epts[v]) for u,v in eedges)

    dirs=unit_directions(bpts,bedges,a.direction_vertices)
    # x -> [known-color-mask, known-neighbor-count]
    state={}
    bset=set(bpts)
    for i,p in enumerate(bpts):
        bit=1<<col[i]
        for d in dirs:
            x=p+d
            if x in bset: continue
            z=state.get(x)
            if z is None: state[x]=[bit,1]
            else: z[0]|=bit; z[1]+=1

    killers=[(cnt,x) for x,(mask,cnt) in state.items() if mask==31 and x not in all_existing]
    killers.sort(key=lambda z:(-z[0],z[1].den,tuple(z[1].a),tuple(z[1].b)))
    pool=killers[:a.pool_limit]
    ppts=[x for _,x in pool]; support=[cnt for cnt,_ in pool]

    crossdeg=[]
    for x in ppts:
        crossdeg.append(sum(1 for q in existing_centers if unit_modulus(x-q)))
    padj=[set() for _ in ppts]
    for i in range(len(ppts)):
        for j in range(i+1,len(ppts)):
            if unit_modulus(ppts[i]-ppts[j]):padj[i].add(j);padj[j].add(i)
    order=sorted(range(len(ppts)),key=lambda i:(-(crossdeg[i]+len(padj[i])),-crossdeg[i],-len(padj[i]),-support[i],i))
    take=order[:min(a.select_count,len(order))]
    fresh=[ppts[i] for i in take]

    # Exact-complete selected fresh centers to every base vertex and validate
    # the counterexample-killing property with the full exact neighborhood.
    fresh_ns=[]
    for x in fresh:
        ns=[i for i,p in enumerate(bpts) if unit_modulus(p-x)]
        assert len({col[v] for v in ns})==5
        fresh_ns.append(ns)

    # Recover exact base neighborhoods of existing centers from the already
    # completed existing graph, and cross-check every saved incidence.
    ex_ns=[[] for _ in existing_centers]
    for u,v in eedges:
        if u<n0<=v: ex_ns[v-n0].append(u)
        elif v<n0<=u: ex_ns[u-n0].append(v)
    for j,x in enumerate(existing_centers):
        ex_ns[j].sort()
        exact=[i for i,p in enumerate(bpts) if unit_modulus(p-x)]
        assert exact==ex_ns[j]

    cpts=existing_centers+fresh; neigh=ex_ns+fresh_ns
    cedges=[];deg=[0]*len(cpts)
    for i in range(len(cpts)):
        for j in range(i+1,len(cpts)):
            if unit_modulus(cpts[i]-cpts[j]):cedges.append((i,j));deg[i]+=1;deg[j]+=1

    candidates=[]
    for i,(x,ns) in enumerate(zip(cpts,neigh)):
        candidates.append({'point':pack(x),'base_neighbors':ns,'exact_base_neighbors':len(ns),
                           'known_direction_neighbors':None,'sample_min_colors':None,'sample_rainbow_count':None,
                           'sample_histogram':{},'center_degree':deg[i],
                           'source':'existing' if i<len(existing_centers) else 'fresh_escape_directed'})
    write_json(a.out_dir/'CENTER_LIBRARY.json',{'candidates':candidates,'center_edges':[list(e) for e in cedges]})

    selected_records=[]
    for rank,i in enumerate(take):
        selected_records.append({'rank':rank,'pool_index':i,'known_support':support[i],
                                 'existing_center_unit_neighbors':crossdeg[i],
                                 'pool_center_degree':len(padj[i]),'point':pack(ppts[i]),
                                 'exact_base_degree':len(fresh_ns[rank])})
    out={'base_vertices':n0,'direction_count':len(dirs),'raw_distinct_generated_candidates':len(state),
         'guaranteed_five_color_killers_outside_existing_graph':len(killers),
         'pool_limit':a.pool_limit,'pool_size':len(pool),'selected_fresh_centers':len(fresh),
         'existing_centers':len(existing_centers),'combined_centers':len(cpts),
         'combined_center_edges':len(cedges),
         'fresh_to_existing_center_edges':sum(1 for u,v in cedges if (u<len(existing_centers))!=(v<len(existing_centers))),
         'fresh_fresh_center_edges':sum(1 for u,v in cedges if u>=len(existing_centers) and v>=len(existing_centers)),
         'selected':selected_records,'all_selected_full_neighborhoods_exact':True,
         'all_combined_center_pairs_exactly_checked':True,'fixed_coloring_kill_is_global_evidence':False}
    write_json(a.out_dir/'DIRECTED_FRONTIER.json',out)
    print(json.dumps({k:v for k,v in out.items() if k!='selected'},indent=2))
    print('top selected',json.dumps(selected_records[:30]))

if __name__=='__main__':main()
