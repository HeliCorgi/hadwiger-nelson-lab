#!/usr/bin/env python3
"""Enumerate terminal relations modulo color permutations, not sampled models.

A locally inconsistent state has an explicit monochromatic terminal-edge
certificate. Otherwise SAT models are saved and verified on the whole graph.
Only a checked UNSAT proof excludes a nonlocal state; UNKNOWN, timeout, unchecked
UNSAT and tool errors remain ALLOWED in the conservative boundary relation.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
from time import monotonic
from hn_certified_color_probe import run_case, write


def partitions(n,k):
    def rec(xs):
        if len(xs)==n:
            yield xs; return
        for c in range(min(k,max(xs)+2)):
            yield from rec(xs+[c])
    if n==0: yield []
    else: yield from rec([0])


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--graph',type=Path,required=True)
    ap.add_argument('--ports',required=True); ap.add_argument('--colors',type=int,default=5)
    ap.add_argument('--solver',default='cadical195'); ap.add_argument('--seconds',type=int,default=20)
    ap.add_argument('--total-seconds',type=int,default=600); ap.add_argument('--proof-checker',default=None)
    ap.add_argument('--out-dir',type=Path,required=True); a=ap.parse_args()
    a.out_dir.mkdir(parents=True,exist_ok=True); g=json.loads(a.graph.read_text())
    names=a.ports.split(','); ports=[g['ports'][name] for name in names]
    if len(set(ports))!=len(ports): raise ValueError('ports must be distinct')
    loc={v:i for i,v in enumerate(ports)}
    pe=[(loc[u],loc[v]) for u,v in g['edges'] if u in loc and v in loc]
    states=list(partitions(len(ports),a.colors)); records=[]; start=monotonic()
    for i,state in enumerate(states):
        bad=next(((u,v) for u,v in pe if state[u]==state[v]),None)
        if bad is not None:
            r={'status':'LOCAL_EDGE_EXCLUDED','edge_port_indices':list(bad)}
        elif monotonic()-start>=a.total_seconds:
            r={'status':'UNKNOWN_TOTAL_BUDGET','conservatively_allowed':True}
        else:
            sec=max(1,min(a.seconds,int(a.total_seconds-(monotonic()-start))))
            r=run_case(a.graph,a.colors,list(zip(ports,state)),a.solver,
                       a.out_dir/('state-%03d'%i),sec,a.proof_checker)
            r={k:v for k,v in r.items() if k in ('status','elapsed_seconds','cnf_sha256','proof_sha256','all_edges_and_pins_validated')}
        excluded=r['status'] in ('LOCAL_EDGE_EXCLUDED','UNSAT_PROOF_VERIFIED')
        records.append({'index':i,'partition':state,'excluded':excluded,**r})
        write(a.out_dir/'ACTIVE.json',{'records':records})
        if bad is None: print(json.dumps(records[-1]),flush=True)
    local=sum(r['status']=='LOCAL_EDGE_EXCLUDED' for r in records)
    sat=sum(r['status']=='SAT' for r in records)
    nonlocal_unsat=sum(r['status']=='UNSAT_PROOF_VERIFIED' for r in records)
    unknown=len(states)-local-sat-nonlocal_unsat
    out={'vertices':len(g['pts']),'edges':len(g['edges']),'color_count':a.colors,
         'ports':dict(zip(names,ports)),'partitions':len(states),'local_edge_exclusions':local,
         'verified_sat_states':sat,'verified_nonlocal_exclusions':nonlocal_unsat,
         'unknown_or_unchecked_states':unknown,'relation_complete':unknown==0,
         'no_extra_relation_on_these_ports':unknown==0 and nonlocal_unsat==0,
         'conservative_allowed_partitions':[r['partition'] for r in records if not r['excluded']],
         'scope':'Only this graph and selected terminals, modulo global color permutations.',
         'records':records}
    write(a.out_dir/'RELATION.json',out)
    print(json.dumps({k:v for k,v in out.items() if k not in ('records','conservative_allowed_partitions')},indent=2))

if __name__=='__main__': main()
