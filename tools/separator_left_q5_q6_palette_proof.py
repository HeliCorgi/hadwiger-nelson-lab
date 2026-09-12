#!/usr/bin/env python3
from __future__ import annotations

import argparse,json
from itertools import combinations
from pathlib import Path
from pysat.solvers import Cadical195,Glucose4
from separator_interface import P,Q,UPSTREAM_SHA,build,components_without,min_vertex_cut

K=5
OUTER=[0,6,8,9,10,266]
SEP=[0,4,8,17,21,30,59,68,105,223]
LOCAL_COMMON=[0,4,8,21]


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


def check_solver(big,edges,Solver):
    sol,X=make_solver(set(big)|set(SEP),edges,Solver)
    try:
        base_sat=sol.solve()

        # Unconditional diagnostic: q6 may share a color with some separator vertices
        # when all five colors occur on the boundary.
        eq_possible={}
        for s in SEP:
            witness=None
            for c in range(K):
                if sol.solve(assumptions=[X(6,c),X(s,c)]): witness=c;break
            eq_possible[str(s)]=witness
        unconditional_absent=all(v is None for v in eq_possible.values())

        # The q22 singleton side can extend only when at least one color is absent
        # from its whole neighborhood SEP. Test the exact conditional statement needed:
        # if SEP omits some color (uses <=4 colors), q6 cannot share a color with
        # any separator vertex. A counterexample is witnessed by s,c,missing with
        # q6=s=c and 'missing' absent from every separator vertex.
        conditional_counterexample=None
        for s in SEP:
            for c in range(K):
                for missing in range(K):
                    ass=[X(6,c),X(s,c)] + [-X(v,missing) for v in SEP]
                    if sol.solve(assumptions=ass):
                        conditional_counterexample={'separator_vertex':s,'shared_color':c,'missing_boundary_color':missing}
                        break
                if conditional_counterexample: break
            if conditional_counterexample: break
        absent_when_at_most4=conditional_counterexample is None

        # Any coloring with <=3 separator colors is contained in some fixed
        # three-color label subset. Rule all ten subsets out exactly.
        at_most3_witness=None
        for subset in combinations(range(K),3):
            Sset=set(subset);ass=[]
            for v in SEP:
                for c in range(K):
                    if c not in Sset:ass.append(-X(v,c))
            if sol.solve(assumptions=ass):at_most3_witness=list(subset);break
        at_least4=at_most3_witness is None

        return {
            'base_sat':base_sat,
            'q6_equal_separator_color_witness':eq_possible,
            'q6_color_unconditionally_absent_from_separator':unconditional_absent,
            'at_most4_boundary_counterexample_to_q6_absence':conditional_counterexample,
            'q6_color_absent_when_boundary_uses_at_most4_colors':absent_when_at_most4,
            'at_most3_separator_colors_witness_subset':at_most3_witness,
            'separator_uses_at_least4_colors':at_least4,
        }
    finally:sol.delete()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--data-dir',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    C,R,vq,E=build(a.data_dir);n=len(R);p,q=vq[P],vq[Q];_,S=min_vertex_cut(n,E,p,q)
    if p!=5 or S!=OUTER:raise RuntimeError((p,S))
    cc=components_without(n,E,S);pc=next(x for x in cc if p in x);left=set(pc)|set(S);ledges=[(u,v) for u,v in E if u in left and v in left];Eset={(min(u,v),max(u,v)) for u,v in ledges}
    old=sorted(left);mp={v:i for i,v in enumerate(old)};redges=[(mp[u],mp[v]) for u,v in ledges]
    cv,cut=min_vertex_cut(len(old),redges,mp[6],mp[22]);sep=[old[x] for x in cut]
    if cv!=10 or sep!=SEP:raise RuntimeError((cv,sep))
    ccs=components_without(len(old),redges,cut);ccs=[[old[x] for x in c] for c in ccs];big=next(c for c in ccs if 6 in c);small=next(c for c in ccs if 22 in c)
    n22=sorted({v for u,v in ledges if u==22}|{u for u,v in ledges if v==22})

    # Standalone graph-theoretic check of the known local K4 equality q5=q22.
    k4_edges=all((min(u,v),max(u,v)) in Eset for u,v in combinations(LOCAL_COMMON,2))
    common_to_both=all((min(5,x),max(5,x)) in Eset and (min(22,x),max(22,x)) in Eset for x in LOCAL_COMMON)

    checks={Solver.__name__:check_solver(big,ledges,Solver) for Solver in (Cadical195,Glucose4)}
    palette_ok=all(
        v['base_sat'] and
        v['q6_color_absent_when_boundary_uses_at_most4_colors'] and
        v['separator_uses_at_least4_colors']
        for v in checks.values()
    )
    human=bool(len(small)==1 and set(n22)==set(SEP) and k4_edges and common_to_both and palette_ok)

    rep={
      'upstream_sha':UPSTREAM_SHA,'separator_qnodes':SEP,'min_cut_value':cv,
      'q6_component_size':len(big),'q22_component_size':len(small),
      'q22_neighbors_in_left':n22,'q22_degree':len(n22),'q22_neighborhood_is_separator':set(n22)==set(SEP),
      'local_q5_eq_q22_k4_witness':LOCAL_COMMON,'local_witness_is_k4':k4_edges,'local_witness_common_to_q5_q22':common_to_both,
      'solver_checks':checks,'conditional_palette_conditions_verified_both':palette_ok,
      'human_proof_available':human,
      'interpretation':(
        'First, q5=q22 follows from the local K4 common-neighborhood lemma using q0,q4,q8,q21. '
        'The minimum q6-q22 separator is exactly the neighborhood of singleton q22. Any coloring extending to q22 '
        'must omit q22 color from this boundary, hence the boundary uses at most four colors. Independently, the large '
        'q6 side forces the separator to use at least four colors, and—conditional on the boundary using at most four—'
        'forces q6 color to be absent from every separator vertex. Therefore every globally viable boundary uses exactly '
        'four colors and both q6 and q22 take the unique missing fifth color. Together with q5=q22 this proves q5=q6 '
        'without enumerating all canonical partitions of the ten-vertex boundary.'
      )
    }
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(rep,indent=2)+'\n')
    print(json.dumps(rep,indent=2))
if __name__=='__main__':main()
