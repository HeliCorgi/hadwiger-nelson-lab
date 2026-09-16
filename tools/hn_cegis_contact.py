#!/usr/bin/env python3
"""Bounded, evidence-aware CEGIS over exact isometric module additions.

A fixed-color extension failure is only a score; free recoloring is mandatory
before any non-colorability claim. UNKNOWN is not a score or a discovery.
Default production target: non-five-colorability. Calibration: Moser spindle/3.
"""
from __future__ import annotations
import argparse, gzip, hashlib, itertools, json, multiprocessing, os, random
import signal, subprocess, time, traceback
from pathlib import Path
from hn_cegis_geometry import P, K, ZERO, ONE, UNIT, ORIGIN, ESCAPE, root, unit, complete, heptagon

SOURCE_SHA='90096518a3c10de93066f6fee70a0b16a218a094de5e5b35285089472d646b8a'

def dump(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    raw=(json.dumps(data,sort_keys=True,separators=(',',':'))+'\n').encode()
    if path.suffix=='.gz':raw=gzip.compress(raw,mtime=0)
    tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_bytes(raw);tmp.replace(path)

def load(path):
    path=Path(path);b=path.read_bytes()
    return json.loads(gzip.decompress(b) if path.suffix=='.gz' else b)

def sha(data):return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def semantic(g):return sha({key:g[key] for key in ('pts','edges')})

def graph_check(g):
    n=len(g['pts']);seen=set()
    for uv in g['edges']:
        if len(uv)!=2 or any(type(i)!=int for i in uv) or not 0<=uv[0]<uv[1]<n:raise ValueError('bad edge')
        if tuple(uv) in seen:raise ValueError('duplicate edge')
        seen.add(tuple(uv))

def validate(g,c,k,pins=()):
    graph_check(g)
    if len(c)!=len(g['pts']) or any(type(x)!=int or not 0<=x<k for x in c):raise ValueError('bad colors')
    if any(c[u]==c[v] for u,v in g['edges']):raise ValueError('monochromatic edge')
    if any(c[v]!=x for v,x in pins):raise ValueError('wrong pins')

def canonical(c):
    d={};return [d.setdefault(x,len(d)) for x in c]

def orbit_blocks(bank,k):
    # Block all renamings so diversity queries cannot return the same partition.
    return [[perm[c] for c in model] for model in bank for perm in itertools.permutations(range(k))]

def clauses(g,k,pins=(),blocks=()):
    if not 2<=k<=7:raise ValueError('bad palette')
    graph_check(g);n=len(g['pts']);cs=[]
    for v in range(n):
        row=[v*k+c+1 for c in range(k)];cs.append(row)
        cs.extend([[-a,-b] for a,b in itertools.combinations(row,2)])
    for u,v in g['edges']:cs.extend([[-(u*k+c+1),-(v*k+c+1)] for c in range(k)])
    for v,c in pins:
        if type(v)!=int or type(c)!=int or not 0<=v<n or not 0<=c<k:raise ValueError('invalid pin')
        cs.append([v*k+c+1])
    for colors in blocks:
        validate(g,colors,k);cs.append([-(v*k+c+1) for v,c in enumerate(colors)])
    return cs

def reference(g,k,pins=(),blocks=()):
    """Exhaustive oracle only for <=9 vertices; used for offline tests."""
    n=len(g['pts'])
    if n>9:raise ValueError('reference size bound')
    for c in itertools.product(range(k),repeat=n):
        if any(c[v]!=x for v,x in pins) or any(tuple(c)==tuple(b) for b in blocks):continue
        if all(c[u]!=c[v] for u,v in g['edges']):return list(c)
    return None

def _worker(g,k,pins,blocks,backend,checker,out,preferences):
    os.setsid();out=Path(out)
    try:
        cs=clauses(g,k,pins,blocks);n=len(g['pts'])
        text=f'p cnf {n*k} {len(cs)}\n'+''.join(' '.join(map(str,c))+' 0\n' for c in cs)
        (out/'INPUT.cnf').write_text(text)
        result={'graph_sha256':semantic(g),'colors':k,'pins':list(pins),'blocked_models':len(blocks),
                'backend':backend,'cnf_sha256':hashlib.sha256(text.encode()).hexdigest()}
        if backend=='reference':
            colors=reference(g,k,pins,blocks)
            result['status']='SAT' if colors is not None else 'UNSAT_EXHAUSTIVE_SMALL'
            result['exhaustive_assignments_upper_bound']=k**n
        elif backend.startswith('external:'):
            r=subprocess.run([backend.split(':',1)[1],str(out/'INPUT.cnf')],capture_output=True,text=True)
            (out/'SOLVER.txt').write_text(r.stdout+'\n'+r.stderr)
            result['status']='UNSAT_UNCHECKED';colors=None
            if r.returncode==10 and 's SATISFIABLE' in r.stdout:
                model=[int(x) for line in r.stdout.splitlines() if line.startswith('v ') for x in line.split()[1:] if x!='0']
                colors=_decode(model,n,k);result['status']='SAT'
            elif r.returncode!=20 or 's UNSATISFIABLE' not in r.stdout:raise RuntimeError('external solver failed')
        else:
            from pysat.solvers import Solver
            if backend!='glucose4':raise ValueError('only glucose4 proof path supported')
            with Solver(name=backend,bootstrap_with=cs,with_proof=True) as solver:
                if preferences:
                    if len(preferences)>n or any(type(c)!=int or not 0<=c<k for c in preferences):raise ValueError('bad phase preferences')
                    solver.set_phases([v*k+c+1 for v,c in enumerate(preferences)])
                answer=solver.solve();colors=_decode(solver.get_model(),n,k) if answer is True else None
                proof=solver.get_proof() if answer is False else None
            result['status']='SAT' if answer is True else ('UNKNOWN' if answer is None else 'UNSAT_UNCHECKED')
            if answer is False:
                if proof is None:raise RuntimeError('missing proof')
                (out/'PROOF.drat').write_text('\n'.join(proof)+'\n')
                if checker:
                    r=subprocess.run([checker,str(out/'INPUT.cnf'),str(out/'PROOF.drat')],capture_output=True,text=True,timeout=45)
                    log=r.stdout+'\n'+r.stderr;(out/'CHECKER.txt').write_text(log)
                    result['status']='UNSAT_PROOF_VERIFIED' if r.returncode==0 and any(x.strip()=='s VERIFIED' for x in log.splitlines()) else 'PROOF_CHECK_FAILED'
        if colors is not None:
            validate(g,colors,k,pins)
            if any(colors==b for b in blocks):raise ValueError('blocked model returned')
            result['model']=colors;result['all_edges_checked']=len(g['edges'])
        dump(out/'RESULT.json',result)
    except BaseException:
        dump(out/'RESULT.json',{'status':'ERROR','traceback':traceback.format_exc()})

def _decode(model,n,k):
    positive={x for x in model if x>0};colors=[]
    for v in range(n):
        row=[c for c in range(k) if v*k+c+1 in positive]
        if len(row)!=1:raise ValueError('model is not one-hot')
        colors.append(row[0])
    return colors

def oracle(g,k,pins,out,seconds,backend='glucose4',checker=None,blocks=(),preferences=None):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True);start=time.monotonic()
    if (out/'RESULT.json').exists():raise ValueError('refuse to overwrite previous probe')
    p=multiprocessing.get_context('fork').Process(target=_worker,args=(g,k,list(pins),list(blocks),backend,checker,out,preferences))
    p.start();p.join(seconds)
    if p.is_alive():
        try:os.killpg(p.pid,signal.SIGKILL)
        except ProcessLookupError:p.kill()
        p.join();dump(out/'RESULT.json',{'status':'UNKNOWN_TIMEOUT','timeout_is_evidence':False})
    if not (out/'RESULT.json').exists():raise RuntimeError('worker exited without result')
    r=load(out/'RESULT.json');r['seconds']=round(time.monotonic()-start,6)
    r['requested_scope']={'graph_sha256':semantic(g),'k':k,'pins':list(pins),'blocks':len(blocks)}
    dump(out/'RESULT.json',r)
    if r['status'] in ('ERROR','PROOF_CHECK_FAILED'):raise RuntimeError(str(r))
    return r

