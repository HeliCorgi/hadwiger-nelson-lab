#!/usr/bin/env python3
"""Exact internal-edge reflections of the sevenfold G3, with full cross edges.

Each new copy fixes both endpoints of a real unit edge. On the pinned G3,
anchors (47,125) and (125,134) each share 165 vertices with the source.
These are geometric identifications, not extra color equalities. No A/B claim
follows from overlap counts; only explicit witnesses or checked proofs count.
"""
from __future__ import annotations
import argparse,json
from collections import Counter
from pathlib import Path
from time import monotonic
from hn_cyclotomic210 import C, GOLD, ONE, unit, complete, from_heptagon
from hn_overlap_probe_common import write,digest,probe,test_small


def build(source: Path, anchors: list[tuple[int,int]], out: Path) -> dict:
    start=monotonic(); raw=source.read_bytes(); g=json.loads(raw)
    base=[from_heptagon(p) for p in g['pts']]; n=len(base)
    if len(set(base))!=n: raise ValueError('duplicate source points')
    ee=[tuple(e) for e in g['edges']]
    if len(set(ee))!=len(ee) or not all(0<=a<b<n and unit(base[a]-base[b]) for a,b in ee):
        raise ValueError('invalid source edges')
    copies=[base]; maps=[]
    for a,b in anchors:
        if not (0<=a<b<n) or (a,b) not in set(ee): raise ValueError('anchor must be a source unit edge')
        d=base[b]-base[a]; r=d*d; t=base[a]-r*base[a].conjugate()
        assert unit(r)
        cp=[r*p.conjugate()+t for p in base]
        assert cp[a]==base[a] and cp[b]==base[b] and len(set(cp))==n
        copies.append(cp); maps.append({'anchor':[a,b],'r':r.pack(),'t':t.pack(),'reflection':True})
    masks={}
    for ci,cp in enumerate(copies):
        for p in cp: masks[p]=masks.get(p,0)|(1<<ci)
    points=sorted(masks,key=C.key); loc={p:i for i,p in enumerate(points)}
    ids=[[loc[p] for p in cp] for cp in copies]
    inherited={tuple(sorted((cp[a],cp[b]))) for cp in ids for a,b in ee}
    edges,audit=complete(points); eset={tuple(e) for e in edges}
    assert inherited<=eset
    degree=Counter(v for e in ee for v in e)
    candidates=sorted(range(n),key=lambda i:(-degree[i],i))
    pair=None
    for i in candidates:
        a,b=ids[0][i],ids[1][i]
        if a!=b and tuple(sorted((a,b))) not in eset:
            pair=(a,b); source_vertex=i; break
    if pair is None: raise ValueError('no distinct nonunit corresponding terminal pair')
    a,b=pair; delta=points[a]-points[b]; norm=delta*delta.conjugate()
    assert norm!=C() and norm!=ONE
    vm=[masks[p] for p in points]
    cross=[e for e in edges if not (vm[e[0]]&vm[e[1]])]
    interior=[e for e in cross if vm[e[0]].bit_count()==1 and vm[e[1]].bit_count()==1]
    graph={'field':'Q(zeta210), embedded sevenfold source subfield','pts':[p.pack() for p in points],
        'edges':edges,'ports':{'a':a,'b':b},'target_is_phi':norm==GOLD*GOLD,
        'terminal_squared_distance':norm.pack(),'audit':audit,
        'construction':{'name':'interior-edge-reflection','source_graph_sha256':digest(raw),
            'isometries_only':True,'maps':maps,'extra_non_geometric_constraints':False}}
    out.mkdir(parents=True,exist_ok=True)
    gr=(json.dumps(graph,separators=(',',':'))+'\n').encode(); (out/'GRAPH.json').write_bytes(gr)
    write(out/'COPY_MAPS.json',{'copies':ids})
    info={'status':'EXACT_GEOMETRY_COMPLETED','anchors':anchors,'vertices':len(points),'edges':len(edges),
        'source_vertices':n,'source_edges':len(ee),'inherited_edges':len(inherited),
        'additional_edges':len(eset-inherited),'cross_copy_edges':len(cross),
        'unique_interior_cross_edges':len(interior),'unique_interior_cross_incident_vertices':len({v for e in interior for v in e}),
        'copy_overlaps':[{'copies':[i,j],'shared_vertices':len(set(ids[i])&set(ids[j]))}
            for i in range(len(ids)) for j in range(i+1,len(ids))],
        'source_graph_sha256':digest(raw),'graph_file_sha256':digest(gr),
        'terminal_indices':[a,b],'terminal_source_vertex':source_vertex,'target_is_phi':graph['target_is_phi'],
        'terminal_squared_distance':norm.pack(),'unit_distance_geometry':audit,
        'elapsed_seconds':round(monotonic()-start,3),'forcing_claim':False}
    write(out/'GEOMETRY.json',info);print(json.dumps(info),flush=True);return info


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out-dir',type=Path,required=True)
    ap.add_argument('--anchor',action='append',required=True)
    ap.add_argument('--seconds',type=int,default=45);ap.add_argument('--solvers',default='cadical195,glucose4')
    ap.add_argument('--proof-checker');ap.add_argument('--geometry-only',action='store_true')
    a=ap.parse_args();test_small()
    if a.seconds<1:ap.error('--seconds must be positive')
    anchors=[tuple(map(int,x.split(','))) for x in a.anchor]
    if any(len(x)!=2 for x in anchors):ap.error('each anchor must be i,j')
    build(a.source,anchors,a.out_dir)
    if not a.geometry_only:print(json.dumps(probe(a.out_dir,a.seconds,a.proof_checker,a.solvers.split(','))),flush=True)

if __name__=='__main__':main()
