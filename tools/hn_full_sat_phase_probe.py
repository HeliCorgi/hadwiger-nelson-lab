#!/usr/bin/env python3
"""Whole-graph 5-color SAT with an arbitrary color assignment as phase hint.

The phase assignment need not be proper.  It is never added as clauses or
assumptions; it only calls the solver's set_phases API.  SAT models are validated
on every saved exact unit edge.  UNSAT still requires the usual independent
certificate/confirmation protocol before an A claim.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from pysat.solvers import Cadical195,Glucose4
from hn_exact import K2,unit_modulus
from hn_unconditional_scan import color_cnf,valid_coloring,write_json
from hn_symmetry_sat_probe import find_triangle,extract

SOLVERS={'cadical195':Cadical195,'glucose4':Glucose4}

def load_phase(path,n):
    s=path.read_text().strip()
    if len(s)==n and all(ch in '01234' for ch in s): return [int(ch) for ch in s]
    d=json.loads(path.read_text())
    for k in ('colors','coloring'):
        if isinstance(d,dict) and k in d:
            c=list(map(int,d[k])); assert len(c)==n and all(0<=x<5 for x in c); return c
    raise ValueError('no phase coloring')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--graph',type=Path,required=True)
    ap.add_argument('--phase-coloring',type=Path,required=True)
    ap.add_argument('--solver',choices=sorted(SOLVERS),required=True)
    ap.add_argument('--out-dir',type=Path,required=True)
    a=ap.parse_args();a.out_dir.mkdir(parents=True,exist_ok=True)
    raw=a.graph.read_bytes();d=json.loads(raw)
    pts=[K2(p['a'],p['b'],p['den']) for p in d['pts']]
    edges=sorted({tuple(map(int,e)) for e in d['edges']});n=len(pts)
    assert len(set(pts))==n and all(unit_modulus(pts[u]-pts[v]) for u,v in edges)
    phase=load_phase(a.phase_coloring,n)
    phase_conflicts=sum(phase[u]==phase[v] for u,v in edges)
    tri=find_triangle(n,edges);assert tri is not None
    assumptions=[tri[0]*5+1,tri[1]*5+2,tri[2]*5+3]
    cls=SOLVERS[a.solver]
    with cls(bootstrap_with=color_cnf(n,edges)) as s:
        if hasattr(s,'set_phases'):
            s.set_phases([v*5+phase[v]+1 for v in range(n)])
        ans=s.solve(assumptions=assumptions);model=s.get_model() if ans else None
    if ans:
        colors=extract(model,n);assert valid_coloring(colors,n,edges)
        out={'status':'SAT','classification':'NOT_A','solver':a.solver,'vertices':n,'edges':len(edges),
             'graph_sha256':hashlib.sha256(raw).hexdigest(),'phase_conflicts':phase_conflicts,
             'phase_hint_only':True,'triangle':list(tri),'symmetry_assumptions_sound':True,
             'all_edges_validated':True,'colors':colors}
        (a.out_dir/'COLORING.txt').write_text(''.join(map(str,colors))+'\n')
    else:
        out={'status':'UNSAT','classification':'A_CANDIDATE_REQUIRES_CERTIFICATE','solver':a.solver,
             'vertices':n,'edges':len(edges),'graph_sha256':hashlib.sha256(raw).hexdigest(),
             'phase_conflicts':phase_conflicts,'phase_hint_only':True,'triangle':list(tri),
             'symmetry_assumptions_sound':True}
    write_json(a.out_dir/'FULL_SAT_PHASE.json',out)
    print(json.dumps({k:v for k,v in out.items() if k!='colors'},indent=2))

if __name__=='__main__':main()
