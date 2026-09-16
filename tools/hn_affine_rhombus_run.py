#!/usr/bin/env python3
"""Resume u/fork with source-G3 affine templates. Positive witnesses only.

A failure/UNSAT of this restricted template is NOT a negative result about the
original graph. All accepted models are lifted and checked on every original edge.
"""
from __future__ import annotations
import argparse,hashlib,json,multiprocessing,shutil,traceback,time
from pathlib import Path
from hn_affine_copy_probe import encode,lift,rhombus_templates,NoAffineModel

EXPECTED={'u':(15908,103045,'7a04684f1a91ec20697387f0af155e0d8d38447f1fb19cf38afe7ff6c67fd6dc'),
          'fork':(23090,154809,'bf17bfe425178823c16d2b3c586ebc8e4706eb2bd6866f6571e4a6223b272af1')}
SOURCE='90096518a3c10de93066f6fee70a0b16a218a094de5e5b35285089472d646b8a'
RHOMBUS='6e341fc9c74f5a7b03ec07a49abe7ba71ea73ec06d199440c9e63dc95c4bebb7'

def sha(raw):return hashlib.sha256(raw).hexdigest()
def semantic(g):return sha(json.dumps({k:g[k] for k in ('pts','edges')},sort_keys=True,separators=(',',':')).encode())
def write(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(x,indent=2)+'\n');tmp.replace(p)
def validate(g,c,k=5):
    if len(c)!=len(g['pts']) or any(type(x)!=int or not 0<=x<k for x in c):raise ValueError('bad colors')
    if any(c[u]==c[v] for u,v in g['edges']):raise ValueError('monochromatic original edge')

def prepare(parent,rhombus,case):
    g=json.loads((parent/'GRAPH.json').read_text());base=json.loads((rhombus/'GRAPH.json').read_text())
    raw=(parent/'SOURCE_G3.json').read_bytes();source=json.loads(raw)
    if (len(g['pts']),len(g['edges']),semantic(g))!=EXPECTED[case]:raise ValueError('wrong parent graph')
    if semantic(base)!=RHOMBUS or sha(raw)!=SOURCE:raise ValueError('wrong source/rhombus')
    outer=json.loads((parent/'COPY_MAPS.json').read_text())
    inner=json.loads((rhombus/'COPY_MAPS.json').read_text())['copies']
    if len(outer)!=(2 if case=='u' else 3) or len(inner)!=4:raise ValueError('wrong copy counts')
    if any(len(cp)!=8520 or len(set(cp))!=8520 or any(type(v)!=int or not 0<=v<len(g['pts']) for v in cp) for cp in outer):raise ValueError('bad outer maps')
    if any(len(cp)!=2131 or len(set(cp))!=2131 or any(type(v)!=int or not 0<=v<8520 for v in cp) for cp in inner):raise ValueError('bad inner maps')
    if any(g['pts'][j]!=base['pts'][i] for i,j in enumerate(outer[0])):raise ValueError('base order mismatch')
    copies=[[cp[j] for j in small] for cp in outer for small in inner]
    edges=set(map(tuple,g['edges']))
    if any(tuple(sorted((cp[u],cp[v]))) not in edges for cp in copies for u,v in source['edges']):raise ValueError('a source edge is not preserved')
    if set(v for cp in copies for v in cp)!=set(range(len(g['pts']))):raise ValueError('uncovered vertex')
    # These are template pins, never an ordinary-colorability equivalence claim.
    def idx(value):
        matches=[i for i,p in enumerate(source['pts']) if p['a'][0]==value*p['den'] and not any(p['a'][1:]) and not any(p['b'])]
        if len(matches)!=1:raise ValueError('source endpoint is not unique')
        return matches[0]
    return g,copies,[(idx(0),0),(idx(1),1)]

