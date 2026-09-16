# Interior reflection probes and an explicit seven-color certificate

2026-09-16 JST. **No new Hadwiger–Nelson bound is claimed.** Both finite reflection graphs tested here have explicit proper five-colorings. Thus both are **NOT_A**. A six-coloring of a finite graph is not evidence that six colors are necessary, nor an upper bound of six for the entire plane.

## Final bounded results

| copies of G3 | vertices | exact unit edges | new interior cross edges | final A status | specified B pair |
|---|---:|---:|---:|---|---|
| 2 | 4,097 | 24,648 | 96 | NOT_A: two validated five-colorings | UNKNOWN |
| 3 | 5,667 | 34,945 | 438 | NOT_A: one validated five-coloring | UNKNOWN |

The two actual terminals have squared distance 3, **not phi squared**. These are A/B probes, not H_phi candidates. The saved positive five-colorings assign the terminals the same color. That does **not** prove forced equality: a proper coloring with different terminal colors has not been found or excluded in these bounded tests.

### Geometry

Start with the exactly reconstructed sevenfold G3 (2,131 vertices / 12,530 edges). For a source unit edge a,b, set d=b-a, r=d*d and t=a-r*conjugate(a). The map p -> r*conjugate(p)+t is an isometric reflection fixing both anchor points. Use source edge (47,125) for the second copy and additionally (125,134) for the third.

Merge actual equal coordinates and include **all** exact unit-distance pairs, including interior cross-copy edges. There are no extra color equalities in these original graphs. The reflections stay in the source sevenfold complex coordinate field; representing them in Q(zeta210) is not a claim of a further field extension.

The 2-copy graph has 165 shared vertices. The 3-copy pairwise overlaps are 165, 165 and 512. Mere overlap or edge counts are not forcing evidence.

### Direct SAT probes, followed by a successful positive lifting test

Actions [35046524554](https://github.com/HeliCorgi/hadwiger-nelson-lab/actions/runs/35046524554), source `a0def9f2fd8121ca0482d9578e957348a169a246`, tested five-color ordinary/equal/different conditions and ordinary six-colorability, with CaDiCaL195 and Glucose4.

All twelve direct five-color tests timed out at 45 seconds each. All four six-color tests returned validated SAT models. Those timeouts were retained as UNKNOWN, never as evidence of non-five-colorability.

Actions [35047081806](https://github.com/HeliCorgi/hadwiger-nelson-lab/actions/runs/35047081806), source `aa6dd28d2de00e1de37d739ce7c76553bcfcb964`, then identified corresponding source indices across copies to form **abstract auxiliary quotients**. These add extra same-color restrictions; the quotients are not claimed to be unit-distance realizations. Only positive models are lifted back.

* 2-copy quotient: 2,050 vertices / 12,325 edges. CaDiCaL195 and Glucose4 both found five-colorings, in approximately 11.9 and 4.5 solver-worker seconds respectively.
* 3-copy quotient: 1,639 vertices / 10,276 edges. CaDiCaL195 found a five-coloring in approximately 52.2 seconds. Glucose4 timed out at 60 seconds.

The three lifted colorings were checked on **every original edge**, both during Actions execution and locally without a SAT solver. This supersedes the original A=UNKNOWN statuses. Quotient UNSAT or timeout would not have excluded ordinary five-colorability of the original graph.

## Independent geometry and witness audit

`tools/hn_verify_reflection_evidence.py` does not import the synthesis arithmetic or a SAT solver. It generates Phi210 with SymPy, uses a separate integer polynomial ring, and checks all 8,390,656 and 16,054,611 unordered point pairs through sound modular filters and exact norm computations. The complete unit-edge sets match the two saved graphs exactly. All four six-color models and all three five-color models were validated.

The eight tests in `tools/test_hn_reflection_evidence.py` passed locally, including rejection of missing unit edges, spurious nonunit edges, duplicate points, monochromatic edges, wrong pins and wrong graph hashes. These tests were local, not an additional Actions job.

`FIVE_COLORINGS.json.gz` stores all three full five-color witnesses, keyed by copy count and solver, with graph and coloring SHA-256 identities. Its gzip SHA-256 is `4d16f822acacc3971a9ec4f34382e8eb073df4c394f615d95e4478e4743e8b6a`.

## Proof-control issue, not a mathematical obstruction

The first two runs, 35045994995 and 35046231650, stopped on an abstract K6/5 control before any candidate probes. The CaDiCaL195 trace lacked a final conflict and drat-trim rejected it. Duplicating the descriptor and destroying the solver did not repair this extraction path. The root cause remains unresolved.

The current new probe wrapper therefore treats CaDiCaL only as a source of directly validated SAT witnesses; its UNSAT is UNSAT_UNCHECKED. Glucose4 negative claims require drat-trim return code 0 and the exact `s VERIFIED` result. No failed proof check has been waived. The historical `hn_certified_color_probe.py` is unchanged.

The Glucose4 K6 control passed drat-trim. It was also independently checked locally as a RUP proof: 140 added lemmas and 41 deletion lines. K6 here is only an abstract solver calibration, **not a planar unit-distance witness**. No candidate non-five-colorability proof was obtained.

## Why seven colors suffice, and the scope of a six-color exclusion

`HEX7_PROOF_ja.md` and `tools/hn_hex7_certificate.py` give the explicit infinite-plane rule `(i+3*j) mod 7` on regular hexagons of circumradius 2/5. Points in one hexagon are at distance at most 4/5; points in distinct same-color hexagons are at distance at least `(2/5)*(sqrt(21)-2)>1`. Boundary points are covered by the strict bounds.

For this **fixed tiling with one color per entire cell**, the center cell and its six neighbors require seven different colors. All 21 cell pairs admit an interior point pair at distance exactly one. This is a K7 in the **cell-conflict** graph, not a seven-chromatic unit-distance point graph. It does not exclude arbitrary six-colorings of the plane. These are explanations and checks of a known upper bound and a restricted obstruction, not a solution of HN.

## Reproduction

The full exact graphs and solver outputs are in the linked Actions artifacts. Their IDs are 10427630689 and 10427566754 for the ordinary probes, and 10427562187 and 10427238662 for the fold probes. They have 90-day retention, with expiry recorded as 2026-12-15; archive downloads are needed for preservation beyond that date. The original G3 is from run 35003232409, artifact 10410248491.

After extracting an ordinary-probe artifact into `/tmp/reflection-2`, run from the repository root:

```sh
python -m pip install numpy==2.3.5 sympy==1.14.0
python tools/hn_verify_reflection_evidence.py \
  --candidate /tmp/reflection-2/candidate \
  --five-bundle results/interior-reflection-2026-09-16/FIVE_COLORINGS.json.gz \
  --out /tmp/independent-audit.json
python -m unittest discover -s tools -p test_hn_reflection_evidence.py -v
python tools/hn_hex7_certificate.py --out /tmp/hex7.json
python tools/hn_verify_rup_control.py \
  --cnf /tmp/reflection-2/controls/glucose4/5/INPUT.cnf \
  --proof /tmp/reflection-2/controls/glucose4/5/PROOF.drat \
  --out /tmp/rup-audit.json
```

The synthesis and bounded solver reruns are defined by `.github/workflows/hn-interior-reflection-probe.yml` and `.github/workflows/hn-reflection-fold-probe.yml`. Do not repeat these unchanged graphs as an A-search: their explicit five-colorings already exclude that target. Their specified B pairs remain unresolved, not established.
