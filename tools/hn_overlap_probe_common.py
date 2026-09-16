#!/usr/bin/env python3
"""Bounded exact-graph color probes; SAT witnesses are checked on every edge.

Negative claims require DRAT verification. Timeout and UNKNOWN never imply
forcing. A candidate remains unpromoted until independent geometry checking.
"""
from __future__ import annotations
import hashlib,json
from pathlib import Path
from hn_cyclotomic210 import selftest


def write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def test_small():
    return selftest()


def probe(out: Path, seconds: int, checker: str | None, solvers: list[str]) -> dict:
    from hn_certified_color_probe import run_case, select_pins
    graph = out/'GRAPH.json'
    g = json.loads(graph.read_text())
    results = []
    for solver in solvers:
        for k, relation in ((5,'ordinary'), (5,'equal'), (5,'different'), (6,'ordinary')):
            pins = select_pins(g,k,relation,'a,b')
            target = out/'probes'/solver/f'{k}-{relation}'
            r = run_case(graph,k,pins,solver,target,seconds,checker)
            results.append({'solver':solver, 'colors':k, 'relation':relation,
                            'status':r['status'], 'result_path':str(target.relative_to(out)/'RESULT.json')})
            if r['status'] == 'SAT':
                (target/'INPUT.cnf').unlink(missing_ok=True)
            print(json.dumps(results[-1]), flush=True)
    def has(k, rel, status):
        return any(r['colors']==k and r['relation']==rel and r['status']==status for r in results)
    def sat5():
        return any(r['colors']==5 and r['status']=='SAT' for r in results)
    bad = []
    for k,rel in ((5,'ordinary'),(5,'equal'),(5,'different'),(6,'ordinary')):
        if has(k,rel,'SAT') and has(k,rel,'UNSAT_PROOF_VERIFIED'):
            bad.append([k,rel])
    if (has(5,'ordinary','UNSAT_PROOF_VERIFIED') or has(6,'ordinary','UNSAT_PROOF_VERIFIED')) and sat5():
        bad.append(['ordinary versus pinned five-coloring'])
    result = {'status':'BOUNDED_PROBES_COMPLETE', 'results':results,
        'A':'NOT_A' if sat5() else ('CANDIDATE_REQUIRES_INDEPENDENT_GEOMETRY' if has(5,'ordinary','UNSAT_PROOF_VERIFIED') else 'UNKNOWN'),
        'H_phi':('NOT_APPLICABLE' if not g.get('target_is_phi',True) else ('NOT_H_PHI' if has(5,'equal','SAT') else ('CANDIDATE_REQUIRES_INDEPENDENT_GEOMETRY' if sat5() and has(5,'equal','UNSAT_PROOF_VERIFIED') else 'UNKNOWN'))),
        'specified_pair_B':'NOT_FORCED_EQUAL' if has(5,'different','SAT') else ('CANDIDATE_REQUIRES_INDEPENDENT_GEOMETRY' if sat5() and has(5,'different','UNSAT_PROOF_VERIFIED') else 'UNKNOWN'),
        'six_color_witness':has(6,'ordinary','SAT'),
        'scope':'Only these exact finite graphs and these two actual terminals. No upper bound on the entire plane.',
        'unknown_is_evidence':False, 'contradictory_results':bad}
    if bad:
        result['status']='ERROR_CONTRADICTORY_RESULTS'
        result['A']=result['H_phi']=result['specified_pair_B']='INVALID'
    write(out/'SUMMARY.json',result)
    if bad:
        raise RuntimeError('inconsistent solver results')
    return result
