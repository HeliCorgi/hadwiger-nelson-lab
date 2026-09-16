#!/usr/bin/env python3
"""Verify archived CEGIS results and export a bounded-run record (no SAT search).

Inputs are the four original artifact ZIPs, named as in ARTIFACTS. Only stdlib
is used. Positive colorings, semantic graph hashes, CNF byte hashes and fixed
CNF unit-propagation conflicts are rechecked. Unit distances are NOT reproved;
separate geometry audit records remain explicitly attributed to the Actions run.
"""
from __future__ import annotations
import argparse, collections, csv, gzip, hashlib, io, json, zipfile
from pathlib import Path

RUN = 35083448620
ARTIFACTS = {
    '11-guided': (10441088371, '1d5038eaeeb736672c2a069895da23ae6935c1ab0d031e2c31ce211cb69e5c45'),
    '11-random': (10440963657, 'cb8f23effb5d882e18632816ff107b88d4598db3ed380e5b804b50ce4b3501a9'),
    '29-guided': (10440929191, '0ef9097b5d2c156520fadb7d99dd36c2a571c0381403a41c88895fa1b9b238db'),
    '29-random': (10441173499, '908ed73888aa0c8a3dec441af90a638418837ec5dfbd6121b89726f57290c013'),
}

def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)

def canonical(data) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(',', ':')).encode()

def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def semantic(g: dict) -> str:
    return digest(canonical({key: g[key] for key in ('pts', 'edges')}))

def get(z: zipfile.ZipFile, name: str):
    raw = z.read(name)
    return json.loads(gzip.decompress(raw) if name.endswith('.gz') else raw)

def validate(g: dict, colors: list[int], k: int = 5, pins=()) -> None:
    n = len(g['pts'])
    require(len(colors) == n and all(type(c) is int and 0 <= c < k for c in colors), 'bad color vector')
    seen = set()
    for e in g['edges']:
        require(len(e) == 2 and all(type(v) is int for v in e) and 0 <= e[0] < e[1] < n, 'bad edge')
        require(tuple(e) not in seen, 'duplicate edge')
        seen.add(tuple(e))
        require(colors[e[0]] != colors[e[1]], 'monochromatic edge')
    require(all(colors[v] == c for v, c in pins), 'pin violation')

def cnf_parse(raw: bytes) -> tuple[int, list[list[int]]]:
    header = None
    cs, pending = [], []
    for line in raw.decode('ascii').splitlines():
        line = line.strip()
        if not line or line.startswith('c'):
            continue
        if line.startswith('p '):
            fields = line.split()
            require(header is None and len(fields) == 4 and fields[:2] == ['p','cnf'], 'bad DIMACS header')
            header = (int(fields[2]), int(fields[3])); continue
        require(header is not None, 'missing header')
        for x in map(int, line.split()):
            require(abs(x) <= header[0], 'variable outside header')
            if x == 0:
                cs.append(pending); pending = []
            else:
                pending.append(x)
    require(header is not None and not pending and len(cs) == header[1], 'bad clause count')
    return header[0], cs

def unit_conflict(cs: list[list[int]]) -> bool:
    """A conflict is a proof for this exact CNF, not for an unpinned graph."""
    true = set()
    while True:
        added = False
        for clause in cs:
            if any(x in true for x in clause):
                continue
            left = [x for x in clause if -x not in true]
            if not left:
                return True
            if len(left) == 1 and left[0] not in true:
                true.add(left[0]); added = True
        if not added:
            return False

def write_json(path: Path, data) -> None:
    path.write_bytes(json.dumps(data, ensure_ascii=False, indent=2).encode() + b'\n')

