#!/usr/bin/env python3
"""Rebuild the archived translation candidates and resume bounded five-color tests.

Every positive model is checked on the original graph. Phase UNSAT is NOT an
original-graph obstruction. CaDiCaL negatives are never promoted.
"""
from __future__ import annotations
import argparse,hashlib,json,multiprocessing,time,traceback
from functools import lru_cache
from itertools import combinations
from pathlib import Path
import numpy as np
from hn_cyclotomic210 import C,ONE,ORIGIN,U,GOLD,MAPS,residues,unit,from_heptagon,selftest
from hn_translation_phase import encode,lift,NoPhaseModel

ROOT=Path(__file__).resolve().parents[1]
INDEX=ROOT/'results/interior-overlap-2026-09-16/ARCHIVE_INDEX.json'
CASES=('g3-shift-2','g3-shift-3','u','one','fork')

def write(p,value):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,indent=2)+'\n')

def semantic(g):
    return hashlib.sha256(json.dumps({k:g[k] for k in ('pts','edges')},sort_keys=True,separators=(',',':')).encode()).hexdigest()

@lru_cache(maxsize=300000)
def isunit(z):return unit(z)

def complete(points):
    if len(set(points))!=len(points):raise ValueError('duplicate exact points')
    red=np.asarray([residues(p) for p in points],dtype=np.int64);edges=[];survivors=0
    for a in range(len(points)-1):
        js=np.arange(a+1,len(points))
        for k,(p,_,_) in enumerate(MAPS):
            js=js[((red[js,k,0]-red[a,k,0])*(red[js,k,1]-red[a,k,1]))%p==1]
        for b0 in js:
            b=int(b0);survivors+=1
            if isunit(points[a]-points[b]):edges.append([a,b])
    return edges,{'all_unordered_pairs':len(points)*(len(points)-1)//2,'filter_survivors':survivors,
      'induced_complete':True,'float_geometry':False,'filter_primes':[p for p,_,_ in MAPS]}

def rebuild(source,name,out):
    start=time.monotonic();selftest();index=json.loads(INDEX.read_text());raw=source.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=index['source_G3_sha256']:raise ValueError('source hash mismatch')
    g=json.loads(raw);base=[from_heptagon(p) for p in g['pts']]
    es,_=complete(base)
    if es!=g['edges']:raise ValueError('source edge completion mismatch')
    if name.startswith('g3-shift-'):
        shifts=[C(tuple([i]+[0]*47)) for i in range(int(name[-1]))]
    else:
        base=sorted({p.rotate(t)+s for s,t in zip((ORIGIN,U,GOLD,U.conjugate()),(21,-21,126,84)) for p in base},key=C.key)
        shifts={'u':[ORIGIN,U],'one':[ORIGIN,ONE],'fork':[ORIGIN,U,U.conjugate()]}[name]
    points=sorted({p+s for p in base for s in shifts},key=C.key);loc={p:i for i,p in enumerate(points)}
    copies=[[loc[p+s] for p in base] for s in shifts];edges,geom=complete(points)
    b=ONE if name.startswith('g3-shift-') else GOLD
    graph={'field':'Q(zeta210)','pts':[p.pack() for p in points],'edges':edges,
      'ports':{'a':loc[ORIGIN],'b':loc[b]},'target_is_phi':not name.startswith('g3-shift-'),
      'construction':{'case':name,'source_sha256':index['source_G3_sha256'],'isometries_only':True},'audit':geom}
    expected=next(x for x in index['cases'] if x['case']==name)
    if (len(points),len(edges),semantic(graph))!=(expected['vertices'],expected['edges'],expected['semantic_sha256']):
        raise ValueError('candidate differs from archived geometry')
    write(out/'GRAPH.json',graph);write(out/'COPY_MAPS.json',copies)
    write(out/'REBUILD.json',{'case':name,'vertices':len(points),'edges':len(edges),
      'archive_semantic_hash_matches':True,'semantic_sha256':semantic(graph),'seconds':round(time.monotonic()-start,3)})
    (out/'SOURCE_G3.json').write_bytes(raw)
    return graph,copies

def validate(g,c,k=5):
    if len(c)!=len(g['pts']) or any(type(x)!=int or not 0<=x<k for x in c):raise ValueError('bad coloring')
    if any(c[a]==c[b] for a,b in g['edges']):raise ValueError('monochromatic original edge')

