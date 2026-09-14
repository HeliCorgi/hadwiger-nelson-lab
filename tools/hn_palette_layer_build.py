#!/usr/bin/env python3
"""Build coupled palette-center layers and optimize fixed-base center colors.

The base graph is assumed induced-complete. A CENTER_LIBRARY from
hn_palette_center_geometry supplies exact center points and screened base
neighborhoods. For a selected center set, this tool recomputes every
center-to-base and center-to-center unit relation exactly, so the resulting
point set is induced-complete whenever the base input is.

For each supplied proper base coloring, the center-color subproblem is solved
exactly as weighted MaxSAT: center-center unit edges are hard inequalities;
assigning center i color c costs the number of its base neighbors already using
c. The optimum gives the minimum possible number of added-edge conflicts for
that fixed base coloring. The best optimum is emitted as a seed for unrestricted
repair. Positive optimum is NOT evidence of non-5-colorability.
"""
from __future__ import annotations
import argparse,hashlib,json
from collections import Counter
from itertools import combinations
from pathlib import Path
from pysat.formula import WCNF
from pysat.examples.rc2 import RC2
from hn_exact import K2,unit_modulus
from hn_unconditional_scan import valid_coloring,write_json


def pack(x): return {'a':x.a,'b':x.b,'den':x.den}