NEG={'UNSAT_PROOF_VERIFIED','UNSAT_EXHAUSTIVE_SMALL'}

def kill_count(results):return sum(r['status'] in NEG for r in results)

def peel(g,k):
    """Empty k-core gives an explicit k-coloring, not a heuristic rejection."""
    adj=[set() for _ in g['pts']]
    for u,v in g['edges']:adj[u].add(v);adj[v].add(u)
    live=set(range(len(adj)));queue=[i for i,a in enumerate(adj) if len(a)<k];order=[];deg=list(map(len,adj))
    while queue:
        v=queue.pop()
        if v not in live:continue
        live.remove(v);order.append(v)
        for u in adj[v]&live:
            deg[u]-=1
            if deg[u]<k:queue.append(u)
    if live:return {'core_vertices':len(live),'model':None}
    c=[-1]*len(adj)
    for v in reversed(order):c[v]=next(x for x in range(k) if all(c[u]!=x for u in adj[v]))
    validate(g,c,k);return {'core_vertices':0,'model':c}

def proposal(g,source,rotation,anchor):
    ps=[P.unpack(p) for p in g['pts']];loc={p:i for i,p in enumerate(ps)};old=len(ps)
    cp=[]
    for p in source:
        q=rotation*(p-anchor)+anchor
        if q not in loc:loc[q]=len(ps);ps.append(q)
        cp.append(loc[q])
    ee,audit=complete(ps);gg={'field':'Q(zeta210,sqrt(-11))','pts':[p.pack() for p in ps],'edges':ee,'center':g['center']}
    oldedges={tuple(e) for e in g['edges']}
    if not oldedges<={tuple(e) for e in ee}:raise ValueError('old edge lost')
    cross=[(u,v) for u,v in ee if u<old<=v]
    shared={v for v in cp if v<old}
    contacts={u for u,v in cross}|shared
    metadata={'old_vertices':old,'added_vertices':len(ps)-old,'old_contact_vertices':len(contacts),
              'shared_old_vertices':len(shared),'cross_edges':len(cross),'new_vertices_outside_source_K':sum(p.b!=ZERO for p in ps[old:]),
              'rotation':rotation.pack(),'anchor':anchor.pack(),'geometry':audit}
    return gg,cp,metadata

