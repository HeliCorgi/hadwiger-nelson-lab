#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from collections import deque
from itertools import combinations
from pathlib import Path
from pysat.solvers import Cadical195
K=5;P,Q=217,490
UPSTREAM_SHA='d1e80998bda337d9fa721f2e96d203ae54e97fc8'
def load(p):return json.loads(Path(p).read_text())
def build(d):
 g=load(d/'g510_k2.json');full=[tuple(map(int,e)) for e in g['edges']];raw=load(d/'B5_MULTICORE.json')['cores'][0];h=[full[i] for i in raw] if raw and isinstance(raw[0],int) else [tuple(map(int,e)) for e in raw];c=[tuple(map(int,e)) for e in load(d/'B5_P2_LEMMA.json')['C_min']];E=sorted({(min(a,b),max(a,b)) for a,b in h});V=sorted({x for e in E for x in e}|{x for e in c for x in e});par={v:v for v in V}
 def f(x):
  while par[x]!=x:par[x]=par[par[x]];x=par[x]
  return x
 def u(a,b):
  a,b=f(a),f(b)
  if a!=b:
   if a>b:a,b=b,a
   par[b]=a
 for a,b in c:u(a,b)
 C={}
 for v in V:C.setdefault(f(v),[]).append(v)
 R=sorted(C,key=lambda r:min(C[r]));qid={r:i for i,r in enumerate(R)};vq={v:qid[f(v)] for v in V};QE=set()
 for a,b in E:
  x,y=vq[a],vq[b]
  if x==y:raise RuntimeError('internal edge')
  QE.add((min(x,y),max(x,y)))
 return C,R,vq,sorted(QE)
def sat_k(nodes,edges,k):
 ns=sorted(nodes);idx={v:i for i,v in enumerate(ns)};cls=[]
 for v in ns:
  lits=[idx[v]*k+c+1 for c in range(k)];cls.append(lits)
  for a,b in combinations(lits,2):cls.append([-a,-b])
 for u,v in edges:
  if u in idx and v in idx:
   for c in range(k):cls.append([-(idx[u]*k+c+1),-(idx[v]*k+c+1)])
 with Cadical195(bootstrap_with=cls) as s:return s.solve()
def shrink_non3(nodes,edges):
 cur=set(nodes);changed=True
 while changed:
  changed=False
  for v in sorted(cur):
   tr=cur-{v};te=[e for e in edges if e[0] in tr and e[1] in tr]
   if tr and not sat_k(tr,te,3):cur=tr;changed=True
 return sorted(cur)
def clique4(nodes,edge_set):
 ns=sorted(nodes)
 for a,b,c,d in combinations(ns,4):
  if all((min(x,y),max(x,y)) in edge_set for x,y in combinations([a,b,c,d],2)):return [a,b,c,d]
 return []
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--data-dir',type=Path,required=True);ap.add_argument('--relations',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();C,R,vq,E=build(a.data_dir);rel=load(a.relations);eq=[x['qnode'] for x in rel['forced_equal_to_p']];p,q=vq[P],vq[Q];adj=[set() for _ in R];es=set(E)
 for u,v in E:adj[u].add(v);adj[v].add(u)
 witnesses=[];W={v:set() for v in eq}
 for i,u in enumerate(eq):
  for v in eq[i+1:]:
   common=sorted(adj[u]&adj[v]);cs=set(common);ce=[e for e in E if e[0] in cs and e[1] in cs]
   if common and not sat_k(common,ce,3):
    core=shrink_non3(common,ce);core_set=set(core);core_e=[e for e in ce if e[0] in core_set and e[1] in core_set];k4=clique4(core,es);W[u].add(v);W[v].add(u);witnesses.append({'pair':[u,v],'common_size':len(common),'common_edges':len(ce),'core_qnodes':core,'core_size':len(core),'core_edges':len(core_e),'core_components':[C[R[x]] for x in core],'contains_K4':bool(k4),'K4_qnodes':k4,'K4_components':[C[R[x]] for x in k4]})
 prev={p:None};dq=deque([p])
 while dq:
  u=dq.popleft()
  if u==q:break
  for v in W[u]:
   if v not in prev:prev[v]=u;dq.append(v)
 chain=[]
 if q in prev:
  x=q
  while x is not None:chain.append(x);x=prev[x]
  chain.reverse()
 pairmap={tuple(w['pair']):w for w in witnesses};chain_w=[]
 for u,v in zip(chain,chain[1:]):chain_w.append(pairmap.get((min(u,v),max(u,v))))
 rep={'upstream_sha':UPSTREAM_SHA,'forced_equal_class_size':len(eq),'local_witness_edges':len(witnesses),'local_witness_graph_components':None,'p_qnodes':[p,q],'p_q_connected_by_local_rule':bool(chain),'shortest_local_rule_chain_qnodes':chain,'shortest_local_rule_chain_components':[C[R[x]] for x in chain],'chain_witnesses':chain_w,'all_witnesses':witnesses,'rule':'If u,v had different colors in a 5-coloring, every common neighbor avoids both colors and has only 3 colors available. Therefore a non-3-colorable common-neighborhood subgraph forces c(u)=c(v).'}
 seen=set();ccs=[]
 for s in eq:
  if s in seen:continue
  st=[s];seen.add(s);cc=[]
  while st:
   u=st.pop();cc.append(u)
   for v in W[u]:
    if v not in seen:seen.add(v);st.append(v)
  ccs.append(sorted(cc))
 rep['local_witness_graph_components']=ccs;a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(rep,indent=2));print(json.dumps({k:rep[k] for k in ['forced_equal_class_size','local_witness_edges','p_q_connected_by_local_rule','shortest_local_rule_chain_qnodes']},indent=2))
if __name__=='__main__':main()
