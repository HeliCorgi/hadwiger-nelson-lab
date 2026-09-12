#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path

from pysat.solvers import Cadical195, Glucose4

from separator_interface import P,Q,UPSTREAM_SHA,build,components_without,min_vertex_cut,rgs

K=5
OUTER=[0,6,8,9,10,266]
Q0Q10=[14,18,54,55,256]
SEP=[23,35,57,86,159]
TARGET=(18,256)
FORBIDDEN=(0,1,2,3,2)  # 01232
VALID_CONTROL=(0,1,2,3,1) # 01231
COMMON_NEQ=[(0,2),(0,3),(0,4),(2,3),(3,4)]


def activation_cnf(nodes,edges,state):
    ns=sorted(nodes); idx={v:i for i,v in enumerate(ns)}; color_n=len(ns)*K
    def X(v,c): return idx[v]*K+c+1
    def A(v): return color_n+idx[v]+1
    cls=[]; V=set(ns)
    for v in ns:
        cls.append([-A(v)]+[X(v,c) for c in range(K)])
        for a,b in combinations(range(K),2): cls.append([-A(v),-X(v,a),-X(v,b)])
    for u,v in edges:
        if u in V and v in V:
            for c in range(K): cls.append([-A(u),-A(v),-X(u,c),-X(v,c)])
    for i,s in enumerate(SEP): cls.append([X(s,state[i])])
    return ns,cls,X,A


def direct_sat(nodes,edges,state,Solver):
    ns=sorted(nodes); idx={v:i for i,v in enumerate(ns)}
    def X(v,c): return idx[v]*K+c+1
    cls=[]; V=set(ns)
    for v in ns:
        lits=[X(v,c) for c in range(K)]; cls.append(lits)
        for a,b in combinations(lits,2): cls.append([-a,-b])
    for u,v in edges:
        if u in V and v in V:
            for c in range(K): cls.append([-X(u,c),-X(v,c)])
    for i,s in enumerate(SEP): cls.append([X(s,state[i])])
    with Solver(bootstrap_with=cls) as sol: return sol.solve()


def degree_order(nodes,edges,reverse=False):
    V=set(nodes); deg={v:0 for v in V}
    for u,v in edges:
        if u in V and v in V: deg[u]+=1;deg[v]+=1
    return sorted(V,key=lambda x:(deg[x],x),reverse=reverse)