def library_extension(g,old,source_colors,cp,k):
    """Positive shortcut only: exhaust color-name permutations of one source model."""
    if len(cp)!=len(source_colors):raise ValueError('bad source coloring')
    for perm in itertools.permutations(range(k)):
        out=list(old)+[-1]*(len(g['pts'])-len(old));ok=True
        for i,v in enumerate(cp):
            col=perm[source_colors[i]]
            if out[v]!=-1 and out[v]!=col:ok=False;break
            out[v]=col
        if ok and all(c>=0 for c in out) and all(out[u]!=out[v] for u,v in g['edges']):
            validate(g,out,k,list(enumerate(old)));return out
    return None # NOT UNSAT: only this stored source coloring was tried.

def delete_center(g):
    p=g['center'];vs=[v for v in range(len(g['pts'])) if v!=p];ids={v:i for i,v in enumerate(vs)}
    return {'pts':[g['pts'][v] for v in vs],'edges':[[ids[u],ids[v]] for u,v in g['edges'] if p not in (u,v)]},vs

def saturated_result(g,k,negative,out,args):
    """A freely checked negative first; then require a coloring with center deleted."""
    if negative['status'] not in NEG:raise ValueError('not a certified free negative')
    parent,vs=delete_center(g)
    r=oracle(parent,k,[],out/'without-center',args.seconds,args.backend,args.checker)
    result={'status':'NON_K_COLORABLE_CANDIDATE_PENDING_GEOMETRY_REVIEW','k':k,'new_HN_bound_claimed':False}
    if r['status']=='SAT':
        c=[k]*len(g['pts'])
        for v,col in zip(vs,r['model']):c[v]=col
        validate(g,c,k+1);result['center_saturation_certified']=True;result['k_plus_one_model']=c
    dump(out/'DISCOVERY.json',result);return result

def initialize(args,out):
    if args.calibration:
        source=[ORIGIN,UNIT,P(root(35)),UNIT+P(root(35))];colors=[0,1,2,0];k=3
        sourcehash='explicit-diamond-in-Q(zeta6)'
    else:
        raw=args.source.read_bytes()
        if args.source.suffix=='.gz':raw=gzip.decompress(raw)
        if hashlib.sha256(raw).hexdigest()!=SOURCE_SHA:raise ValueError('unexpected G3 source')
        original=json.loads(raw);source=[heptagon(p) for p in original['pts']]
        colors=[int(c) for c in args.source_coloring.read_text().strip()];k=5;sourcehash=SOURCE_SHA
    ee,audit=complete(source);center=source.index(ORIGIN)
    g={'field':'Q(zeta210,sqrt(-11))','pts':[p.pack() for p in source],'edges':ee,'center':center}
    if not args.calibration and ee!=original['edges']:raise ValueError('source edge mismatch')
    validate(g,colors,k)
    dump(out/'SOURCE.json.gz',{'points':g['pts'],'colors':colors,'k':k,'source_sha256':sourcehash})
    dump(out/'INITIAL.json.gz',g)
    return source,colors,k,g,[canonical(colors)]

