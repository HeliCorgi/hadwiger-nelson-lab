#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path

from pysat.solvers import Glucose4

from separator_interface import P, Q, UPSTREAM_SHA, build, components_without, min_vertex_cut, rgs

K = 5
OUTER = [0, 6, 8, 9, 10, 266]
TARGET = (0, 10)
EXPECTED_SEP = [14, 18, 54, 55, 256]
LOCAL_Q0_PARTNER = 62


def make_solver(nodes, edges):
    ns = sorted(nodes)
    idx = {v: i for i, v in enumerate(ns)}
    cls = []
    def X(v, c): return idx[v] * K + c + 1
    for v in ns:
        lits = [X(v, c) for c in range(K)]
        cls.append(lits)
        for a, b in combinations(lits, 2):
            cls.append([-a, -b])
    V = set(ns)
    for u, v in edges:
        if u in V and v in V:
            for c in range(K): cls.append([-X(u,c), -X(v,c)])
    return Glucose4(bootstrap_with=cls), X


def opts(sol, X, sep, st, v):
    base = [X(x, st[i]) for i, x in enumerate(sep)]
    return [c for c in range(K) if sol.solve(assumptions=base + [X(v,c)])]


def canonicalize(colors):
    mp={}; out=[]
    for c in colors:
        if c not in mp: mp[c]=len(mp)
        out.append(mp[c])
    return tuple(out)


def state_relations(states, nodes):
    rels = []
    for i, j in combinations(range(len(nodes)), 2):
        vals = {(st[i] == st[j]) for st in states}
        if len(vals) == 1:
            rels.append({'positions':[i,j], 'qnodes':[nodes[i],nodes[j]], 'kind':'eq' if True in vals else 'neq'})
    return rels


