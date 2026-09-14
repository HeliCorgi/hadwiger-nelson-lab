#!/usr/bin/env python3
"""Core-guided repair of a near proper 5-coloring.

The full exact graph CNF is loaded once. Initially every vertex except endpoints of
seed-conflict edges is pinned to its seed color using assumptions. On each UNSAT,
CaDiCaL's assumption core identifies a subset of pins sufficient for the current
incompatibility; all vertices in that core are released. This monotonically relaxes
only boundary pins implicated by actual SAT reasoning.

SAT is expanded and validated on every graph edge. UNKNOWN is non-evidence. If an
UNSAT solve ever has no assumptions left, that is a whole-graph UNSAT candidate and
requires independent confirmation/certificate before final promotion.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from pysat.solvers import Cadical195
from hn_exact import K2,unit_modulus
from hn_unconditional_scan import color_cnf,valid_coloring,write_json
from hn_lns_sat_repair import load_coloring


def extract(model,n):
    pos={x for x in model if x>0}
    return [next(c for c in range(5) if v*5+c+1 in pos) for v in range(n)]


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--graph',type=Path,required=True); ap.add_argument('--seed-coloring',type=Path,required=True)
    ap.add_argument('--out-dir',type=Path,required=True); ap.add_argument('--rounds',type=int,default=30)
    ap.add_argument('--conflicts',type=int,default=8_000_000)
    a=ap.parse_args(); a.out_dir.mkdir(parents=True,exist_ok=True)
    d=json.loads(a.graph.read_text()); pts=[K2(p['a'],p['b'],p['den']) for p in d['pts']]
    edges=sorted({tuple(map(int,e)) for e in d['edges']}); n=len(pts)
    assert len(set(pts))==n and all(unit_modulus(pts[u]-pts[v]) for u,v in edges)
    seed=load_coloring(a.seed_coloring,n); bad=[(u,v) for u,v in edges if seed[u]==seed[v]]
    free={x for e in bad for x in e}; fixed=set(range(n))-free
    clauses=color_cnf(n,edges); records=[]; result=None; whole_unsat=False
    with Cadical195(bootstrap_with=clauses) as s:
        s.set_phases([v*5+seed[v]+1 for v in range(n)])
        for rnd in range(a.rounds):
            assumptions=[v*5+seed[v]+1 for v in sorted(fixed)]
            s.conf_budget(a.conflicts)
            ans=s.solve_limited(assumptions=assumptions)
            rec={'round':rnd,'free_vertices':len(free),'fixed_vertices':len(fixed),
                 'status':'SAT' if ans is True else 'UNSAT' if ans is False else 'UNKNOWN'}
            if ans is True:
                colors=extract(s.get_model(),n); assert valid_coloring(colors,n,edges)
                result=colors; records.append(rec); break
            if ans is None:
                records.append(rec); break
            core=s.get_core() or []
            core_vertices=sorted({(abs(lit)-1)//5 for lit in core})
            rec['core_literals']=len(core); rec['core_vertices']=len(core_vertices)
            records.append(rec); print(json.dumps(rec),flush=True)
            if not assumptions:
                whole_unsat=True; break
            if not core_vertices:
                # UNSAT independent of the current pins means the base CNF itself is UNSAT.
                whole_unsat=True; break
            before=len(fixed); fixed.difference_update(core_vertices); free.update(core_vertices)
            assert len(fixed)<before
    if result is not None:
        out={'status':'SAT','classification':'NOT_A','vertices':n,'edges':len(edges),
             'seed_conflicts':len(bad),'initial_free_vertices':len({x for e in bad for x in e}),
             'final_free_vertices':len(free),'records':records,'all_edges_validated':True,'colors':result}
        (a.out_dir/'COLORING.txt').write_text(''.join(map(str,result))+'\n')
    elif whole_unsat:
        out={'status':'WHOLE_GRAPH_UNSAT_CANDIDATE','classification':'A_CANDIDATE_REQUIRES_INDEPENDENT_CONFIRMATION',
             'vertices':n,'edges':len(edges),'seed_conflicts':len(bad),'final_free_vertices':len(free),
             'records':records,'single_solver_unsat_requires_certificate':True}
    else:
        out={'status':'UNKNOWN','classification':None,'vertices':n,'edges':len(edges),'seed_conflicts':len(bad),
             'final_free_vertices':len(free),'records':records,'timeout_or_unknown_is_evidence':False}
    write_json(a.out_dir/'CORE_GUIDED.json',out)
    print(json.dumps({k:v for k,v in out.items() if k not in ('colors','records')},indent=2))

if __name__=='__main__': main()
