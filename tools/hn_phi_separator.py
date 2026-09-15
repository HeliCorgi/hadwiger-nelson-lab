#!/usr/bin/env python3
"""Certify the four-terminal separation, then join concrete SAT witnesses.

Extraction uses a parent whose complete unit graph was computed exactly.
Every parent edge must belong to a side; sides intersect in exactly the four
named rhombus vertices. Joining validates every parent edge, not just ports.
Nonexistence of a witness is never converted to full-graph UNSAT here.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from hn_cyclotomic210 import C,ORIGIN,U,GOLD

PORTS=('a','u','b','v')

def dump(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2)+'\n')

def extract(assembly,out):
    graph=json.loads((assembly/'GRAPH.json').read_text())
    copies=json.loads((assembly/'COPY_MAPS.json').read_text())['copies']
    assert graph['audit']['induced_complete'] is True
    sets=[set(c) for c in copies]
    left=sets[0]|sets[2];right=sets[1]|sets[3]
    loc={C.unpack(p):i for i,p in enumerate(graph['pts'])}
    ports=[loc[x] for x in (ORIGIN,U,GOLD,U.conjugate())]
    assert left&right==set(ports)
    assert left|right==set(range(len(graph['pts'])))
    assert all((u in left and v in left) or (u in right and v in right) for u,v in graph['edges'])
    meta={}
    for name,vs in [('long',left),('short',right)]:
        vs=sorted(vs);index={v:i for i,v in enumerate(vs)}
        edges=[[index[u],index[v]] for u,v in graph['edges'] if u in index and v in index]
        g={'field':graph['field'],'basis_degree':48,'cyclotomic_polynomial':graph['cyclotomic_polynomial'],
           'pts':[graph['pts'][v] for v in vs],'edges':edges,
           'ports':{key:index[v] for key,v in zip(PORTS,ports)},
           'audit':{'induced_complete':True,'scope':'Induced subset of exactly completed parent',
                    'parent_graph_sha256':hashlib.sha256((assembly/'GRAPH.json').read_bytes()).hexdigest()},
           'parent_indices':vs}
        dump(out/(name+'.json'),g)
        ppos={g['ports'][key]:i for i,key in enumerate(PORTS)}
        pe=sorted([sorted([ppos[u],ppos[v]]) for u,v in edges if u in ppos and v in ppos])
        assert pe==[[0,1],[0,3],[1,2],[2,3]]
        meta[name]={'vertices':len(vs),'edges':len(edges),'port_edges':pe}
    report={'status':'EXACT_FOUR_VERTEX_SEPARATOR','ports':dict(zip(PORTS,ports)),
            'intersection_vertices':4,'all_parent_edges_covered':True,'sides':meta}
    dump(out/'SEPARATOR.json',report)
    print(json.dumps(report),flush=True)

def witness(relations,state_index,graph):
    for path in relations:
        if not path.exists(): continue
        d=json.loads(path.read_text())
        rec=next((r for r in d['records'] if r['index']==state_index),None)
        if rec is None or rec['status']!='SAT': continue
        txt=(path.parent/('state-%03d'%state_index)/'COLORING.txt').read_text()
        c=[int(x) for x in txt.strip()]
        assert len(c)==len(graph['pts']) and all(0<=x<5 for x in c)
        assert all(c[u]!=c[v] for u,v in graph['edges'])
        assert all(c[graph['ports'][key]]==p for key,p in zip(PORTS,rec['partition']))
        return c,rec['partition'],str(path)
    return None

def join(assembly,sides,long_rel,short_rel,out):
    parent=json.loads((assembly/'GRAPH.json').read_text())
    l=json.loads((sides/'long.json').read_text());r=json.loads((sides/'short.json').read_text())
    records=[]
    for i in range(15):
        a=witness(long_rel,i,l);b=witness(short_rel,i,r)
        if a is None or b is None: continue
        assert a[1]==b[1]
        c=[None]*len(parent['pts'])
        for g,src in ((l,a[0]),(r,b[0])):
            for j,v in enumerate(g['parent_indices']):
                if c[v] is not None: assert c[v]==src[j]
                c[v]=src[j]
        assert all(isinstance(x,int) and 0<=x<5 for x in c)
        assert all(c[u]!=c[v] for u,v in parent['edges'])
        text=''.join(map(str,c))+'\n'
        out.mkdir(parents=True,exist_ok=True)
        (out/('state-%03d-COLORING.txt'%i)).write_text(text)
        records.append({'index':i,'partition':a[1],'all_parent_edges_validated':True,
          'sources':[a[2],b[2]],'coloring_sha256':hashlib.sha256(text.encode()).hexdigest()})
    equal=any(x['partition'][0]==x['partition'][2] for x in records)
    different=any(x['partition'][0]!=x['partition'][2] for x in records)
    report={'vertices':len(parent['pts']),'edges':len(parent['edges']),
      'status':'SAT_WITNESSES_JOINED' if records else 'NO_JOINED_WITNESS_YET',
      'classification_A':'NOT_A' if records else None,
      'classification_H_phi':'NOT_H_PHI' if equal else None,
      'specified_pair_B':'NOT_FORCED_EQUAL' if different else None,
      'both_phi_terminal_relations_witnessed':equal and different,
      'all_four_locally_admissible_boundary_states_witnessed':len(records)==4,
      'records':records,'missing_state_is_unsat_evidence':False,
      'parent_graph_sha256':hashlib.sha256((assembly/'GRAPH.json').read_bytes()).hexdigest()}
    dump(out/'JOIN.json',report);print(json.dumps(report),flush=True)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['extract','join'])
    ap.add_argument('--assembly',type=Path,required=True);ap.add_argument('--out-dir',type=Path,required=True)
    ap.add_argument('--sides',type=Path);ap.add_argument('--long-relations',type=Path,nargs='*',default=[])
    ap.add_argument('--short-relations',type=Path,nargs='*',default=[])
    a=ap.parse_args()
    if a.action=='extract':extract(a.assembly,a.out_dir)
    else:
        if a.sides is None:ap.error('--sides required for join')
        join(a.assembly,a.sides,a.long_relations,a.short_relations,a.out_dir)

if __name__=='__main__':main()