def phase_worker(graph_path,copies,phases,solver,out):
    out=Path(out)
    try:
        from pysat.solvers import Solver
        g=json.loads(Path(graph_path).read_text())
        try:cs,recipe,n=encode(len(g['pts']),g['edges'],copies,phases)
        except NoPhaseModel as exc:
            write(out/'RESULT.json',{'status':'NO_PHASE_MODEL','reason':str(exc),'original_graph_conclusion':None});return
        cnf=f'p cnf {n*5} {len(cs)}\n'+''.join(' '.join(map(str,c))+' 0\n' for c in cs)
        (out/'INPUT.cnf').write_text(cnf);write(out/'RECIPE.json',{'phases':phases,'vertex_lift':recipe,'root_count':n})
        with Solver(name=solver,bootstrap_with=cs) as s:
            ans=s.solve()
            if ans is True:
                colors=lift(s.get_model(),recipe,n);validate(g,colors)
                text=''.join(map(str,colors))+'\n';(out/'COLORING.txt').write_text(text)
                write(out/'RESULT.json',{'status':'SAT','method':'positive_phase_lift','phases':phases,
                  'root_count':n,'vertices':len(colors),'original_edges_checked':len(g['edges']),
                  'coloring_sha256':hashlib.sha256(text.encode()).hexdigest()})
            else:write(out/'RESULT.json',{'status':'PHASE_UNSAT_NOT_ORIGINAL_EVIDENCE' if ans is False else 'UNKNOWN','original_graph_conclusion':None})
    except BaseException:write(out/'RESULT.json',{'status':'ERROR','traceback':traceback.format_exc()})

def phase_probe(path,copies,phases,solver,out,seconds):
    out.mkdir(parents=True,exist_ok=True)
    p=multiprocessing.get_context('fork').Process(target=phase_worker,args=(path,copies,phases,solver,out))
    p.start();p.join(seconds)
    if p.is_alive():
        p.kill();p.join();write(out/'RESULT.json',{'status':'UNKNOWN_TIMEOUT','original_graph_conclusion':None})
    if not (out/'RESULT.json').exists():raise RuntimeError('phase worker exited without result')
    return json.loads((out/'RESULT.json').read_text())

def classify(records):
    sat5=any(r['colors']==5 and r['status']=='SAT' for r in records)
    neg5=any(r['method']=='direct' and r['colors']==5 and r['status']=='UNSAT_PROOF_VERIFIED' for r in records)
    neg6=any(r['method']=='direct' and r['colors']==6 and r['status']=='UNSAT_PROOF_VERIFIED' for r in records)
    if neg6 or (sat5 and neg5):
        raise RuntimeError('contradictory validated results')
    return {'target_A':'NOT_A' if sat5 else ('CANDIDATE_REQUIRES_INDEPENDENT_REVIEW' if neg5 else 'UNKNOWN'),
      'new_HN_bound_claimed':False,'phase_negatives_are_original_evidence':False}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--source',type=Path,required=True)
    ap.add_argument('--case',choices=CASES,required=True);ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--solver',choices=('cadical195','glucose4'),required=True)
    ap.add_argument('--checker',required=True);ap.add_argument('--seconds',type=int,default=90)
    ap.add_argument('--phase-seconds',type=int,default=15);a=ap.parse_args()
    if not 5<=a.seconds<=180 or not 1<=a.phase_seconds<=30:ap.error('invalid bounded time limits')
    from hn_closed_trace_color_probe import run_case
    from hn_certified_color_probe import select_pins
    from hn_cyclotomic210_independent_audit import audit
    a.out.mkdir(parents=True,exist_ok=True)
    control=a.out/'CONTROL_K6.json';write(control,{'pts':list(range(6)),'edges':list(combinations(range(6),2))})
    for k in (5,6):
        r=run_case(control,k,[],a.solver,a.out/'controls'/str(k),30,a.checker)
        expected='SAT' if k==6 else ('UNSAT_PROOF_VERIFIED' if a.solver=='glucose4' else 'UNSAT_UNCHECKED')
        if r['status']!=expected:raise RuntimeError(f'failed abstract control: {r}')
    g,copies=rebuild(a.source,a.case,a.out);write(a.out/'INDEPENDENT_GEOMETRY.json',audit(g))
    records=[]
    def keep(r,method,k,folder):
        if r['status'].startswith('ERROR') or r['status']=='PROOF_CHECK_FAILED':raise RuntimeError(str(r))
        entry={'status':r['status'],'method':method,'colors':k,'folder':folder};records.append(entry)
        result={'case':a.case,'solver':a.solver,'records':records,'classification':classify(records)}
        write(a.out/'SUMMARY.json',result);print(json.dumps(entry),flush=True)
    for k in (5,6):
        folder=f'direct{k}';pins=select_pins(g,k,'ordinary','')
        r=run_case(a.out/'GRAPH.json',k,pins,a.solver,a.out/folder,a.seconds if k==5 else 30,a.checker)
        keep(r,'direct',k,folder)
    if not any(r['colors']==5 and r['status']=='SAT' for r in records):
        for t in range(1,5):
            phases=[(i*t)%5 for i in range(len(copies))]
            if a.case=='fork':phases=[0,t,t]
            folder=f'phase{t}';r=phase_probe(a.out/'GRAPH.json',copies,phases,a.solver,a.out/folder,a.phase_seconds)
            keep(r,'phase',5,folder)
            if r['status']=='SAT':break
    print(json.dumps(classify(records)),flush=True)
if __name__=='__main__':main()
