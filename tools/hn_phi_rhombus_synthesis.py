#!/usr/bin/env python3
"""Finite terminal-oriented Q(zeta210) synthesis; NOT a forcing assertion.

Target endpoints 0 and phi. Copy an exact heptagon module onto each side of
0,u,phi,conj(u), where u=zeta10 and phi=u+conj(u). The module contains 0,1;
every copy map is an isometry (optionally reflected), never a rescaling.
All exact overlaps are merged and ALL unit pairs including inter-copy pairs
are computed. Equal-terminal 5-color SAT falsifies this candidate for H_phi.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from time import monotonic
from hn_cyclotomic210 import C,PHI,ONE,ORIGIN,GOLD,U,from_heptagon,unit,complete,selftest

SCHEMES={'same':(False,False,False,False),'alternating':(False,True,False,True)}

def semantic(points,edges):
    return hashlib.sha256(json.dumps({'pts':[x.pack() for x in points],'edges':edges},
                 sort_keys=True,separators=(',',':')).encode()).hexdigest()

def components(verts,adj):
    unseen=set(verts); sizes=[]
    while unseen:
        s=unseen.pop(); stack=[s]; size=0
        while stack:
            v=stack.pop(); size+=1; ns=adj[v]&unseen
            unseen.difference_update(ns); stack.extend(ns)
        sizes.append(size)
    return sorted(sizes,reverse=True)

def build(g,scheme,out):
    started=monotonic(); points=[from_heptagon(p) for p in g['pts']]
    assert len(set(points))==len(points)
    assert ORIGIN in points and ONE in points
    assert all(unit(points[u]-points[v]) for u,v in g['edges'])
    embedded_edges,embedded_audit=complete(points)
    assert embedded_edges==g['edges'], 'input edge set differs under exact embedding'
    shifts=(ORIGIN,U,GOLD,U.conjugate()); turns=(21,-21,126,84)
    copies=[]; members={}
    for ci,(shift,turn,refl) in enumerate(zip(shifts,turns,SCHEMES[scheme])):
        cp=[(p.conjugate() if refl else p).rotate(turn)+shift for p in points]
        assert len(set(cp))==len(points)
        for x in cp: members[x]=members.get(x,0)|(1<<ci)
        copies.append(cp)
    full=sorted(members,key=C.key); loc={x:i for i,x in enumerate(full)}
    inherited=set()
    for cp in copies:
        for u,v in g['edges']: inherited.add(tuple(sorted((loc[cp[u]],loc[cp[v]]))))
    edges,audit=complete(full); eset={tuple(e) for e in edges}
    assert inherited <= eset
    adj=[set() for _ in full]
    for u,v in edges: adj[u].add(v); adj[v].add(u)
    a,b=loc[ORIGIN],loc[GOLD]
    assert a!=b and (min(a,b),max(a,b)) not in eset
    assert (full[b]-full[a])==GOLD
    cpids=[[loc[x] for x in cp] for cp in copies]
    pairwise=[]
    for i in range(4):
        for j in range(i+1,4):
            overlap=sorted(set(cpids[i])&set(cpids[j]))
            pairwise.append({'copies':[i,j],'overlap_vertices':len(overlap),
                  'overlap_internal_edges':sum(v in adj[u] for ii,u in enumerate(overlap) for v in overlap[ii+1:])})
    graph={'field':'Q(zeta210)','basis_degree':48,'cyclotomic_polynomial':list(PHI),
      'pts':[p.pack() for p in full],'edges':edges,'ports':{'a':a,'b':b},'audit':audit,
      'construction':{'name':'four-sided phi rhombus','reflection_scheme':scheme,
       'side_rotations_zeta210_exponents':list(turns),'input_vertices':len(points),
       'isometries_only':True,'no_extra_color_constraints_in_graph':True}}
    out.mkdir(parents=True,exist_ok=True)
    (out/'GRAPH.json').write_text(json.dumps(graph,separators=(',',':'))+'\n')
    (out/'COPY_MAPS.json').write_text(json.dumps({'copies':cpids},separators=(',',':'))+'\n')
    report={'status':'EXACT_GEOMETRY_ONLY','target':'proper five-coloring AND equal-terminal UNSAT',
      'vertices':len(full),'edges':len(edges),'semantic_pts_edges_sha256':semantic(full,edges),
      'input_vertices':len(points),'input_edges':len(g['edges']),'embedded_input_audit':embedded_audit,
      'scheme':scheme,'port_indices':[a,b],'terminal_degrees':[len(adj[a]),len(adj[b])],
      'copy_internal_edge_union':len(inherited),'additional_unit_edges':len(eset-inherited),
      'copy_overlaps':pairwise,'components':components(range(len(full)),adj),
      'geometry_audit':audit,'coloring_classification':None,
      'elapsed_seconds':round(monotonic()-started,3)}
    (out/'GEOMETRY.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)
    return report

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--graph',type=Path,required=True)
    ap.add_argument('--scheme',choices=SCHEMES,required=True)
    ap.add_argument('--out-dir',type=Path,required=True)
    args=ap.parse_args(); selftest()
    raw=args.graph.read_bytes(); g=json.loads(raw)
    result=build(g,args.scheme,args.out_dir)
    result['input_graph_file_sha256']=hashlib.sha256(raw).hexdigest()
    (args.out_dir/'GEOMETRY.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__': main()
