#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path

from pysat.solvers import Cadical195, Glucose4

from separator_interface import P, Q, UPSTREAM_SHA, build, components_without, min_vertex_cut, rgs

K=5
OUTER=[0,6,8,9,10,266]
TARGET=(0,10)
SEP=[14,18,54,55,256]
EXPECTED_STATES=[(0,1,2,3,0),(0,1,2,3,3),(0,1,2,3,4)]


def make_cnf(nodes, edges):
    ns=sorted(nodes); idx={v:i for i,v in enumerate(ns)}; cls=[]
    def X(v,c): return idx[v]*K+c+1
    for v in ns:
        lits=[X(v,c) for c in range(K)]; cls.append(lits)
        for a,b in combinations(lits,2): cls.append([-a,-b])
    V=set(ns)
    for u,v in edges:
        if u in V and v in V:
            for c in range(K): cls.append([-X(u,c),-X(v,c)])
    return ns,cls,X


def eq_class(Solver, clauses, X, ns, anchor):
    out=[]
    with Solver(bootstrap_with=clauses) as s:
        if not s.solve(assumptions=[X(anchor,0)]): raise RuntimeError(('anchor UNSAT',anchor))
        for v in ns:
            if v==anchor: out.append(v); continue
            if not any(s.solve(assumptions=[X(anchor,0),X(v,c)]) for c in range(1,K)):
                out.append(v)
    return sorted(out)


def pair_relations(states, nodes):
    out=[]
    for i,j in combinations(range(len(nodes)),2):
        vals={st[i]==st[j] for st in states}
        if len(vals)==1:
            out.append({'positions':[i,j],'qnodes':[nodes[i],nodes[j]],'kind':'eq' if True in vals else 'neq'})
    return out


def min_bases(all_states, target_states, rels):
    target=set(target_states); bad=[st for st in all_states if st not in target]
    masks=[]
    for r in rels:
        i,j=r['positions']; want=r['kind']=='eq'; m=0
        for k,st in enumerate(bad):
            if ((st[i]==st[j])!=want): m|=1<<k
        masks.append(m)
    full=(1<<len(bad))-1
    for sz in range(1,len(rels)+1):
        ans=[]
        for ii in combinations(range(len(rels)),sz):
            m=0
            for x in ii:m|=masks[x]
            if m==full:ans.append([rels[x] for x in ii])
        if ans:return sz,ans
    return None,[]


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--data-dir',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    C,R,vq,E=build(a.data_dir); n=len(R); p,q=vq[P],vq[Q]
    val,S=min_vertex_cut(n,E,p,q)
    if p!=5 or S!=OUTER: raise RuntimeError((p,q,val,S))
    cc=components_without(n,E,S); pc=next(x for x in cc if p in x); left=set(pc)|set(S)
    ledges=[(u,v) for u,v in E if u in left and v in left]
    old=sorted(left); mp={v:i for i,v in enumerate(old)}; redges=[(mp[u],mp[v]) for u,v in ledges]
    cv,cn=min_vertex_cut(len(old),redges,mp[0],mp[10]); sep=[old[x] for x in cn]
    if cv!=5 or sep!=SEP: raise RuntimeError((cv,sep))
    compsnew=components_without(len(old),redges,cn); comps=[[old[x] for x in z] for z in compsnew]
    q0comp=next(z for z in comps if 0 in z); q0bag=set(q0comp)|set(SEP)
    q0edges=[(u,v) for u,v in ledges if u in q0bag and v in q0bag]
    ns,clauses,X=make_cnf(q0bag,q0edges)

    # Re-enumerate the q0-side boundary states with CaDiCaL.
    states=[]
    with Cadical195(bootstrap_with=clauses) as s:
        for st in rgs(len(SEP)):
            ass=[X(v,st[i]) for i,v in enumerate(SEP)]
            if s.solve(assumptions=ass): states.append(tuple(st))
    if states!=EXPECTED_STATES: raise RuntimeError(('unexpected states',states))

    rels=pair_relations(states,SEP)
    all_states=list(rgs(len(SEP)))
    bsz,bases=min_bases(all_states,states,rels)
    Eset={(min(u,v),max(u,v)) for u,v in q0edges}

    classes={}
    for anchor in SEP:
        ca=eq_class(Cadical195,clauses,X,ns,anchor)
        gl=eq_class(Glucose4,clauses,X,ns,anchor)
        if ca!=gl: raise RuntimeError(('solver class disagreement',anchor,ca,gl))
        classes[str(anchor)]=ca

    relation_explanations=[]
    for r in rels:
        u,v=r['qnodes']; cu=classes[str(u)]; cvv=classes[str(v)]
        witnesses=[]
        for x in cu:
            for y in cvv:
                if x==y: continue
                e=(min(x,y),max(x,y))
                if e in Eset: witnesses.append([x,y])
        rr=dict(r)
        rr['direct_edge']=(min(u,v),max(u,v)) in Eset
        rr['left_eq_class']=cu; rr['right_eq_class']=cvv
        rr['class_edge_witnesses']=witnesses
        rr['explained_by_eq_classes_plus_edge']=bool(witnesses) if r['kind']=='neq' else None
        relation_explanations.append(rr)

    rep={
      'upstream_sha':UPSTREAM_SHA,'q0_side_bag_size':len(q0bag),'q0_side_edge_count':len(q0edges),
      'separator_qnodes':SEP,'extendable_states':[''.join(map(str,x)) for x in states],
      'common_pair_relations':rels,'minimum_pairwise_basis_size':bsz,'minimum_pairwise_bases':bases,
      'separator_equality_classes_q0_side':classes,
      'relation_explanations':relation_explanations,
      'all_required_neq_explained_by_eq_classes_plus_edge':all(x['explained_by_eq_classes_plus_edge'] for x in relation_explanations if x['kind']=='neq'),
      'interpretation':'The q0-side three-state boundary language is exactly a conjunction of pairwise disequalities. The first four separator vertices form a color K4 and q256 must additionally differ from q18 and q54. Equality classes are reconstructed with both CaDiCaL195 and Glucose4; an edge between two equality classes gives a graph-theoretic witness for the corresponding forced disequality.'
    }
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(rep,indent=2)+'\n')
    print(json.dumps({
      'states':rep['extendable_states'],'basis_size':bsz,
      'basis_count':len(bases),
      'class_sizes':{k:len(v) for k,v in classes.items()},
      'relations':[{k:x[k] for k in ['qnodes','kind','direct_edge','explained_by_eq_classes_plus_edge']}|{'class_edge_witnesses':x['class_edge_witnesses'][:5]} for x in relation_explanations],
      'all_neq_explained':rep['all_required_neq_explained_by_eq_classes_plus_edge']
    },indent=2))

if __name__=='__main__':main()