def run(source: Path, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=False)
    rows, arms, witnesses, checkpoints, records = [], [], [], [], []
    totals = collections.Counter()
    for arm, (artifact_id, expected) in ARTIFACTS.items():
        path = source / f'cegis-{arm}-{RUN}.zip'
        require(digest(path.read_bytes()) == expected, f'ZIP hash mismatch: {arm}')
        with zipfile.ZipFile(path) as z:
            names = set(z.namelist())
            s = get(z, 'output/SUMMARY.json'); cp = get(z, 'output/CHECKPOINT.json')
            current = get(z, 'output/CURRENT.json.gz'); geometry = get(z, 'output/INDEPENDENT_AUDIT.json')
            require(s['status'] == 'BOUNDED_NO_DISCOVERY' and s['discovery'] is None and not s['new_HN_bound_claimed'], 'unexpected discovery')
            require(semantic(current) == s['current_graph_sha256'] == cp['current_graph_sha256'] == geometry['graph_sha256'], 'graph binding mismatch')
            require(cp['bank'] == s['current_colorings'] and cp['next_round'] == 4, 'checkpoint mismatch')
            require(geometry['status'] == 'PASS' and geometry['edges'] == len(current['edges']), 'bad Actions audit')
            for model in cp['bank']:
                validate(current, model)
            checkpoints.append({'arm': arm, 'artifact_id': artifact_id, 'checkpoint': cp,
                'checkpoint_sha256': digest(z.read('output/CHECKPOINT.json')),
                'current_file_sha256': digest(z.read('output/CURRENT.json.gz')),
                'source_file_sha256': digest(z.read('output/SOURCE.json.gz'))})
            counts = collections.Counter()
            for rnd in s['rounds']:
                selected = rnd['selected']['folder']
                for c in rnd['candidate_scores']:
                    folder = 'output/' + c['folder']
                    g = get(z, folder + '/GRAPH.json.gz')
                    require(semantic(g) == c['graph_sha256'], 'candidate hash mismatch')
                    fixed = [get(z, n) for n in sorted(names) if n.startswith(folder+'/fixed-') and n.endswith('/RESULT.json')]
                    require([r['status'] for r in fixed] == c['fixed_statuses'], 'fixed status mismatch')
                    positive = [r for r in fixed if r['status'] in ('SAT','SAT_LIBRARY')]
                    for result in positive:
                        validate(g, result['model'], pins=result.get('pins', []))
                        witnesses.append({'arm': arm, 'artifact_id': artifact_id, 'folder': c['folder'],
                            'graph_sha256': semantic(g), 'colors': ''.join(map(str,result['model']))})
                    negative = sum(r['status'] == 'UNSAT_PROOF_VERIFIED' for r in fixed)
                    require(negative == c['certified_fixed_witness_kills'], 'score mismatch')
                    classification = 'NOT_A' if positive else 'UNKNOWN'
                    counts[classification] += 1; counts['fixed_blocked'] += bool(negative)
                    rows.append({'arm': arm, 'round': rnd['round'], 'candidate': c['folder'],
                        'vertices': len(g['pts']), 'edges': len(g['edges']),
                        'target_A': classification, 'fixed_status': '|'.join(c['fixed_statuses']),
                        'free_status': rnd['free_status'] if selected == c['folder'] else 'NOT_RUN',
                        'graph_sha256': semantic(g), 'artifact_id': artifact_id})
                if rnd['free_status'] == 'UNKNOWN_TIMEOUT': counts['free_timeouts'] += 1
            for name in sorted(names):
                if not name.endswith('/RESULT.json'):
                    continue
                result = get(z, name); cnf_name = name[:-len('RESULT.json')] + 'INPUT.cnf'
                if cnf_name in names:
                    raw = z.read(cnf_name); sh = digest(raw)
                    if 'cnf_sha256' in result:
                        require(sh == result['cnf_sha256'], 'CNF byte hash mismatch')
                    totals['saved_CNF_files'] += 1
                    if result['status'] == 'UNSAT_PROOF_VERIFIED':
                        require('/fixed-' in name, 'unexpected free negative')
                        checker = z.read(name[:-len('RESULT.json')]+'CHECKER.txt').decode()
                        require(any(x.strip() == 's VERIFIED' for x in checker.splitlines()), 'checker not verified')
                        _, clauses = cnf_parse(raw)
                        require(unit_conflict(clauses), 'fixed contradiction not reproduced')
                        totals['fixed_conflicts_reproved'] += 1
                if '/diversify-' in name:
                    require(result['status'] == 'UNKNOWN_TIMEOUT', 'unexpected diversification result')
                    totals['diversification_timeouts'] += 1
                records.append({'arm':arm, 'path':name, 'status':result['status'],
                    'result_sha256':digest(z.read(name)),
                    'cnf_sha256':digest(z.read(cnf_name)) if cnf_name in names else None})
            arms.append({'arm':arm, 'artifact_id':artifact_id, 'artifact_zip_sha256':expected,
                'candidate_evaluations': sum(counts[k] for k in ('NOT_A','UNKNOWN')),
                **dict(counts), 'retained_vertices':len(current['pts']), 'retained_edges':len(current['edges']),
                'retained_graph_sha256':semantic(current), 'next_round':cp['next_round'],
                'retained_colorings':len(cp['bank']), 'actions_geometry_audit':geometry,
                'checkpoint_sha256':digest(z.read('output/CHECKPOINT.json'))})
            totals.update(counts)
    require(len(rows)==24 and len(witnesses)==12 and totals['fixed_conflicts_reproved']==7, 'unexpected totals')
    summary = {'run_id':RUN, 'status':'RECORDED_BOUNDED_NO_DISCOVERY', 'new_HN_bound_claimed':False,
        'pr_head_sha':'7fb39ba28fe64bc35f0fbdc6ded444d41d515ee7',
        'executed_merge_sha':'907902493914541888a0d0630b74211794cb90a9',
        'base_main_sha':'2275bbacac02776d0c8ef736cc47869befb2b9af',
        'candidate_evaluations':len(rows), 'totals':dict(totals), 'arms':arms,
        'scope':'12 positive five-color candidates; 12 UNKNOWN. Fixed-parent conflicts are not free-coloring impossibility.',
        'geometry_reproved_by_this_script':False,
        'resume':'Use output/CHECKPOINT.json with CURRENT.json.gz and SOURCE.json.gz; next_round=4. Original workflow restores round 2.',
        'artifact_expiry_UTC':'2026-12-15T10:09:33Z',
        'evidence':'Full graph/CNF/proof records remain in original hash-bound Actions artifacts; verify_export.py can export full witness/checkpoint bundle.'}
    write_json(out/'SUMMARY.json', summary)
    write_json(out/'PROBE_INDEX.json', records)
    with (out/'CANDIDATES.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
    full = {'run_id':RUN, 'witnesses':witnesses, 'checkpoints':checkpoints}
    raw=canonical(full)+b'\n'
    # Fix the header OS byte too, so compressed bytes do not depend on Python version.
    packed=bytearray(gzip.compress(raw,mtime=0));packed[9]=255
    (out/'WITNESSES_AND_CHECKPOINTS.json.gz').write_bytes(packed)
    write_json(out/'EXPORT_HASHES.json', {'uncompressed_sha256':digest(raw), 'gzip_sha256':digest(packed),
        'candidate_csv_sha256':digest((out/'CANDIDATES.csv').read_bytes()),
        'probe_index_sha256':digest((out/'PROBE_INDEX.json').read_bytes())})
    print(json.dumps({'candidates':len(rows),'witnesses':len(witnesses),'totals':dict(totals)}))
    return summary

if __name__ == '__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--artifact-dir',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();run(args.artifact_dir,args.out)