def semantic_sha(pts,edges):
    o={'pts':[pack(p) for p in pts],'edges':[list(e) for e in sorted(edges)]}
    return hashlib.sha256(json.dumps(o,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def load_base_models(path,n,edges,seed_path=None):
    out=[];seen=set();orig=[]
    if path:
        d=json.loads(path.read_text())
        for i,c in enumerate(d.get('models',d.get('colorings',[]))):
            c=list(map(int,c)); assert valid_coloring(c,n,edges)
            t=tuple(c)
            if t not in seen: seen.add(t);out.append(c);orig.append(f'witness:{i}')
    if seed_path:
        s=seed_path.read_text().strip(); assert len(s)==n and all(ch in '01234' for ch in s)
        c=list(map(int,s)); assert valid_coloring(c,n,edges)
        t=tuple(c)
        if t not in seen:seen.add(t);out.append(c);orig.append('seed')
    assert out
    return out,orig

def choose(tag,cands,cedges):
    deg=[0]*len(cands);adj=[set() for _ in cands]
    for u,v in cedges: deg[u]+=1;deg[v]+=1;adj[u].add(v);adj[v].add(u)
    seen=set();comps=[]
    for s in range(len(cands)):
        if s in seen:continue
        stack=[s];seen.add(s);vs=[]
        while stack:
            u=stack.pop();vs.append(u)
            for v in adj[u]:
                if v not in seen:seen.add(v);stack.append(v)
        es=sum(len(adj[v]) for v in vs)//2
        comps.append((es,len(vs),set(vs)))
    largest=max(comps,key=lambda x:(x[0],x[1]))[2]
    cegis6={0,1,2,6,25,79}
    if tag in ('largest16','largest_component'): S=set(largest)
    elif tag in ('hybrid25','adaptive47'):
        S=set(largest)|cegis6
        for i in list(cegis6):S|=adj[i]
        if tag=='adaptive47':
            killers={4,5,7,9,13,15,18,20,21,36,63,65,75,127}
            assert max(killers)<len(cands)
            S|=killers
            for i in list(killers):S|=adj[i]
    elif tag=='adaptive95':
        # CEGIS extension of the validated adaptive47 escape coloring, now in
        # the top-400 library.  Includes the 18 exact rainbow killers of that
        # counterexample and every immediate center-edge partner.  This list is
        # the resulting exact closure, pinned for reproducibility.
        S={0,1,2,4,5,6,7,9,10,11,13,15,16,17,18,20,21,22,24,25,27,32,36,37,39,41,43,45,49,53,56,59,63,65,71,73,75,79,84,86,88,89,91,96,99,100,101,102,103,105,107,109,111,113,116,118,120,121,127,128,134,135,138,139,146,149,150,151,163,165,168,172,176,178,184,207,244,255,256,262,268,269,282,283,294,302,305,314,316,328,339,341,352,364,386}
        assert max(S)<len(cands) and len(S)==95
    elif tag=='nonisolated': S={i for i,d in enumerate(deg) if d>0}
    elif tag in ('all160','all'): S=set(range(len(cands)))
    else: raise ValueError(tag)
    return sorted(S),deg

def optimize_centers(base, neighborhoods, center_edges):
    m=len(neighborhoods); w=WCNF()
    def var(i,c):return i*5+c+1
    for i in range(m):
        xs=[var(i,c) for c in range(5)];w.append(xs)
        for a,b in combinations(xs,2):w.append([-a,-b])
    for i,j in center_edges:
        for c in range(5):w.append([-var(i,c),-var(j,c)])
    costs=[]
    for i,ns in enumerate(neighborhoods):
        cnt=Counter(base[v] for v in ns); row=[]
        for c in range(5):
            cost=cnt[c];row.append(cost)
            if cost:w.append([-var(i,c)],weight=cost)
        costs.append(row)
    with RC2(w,solver='g4') as rc2:
        model=rc2.compute(); opt=rc2.cost
    pos=set(x for x in model if x>0);cc=[]
    for i in range(m):
        vals=[c for c in range(5) if var(i,c) in pos];assert len(vals)==1;cc.append(vals[0])
    calc=sum(costs[i][cc[i]] for i in range(m));assert calc==opt
    assert all(cc[i]!=cc[j] for i,j in center_edges)
    return int(opt),cc,costs

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--graph',type=Path,required=True);ap.add_argument('--library',type=Path,required=True)
    ap.add_argument('--tag',choices=['largest16','largest_component','hybrid25','adaptive47','adaptive95','nonisolated','all160','all'],required=True)
    ap.add_argument('--witnesses',type=Path,default=None);ap.add_argument('--seed-coloring',type=Path,default=None)
    ap.add_argument('--out-dir',type=Path,required=True)
    a=ap.parse_args();a.out_dir.mkdir(parents=True,exist_ok=True)
    gd=json.loads(a.graph.read_text());pts=[K2(p['a'],p['b'],p['den']) for p in gd['pts']]
    edges={tuple(map(int,e)) for e in gd['edges']};n=len(pts)
    assert len(set(pts))==n and all(unit_modulus(pts[u]-pts[v]) for u,v in edges)
    ld=json.loads(a.library.read_text());cands=ld['candidates'];cedges=[tuple(e) for e in ld['center_edges']]
    selected,all_deg=choose(a.tag,cands,cedges)
    pointset=set(pts);selpts=[];neigh=[]
    for idx in selected:
        q=cands[idx]['point'];x=K2(q['a'],q['b'],q['den']);assert x not in pointset
        ns=[i for i,p in enumerate(pts) if unit_modulus(p-x)]
        assert ns==list(map(int,cands[idx]['base_neighbors']))
        selpts.append(x);neigh.append(ns)
    assert len(set(selpts))==len(selpts)
    sel_center_edges=[]
    for i,j in combinations(range(len(selpts)),2):
        if unit_modulus(selpts[i]-selpts[j]):sel_center_edges.append((i,j))
    loc={g:i for i,g in enumerate(selected)}
    expected=sorted((loc[u],loc[v]) for u,v in cedges if u in loc and v in loc)
    assert sorted(sel_center_edges)==expected
    fullpts=list(pts)+selpts;fulledges=set(edges)
    for i,ns in enumerate(neigh):
        cv=n+i
        for v in ns:fulledges.add((min(v,cv),max(v,cv)))
    for i,j in sel_center_edges:fulledges.add((n+i,n+j))
    assert all(unit_modulus(fullpts[u]-fullpts[v]) for u,v in fulledges)
    base_models,origins=load_base_models(a.witnesses,n,sorted(edges),a.seed_coloring)
    trials=[];best=None
    for c,origin in zip(base_models,origins):
        opt,cc,costs=optimize_centers(c,neigh,sel_center_edges)
        rec={'origin':origin,'fixed_base_min_conflicts':opt,'center_colors':cc};trials.append(rec)
        key=(opt,origin)
        if best is None or key<best[0]:best=(key,c,cc,costs,origin)
    _,base,cc,costs,origin=best
    seed=base+cc
    bad=[(u,v) for u,v in fulledges if seed[u]==seed[v]];assert len(bad)==best[0][0]
    outgraph={'pts':[pack(p) for p in fullpts],'edges':[list(e) for e in sorted(fulledges)],
              'construction':'coupled palette center layer '+a.tag,'selected_center_indices':selected,
              'all_saved_edges_exact_unit':True,'induced_unit_edge_completion_pending':False,
              'base_graph_induced_complete':True,'all_added_center_pairs_exactly_checked':True}
    write_json(a.out_dir/'GRAPH.json',outgraph);(a.out_dir/'SEED.txt').write_text(''.join(map(str,seed))+'\n')
    out={'tag':a.tag,'vertices':len(fullpts),'edges':len(fulledges),'base_vertices':n,'selected_centers':len(selected),
         'selected_center_indices':selected,'center_center_edges':len(sel_center_edges),
         'center_degrees':dict(Counter(sum(([i,j] for i,j in sel_center_edges),[]))),
         'center_base_incidences':sum(map(len,neigh)),'base_incidence_union':len(set().union(*map(set,neigh))) if neigh else 0,
         'semantic_pts_edges_sha256':semantic_sha(fullpts,fulledges),'base_models_tested':len(base_models),
         'best_fixed_base_min_conflicts':len(bad),'best_origin':origin,'best_center_colors':cc,
         'best_conflict_edges':[list(e) for e in bad],'trials':trials,
         'positive_fixed_base_optimum_is_evidence':False,'all_geometry_exact':True}
    write_json(a.out_dir/'BUILD_SEED.json',out)
    print(json.dumps({k:v for k,v in out.items() if k not in ('trials','best_conflict_edges','center_degrees')},indent=2))

if __name__=='__main__':main()
