#!/usr/bin/env python3
from __future__ import annotations

import argparse,json,heapq
from itertools import combinations
from pathlib import Path
from separator_interface import P,Q,UPSTREAM_SHA,build,components_without,min_vertex_cut

OUTER=[0,6,8,9,10,266]
CLASSES={
 '5-6':[3,5,6,22,33,54,63,65,86,189,210,222,252],
 '8-9':[1,8,9,17,19,55,61,71,72,74,82,100,104],
 '0-10':[0,10,39,62,98,105,214,251],
}
TARGETS={'5-6':(5,6),'8-9':(8,9),'0-10':(0,10)}
LOCAL_ZERO={'5-6':{(5,22)},'8-9':{(8,17)},'0-10':{(0,62)}}


def minimax_path(nodes,weights,s,t,zero_edges):
    adj={x:[] for x in nodes}
    for (a,b),w in weights.items():
        ww=0 if (min(a,b),max(a,b)) in zero_edges else w
        adj[a].append((b,ww,w));adj[b].append((a,ww,w))
    inf=10**9;dist={x:inf for x in nodes};prev={};dist[s]=0;pq=[(0,0,s)]
    while pq:
        d,h,x=heapq.heappop(pq)
        if d!=dist[x]:continue
        if x==t:break
        for y,ew,raw in adj[x]:
            nd=max(d,ew)
            if nd<dist[y]:
                dist[y]=nd;prev[y]=(x,raw,ew);heapq.heappush(pq,(nd,h+1,y))
    path=[t];edges=[];x=t
    while x!=s:
        p,raw,ew=prev[x];edges.append({'pair':[p,x],'min_cut':raw,'route_weight':ew});path.append(p);x=p
    path.reverse();edges.reverse();return dist[t],path,edges


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--data-dir',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    C,R,vq,E=build(a.data_dir);n=len(R);p,q=vq[P],vq[Q];_,S=min_vertex_cut(n,E,p,q)
    if p!=5 or S!=OUTER:raise RuntimeError((p,S))
    cc=components_without(n,E,S);pc=next(x for x in cc if p in x);left=set(pc)|set(S);ledges=[(u,v) for u,v in E if u in left and v in left]
    old=sorted(left);mp={v:i for i,v in enumerate(old)};redges=[(mp[u],mp[v]) for u,v in ledges]
    result={}
    for name,cls in CLASSES.items():
        weights={};details={}
        for u,v in combinations(sorted(cls),2):
            cv,cut=min_vertex_cut(len(old),redges,mp[u],mp[v]);sep=[old[x] for x in cut]
            weights[(u,v)]=cv
            comps=components_without(len(old),redges,cut);comps=[[old[x] for x in c] for c in comps]
            uc=next(c for c in comps if u in c);vc=next(c for c in comps if v in c)
            details[f'{u}-{v}']={'pair':[u,v],'min_cut':cv,'separator_qnodes':sep,'u_component_size':len(uc),'v_component_size':len(vc),'other_component_sizes':[len(c) for c in comps if c is not uc and c is not vc]}
        z={(min(u,v),max(u,v)) for u,v in LOCAL_ZERO[name]}
        score,path,pedges=minimax_path(sorted(cls),weights,*TARGETS[name],z)
        for e in pedges:
            a1,b1=e['pair'];e.update(details[f'{min(a1,b1)}-{max(a1,b1)}'])
            e['is_known_local_k4_equality']=(min(a1,b1),max(a1,b1)) in z
        vals=sorted(weights.values())
        result[name]={'equality_class':sorted(cls),'pair_count':len(weights),'min_cut_min':min(vals),'min_cut_median':vals[len(vals)//2],'min_cut_max':max(vals),
                      'pairs_with_cut_le_8':sorted([{'pair':list(k),'min_cut':v,'separator_qnodes':details[f'{k[0]}-{k[1]}']['separator_qnodes']} for k,v in weights.items() if v<=8],key=lambda x:(x['min_cut'],x['pair'])),
                      'known_local_k4_edges':[list(x) for x in sorted(z)],'best_minimax_route_score':score,'best_minimax_route':path,'best_minimax_route_edges':pedges}
    rep={'upstream_sha':UPSTREAM_SHA,'left_bag_size':len(left),'results':result,
         'interpretation':'Every listed class consists of vertices already independently verified to be forced equal in all 5-colorings of the 267-qnode left bag. This scan asks whether the target equality can be factored through intermediate equal-class vertices so that each nonlocal step crosses a much smaller vertex separator. Known one-step K4 common-neighborhood equalities are assigned route weight zero; all other route edges are weighted by exact minimum vertex-cut size.'}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(rep,indent=2)+'\n')
    print(json.dumps({k:{'cut_range':[v['min_cut_min'],v['min_cut_median'],v['min_cut_max']],'le8_count':len(v['pairs_with_cut_le_8']),'route_score':v['best_minimax_route_score'],'route':v['best_minimax_route'],'route_edges':v['best_minimax_route_edges']} for k,v in result.items()},indent=2))
if __name__=='__main__':main()
