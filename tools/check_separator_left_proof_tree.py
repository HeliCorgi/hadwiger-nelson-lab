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
    mp = {q: i for i, q in enumerate(sep)}
    a, b = rel['qnodes']
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

    # q0-side three-state language: exactly eight pairwise disequalities.
    sep1 = q0rel['separator_qnodes']
    rels1 = q0rel['common_pair_relations']
    selected1 = [
        key(st) for st in rgs(len(sep1))
        if all(relation_holds(st, tuple(r['positions']), r['kind']) for r in rels1)
    ]
    record(checks, 'q0_side_pairwise_language_exact', selected1 == q0rel['extendable_states'], {'selected': selected1})
    record(checks, 'q0_side_basis_size_eight', q0rel['minimum_pairwise_basis_size'] == 8 and len(rels1) == 8)
    unexplained = [r['qnodes'] for r in q0rel['relation_explanations'] if not r['explained_by_eq_classes_plus_edge']]
    record(checks, 'q0_side_single_residual_disequality', unexplained == [[18, 256]], {'unexplained': unexplained})

    # q18!=q256 recursive palette gate.
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
    record(
        checks,
        'q18_q256_palette_gate',
        bool(irows) and palette_ok and q18['all_intersection_cross_disjoint'],
        {'intersection_count': len(irows)},
    )
    excluded = [r['state'] for r in q18['u_side_rows_excluded_by_v_side']]
    record(checks, 'q18_q256_only_all_five_state_rejected', excluded == ['01234'])
    record(checks, 'q256_is_full_degree5_gate', q18['q256_degree'] == 5 and q18['q256_neighborhood_is_separator'])

    # q0=q10 composition.
    q0_inter = q0eq['intersection']
    q0_keys = [r['key'] for r in q0_inter]
    record(checks, 'q0_q10_interface_states', q0_keys == ['01230', '01233'], {'states': q0_keys})
    record(
        checks,
        'q0_q10_same_singleton_color',
        all(r['u_colors'] == [4] and r['v_colors'] == [4] and r['equal'] for r in q0_inter),
    )
    record(checks, 'q10_full_neighborhood_gate', q0eq['q10_degree_in_left'] == 5 and q0eq['q10_neighborhood_is_separator'])

    # q5=q6 composition from local q5=q22 plus conditional palette leaves.
    sc = q5['solver_checks']
    solver_palette_ok = all(
        x['base_sat']
        and x['q6_color_absent_when_boundary_uses_at_most4_colors']
        and x['separator_uses_at_least4_colors']
        for x in sc.values()
    )
    record(checks, 'q5_q6_palette_leafs_crosschecked', solver_palette_ok and q5['conditional_palette_conditions_verified_both'])
    record(
        checks,
        'q5_q22_local_k4',
        q5['local_witness_is_k4']
        and q5['local_witness_common_to_q5_q22']
        and q5['local_q5_eq_q22_k4_witness'] == [0, 4, 8, 21],
    )
    record(checks, 'q22_is_full_neighborhood_gate', q5['q22_neighborhood_is_separator'] and q5['q22_degree'] == 10)
    ct = q5basis['conditional_targets']
    record(
        checks,
        'q5_q6_conditional_basis',
        ct['q6_equals_q4']['minimum_forbid_fifth_basis_size'] == 6
        and ct['q6_equals_q4']['minimum_bases'] == [[17, 30, 59, 68, 105, 223]]
        and ct['q6_equals_q8']['minimum_forbid_fifth_basis_size'] == 1
        and ct['q6_equals_q8']['minimum_bases'] == [[17]],
    )

    # q8/q9 large-side 12-state language: exact pairwise + width-2 relation CNF.
    sep3 = q8cnf['separator_qnodes']
    common3 = q8cnf['common_pairwise_relations']
    clauses3 = q8cnf['chosen_width2_clauses']

    def q8_formula(st):
        if not all(relation_by_qnodes(st, sep3, r) for r in common3):
            return False
        return all(any(relation_by_qnodes(st, sep3, lit) for lit in clause['literals']) for clause in clauses3)

    selected3 = [key(st) for st in rgs(len(sep3)) if q8_formula(st)]
    q8_rows = [r['state'] for r in q8['big_side_rows']]
    record(
        checks,
        'q8_large_side_cnf_exact',
        selected3 == q8cnf['large_side_states'] == q8_rows,
        {'selected_count': len(selected3)},
    )
    record(
        checks,
        'q8_large_side_cnf_minimum_unique',
        q8cnf['minimum_width2_clause_cover_size'] == 4
        and q8cnf['minimum_cover_count'] == 1
        and q8cnf['exact_formula_verified'],
    )

    # q104 singleton gate leaves exactly two four-color states and forces q8=q9=q104.
    q8_inter = q8['intersection_rows']
    q8_keys = [r['state'] for r in q8_inter]
    q8_gate_ok = True
    for row in q8_inter:
        used = sorted(set(map(int, row['state'])))
        missing = sorted(set(range(K)) - set(used))
        q8_gate_ok &= len(used) == 4 and len(missing) == 1
        q8_gate_ok &= row['missing_colors'] == missing
        q8_gate_ok &= row['q8_colors'] == missing
        q8_gate_ok &= row['q9_colors'] == missing
        q8_gate_ok &= row['q104_colors'] == missing
        q8_gate_ok &= row['all_three_same_singleton']
    record(checks, 'q8_q9_q104_two_state_gate', q8_keys == ['0112323', '0112333'] and q8_gate_ok, {'states': q8_keys})
    record(checks, 'q104_full_neighborhood_gate', q8['q104_neighborhood_is_separator'] and q8['q104_degree'] == 7)

    # Outer composition: the two surviving six-boundary states satisfy all three equalities,
    # and the port color equals q6 in each state.
    outer_sep = outer['separator_qnodes']
    omp = {q: i for i, q in enumerate(outer_sep)}
    outer_states = outer['left_extendable_states']
    outer_ok = outer_states == ['012202', '012203']
    for skey in outer_states:
        st = tuple(map(int, skey))
        outer_ok &= st[omp[0]] == st[omp[10]]
        outer_ok &= st[omp[8]] == st[omp[9]]
        pcolors = outer['left_state_port_colors'][skey]
        outer_ok &= pcolors == [st[omp[6]]]
    record(checks, 'outer_two_states_realize_three_equalities', outer_ok, {'states': outer_states})

    # Human K4-e composition: after naming A={p,q6}, B={q0,q10}, C={q8,q9}, D={q266},
    # all class edges except C-D force A,B,C pairwise distinct and D distinct from A,B.
    # Canonically this has exactly two boundary states.
    class_states = []
    for A in range(K):
        for B in range(K):
            for C in range(K):
                for D in range(K):
                    if A == B or A == C or A == D or B == C or B == D:
                        continue
                    # Translate to [q0,q6,q8,q9,q10,q266], then canonicalize.
                    raw = [B, A, C, C, B, D]
                    ren = {}
                    nxt = 0
                    canon = []
                    for x in raw:
                        if x not in ren:
                            ren[x] = nxt
                            nxt += 1
                        canon.append(ren[x])
                    class_states.append(key(canon))
    class_states = sorted(set(class_states))
    record(checks, 'k4_minus_edge_gives_exactly_outer_two_states', class_states == ['012202', '012203'], {'states': class_states})

    report = {
        'status': 'PROOF-TREE-COMPOSITION-VERIFIED',
        'checks': checks,
        'all_checks_passed': all(v['ok'] for v in checks.values()),
        'trust_boundary': (
            'This checker uses only Python standard-library logic and saved JSON evidence. It independently verifies the '
            'composition of the hierarchical human-readable proof tree, canonical-state formulas, palette-set deductions, '
            'and the final K4-minus-edge reduction. It does NOT re-solve the graph-coloring SAT instances that produced the '
            'leaf state tables/palette predicates. Those leaves remain supported by the separately recorded CaDiCaL195/Glucose4 cross-checks.'
        ),
        'finite_conclusion_checked': (
            'Given the saved, solver-crosschecked leaf lemmas, the left side of the six-vertex quotient separator permits '
            'exactly 012202 and 012203, via q5=q6, q0=q10, q8=q9 and the final K4-minus-one-edge relation.'
        ),
        'geometric_scope': 'Conditional quotient/P2 finite statement only; no new unit-distance or Hadwiger-Nelson lower-bound claim.',
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'status': report['status'], 'check_count': len(checks), 'all_checks_passed': report['all_checks_passed']}, indent=2))


if __name__ == '__main__':
    main()
