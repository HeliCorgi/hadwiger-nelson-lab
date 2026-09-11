#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from itertools import combinations
from pathlib import Path
from pysat.solvers import Glucose4
from separator_interface import build,min_vertex_cut,components_without,rgs,K,P,Q,UPSTREAM_SHA

def make_cnf(nodes,E):
    ns=sorted(nodes); idx={v:i for i,v in enumerate(ns)}; cls=[]
    def X(v,c): return idx[v]*K+c+1
    for v in ns:
        lits=[X(v,c) for c in range(K)]; cls.append(lits)
        for a,b in combinations(lits,2): cls.append([-a,-b])
    for u,v in E:
        if u in idx and v in idx:
            for c in range(K): cls.append([-X(u,c),-X(v,c)])
    return ns,cls,X

def options(sol,X,S,st,v):
    base=[X(x,st[i]) for i,x in enumerate(S)]
    return [c for c in range(K) if sol.solve(assumptions=base+[X(v,c)])]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--data-dir',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    C,R,vq,E=build(a.data_dir); n=len(R); p,q=vq[P],vq[Q]; val,S=min_vertex_cut(n,E,p,q); cc=components_without(n,E,S); pc=next(x for x in cc if p in x); qc=next(x for x in cc if q in x)
    _,pcls,pX=make_cnf(set(pc)|set(S),E); _,qcls,qX=make_cnf(set(qc)|set(S),E)
    psol=Glucose4(bootstrap_with=pcls); qsol=Glucose4(bootstrap_with=qcls)
    left=[]; right=[]; both=[]
    try:
        for st in rgs(len(S)):
            key=''.join(map(str,st)); pa=[pX(x,st[i]) for i,x in enumerate(S)]; qa=[qX(x,st[i]) for i,x in enumerate(S)]
            lp=psol.solve(assumptions=pa); rq=qsol.solve(assumptions=qa)
            if lp:left.append(key)
            if rq:right.append(key)
            if lp and rq:
                po=options(psol,pX,S,st,p); qo=options(qsol,qX,S,st,q)
                both.append({'boundary_state':key,'p_colors':po,'q_colors':qo,'all_cross_pairs_equal':all(x==y for x in po for y in qo)})
    finally:
        psol.delete(); qsol.delete()
    target='012203'
    report={
      'upstream_sha':UPSTREAM_SHA,'solver':'Glucose4 independent from Cadical195 discovery','separator_qnodes':S,'separator_components':[C[R[x]] for x in S],
      'p_component_size':len(pc),'q_component_size':len(qc),'all_canonical_boundary_states':sum(1 for _ in rgs(len(S))),
      'left_extendable_count':len(left),'right_extendable_count':len(right),'intersection_count':len(both),
      'left_extendable_states':left,'right_extendable_states':right,'intersection_states':both,
      'target_state':target,'target_in_intersection':any(x['boundary_state']==target for x in both),
      'verified_unique_intersection':len(both)==1 and both[0]['boundary_state']==target,
      'verified_ports_same_singleton':len(both)==1 and both[0]['p_colors']==both[0]['q_colors'] and len(both[0]['p_colors'])==1,
      'boundary_partition_blocks':[[S[i] for i,x in enumerate(target) if x==lab] for lab in sorted(set(target))],
      'interpretation':'Each side is solved independently by Glucose4 with the six separator colors fixed to canonical restricted-growth states. Since there are no cross-edges after deleting S, global extendability is exactly intersection of the two side tables.'
    }
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2));print(json.dumps({k:report[k] for k in ['all_canonical_boundary_states','left_extendable_count','right_extendable_count','intersection_count','intersection_states','verified_unique_intersection','verified_ports_same_singleton','boundary_partition_blocks']},indent=2))
if __name__=='__main__':main()