def worker(graph_path,copies,pins,case,t,solver,out):
    out=Path(out);start=time.monotonic()
    try:
        from pysat.solvers import Solver
        import pysat
        g=json.loads(Path(graph_path).read_text());slopes,offsets=rhombus_templates(case,t)
        base={'case':case,'multiplier':t,'solver':solver,'python_sat_version':pysat.__version__,
              'semantic_sha256':semantic(g),'original_graph_negative_claim':False}
        try:cs,recipe,n=encode(len(g['pts']),g['edges'],copies,slopes,offsets,source_pins=pins)
        except NoAffineModel as exc:
            write(out/'RESULT.json',dict(base,status='NO_AFFINE_MODEL',reason=str(exc)));return
        cnf=f'p cnf {n*5} {len(cs)}\n'+''.join(' '.join(map(str,c))+' 0\n' for c in cs)
        (out/'INPUT.cnf').write_text(cnf)
        write(out/'RECIPE.json',{'slopes':slopes,'offsets':offsets,'source_pins':pins,'root_count':n,'vertex_lift':recipe})
        base.update(roots=n,clauses=len(cs),cnf_sha256=sha(cnf.encode()))
        write(out/'RESULT.json',dict(base,status='RUNNING'))
        with Solver(name=solver,bootstrap_with=cs) as s:
            ans=s.solve()
            if ans is not True:
                write(out/'RESULT.json',dict(base,status='AFFINE_UNSAT_NOT_ORIGINAL_EVIDENCE' if ans is False else 'UNKNOWN'));return
            model=s.get_model();pos={x for x in model if x>0}
            if not all(any((lit>0)==(abs(lit) in pos) for lit in clause) for clause in cs):raise ValueError('invalid Boolean model')
            colors=lift(model,recipe,n);validate(g,colors)
        text=''.join(map(str,colors))+'\n';(out/'COLORING.txt').write_text(text)
        pair=[colors[g['ports'][p]] for p in ('a','b')]
        write(out/'RESULT.json',dict(base,status='SAT',vertices=len(colors),original_edges_checked=len(g['edges']),
           coloring_sha256=sha(text.encode()),terminal_colors=pair,terminals_equal=pair[0]==pair[1],seconds=round(time.monotonic()-start,3)))
    except BaseException:write(out/'RESULT.json',{'status':'ERROR','original_graph_negative_claim':False,'traceback':traceback.format_exc()})

def run_probe(graph,copies,pins,case,t,solver,out,seconds):
    out.mkdir(parents=True,exist_ok=True)
    p=multiprocessing.get_context('fork').Process(target=worker,args=(graph,copies,pins,case,t,solver,out))
    p.start();p.join(seconds)
    if p.is_alive():
        p.kill();p.join();write(out/'RESULT.json',{'status':'UNKNOWN_TIMEOUT','case':case,'multiplier':t,'solver':solver,'wall_seconds':seconds,'original_graph_negative_claim':False})
    if not (out/'RESULT.json').exists():raise RuntimeError('worker exited without result')
    result=json.loads((out/'RESULT.json').read_text())
    if result['status']=='ERROR':raise RuntimeError(str(result))
    return result

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--parent',type=Path,required=True);ap.add_argument('--rhombus',type=Path,required=True)
    ap.add_argument('--case',choices=EXPECTED,required=True);ap.add_argument('--solver',choices=('cadical195','glucose4'),required=True)
    ap.add_argument('--out',type=Path,required=True);ap.add_argument('--seconds',type=int,default=60)
    a=ap.parse_args()
    if not 1<=a.seconds<=120:ap.error('seconds must be in 1..120')
    a.out.mkdir(parents=True,exist_ok=True);g,copies,pins=prepare(a.parent,a.rhombus,a.case)
    shutil.copyfile(a.parent/'GRAPH.json',a.out/'GRAPH.json');write(a.out/'G3_COPY_MAPS.json',copies)
    write(a.out/'INPUT_IDENTITY.json',{'case':a.case,'semantic_sha256':semantic(g),'source_sha256':SOURCE,'rhombus_semantic_sha256':RHOMBUS,
          'copies':len(copies),'source_pins':pins,'source_edges_preserved':True})
    records=[]
    for t in (1,4,2,3):
        r=run_probe(a.out/'GRAPH.json',copies,pins,a.case,t,a.solver,a.out/f't{t}',a.seconds);records.append(r)
        sat=[x for x in records if x['status']=='SAT']
        summary={'case':a.case,'solver':a.solver,'records':records,'target_A':'NOT_A' if sat else 'UNKNOWN',
                 'specified_pair_B':'NOT_FORCED_EQUAL' if any(not x['terminals_equal'] for x in sat) else 'UNKNOWN',
                 'H_phi':'NOT_H_PHI' if any(x['terminals_equal'] for x in sat) else 'UNKNOWN',
                 'new_HN_bound_claimed':False,'negative_template_results_are_original_evidence':False}
        write(a.out/'SUMMARY.json',summary);print(json.dumps(r),flush=True)
        if any(x['terminals_equal'] for x in sat) and any(not x['terminals_equal'] for x in sat):break
if __name__=='__main__':main()