def minimize(ns,cls,A,start,edges,order):
    active=set(start)|set(SEP); protected=set(SEP)
    with Cadical195(bootstrap_with=cls) as sol:
        if order=='asc': seq=sorted(active)
        elif order=='desc': seq=sorted(active,reverse=True)
        elif order=='degree-asc': seq=degree_order(active,edges,False)
        elif order=='degree-desc': seq=degree_order(active,edges,True)
        else: raise ValueError(order)
        for x in seq:
            if x in protected or x not in active: continue
            trial=active-{x}; ass=[A(z) if z in trial else -A(z) for z in ns]
            if not sol.solve(assumptions=ass): active=trial
        # verify inclusion-minimal wrt unprotected active vertices
        critical=[]
        for x in sorted(active-protected):
            trial=active-{x}; ass=[A(z) if z in trial else -A(z) for z in ns]
            sat=sol.solve(assumptions=ass); critical.append({'vertex':x,'forbidden_state_becomes_sat_if_deleted':sat})
            if not sat: raise RuntimeError((order,x,'not minimal'))
    return sorted(active),critical


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--data-dir',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    C,R,vq,E=build(a.data_dir); n=len(R); p,q=vq[P],vq[Q]
    _,S=min_vertex_cut(n,E,p,q)
    if p!=5 or S!=OUTER: raise RuntimeError((p,S))
    cc=components_without(n,E,S); pc=next(x for x in cc if p in x); left=set(pc)|set(S); ledges=[(u,v) for u,v in E if u in left and v in left]
    old=sorted(left); mp={v:i for i,v in enumerate(old)}; redges=[(mp[u],mp[v]) for u,v in ledges]
    cv2,cut2=min_vertex_cut(len(old),redges,mp[0],mp[10]); sep2=[old[x] for x in cut2]
    if cv2!=5 or sep2!=Q0Q10: raise RuntimeError((cv2,sep2))
    cc2=components_without(len(old),redges,cut2); cc2=[[old[x] for x in c] for c in cc2]; q0c=next(c for c in cc2 if 0 in c)
    bag=set(q0c)|set(sep2); bedges=[(u,v) for u,v in ledges if u in bag and v in bag]
    bold=sorted(bag); bmp={v:i for i,v in enumerate(bold)}; bredges=[(bmp[u],bmp[v]) for u,v in bedges]
    cv3,cut3=min_vertex_cut(len(bold),bredges,bmp[18],bmp[256]); sep3=[bold[x] for x in cut3]
    if cv3!=5 or sep3!=SEP: raise RuntimeError((cv3,sep3))
    cc3=components_without(len(bold),bredges,cut3); cc3=[[bold[x] for x in c] for c in cc3]; uc=next(c for c in cc3 if 18 in c)
    side=set(uc)|set(SEP); sedges=[(u,v) for u,v in bedges if u in side and v in side]

    # Pairwise relations alone admit exactly one extra canonical state.
    candidates=[]
    for st0 in rgs(5):
        st=tuple(st0)
        if all(st[i]!=st[j] for i,j in COMMON_NEQ): candidates.append(''.join(map(str,st)))
    expected=['00121','00123','01121','01123','01212','01213','01231','01232','01234']
    if candidates!=expected: raise RuntimeError(candidates)

    forbidden_checks={S.__name__:direct_sat(side,sedges,FORBIDDEN,S) for S in (Cadical195,Glucose4)}
    control_checks={S.__name__:direct_sat(side,sedges,VALID_CONTROL,S) for S in (Cadical195,Glucose4)}
    if any(forbidden_checks.values()) or not all(control_checks.values()): raise RuntimeError((forbidden_checks,control_checks))

    ns,cls,X,A=activation_cnf(side,sedges,FORBIDDEN)
    with Cadical195(bootstrap_with=cls) as sol:
        ass=[A(z) for z in ns]
        if sol.solve(assumptions=ass): raise RuntimeError('forbidden state unexpectedly SAT')
        raw=sol.get_core() or []
    inv={A(z):z for z in ns}; rawv=sorted({inv[x] for x in raw if x>0 and x in inv}|set(SEP))
    trials=[]
    for order in ['asc','desc','degree-asc','degree-desc']:
        core,crit=minimize(ns,cls,A,rawv,sedges,order); V=set(core); es=[(u,v) for u,v in sedges if u in V and v in V]
        trials.append({'order':order,'vertices':core,'vertex_count':len(core),'edge_count':len(es),'edges':[list(x) for x in es],
                       'forbidden_sat_cadical195':direct_sat(core,sedges,FORBIDDEN,Cadical195),
                       'forbidden_sat_glucose4':direct_sat(core,sedges,FORBIDDEN,Glucose4),
                       'valid_control_sat_cadical195':direct_sat(core,sedges,VALID_CONTROL,Cadical195),
                       'valid_control_sat_glucose4':direct_sat(core,sedges,VALID_CONTROL,Glucose4),
                       'deletion_criticality':crit})
    best=min(trials,key=lambda x:(x['vertex_count'],x['edge_count'],x['order']))
    rep={
      'upstream_sha':UPSTREAM_SHA,'separator_qnodes':SEP,'q18_side_size':len(side),'q18_side_edge_count':len(sedges),
      'five_common_pairwise_disequalities':[[SEP[i],SEP[j]] for i,j in COMMON_NEQ],
      'states_satisfying_only_those_disequalities':candidates,'unique_extra_state':'01232',
      'forbidden_state':'01232','forbidden_state_full_side_sat':forbidden_checks,'valid_control_state':'01231','valid_control_full_side_sat':control_checks,
      'raw_assumption_core_size':len(rawv),'core_trials':trials,'best_core':best,
      'interpretation':'The q18-side eight-state boundary language differs from the conjunction of its five common pairwise disequalities by exactly one canonical partition, 01232. Thus all higher-order information on this five-vertex interface is concentrated in one forbidden partition. The reported core is an inclusion-minimal induced subgraph (not guaranteed minimum-size) whose fixed 01232 boundary is UNSAT, while the nearby valid control 01231 remains SAT; both facts are checked with CaDiCaL195 and Glucose4.'
    }
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(rep,indent=2)+'\n')
    print(json.dumps({'candidate_states':candidates,'raw_core_size':len(rawv),'best_core':{k:best[k] for k in ['order','vertex_count','edge_count','forbidden_sat_cadical195','forbidden_sat_glucose4','valid_control_sat_cadical195','valid_control_sat_glucose4']}},indent=2))

if __name__=='__main__': main()