def run(args):
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    if (out/'CHECKPOINT.json').exists():raise ValueError('use a fresh output directory, or --resume to a new directory')
    if args.resume:
        prior=load(args.resume/'CHECKPOINT.json');src=load(args.resume/'SOURCE.json.gz')
        source=[P.unpack(p) for p in src['points']];source_colors=src['colors'];k=src['k']
        g=load(args.resume/'CURRENT.json.gz');bank=prior['bank'];start_round=prior['next_round']
        if args.seed!=prior['seed'] or args.mode!=prior['mode']:raise ValueError('resume seed/mode mismatch')
        if semantic(g)!=prior['current_graph_sha256']:raise ValueError('resume graph hash mismatch')
        for c in bank:validate(g,c,k)
        if complete([P.unpack(p) for p in g['pts']])[0]!=g['edges']:raise ValueError('bad resume geometry')
        dump(out/'SOURCE.json.gz',src)
    else:
        source,source_colors,k,g,bank=initialize(args,out);start_round=0
    records=[];discovery=None
    seen=set(prior.get('seen_graph_sha256',[])) if args.resume else set()
    for step in range(start_round,start_round+args.rounds):
        rng=random.Random(args.seed+1009*step);specs=[(turn,sign,ai) for turn in (0,35,70,140,175) for sign in (1,-1) for ai in (0,1)]
        rng.shuffle(specs)
        screened=[]
        if args.calibration:specs=[(0,1,0)]
        candidates=[]
        for turn,sign,ai in specs:
            if len(candidates)>=args.pool:break
            anchor=ORIGIN if ai==0 else source[source.index(UNIT)]
            rotation=(ESCAPE if sign==1 else ESCAPE.conjugate())*P(root(turn))
            child,cp,meta=proposal(g,source,rotation,anchor)
            h=semantic(child)
            if h in seen or not meta['added_vertices'] or len(child['pts'])>args.max_vertices:continue
            seen.add(h)
            # Exact source-field escape check, NOT a claim that every upper-bound barrier is gone.
            if not meta['new_vertices_outside_source_K']:continue
            if meta['old_contact_vertices']<=1:
                screened.append({'graph_sha256':h,'reason':'one-contact module; a stored source coloring can be color-renamed to extend any parent coloring'})
                continue
            folder=out/f'round-{step:03d}'/f'candidate-{len(candidates):02d}'
            dump(folder/'GRAPH.json.gz',child);dump(folder/'PLACEMENT.json',meta)
            core=peel(child,k);ext=[]
            for bidx,c in enumerate(bank):
                model=library_extension(child,c,source_colors,cp,k)
                if model is not None:
                    r={'status':'SAT_LIBRARY','model':model,'all_edges_checked':len(child['edges'])}
                    dump(folder/f'fixed-{bidx}'/'RESULT.json',r)
                else:r=oracle(child,k,list(enumerate(c)),folder/f'fixed-{bidx}',args.fixed_seconds,args.backend,args.checker)
                ext.append(r)
            score=kill_count(ext)
            info={'graph_sha256':h,'metadata':meta,'certified_fixed_witness_kills':score,
                  'fixed_statuses':[r['status'] for r in ext],'k_core_vertices':core['core_vertices'],
                  'folder':str(folder.relative_to(out))}
            dump(folder/'SCORE.json',info);candidates.append((child,info,ext,core))
        if not candidates:break
        if args.mode=='random':chosen=rng.randrange(len(candidates))
        else:chosen=max(range(len(candidates)),key=lambda i:(candidates[i][1]['certified_fixed_witness_kills'],candidates[i][1]['metadata']['old_contact_vertices'], -candidates[i][1]['metadata']['added_vertices']))
        child,info,ext,core=candidates[chosen];folder=out/info['folder']
        positives=[r['model'] for r in ext if r['status'] in ('SAT','SAT_LIBRARY')]
        if core['model'] is not None:positives.append(core['model'])
        if positives:free={'status':'SAT_VALIDATED_EXTENSION','model':positives[0]}
        else:
            # Only center color is symmetry-fixed; ALL previous vertex colors are free.
            free=oracle(child,k,[(child['center'],0)],folder/'free',args.seconds,args.backend,args.checker,preferences=bank[0])
        row={'round':step,'selected':info,'candidate_scores':[x[1] for x in candidates],'screened':screened,
             'free_status':free['status'],'fixed_UNSAT_is_global_evidence':False}
        records.append(row)
        if free['status'] in NEG:
            discovery=saturated_result(child,k,free,folder,args);g=child;break
        if free['status'] in ('SAT','SAT_VALIDATED_EXTENSION'):
            positives.append(free['model']);unique={tuple(canonical(c)):canonical(c) for c in positives}
            bank=list(unique.values())[:args.bank];g=child
            # Independent free recolorings, with whole-vector blocks; no old hard pins.
            for attempt in range(args.extra_models):
                r=oracle(g,k,[(g['center'],0)],folder/f'diversify-{attempt}',args.fixed_seconds,args.backend,args.checker,blocks=orbit_blocks(bank,k))
                if r['status']=='SAT':
                    c=canonical(r['model']);validate(g,c,k)
                    if c not in bank:bank.append(c)
                    bank=bank[:args.bank]
                # A blocked-formula negative is NOT an original-graph negative.
        # UNKNOWN leaves current graph unchanged but retains the candidate artifacts.
        for c in bank:validate(g,c,k)
        dump(out/'CURRENT.json.gz',g)
        dump(out/'CHECKPOINT.json',{'next_round':step+1,'seed':args.seed,'mode':args.mode,'bank':bank,'current_graph_sha256':semantic(g),'k':k,'stores_solver_learned_clauses':False,'seen_graph_sha256':sorted(seen)})
        print(json.dumps({'round':step,'selected_vertices':len(child['pts']),'fixed_witness_kills':info['certified_fixed_witness_kills'],'free_status':free['status'],'bank_size':len(bank)}),flush=True)
    dump(out/'CURRENT.json.gz',g)
    result={'status':'CALIBRATION_DISCOVERY' if args.calibration and discovery else ('CANDIDATE_FOR_REVIEW' if discovery else 'BOUNDED_NO_DISCOVERY'),
            'k':k,'seed':args.seed,'mode':args.mode,'rounds':records,'discovery':discovery,
            'new_HN_bound_claimed':False,'current_vertices':len(g['pts']),'current_edges':len(g['edges']),
            'current_graph_sha256':semantic(g),'current_colorings':bank if discovery is None else [],
            'limits':{key:getattr(args,key) for key in ('rounds','pool','seconds','fixed_seconds','max_vertices')},
            'known_periodic_family_membership_not_tested':True,'field_escape_does_not_imply_color_forcing':True}
    dump(out/'SUMMARY.json',result);return result

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source',type=Path);ap.add_argument('--source-coloring',type=Path)
    ap.add_argument('--out',type=Path,required=True);ap.add_argument('--resume',type=Path)
    ap.add_argument('--seed',type=int,default=11);ap.add_argument('--mode',choices=('guided','random'),default='guided')
    ap.add_argument('--calibration',action='store_true');ap.add_argument('--rounds',type=int,default=2)
    ap.add_argument('--pool',type=int,default=3);ap.add_argument('--bank',type=int,default=3)
    ap.add_argument('--extra-models',type=int,default=1);ap.add_argument('--max-vertices',type=int,default=9000)
    ap.add_argument('--seconds',type=float,default=30);ap.add_argument('--fixed-seconds',type=float,default=3)
    ap.add_argument('--backend',default='glucose4');ap.add_argument('--checker')
    args=ap.parse_args()
    if not args.calibration and not args.resume and (not args.source or not args.source_coloring):ap.error('source and source coloring required')
    if not(1<=args.rounds<=10 and 1<=args.pool<=8 and 1<=args.bank<=6 and 0<=args.extra_models<=3 and 0<args.seconds<=120 and 0<args.fixed_seconds<=15 and 7<=args.max_vertices<=25000):ap.error('out of bounded limits')
    run(args)
if __name__=='__main__':main()
