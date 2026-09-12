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


def assumptions(X,forbid_fifth,target_color):
    return [X(v,c) for v,c in FIX.items()] + [-X(v,4) for v in forbid_fifth] + [X(6,target_color)]


def sat_with(nodes,edges,Solver,forbid_fifth,target_color):
    sol,X=make_solver(nodes,edges,Solver)
    try:return sol.solve(assumptions=assumptions(X,forbid_fifth,target_color))
    finally:sol.delete()


def witness_projection(nodes,edges,Solver,forbid_fifth,target_color):
    sol,X=make_solver(nodes,edges,Solver)
    try:
        if not sol.solve(assumptions=assumptions(X,forbid_fifth,target_color)):return None
        pos={x for x in sol.get_model() if x>0}
        verts=K4+[6]+EXTRA
        return {str(v):next(c for c in range(K) if X(v,c) in pos) for v in verts}
    finally:sol.delete()


def min_forbid_sets(nodes,edges,target_color,Solver):
    good=[]
    for r in range(len(EXTRA)+1):
        for ss in combinations(EXTRA,r):
            if not sat_with(nodes,edges,Solver,ss,target_color):good.append(list(ss))
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
        cad=min_forbid_sets(big,bedges,target_color,Cadical195);glu=min_forbid_sets(big,bedges,target_color,Glucose4)
        if cad!=glu:raise RuntimeError((label,'solver minimum bases differ',cad,glu))
        mins=cad
        result[label]={'target_color':target_color,'minimum_forbid_fifth_basis_size':len(mins[0]) if mins else None,'minimum_bases':mins,
                       'full_six_constraints_unsat_both':not sat_with(big,bedges,Cadical195,EXTRA,target_color) and not sat_with(big,bedges,Glucose4,EXTRA,target_color)}

    # Make the six-literal OR in the q6=q4 case concrete: if the fifth-color ban
    # is lifted at exactly one extra boundary vertex, record a coloring. Minimality
    # implies that the freed vertex must in fact take color 4 in such a witness.
    rescue=[]
    for free in EXTRA:
        forbid=[v for v in EXTRA if v!=free]
        ca=witness_projection(big,bedges,Cadical195,forbid,1);gl=witness_projection(big,bedges,Glucose4,forbid,1)
        if ca is None or gl is None:raise RuntimeError(('expected rescue witness',free))
        rescue.append({'freed_vertex':free,'cadical_projection':ca,'glucose_projection':gl,
                       'freed_vertex_is_fifth_in_both':ca[str(free)]==4 and gl[str(free)]==4})
    result['q6_equals_q4']['single_literal_rescue_witnesses']=rescue

    # q6=q8 is stronger: forbidding only q17 from color 4 is already UNSAT, so
    # q6=q8 implies q17 takes the fifth color. Record example unconstrained models.
    ca8=witness_projection(big,bedges,Cadical195,[],2);gl8=witness_projection(big,bedges,Glucose4,[],2)
    result['q6_equals_q8']['unconstrained_example_cadical']=ca8
    result['q6_equals_q8']['unconstrained_example_glucose']=gl8
    result['q6_equals_q8']['examples_have_q17_fifth']=ca8 is not None and gl8 is not None and ca8['17']==4 and gl8['17']==4

    direct={str(v):((min(6,v),max(6,v)) in Eset) for v in K4}
    rep={'upstream_sha':UPSTREAM_SHA,'separator_qnodes':SEP,'k4_anchors':K4,'k4_fixed_colors':FIX,'extra_boundary_vertices':EXTRA,
         'k4_is_clique':k4_ok,'q6_direct_edges_to_k4':direct,'conditional_targets':result,
         'solver_crosscheck':'CaDiCaL195 and Glucose4 found identical minimum-cardinality fifth-color-ban bases. Rescue witnesses are recorded separately for each solver.',
         'human_clause':(
            'Fix q0,q4,q8,q21 to colors 0,1,2,3. Edges q6-q0 and q6-q21 rule out colors 0 and 3. '
            'If q6 has q8 color 2, q17 is forced to the fifth color 4. If q6 has q4 color 1, at least one of '
            'q17,q30,q59,q68,q105,q223 is forced to color 4; this six-literal OR is minimal in the sense that freeing '
            'any one literal while banning color 4 at the other five restores satisfiability. Therefore if the whole '
            'separator is restricted to the four K4 colors, q6 cannot use any K4 color and must use the fifth color.'
         ),
         'interpretation':'Because q0,q4,q8,q21 form a K4, any boundary using at most four colors uses exactly their four colors. The scan compresses the remaining conditional q6 argument into one forced literal (q6=q8 => q17=fifth) and one minimal six-literal OR (q6=q4 => at least one extra boundary vertex=fifth).'}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(rep,indent=2)+'\n')
    print(json.dumps({'q6_direct_edges_to_k4':direct,'conditional_targets':result,'human_clause':rep['human_clause']},indent=2))
if __name__=='__main__':main()
