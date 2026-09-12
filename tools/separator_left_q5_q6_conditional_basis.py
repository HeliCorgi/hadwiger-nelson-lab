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
K4=[0,4,8,21]
EXTRA=[17,30,59,68,105,223]
FIX={0:0,4:1,8:2,21:3}


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


def sat_with(nodes,edges,Solver,forbid_fifth,target_color,extra_assumptions=()):
    sol,X=make_solver(nodes,edges,Solver)
    try:
        ass=[X(v,c) for v,c in FIX.items()]
        ass += [-X(v,4) for v in forbid_fifth]
        ass += [X(6,target_color)]
        ass += list(extra_assumptions)
        return sol.solve(assumptions=ass)
    finally:sol.delete()


def min_forbid_sets(nodes,edges,target_color,Solver):
    good=[]
    for r in range(len(EXTRA)+1):
        for ss in combinations(EXTRA,r):
            if not sat_with(nodes,edges,Solver,ss,target_color):
                good.append(list(ss))
        if good:return good
    return []


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--data-dir',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    C,R,vq,E=build(a.data_dir);n=len(R);p,q=vq[P],vq[Q];_,S=min_vertex_cut(n,E,p,q)
    if p!=5 or S!=OUTER:raise RuntimeError((p,S))
    cc=components_without(n,E,S);pc=next(x for x in cc if p in x);left=set(pc)|set(S);ledges=[(u,v) for u,v in E if u in left and v in left];Eset={(min(u,v),max(u,v)) for u,v in ledges}
    old=sorted(left);mp={v:i for i,v in enumerate(old)};redges=[(mp[u],mp[v]) for u,v in ledges]
    cv,cut=min_vertex_cut(len(old),redges,mp[6],mp[22]);sep=[old[x] for x in cut]
    if cv!=10 or sep!=SEP:raise RuntimeError((cv,sep))
    ccs=components_without(len(old),redges,cut);ccs=[[old[x] for x in c] for c in ccs];big=set(next(c for c in ccs if 6 in c))|set(SEP);bedges=[(u,v) for u,v in ledges if u in big and v in big]
    k4_ok=all((min(u,v),max(u,v)) in Eset for u,v in combinations(K4,2))
    if not k4_ok:raise RuntimeError('expected K4 missing')

    result={}
    for label,target_color in [('q6_equals_q4',1),('q6_equals_q8',2)]:
        cad=min_forbid_sets(big,bedges,target_color,Cadical195)
        glu=min_forbid_sets(big,bedges,target_color,Glucose4)
        if cad!=glu:raise RuntimeError((label,'solver minimal bases differ',cad,glu))
        mins=cad
        # Every proper subset of a returned minimum-cardinality basis is SAT by construction.
        result[label]={'target_color':target_color,'minimum_forbid_fifth_basis_size':len(mins[0]) if mins else None,'minimum_bases':mins,
                       'full_six_constraints_unsat_both':not sat_with(big,bedges,Cadical195,EXTRA,target_color) and not sat_with(big,bedges,Glucose4,EXTRA,target_color)}

    # Check q6 already has direct graph edges to which K4 anchors.
    direct={str(v):((min(6,v),max(6,v)) in Eset) for v in K4}
    rep={'upstream_sha':UPSTREAM_SHA,'separator_qnodes':SEP,'k4_anchors':K4,'k4_fixed_colors':FIX,'extra_boundary_vertices':EXTRA,
         'k4_is_clique':k4_ok,'q6_direct_edges_to_k4':direct,'conditional_targets':result,
         'solver_crosscheck':'CaDiCaL195 and Glucose4 found identical minimum-cardinality subsets of extra boundary vertices whose exclusion of the fifth color blocks q6 from taking the q4 or q8 K4 colors.',
         'interpretation':'Because q0,q4,q8,q21 form a K4, any boundary using at most four colors uses exactly their four colors. By color symmetry fix them to 0,1,2,3; then each extra separator vertex must avoid color 4. q6 is already graph-adjacent to whichever K4 anchors are marked true. The only nontrivial cases are q6=q4 and q6=q8. This scan finds the smallest subset of the six extra boundary vertices that must merely avoid the fifth color in order to make each case impossible.'}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(rep,indent=2)+'\n')
    print(json.dumps(rep,indent=2))
if __name__=='__main__':main()
