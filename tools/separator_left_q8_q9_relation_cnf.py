#!/usr/bin/env python3
from __future__ import annotations

import argparse,json
from itertools import combinations
from pathlib import Path
from pysat.solvers import Cadical195,Glucose4
from separator_interface import P,Q,UPSTREAM_SHA,build,components_without,min_vertex_cut,rgs

K=5
OUTER=[0,6,8,9,10,266]
SEP=[4,5,33,62,68,78,226]
EXPECTED_STATES=['0112323','0112324','0112333','0112334','0112340','0112343','0112344','0123224','0123234','0123420','0123424','0123434']


def state_tuple(s):return tuple(map(int,s))
def atom(st,p):return st[p[0]]==st[p[1]]

def make_solver(nodes,edges,Solver):
    ns=sorted(nodes);idx={v:i for i,v in enumerate(ns)}
    def X(v,c):return idx[v]*K+c+1
    cls=[];V=set(ns)
    for v in ns:
        lits=[X(v,c) for c in range(K)];cls.append(lits)
        for a,b in combinations(lits,2):cls.append([-a,-b])
    for u,v in edges:
        if u in V and v in V:
            for c in range(K):cls.append([-X(u,c),-X(v,c)])
    return Solver(bootstrap_with=cls),X

def side_states(big,edges,Solver):
    sol,X=make_solver(set(big)|set(SEP),edges,Solver);out=[]
    try:
        for st0 in rgs(len(SEP)):
            st=tuple(st0);ass=[X(v,st[i]) for i,v in enumerate(SEP)]
            if sol.solve(assumptions=ass):out.append(''.join(map(str,st)))
    finally:sol.delete()
    return out

def lit_true(st,pairs,lit):
    pi,val=lit;return atom(st,pairs[pi])==val

def fmt_lit(pairs,lit):
    pi,val=lit;i,j=pairs[pi]
    return {'qnodes':[SEP[i],SEP[j]],'kind':'eq' if val else 'neq','positions':[i,j]}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--data-dir',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    C,R,vq,E=build(a.data_dir);n=len(R);p,q=vq[P],vq[Q];_,S=min_vertex_cut(n,E,p,q)
    if p!=5 or S!=OUTER:raise RuntimeError((p,S))
    cc=components_without(n,E,S);pc=next(x for x in cc if p in x);left=set(pc)|set(S);ledges=[(u,v) for u,v in E if u in left and v in left];Eset={(min(u,v),max(u,v)) for u,v in ledges}
    old=sorted(left);mp={v:i for i,v in enumerate(old)};redges=[(mp[u],mp[v]) for u,v in ledges];cv,cut=min_vertex_cut(len(old),redges,mp[8],mp[104]);sep=[old[x] for x in cut]
    if cv!=7 or sep!=SEP:raise RuntimeError((cv,sep))
    ccs=components_without(len(old),redges,cut);ccs=[[old[x] for x in c] for c in ccs];big=next(c for c in ccs if 8 in c)
    if 9 not in big:raise RuntimeError('q9 not in big side')
    ca=side_states(big,ledges,Cadical195);gl=side_states(big,ledges,Glucose4)
    if ca!=gl or ca!=EXPECTED_STATES:raise RuntimeError(('state mismatch',ca,gl))

    actual=[state_tuple(s) for s in ca];actual_set=set(actual);pairs=list(combinations(range(len(SEP)),2));all_states=[tuple(x) for x in rgs(len(SEP))]
    common=[]
    for pi,pair in enumerate(pairs):
        vals={atom(st,pair) for st in actual}
        if len(vals)==1:
            val=next(iter(vals));u,v=SEP[pair[0]],SEP[pair[1]]
            common.append({'pair_index':pi,'positions':list(pair),'qnodes':[u,v],'kind':'eq' if val else 'neq','value':val,'direct_edge':(min(u,v),max(u,v)) in Eset})
    pairwise_candidates=[st for st in all_states if all(atom(st,tuple(r['positions']))==r['value'] for r in common)]
    extras=[st for st in pairwise_candidates if st not in actual_set]

    literals=[(pi,val) for pi in range(len(pairs)) for val in (False,True)]
    valid_clauses=[]
    for ai,bi in combinations(range(len(literals)),2):
        la,lb=literals[ai],literals[bi]
        if la[0]==lb[0] and la[1]!=lb[1]:continue
        if not all(lit_true(st,pairs,la) or lit_true(st,pairs,lb) for st in actual):continue
        elim=[i for i,st in enumerate(extras) if not (lit_true(st,pairs,la) or lit_true(st,pairs,lb))]
        if elim:valid_clauses.append({'lits':[la,lb],'eliminates':elim})
    full=set(range(len(extras)));covers=[set(x['eliminates']) for x in valid_clauses];solutions=[]
    for sz in range(1,len(valid_clauses)+1):
        for inds in combinations(range(len(valid_clauses)),sz):
            if set().union(*(covers[i] for i in inds))==full:solutions.append(inds)
        if solutions:break
    if not solutions:raise RuntimeError('no width-2 cover')
    chosen=solutions[0]
    clauses=[]
    for i in chosen:
        c=valid_clauses[i]
        clauses.append({'literals':[fmt_lit(pairs,x) for x in c['lits']],
                        'eliminates_states':[''.join(map(str,extras[j])) for j in c['eliminates']]})

    def formula_holds(st):
        if not all(atom(st,tuple(r['positions']))==r['value'] for r in common):return False
        for i in chosen:
            la,lb=valid_clauses[i]['lits']
            if not (lit_true(st,pairs,la) or lit_true(st,pairs,lb)):return False
        return True
    selected=[''.join(map(str,st)) for st in all_states if formula_holds(st)]
    if selected!=ca:raise RuntimeError(('formula not exact',selected))

    rep={'upstream_sha':UPSTREAM_SHA,'separator_qnodes':SEP,'large_side_state_count':len(ca),'large_side_states':ca,'solver_crosscheck':'Cadical195 and Glucose4 state lists identical',
         'common_pairwise_relation_count':len(common),'common_pairwise_relations':common,
         'pairwise_closure_state_count':len(pairwise_candidates),'pairwise_closure_states':[''.join(map(str,x)) for x in pairwise_candidates],
         'pairwise_closure_extra_state_count':len(extras),'pairwise_closure_extra_states':[''.join(map(str,x)) for x in extras],
         'valid_width2_clause_count':len(valid_clauses),'minimum_width2_clause_cover_size':len(chosen),'minimum_cover_count':len(solutions),'chosen_width2_clauses':clauses,
         'exact_formula_selects_states':selected,'exact_formula_verified':selected==ca,
         'interpretation':'The 12-state large-side language on the seven-vertex q104 separator is exactly a small Boolean relation over color-equality atoms: 13 pairwise disequalities common to all states, plus four two-literal disjunctive clauses. The common pairwise constraints alone allow 21 canonical partitions, so the four clauses encode the residual higher-order information. This is a color-name-invariant CNF compression of the SAT state table.'}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(rep,indent=2)+'\n')
    print(json.dumps(rep,indent=2))
if __name__=='__main__':main()
