#!/usr/bin/env python3
"""Try the unchanged fork template with soft phases from a validated u coloring.

No variables are frozen. Seed proximity and every negative remain non-evidence
about ordinary colorability. Only full original-graph witnesses are accepted.
"""
from __future__ import annotations
import argparse,collections,json,multiprocessing,shutil,time,traceback
from pathlib import Path
from hn_affine_copy_probe import encode,lift,rhombus_templates
from hn_affine_rhombus_run import semantic,validate,write,sha,EXPECTED

def seed_phases(source_colors,first_copy,recipe,roots,k=5):
    if len(source_colors)!=len(first_copy):raise ValueError('source length')
    votes=[collections.Counter() for _ in range(roots)]
    for x,v in zip(source_colors,first_copy):
        r,a,b=recipe[v];votes[r][(x-b)*pow(a,-1,k)%k]+=1
    if any(not d for d in votes):raise ValueError('unseeded root')
    preferred=[max(range(k),key=lambda c:(votes[r][c],-c)) for r in range(roots)]
    phases=[r*k+c+1 if c==preferred[r] else -(r*k+c+1) for r in range(roots) for c in range(k)]
    return phases

def worker(parent,seed,t,solver,out):
    start=time.monotonic();out=Path(out)
    try:
        from pysat.solvers import Solver
        parent=Path(parent);seed=Path(seed)
        g=json.loads((parent/'GRAPH.json').read_text());u=json.loads((seed/'GRAPH.json').read_text())
        for name,graph in [('fork',g),('u',u)]:
            if (len(graph['pts']),len(graph['edges']),semantic(graph))!=EXPECTED[name]:raise ValueError('wrong graph')
        seed_result=json.loads((seed/f't{t}/RESULT.json').read_text());raw=(seed/f't{t}/COLORING.txt').read_bytes()
        if seed_result['status']!='SAT' or sha(raw)!=seed_result['coloring_sha256']:raise ValueError('wrong seed witness')
        colors=[int(c) for c in raw.decode().strip()];validate(u,colors)
        ucps=json.loads((seed/'G3_COPY_MAPS.json').read_text());fcps=json.loads((parent/'G3_COPY_MAPS.json').read_text())
        identity=json.loads((parent/'INPUT_IDENTITY.json').read_text());sl,of=rhombus_templates('fork',t)
        cs,recipe,n=encode(len(g['pts']),g['edges'],fcps,sl,of,source_pins=identity['source_pins'])
        cnf=f'p cnf {n*5} {len(cs)}\n'+''.join(' '.join(map(str,c))+' 0\n' for c in cs)
        if cnf!=(parent/f't{t}/INPUT.cnf').read_text():raise ValueError('CNF differs from unseeded run')
        phases=seed_phases([colors[v] for v in ucps[0]],fcps[0],recipe,n)
        (out/'INPUT.cnf').write_text(cnf);write(out/'PREFERRED_PHASES.json',phases)
        pos={x for x in phases if x>0}
        info={'case':'fork','multiplier':t,'solver':solver,'semantic_sha256':semantic(g),'seed_coloring_sha256':sha(raw),
              'cnf_sha256':sha(cnf.encode()),'CNF_unchanged_from_unseeded_run':True,'frozen_variables':0,
              'initial_unsatisfied_clauses':sum(not any((v>0)==(abs(v) in pos) for v in cl) for cl in cs),
              'original_graph_negative_claim':False}
        with Solver(name=solver,bootstrap_with=cs) as s:
            s.set_phases(phases);ans=s.solve()
            if ans is not True:
                write(out/'RESULT.json',dict(info,status='AFFINE_UNSAT_NOT_ORIGINAL_EVIDENCE' if ans is False else 'UNKNOWN'));return
            model=s.get_model();pos={v for v in model if v>0}
            if not all(any((v>0)==(abs(v) in pos) for v in cl) for cl in cs):raise ValueError('invalid SAT model')
            lifted=lift(model,recipe,n);validate(g,lifted)
        text=''.join(map(str,lifted))+'\n';(out/'COLORING.txt').write_text(text)
        pair=[lifted[g['ports'][p]] for p in ('a','b')]
        write(out/'RESULT.json',dict(info,status='SAT',vertices=len(lifted),original_edges_checked=len(g['edges']),
           coloring_sha256=sha(text.encode()),terminal_colors=pair,terminals_equal=pair[0]==pair[1],seconds=round(time.monotonic()-start,3)))
    except BaseException:write(out/'RESULT.json',{'status':'ERROR','traceback':traceback.format_exc()})

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ('parent','seed','out'):ap.add_argument('--'+name,type=Path,required=True)
    ap.add_argument('--multiplier',type=int,choices=(1,4),required=True)
    ap.add_argument('--solver',choices=('cadical195','glucose4'),required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(a.parent/'GRAPH.json',a.out/'GRAPH.json')
    p=multiprocessing.get_context('fork').Process(target=worker,args=(a.parent,a.seed,a.multiplier,a.solver,a.out))
    p.start();p.join(60)
    if p.is_alive():
        p.kill();p.join();write(a.out/'RESULT.json',{'status':'UNKNOWN_TIMEOUT','case':'fork','multiplier':a.multiplier,'solver':a.solver,'wall_seconds':60,'original_graph_negative_claim':False})
    if not (a.out/'RESULT.json').exists():raise RuntimeError('no result')
    result=json.loads((a.out/'RESULT.json').read_text());print(json.dumps(result),flush=True)
    if result['status']=='ERROR':raise RuntimeError(str(result))
if __name__=='__main__':main()
