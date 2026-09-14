#!/usr/bin/env python3
"""Unbudgeted whole-graph 5-color SAT solve with sound triangle color symmetry.

SAT returns a full coloring validated on every supplied exact edge. UNSAT is the
solver's completed result; use multiple independent solvers/certificates before a
final mathematical claim.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from pysat.solvers import Cadical195,Glucose4
from hn_exact import K2,unit_modulus
from hn_unconditional_scan import color_cnf,valid_coloring,write_json
from hn_symmetry_sat_probe import find_triangle,extract

SOLVERS={'cadical195':Cadical195,'glucose4':Glucose4}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--graph',type=Path,required=True); ap.add_argument('--out-dir',type=Path,required=True); ap.add_argument('--solver',choices=sorted(SOLVERS),required=True)
    a=ap.parse_args(); a.out_dir.mkdir(parents=True,exist_ok=True)
    raw=a.graph.read_bytes(); d=json.loads(raw); pts=[K2(p['a'],p['b'],p['den']) for p in d['pts']]; edges=sorted({tuple(map(int,e)) for e in d['edges']}); n=len(pts)
    assert len(set(pts))==n and all(unit_modulus(pts[u]-pts[v]) for u,v in edges)
    tri=find_triangle(n,edges); assert tri is not None; assumptions=[tri[0]*5+1,tri[1]*5+2,tri[2]*5+3]; clauses=color_cnf(n,edges)
    cls=SOLVERS[a.solver]
    with cls(bootstrap_with=clauses) as s:
        ans=s.solve(assumptions=assumptions); model=s.get_model() if ans else None
    if ans:
        colors=extract(model,n); assert valid_coloring(colors,n,edges); out={'status':'SAT','classification':'NOT_A','solver':a.solver,'vertices':n,'edges':len(edges),'graph_sha256':hashlib.sha256(raw).hexdigest(),'triangle':list(tri),'symmetry_assumptions_sound':True,'all_edges_validated':True,'colors':colors}; (a.out_dir/'COLORING.txt').write_text(''.join(map(str,colors))+'\n')
    else:
        out={'status':'UNSAT','classification':'A_CANDIDATE_REQUIRES_CERTIFICATE','solver':a.solver,'vertices':n,'edges':len(edges),'graph_sha256':hashlib.sha256(raw).hexdigest(),'triangle':list(tri),'symmetry_assumptions_sound':True}
    write_json(a.out_dir/'FULL_SAT.json',out); print(json.dumps({k:v for k,v in out.items() if k!='colors'},indent=2))

if __name__=='__main__': main()
