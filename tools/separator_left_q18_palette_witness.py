#!/usr/bin/env python3
from __future__ import annotations

import argparse,json
from itertools import combinations
from pathlib import Path
from pysat.solvers import Cadical195,Glucose4
from separator_interface import P,Q,UPSTREAM_SHA,build,components_without,min_vertex_cut

K=5; OUTER=[0,6,8,9,10,266]; Q0Q10=[14,18,54,55,256]; SEP=[23,35,57,86,159]; ANCHORS=[23,35,57,86,159]


def solver_for(nodes,edges,Solver):
    ns=sorted(nodes); idx={v:i for i,v in enumerate(ns)}
    def X(v,c): return idx[v]*K+c+1
    cls=[];V=set(ns)
    for v in ns:
        lits=[X(v,c) for c in range(K)];cls.append(lits)
        for a,b in combinations(lits,2):cls.append([-a,-b])
    for u,v in edges:
        if u in V and v in V:
            for c in range(K):cls.append([-X(u,c),-X(v,c)])
    return Solver(bootstrap_with=cls),X


def eq_class(nodes,edges,anchor,Solver):
    sol,X=solver_for(nodes,edges,Solver); out=[]
    try:
        for v in sorted(nodes):
            if v==anchor: out.append(v);continue
            # anchor != v; UNSAT means globally equal.
            ass=[]
            # Check existence of distinct colors by explicit pairs.
            diff=False
            for a in range(K):
                for b in range(K):
                    if a!=b and sol.solve(assumptions=[X(anchor,a),X(v,b)]):
                        diff=True;break
                if diff:break
            if not diff:out.append(v)
    finally:sol.delete()
    return out


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--data-dir',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    C,R,vq,E=build(a.data_dir);n=len(R);p,q=vq[P],vq[Q];_,S=min_vertex_cut(n,E,p,q)
    if p!=5 or S!=OUTER:raise RuntimeError((p,S))
    cc=components_without(n,E,S);pc=next(x for x in cc if p in x);left=set(pc)|set(S);ledges=[(u,v) for u,v in E if u in left and v in left]
    old=sorted(left);mp={v:i for i,v in enumerate(old)};redges=[(mp[u],mp[v]) for u,v in ledges];cv2,c2=min_vertex_cut(len(old),redges,mp[0],mp[10]);s2=[old[x] for x in c2]
    if cv2!=5 or s2!=Q0Q10:raise RuntimeError((cv2,s2))
    cc2=components_without(len(old),redges,c2);cc2=[[old[x] for x in c] for c in cc2];q0c=next(c for c in cc2 if 0 in c);bag=set(q0c)|set(s2);bedges=[(u,v) for u,v in ledges if u in bag and v in bag]
    bold=sorted(bag);bmp={v:i for i,v in enumerate(bold)};bredges=[(bmp[u],bmp[v]) for u,v in bedges];cv3,c3=min_vertex_cut(len(bold),bredges,bmp[18],bmp[256]);s3=[bold[x] for x in c3]
    if cv3!=5 or s3!=SEP:raise RuntimeError((cv3,s3))
    cc3=components_without(len(bold),bredges,c3);cc3=[[bold[x] for x in c] for c in cc3];uc=next(c for c in cc3 if 18 in c);side=set(uc)|set(SEP);sedges=[(u,v) for u,v in bedges if u in side and v in side];Eset={(min(u,v),max(u,v)) for u,v in sedges}

    ca={str(x):eq_class(side,sedges,x,Cadical195) for x in ANCHORS};gl={str(x):eq_class(side,sedges,x,Glucose4) for x in ANCHORS}
    if ca!=gl:raise RuntimeError('solver equality classes differ')
    classes=[set(ca['23']),set(ca['35']),set(ca['57'])|set(ca['159']),set(ca['86'])]
    # Under the conditional hypothesis c57=c159 these four classes represent the four distinct colors of forbidden 01232.
    witnesses=[]
    occupied=set().union(*classes)
    for w in sorted(side-occupied):
        hits=[]
        for cl in classes:
            es=[]
            for x in cl:
                if (min(w,x),max(w,x)) in Eset:es.append([w,x])
            hits.append(es)
        if all(hits):witnesses.append({'vertex':w,'class_edge_witnesses':hits})
    W={x['vertex'] for x in witnesses};wedges=[[u,v] for u,v in sedges if u in W and v in W]
    raw_classes=[{23},{35},{57,159},{86}]
    rawW=[]
    for w in sorted(side-set().union(*raw_classes)):
        hits=[]
        for cl in raw_classes:
            es=[[w,x] for x in cl if (min(w,x),max(w,x)) in Eset];hits.append(es)
        if all(hits):rawW.append({'vertex':w,'class_edge_witnesses':hits})
    RW={x['vertex'] for x in rawW};rawedges=[[u,v] for u,v in sedges if u in RW and v in RW]
    rep={'upstream_sha':UPSTREAM_SHA,'q18_side_size':len(side),'anchor_equality_classes':ca,'solver_crosscheck':'Cadical195 and Glucose4 equality classes identical',
         'conditional_color_classes_under_q57_eq_q159':[sorted(x) for x in classes],
         'raw_conditional_common_neighbors':rawW,'raw_witness_edges':rawedges,
         'equality_class_conditional_common_neighbors':witnesses,'equality_class_witness_edges':wedges,
         'has_raw_two_adjacent_fifth_color_witnesses':bool(rawedges),'has_eqclass_two_adjacent_fifth_color_witnesses':bool(wedges),
         'interpretation':'Assume q57=q159 and q23,q35,q57,q86 use four distinct colors, as in forbidden state 01232. Any vertex adjacent to each of the four corresponding color classes must use the fifth color. If two such witness vertices are adjacent, the assumption is impossible. The scan tests this first on raw tracked classes and then after replacing each anchor by its exact forced-equality class, independently reconstructed with CaDiCaL195 and Glucose4.'}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(rep,indent=2)+'\n')
    print(json.dumps({'class_sizes':{k:len(v) for k,v in ca.items()},'raw_witness_vertices':[x['vertex'] for x in rawW],'raw_witness_edges':rawedges,'eqclass_witness_vertices':[x['vertex'] for x in witnesses],'eqclass_witness_edges':wedges},indent=2))
if __name__=='__main__':main()
