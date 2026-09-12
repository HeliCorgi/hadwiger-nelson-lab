#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

K = 5


def load(root: Path, rel: str):
    return json.loads((root / rel).read_text())


def rgs(n: int):
    if n == 0:
        yield ()
        return
    a = [0] * n
    def rec(i: int, m: int):
        if i == n:
            yield tuple(a)
            return
        for x in range(min(m + 1, K - 1) + 1):
            a[i] = x
            yield from rec(i + 1, max(m, x))
    a[0] = 0
    yield from rec(1, 0)


def key(st):
    return ''.join(map(str, st))


def relation_holds(st, pos, kind):
    eq = st[pos[0]] == st[pos[1]]
    return eq if kind == 'eq' else not eq


def relation_by_qnodes(st, sep, rel):
    mp = {q:i for i,q in enumerate(sep)}
    a,b = rel['qnodes']
    return relation_holds(st, (mp[a], mp[b]), rel['kind'])


def record(checks, name, ok, detail=None):
    checks[name] = {'ok': bool(ok)}
    if detail is not None:
        checks[name]['detail'] = detail
    if not ok:
        raise RuntimeError(f'proof-tree check failed: {name}: {detail}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo-root', type=Path, default=Path('.'))
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    root = args.repo_root
    checks = {}

    outer = load(root, 'results/separator-left-compression/analysis.json')
    q0rel = load(root, 'results/separator-left-q0-side-relation/analysis.json')
    q0eq = load(root, 'results/separator-left-q0-q10-compression/analysis.json')
    q18 = load(root, 'results/separator-left-q18-q256-compression/analysis.json')
    q5 = load(root, 'results/separator-left-q5-q6-palette-proof/analysis.json')
    q5basis = load(root, 'results/separator-left-q5-q6-conditional-basis/analysis.json')
    q8 = load(root, 'results/separator-left-q8-q9-via-q104/analysis.json')
    q8cnf = load(root, 'results/separator-left-q8-q9-relation-cnf/analysis.json')

    # Leaf A: q0-side three-state language really is exactly eight disequalities.
    sep1 = q0rel['separator_qnodes']
    rels1 = q0rel['common_pair_relations']
    selected1 = [key(st) for st in rgs(len(sep1)) if all(relation_holds(st, tuple(r['positions']), r['kind']) for r in rels1)]
    record(checks, 'q0_side_pairwise_language_exact', selected1 == q0rel['extendable_states'], {'selected': selected1})
    record(checks, 'q0_side_basis_size_eight', q0rel['minimum_pairwise_basis_size'] == 8 and len(rels1) == 8)
    unexplained = [r['qnodes'] for r in q0rel['relation_explanations'] if not r['explained_by_eq_classes_plus_edge']]
    record(checks, 'q0_side_single_residual_disequality', unexplained == [[18,256]], {'unexplained': unexplained})

    # Leaf B: recursive q18!=q256 palette gate.
    irows = q18['intersection_rows']
    palette_ok = True
    for row in irows:
        st = tuple(map(int, row['state']))
        used = sorted(set(st))
        missing = sorted(set(range(K)) - set(used))
        palette_ok &= row['used_colors'] == used
        palette_ok &= row['missing_colors'] == missing
        palette_ok &= set(row['u_colors']).issubset(used)
        palette_ok &= row['v_colors'] == missing
        palette_ok &= set(row['u_colors']).isdisjoint(row['v_colors'])
    record(checks, 'q18_q256_palette_gate', bool(irows) and palette_ok and q18['all_intersection_cross_disjoint'], {'intersection_count': len(irows)})
    excluded = [r['state'] for r in q18['u_side_rows_excluded_by_v_side']]
    record(checks, 'q18_q256_only_all_five_state_rejected', excluded == ['01234'])

    # Compose q0=q10. q10 is the singleton missing-color gate; common states force both endpoints equal.
    q0_inter = q0eq['intersection']
    q0_keys = [r['key'] for r in q0_inter]
    record(checks, 'q0_q10_interface_states', q0_keys == ['01230','01233'], {'states': q0_keys})
    record(checks, 'q0_q10_same_singleton_color', all(r['u_colors'] == [4] and r['v_colors'] == [4] and r['equal'] for r in q0_inter))
    record(checks, 'q10_full_neighborhood_gate', q0eq['q10_degree_in_left'] == 5 and q0eq['q10_neighborhood_is_separator'])

    # Leaf C / composition: q5=q6 palette proof.
    sc = q5['solver_checks']
    solver_palette_ok = all(
        x['base_sat'] and x['q6_color_absent_when_boundary_uses_at_most4_colors'] and x['separator_uses_at_least4_colors']
        for x in sc.values()
    )
    record(checks, 'q5_q6_palette_leafs_crosschecked', solver_palette_ok and q5['conditional_palette_conditions_verified_both'])
    record(checks, 'q5_q22_local_k4', q5['local_witness_is_k4'] and q5['local_witness_common_to_q5_q22'] and q5['local_q5_eq_q22_k4_witness'] == [0,4,8,21])
    ct = q5basis['conditional_targets']
    record(checks, 'q5_q6_conditional_basis', ct['q6_equals_q4']['minimum_forbid_fifth_basis_size'] == 6 and ct['q6_equals_q8']['minimum_forbid_fifth_basis_size'] == 1 and ct['q6_equals_q8']['minimum_bases'] == [[17]])

    # Leaf D: q8/q9 12-state language compressed to pairwise atoms + width-2 clauses.
    sep3 = q8cnf['separator_qnodes']
    common3 = q8cnf['common_pairwise_relations']
    clauses3 = q8cnf['chosen_width2_clauses']
    def q8_formula(st):
        if not all(relation_by_qnodes(st, sep3, r) for r in common3):
            return False
        for clause in clauses3:
            if not any(relation_by_qnodes(st, sep3, lit) for lit in clause['literals']):
                return False
        return True
    selected3 = [key(st) for st in rgs(len(sep3)) if q8_formula(st)]
    record(checks, 'q8_large_side_cnf_exact', selected3 == q8cnf['large_side_states'] == q8['big_side_rows'] and False, 'internal type guard')

if __name__ == '__main__':
    main()