def min_relation_bases(all_states, viable_states, rels):
    target = {tuple(x) for x in viable_states}
    bad = [st for st in all_states if tuple(st) not in target]
    masks = []
    for r in rels:
        i,j = r['positions']; want = (r['kind']=='eq')
        elim = 0
        for k, st in enumerate(bad):
            if ((st[i]==st[j]) != want): elim |= 1 << k
        masks.append(elim)
    full = (1 << len(bad)) - 1
    out = []
    for sz in range(1, len(rels)+1):
        for idxs in combinations(range(len(rels)), sz):
            m=0
            for x in idxs: m |= masks[x]
            if m == full:
                out.append([rels[x] for x in idxs])
        if out: return sz, out
    return None, []


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--data-dir',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    C,R,vq,E=build(a.data_dir); n=len(R); p,q=vq[P],vq[Q]
    val,S=min_vertex_cut(n,E,p,q)
    if S != OUTER or p != 5: raise RuntimeError((p,q,S))
    cc=components_without(n,E,S); pc=next(x for x in cc if p in x); left=set(pc)|set(S)
    ledges=[(u,v) for u,v in E if u in left and v in left]
    old=sorted(left); mp={v:i for i,v in enumerate(old)}; redges=[(mp[u],mp[v]) for u,v in ledges]
    cutval,cutnew=min_vertex_cut(len(old),redges,mp[TARGET[0]],mp[TARGET[1]])
    sep=[old[x] for x in cutnew]
    if cutval != 5 or sep != EXPECTED_SEP: raise RuntimeError((cutval,sep))
    compsnew=components_without(len(old),redges,cutnew); comps=[[old[x] for x in c] for c in compsnew]
    uc=next(c for c in comps if TARGET[0] in c); vc=next(c for c in comps if TARGET[1] in c)
    usol,uX=make_solver(set(uc)|set(sep),ledges); vsol,vX=make_solver(set(vc)|set(sep),ledges)
    left_rows=[]; right_rows=[]; both=[]; all_states=[]
    try:
        for st in rgs(len(sep)):
            st=tuple(st); all_states.append(st); key=''.join(map(str,st))
            ua=[uX(x,st[i]) for i,x in enumerate(sep)]; va=[vX(x,st[i]) for i,x in enumerate(sep)]
            lu=usol.solve(assumptions=ua); rv=vsol.solve(assumptions=va)
            uo=opts(usol,uX,sep,st,TARGET[0]) if lu else []
            vo=opts(vsol,vX,sep,st,TARGET[1]) if rv else []
            if lu:left_rows.append({'state':st,'key':key,'u_colors':uo})
            if rv:right_rows.append({'state':st,'key':key,'v_colors':vo})
            if lu and rv:
                both.append({'state':st,'key':key,'u_colors':uo,'v_colors':vo,'equal':all(x==y for x in uo for y in vo)})
    finally:
        usol.delete(); vsol.delete()

    viable=[x['state'] for x in both]
    rels=state_relations(viable,sep)
    Eset={(min(u,v),max(u,v)) for u,v in ledges}
    for r in rels:
        r['direct_edge']=(min(r['qnodes']),max(r['qnodes'])) in Eset
    bsz,bases=min_relation_bases(all_states,viable,rels)

    tracked=[TARGET[0]]+sep
    left_aug=[]
    left_aug_sources=[]
    for row in left_rows:
        for c in row['u_colors']:
            st=canonicalize((c,)+row['state'])
            left_aug.append(st)
            left_aug_sources.append({'separator_state':row['key'],'q0_color':c,'canonical_augmented_state':list(st)})
    left_aug=sorted(set(left_aug))
    all_aug=list(rgs(len(tracked)))
    left_rels=state_relations(left_aug,tracked)
    for r in left_rels:
        r['direct_edge']=(min(r['qnodes']),max(r['qnodes'])) in Eset
    left_bsz,left_bases=min_relation_bases(all_aug,left_aug,left_rels)

    n10=sorted({v for u,v in ledges if u==10}|{u for u,v in ledges if v==10})
    n0=sorted({v for u,v in ledges if u==0}|{u for u,v in ledges if v==0})
    n62=sorted({v for u,v in ledges if u==LOCAL_Q0_PARTNER}|{u for u,v in ledges if v==LOCAL_Q0_PARTNER})
    q0local_class={0,LOCAL_Q0_PARTNER}
    q0class_to_sep=[]
    for s in sep:
        witnesses=[]
        for x in q0local_class:
            if (min(x,s),max(x,s)) in Eset: witnesses.append([x,s])
        q0class_to_sep.append({'separator_qnode':s,'edge_witnesses':witnesses,'adjacent_after_q0_eq_62':bool(witnesses)})

    rep={
      'upstream_sha':UPSTREAM_SHA,'target_pair':list(TARGET),'separator_qnodes':sep,'min_cut_value':cutval,
      'u_component_size':len(uc),'v_component_size':len(vc),'all_canonical_states':len(all_states),
      'u_side_extendable_count':len(left_rows),'v_side_extendable_count':len(right_rows),'intersection_count':len(both),
      'u_side_rows':[{**x,'state':list(x['state'])} for x in left_rows],
      'v_side_rows':[{**x,'state':list(x['state'])} for x in right_rows],
      'intersection':[{k:(list(v) if k=='state' else v) for k,v in x.items()} for x in both],
      'verified_all_intersection_states_force_equal':bool(both) and all(x['equal'] for x in both),
      'q10_neighbors_in_left':n10,'q10_degree_in_left':len(n10),'q10_neighborhood_is_separator':set(n10)==set(sep),
      'q0_neighbors_in_left':n0,'q0_degree_in_left':len(n0),'q62_neighbors_in_left':n62,
      'separator_induced_edges':[[u,v] for u,v in ledges if u in set(sep) and v in set(sep)],
      'common_pair_relations_global_two_states':rels,'minimum_pairwise_basis_size_global_two_states':bsz,'minimum_pairwise_bases_global_two_states':bases,
      'q0_side_augmented_nodes':tracked,'q0_side_augmented_states':[list(x) for x in left_aug],
      'q0_side_augmented_sources':left_aug_sources,
      'q0_side_common_pair_relations':left_rels,'q0_side_minimum_pairwise_basis_size':left_bsz,'q0_side_minimum_pairwise_bases':left_bases,
      'q0_eq_62_local_class_to_separator_edges':q0class_to_sep,
      'interpretation':'Glucose4 independently reconstructs the size-5 recursive interface for q0=q10. The q0 side permits exactly three separator states. The third state 01234 allows q0 colors 3 or 4, but q10 is a singleton of degree five adjacent exactly to the separator, so that all-five-colors boundary state is impossible globally. The remaining states 01230 and 01233 force both q0 and q10 to color 4.'
    }
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(rep,indent=2)+'\n')
    print(json.dumps({
      'u_side_rows':rep['u_side_rows'],
      'intersection_keys':[x['key'] for x in both],
      'q10_degree':rep['q10_degree_in_left'],
      'q10_neighborhood_is_separator':rep['q10_neighborhood_is_separator'],
      'q0_side_augmented_states':rep['q0_side_augmented_states'],
      'q0_side_minimum_pairwise_basis_size':rep['q0_side_minimum_pairwise_basis_size'],
      'q0_eq_62_local_class_to_separator_edges':rep['q0_eq_62_local_class_to_separator_edges'],
    },indent=2))

if __name__=='__main__': main()
