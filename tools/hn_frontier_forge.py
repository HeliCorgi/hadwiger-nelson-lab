#!/usr/bin/env python3
"""Unconditional exact copies glued along newly created frontier edges.

Only literal unit-distance edges are added. Old colorings are fixed solely in
candidate-scoring experiments; the two reported graph decisions are always
unconditional 5-colorability and 5-colorability with c217 != c490.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import random
import threading
from pathlib import Path
from time import monotonic

import numpy as np
from pysat.solvers import Cadical195, Glucose4
from hn_exact import K2, ONE, unit_modulus
from hn_unconditional_scan import color_cnf, valid_coloring, write_json


def pack(z):
    return {'a': z.a, 'b': z.b, 'den': z.den}


def sig(z):
    return (tuple(z.a), tuple(z.b), z.den)


def sat_call(n, edges, assumptions, budget, seconds):
    started = monotonic()
    with Glucose4(bootstrap_with=color_cnf(n, edges)) as solver:
        solver.conf_budget(budget)
        timer = threading.Timer(max(.05, seconds), solver.interrupt)
        timer.daemon = True
        timer.start()
        try:
            result = solver.solve_limited(assumptions=assumptions, expect_interrupt=True)
        finally:
            timer.cancel()
            timer.join()
            solver.clear_interrupt()
        model = None
        if result is True:
            positive = set(solver.get_model())
            model = [next(c for c in range(5) if 5*v+c+1 in positive) for v in range(n)]
            assert valid_coloring(model, n, edges)
            assert all((5*v+c+1 in positive) for v, c in enumerate(model))
            assert all(lit in positive for lit in assumptions)
        return {'status': 'SAT' if result is True else 'UNSAT_UNCERTIFIED' if result is False else 'UNKNOWN',
                'model': model, 'seconds': round(monotonic()-started, 3), 'conflict_budget': budget,
                'wall_guard_seconds': seconds, 'solver': 'Glucose4'}


def compose(points, edges, base, bedges, rotation, translation, reflection):
    assert unit_modulus(rotation)
    image = [rotation*(z.conj() if reflection else z)+translation for z in base]
    merged = list(points)
    loc = {z: i for i, z in enumerate(points)}
    mapping = []
    for z in image:
        if z not in loc:
            loc[z] = len(merged)
            merged.append(z)
        mapping.append(loc[z])
    copy_edges = {tuple(sorted((mapping[u], mapping[v]))) for u, v in bedges}
    existing = set(edges)
    united = existing | copy_edges
    # Floating point proposes pairs only. All accepted edges pass exact K2 norm.
    oldxy = np.array([z.emb() for z in points], dtype=np.complex128)
    newxy = np.array([z.emb() for z in image], dtype=np.complex128)
    distance = np.abs(oldxy[:, None]-newxy[None, :])
    ii, jj = np.nonzero(np.abs(distance-1.0) < 1e-7)
    cross = set()
    for u, j in zip(ii.tolist(), jj.tolist()):
        v = mapping[j]
        pair = tuple(sorted((u, v)))
        if u != v and pair not in united and unit_modulus(merged[u]-merged[v]):
            cross.add(pair)
    united |= cross
    return merged, sorted(united), mapping, {'new_vertices': len(merged)-len(points),
            'merged_vertices': len(base)-(len(merged)-len(points)), 'new_copy_edges': len(copy_edges-existing),
            'new_cross_edges': len(cross), 'cross_edges': sorted(cross)}


def audit(args):
    """Rebuild every selected copy and crosscheck scoring UNSAT independently."""
    base_data = json.loads(args.base.read_text(encoding='utf-8'))
    base = [K2(**p) for p in base_data['pts']]
    previous_points = list(base)
    previous_edges = {tuple(e) for e in base_data['edges']}
    summary = json.loads((args.out_dir/'SUMMARY.json').read_text(encoding='utf-8'))
    assert summary['base_sha256'] == hashlib.sha256(args.base.read_bytes()).hexdigest()
    audit_rows = []
    for step in summary['steps']:
        number = step['step']
        graph_path = args.out_dir/f'step{number}_graph.json'
        assert step['graph_sha256'] == hashlib.sha256(graph_path.read_bytes()).hexdigest()
        data = json.loads(graph_path.read_text(encoding='utf-8'))
        record = json.loads((args.out_dir/f'step{number}_analysis.json').read_text(encoding='utf-8'))
        points = [K2(**p) for p in data['pts']]
        edges = {tuple(e) for e in data['edges']}
        assert points[:len(previous_points)] == previous_points
        assert previous_edges <= edges
        assert len(set(points)) == len(points)
        assert all(unit_modulus(points[u]-points[v]) for u, v in edges)
        chosen = record['selected']
        rotation, translation = K2(**chosen['rotation']), K2(**chosen['translation'])
        assert unit_modulus(rotation)
        mapping = record['copy_base_to_global']
        for v, z in enumerate(base):
            assert points[mapping[v]] == rotation*(z.conj() if chosen['reflection'] else z)+translation
        assert all(tuple(sorted((mapping[u], mapping[v]))) in edges for u, v in base_data['edges'])
        old = record['prior_unequal_coloring']
        assert valid_coloring(old, len(previous_points), previous_edges)
        assert old[217] != old[490]
        for key in ('ordinary_5sat', 'target_unequal_5sat'):
            assert record[key]['status'] == 'SAT'
            assert valid_coloring(record[key]['model'], len(points), edges)
        assert record['target_unequal_5sat']['model'][217] != record['target_unequal_5sat']['model'][490]
        # A second solver repeats the selected old-coloring extension query.
        with Cadical195(bootstrap_with=color_cnf(len(points), sorted(edges))) as solver:
            solver.conf_budget(100000)
            answer = solver.solve_limited(assumptions=[5*v+c+1 for v, c in enumerate(old)])
        assert answer is not True, 'saved killed witness extends after all'
        audit_rows.append({'step': number, 'all_saved_edges_exact': True,
                           'copy_map_and_reflection_exact': True,
                           'both_full_SAT_models_valid': True,
                           'old_unequal_witness_valid': True,
                           'old_witness_extension_Cadical195': 'UNSAT_UNCERTIFIED' if answer is False else 'UNKNOWN',
                           'conflict_budget': 100000})
        previous_points, previous_edges = points, edges
    write_json(args.out_dir/'COPY_AUDIT.json', {'steps': audit_rows,
               'no_quotients_no_color_equalities_no_conditional_system': True,
               'scope': 'Every stored edge is exact unit length. No completeness claim for omitted edges. UNSAT scoring is solver-crosschecked, not a proof certificate.'})
    print(json.dumps({'audited_steps': len(audit_rows), 'all_old_witness_extension_rechecks_unsat': all(r['old_witness_extension_Cadical195'] == 'UNSAT_UNCERTIFIED' for r in audit_rows)}))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', type=Path, required=True)
    ap.add_argument('--out-dir', type=Path, required=True)
    ap.add_argument('--steps', type=int, default=6)
    ap.add_argument('--samples', type=int, default=16)
    ap.add_argument('--seconds', type=float, default=240)
    ap.add_argument('--seed', type=int, default=20260913)
    ap.add_argument('--audit-only', action='store_true')
    args = ap.parse_args()
    if args.audit_only:
        audit(args)
        return
    started = monotonic()
    deadline = started+args.seconds
    rng = random.Random(args.seed)
    data = json.loads(args.base.read_text(encoding='utf-8'))
    base = [K2(p['a'], p['b'], p['den']) for p in data['pts']]
    bedges = sorted(tuple(e) for e in data['edges'])
    assert len(base) == 510 and len(set(base)) == 510
    assert all(unit_modulus(base[u]-base[v]) for u, v in bedges)
    points, edges = list(base), list(bedges)
    seed = sat_call(510, edges, [217*5+1, 490*5+2], 100000, min(15, args.seconds))
    assert seed['status'] == 'SAT', seed
    current_model = seed['model']
    records = []
    signatures = {(sig(ONE), sig(K2([0]*8)), False)}
    frontier = set(range(510))
    ustar = K2([-1]+[0]*7, [3]+[0]*7, 10)
    assert unit_modulus(ustar)
    write_json(args.out_dir/'SEED.json', seed)
    for step in range(1, args.steps+1):
        if monotonic() >= deadline:
            break
        candidates = []
        if step == 1:
            specs = [(ustar, base[217]-ustar*base[217], False,
                      {'kind': 'ustar_about_217', 'center': 217})]
        else:
            frontier_edges = [e for e in edges if any(v in frontier for v in e)]
            assert frontier_edges
            specs = []
            attempts = 0
            while len(specs) < args.samples and attempts < args.samples*10:
                attempts += 1
                u, v = rng.choice(frontier_edges)
                if rng.randrange(2):
                    u, v = v, u
                a, b = rng.choice(bedges)
                reflection = bool(rng.randrange(2))
                source_a = base[a].conj() if reflection else base[a]
                source_b = base[b].conj() if reflection else base[b]
                rotation = (points[v]-points[u])*(source_b-source_a).conj()
                translation = points[u]-rotation*source_a
                signature = (sig(rotation), sig(translation), reflection)
                if signature in signatures or any(signature == (sig(r), sig(t), f) for r, t, f, _ in specs):
                    continue
                specs.append((rotation, translation, reflection, {'kind': 'frontier_edge', 'target_edge': [u, v], 'source_edge': [a, b]}))
        for candidate_id, (rotation, translation, reflection, origin) in enumerate(specs):
            if monotonic() >= deadline:
                break
            newpts, newedges, mapping, stats = compose(points, edges, base, bedges, rotation, translation, reflection)
            if stats['new_vertices'] == 0:
                continue
            assumptions = [5*v+c+1 for v, c in enumerate(current_model)] if current_model is not None else []
            environment = sat_call(len(newpts), newedges, assumptions, 15000, min(3, max(.1, deadline-monotonic())))
            metadata = {'candidate': candidate_id, 'origin': origin, 'rotation': pack(rotation), 'translation': pack(translation),
                        'reflection': reflection, **stats, 'fixed_old_coloring_status': environment['status'],
                        'environment_seconds': environment['seconds'], 'environment_conflict_budget': 15000,
                        'environment_wall_guard_seconds': 3}
            score = (environment['status'] == 'UNSAT_UNCERTIFIED', stats['new_cross_edges'], stats['merged_vertices'], -stats['new_vertices'])
            candidates.append((score, newpts, newedges, mapping, metadata, environment))
        if not candidates:
            break
        selected = max(candidates, key=lambda row: row[0])
        _, newpts, newedges, mapping, chosen, environment = selected
        all_exact = all(unit_modulus(newpts[u]-newpts[v]) for u, v in newedges)
        assert all_exact and len(set(newpts)) == len(newpts)
        frontier = set(range(len(points), len(newpts)))
        old_model = current_model
        points, edges = newpts, newedges
        signatures.add((sig(K2(**chosen['rotation'])), sig(K2(**chosen['translation'])), chosen['reflection']))
        ordinary = sat_call(len(points), edges, [], 150000, min(15, max(.1, deadline-monotonic())))
        unequal = sat_call(len(points), edges, [217*5+1, 490*5+2], 150000, min(15, max(.1, deadline-monotonic())))
        current_model = unequal['model'] or ordinary['model']
        graph_path = args.out_dir/f'step{step}_graph.json'
        write_json(graph_path, {'pts': [pack(z) for z in points], 'edges': edges, 'phi_pairs': [[217, 490]],
                    'scope': 'saved edge graph; floating pair proposal does not certify completeness of all unit distances',
                    'no_conditional_constraints': True})
        record = {'step': step, 'vertices': len(points), 'edges': len(edges), 'selected': chosen,
                  'copy_base_to_global': mapping, 'sampled_candidates': [c[4] for c in candidates],
                  'prior_unequal_coloring': old_model, 'ordinary_5sat': ordinary, 'target_unequal_5sat': unequal,
                  'all_saved_edges_exact_unit_distance': True, 'distinct_exact_coordinates': True,
                  'graph_sha256': hashlib.sha256(graph_path.read_bytes()).hexdigest(),
                  'elapsed_seconds': round(monotonic()-started, 3)}
        write_json(args.out_dir/f'step{step}_analysis.json', record)
        records.append({k: record[k] for k in ('step', 'vertices', 'edges', 'elapsed_seconds', 'graph_sha256') } |
                       {'ordinary_status': ordinary['status'], 'target_unequal_status': unequal['status'],
                        'selected_new_cross_edges': chosen['new_cross_edges'],
                        'selected_environment_status': chosen['fixed_old_coloring_status']})
        write_json(args.out_dir/'SUMMARY.json', {'base_sha256': hashlib.sha256(args.base.read_bytes()).hexdigest(),
                    'seed': args.seed, 'requested_steps': args.steps, 'sample_limit_per_step': args.samples,
                    'wall_budget_seconds': args.seconds, 'steps': records, 'no_conditional_constraints': True,
                    'status': 'ACTIVE', 'scope': 'saved actual unit-edge graphs, not certified all-unit-edge induced completions'})
        print(json.dumps(records[-1]), flush=True)
        if ordinary['status'] != 'SAT' or unequal['status'] != 'SAT':
            break
    summary = json.loads((args.out_dir/'SUMMARY.json').read_text(encoding='utf-8'))
    summary['status'] = 'COMPLETED_BOUNDED_SEARCH'
    summary['elapsed_seconds'] = round(monotonic()-started, 3)
    summary['final_graph'] = f"step{len(records)}_graph.json"
    write_json(args.out_dir/'SUMMARY.json', summary)


if __name__ == '__main__':
    main()
