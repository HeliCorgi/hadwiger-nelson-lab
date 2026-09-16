#!/usr/bin/env python3
"""Search only for LIFTABLE positive 5-colorings via a reflection quotient.

Identify corresponding source indices in the isometric copies, also respecting
actual merged vertices. This imposes EXTRA color equalities. A quotient SAT
model lifts to the original exact graph; quotient UNSAT/timeout says nothing
about ordinary five-colorability of the original graph. The quotient is not
claimed to be a geometrically realized unit-distance graph.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from hn_closed_trace_color_probe import run_case
from hn_certified_color_probe import select_pins


def write(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,indent=2)+'\n')


def build(assembly,out):
    raw=(assembly/'GRAPH.json').read_bytes();g=json.loads(raw)
    copies=json.loads((assembly/'COPY_MAPS.json').read_text())['copies']
    n=len(g['pts']);parent=list(range(n))
    assert len(copies)>=2 and len({len(cp) for cp in copies})==1
    assert all(len(set(cp))==len(cp) and all(type(v) is int and 0<=v<n for v in cp) for cp in copies)
    assert set().union(*map(set,copies))==set(range(n))
    def find(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for i in range(len(copies[0])):
        for cp in copies[1:]:parent[find(cp[i])]=find(copies[0][i])
    roots=sorted({find(i) for i in range(n)});loc={r:i for i,r in enumerate(roots)}
    projection=[loc[find(i)] for i in range(n)]
    edges=sorted({tuple(sorted((projection[a],projection[b]))) for a,b in g['edges']})
    loops=[e for e in edges if e[0]==e[1]]
    data={'source_graph_sha256':hashlib.sha256(raw).hexdigest(),'source_vertices':n,'source_edges':len(g['edges']),
        'quotient_vertices':len(roots),'quotient_edges':len(edges),'loops':loops,'projection':projection,
        'scope':'Extra same-color assumptions. Only validated SAT lifts imply anything positive about the original graph.'}
    out.mkdir(parents=True,exist_ok=True);write(out/'PROJECTION.json',data)
    if not loops:
        write(out/'QUOTIENT.json',{'pts':list(range(len(roots))),'edges':edges,
            'abstract_quotient_not_unit_distance_witness':True})
    return g,data


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--assembly',type=Path,required=True)
    ap.add_argument('--out-dir',type=Path,required=True);ap.add_argument('--seconds',type=int,default=60)
    ap.add_argument('--solvers',default='cadical195,glucose4');ap.add_argument('--proof-checker')
    a=ap.parse_args();g,data=build(a.assembly,a.out_dir);results=[];lifted=[]
    if not data['loops']:
        qp=a.out_dir/'QUOTIENT.json';q=json.loads(qp.read_text());pins=select_pins(q,5,'ordinary','')
        for solver in a.solvers.split(','):
            dest=a.out_dir/solver;r=run_case(qp,5,pins,solver,dest,a.seconds,a.proof_checker)
            results.append({'solver':solver,'status':r['status']})
            if r['status']=='SAT':
                s=(dest/'COLORING.txt').read_text().strip();assert len(s)==data['quotient_vertices']
                colors=[int(s[v]) for v in data['projection']]
                assert all(0<=c<5 for c in colors) and all(colors[u]!=colors[v] for u,v in g['edges'])
                text=''.join(map(str,colors))+'\n';(dest/'LIFTED_COLORING.txt').write_text(text)
                rel='equal' if colors[g['ports']['a']]==colors[g['ports']['b']] else 'different'
                lifted.append({'solver':solver,'sha256':hashlib.sha256(text.encode()).hexdigest(),
                    'all_original_edges_validated':True,'terminal_relation':rel})
            print(json.dumps(results[-1]),flush=True)
    result={'status':'LIFTED_FIVE_COLORING' if lifted else 'NO_LIFT_FOUND',
        'original_A_classification':'NOT_A' if lifted else 'UNKNOWN',
        'original_pair_B_classification':'NOT_FORCED_EQUAL' if any(x['terminal_relation']=='different' for x in lifted) else 'UNKNOWN',
        'source_graph_sha256':data['source_graph_sha256'],'source_vertices':data['source_vertices'],
        'source_edges':data['source_edges'],'quotient_vertices':data['quotient_vertices'],
        'quotient_edges':data['quotient_edges'],'quotient_loops':len(data['loops']),
        'results':results,'lifted':lifted,
        'negative_quotient_result_does_not_imply_original_UNSAT':True,'no_new_HN_bound':True}
    write(a.out_dir/'SUMMARY.json',result);print(json.dumps(result),flush=True)

if __name__=='__main__':main()
