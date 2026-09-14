# Handoff — Hadwiger–Nelson unconditional mainline

Last updated: 2026-09-14

## Active goal

Seek only unconditional finite planar unit-distance constructions aimed at:

- **A:** a finite planar unit-distance graph that is not 5-colorable;
- **B:** a finite 5-colorable planar unit-distance graph with a fixed distinct pair that has the same color in every proper 5-coloring;
- **C:** a concrete incomplete unconditional construction;
- **D:** a tested unconditional construction family/instance that fails its intended mechanism.

The Lean-checked `PositiveDistance` reduction means any B pair at any positive distance is enough. UNKNOWN, timeout, heuristic failure, or solver difficulty is never evidence.

## Current checkpoint — first asymmetric linked-orbit candidate is closed D

The post-Cycle-7 program now has three exact completed controls: one order-3 closed ring, one order-6 closed ring, and one genuinely asymmetric two-ring linker. All three are D for both A and B. Do not rerun them unchanged.

### Single closed ring: order 3 / anchor `(95,101)` — D for A and B

- 1,192 vertices;
- 7,008 exact induced unit-distance edges;
- 709,836 unordered pairs checked exactly;
- semantic `{pts,edges}` SHA-256 `35898dab08d69084b0ac6323e3fccfadbcfa63d62d4cccf38fc8a430f42e28f4`;
- proper 5-coloring exists;
- 14 validated proper 5-colorings separate every distinct pair.

Evidence: `results/unconditional-2026-09-14/closed-copy/SUMMARY.md` and `results/unconditional-2026-09-14/closed-copy-anchor95/SUMMARY.md`.

### Single closed ring: order 6 / anchor `(45,173)` — D for A and B

- 2,628 vertices;
- 15,708 exact induced unit-distance edges;
- 3,451,878 unordered pairs checked exactly;
- exact completion added zero missed unit edges;
- completed graph SHA-256 `2275306ce8ad3d5bdb7d6c514990f08c103fa2474bfdc36a954c8abcac902bcb`.

A is closed negatively by two independent proper-5-color witnesses: sound triangle color-symmetry SAT and an independent TabuCol zero-conflict coloring, both validated on every exact edge.

B is also closed negatively:

- Actions run `34789803241` generated 690 validated proper 5-colorings with zero repair failures;
- remaining unseparated pairs: 0;
- greedy compression retained 205 colorings;
- durable independent verifier confirms all 205 are proper and all 2,628 vertex signatures are distinct.

Evidence:

- `results/unconditional-2026-09-14/closed-copy-anchor45-order6/SEPARATION.json`
- `results/unconditional-2026-09-14/closed-copy-anchor45-order6/VERIFICATION.json`
- `tools/verify_coloring_separation_certificate.py`
- durable rebuild/verify/store run `34789955622`.

### Asymmetric two-closed-orbit linker — D for A and B

Construction:

- start from the exact order-3 `(95,101)` closed ring;
- take a second exact isometric copy;
- rotate it by the non-root exact unit
  `r = (-1 + 3*sqrt(-11))/10`;
- translate so pivot `src=911` on the second orbit is identified with `dst=0` on the first;
- include only actual exact unit-distance edges;
- exact-complete all unordered point pairs before final classification.

Exact induced graph:

- **2,373 vertices**;
- **14,178 exact unit-distance edges**;
- **2,814,378 unordered point pairs checked exactly**;
- exact completion added **0** missed unit edges;
- semantic `{pts,edges}` SHA-256 `866590e7d7b61e10fd59d551dfa98ce73c98532c79364068ee073ce3d947fc06`.

A is closed negatively:

- portfolio Actions run `34790263403` found SAT on the selected exact screening graph, and exact completion added no edges;
- sound triangle-symmetry SAT on the completed graph returned SAT;
- independent TabuCol also returned a fully validated proper 5-coloring.

B is closed negatively by the independent local-separation route:

- Actions run `34822345980`;
- one validated symmetry-SAT coloring was used as the seed;
- targeted local repair generated **380** validated proper 5-colorings;
- one intermediate repair attempt failed with best conflict count 2, which is explicitly non-evidence; the search continued on other residual blocks;
- final remaining unseparated pairs: **0**;
- greedy compression retained **119** proper 5-colorings;
- all saved colorings were validated on all 14,178 exact edges.

Evidence:

- `results/unconditional-2026-09-14/linked-closed-orbits-local-separation/SUMMARY.md`
- `results/unconditional-2026-09-14/linked-closed-orbits-local-separation/SEPARATION.json`
- `results/unconditional-2026-09-14/linked-closed-orbits-local-separation/WITNESSES.json`
- `tools/hn_linked_closed_orbits_direct.py`
- `tools/hn_local_pair_separation.py`.

**This concrete asymmetric two-ring graph is D for both A and B. Do not rerun it unchanged.**

A smaller 16-placement fast control selected a different graph (2,379 / 14,142) and independently found proper 5-colorings by both SAT and TabuCol. It was only an A control; no B conclusion is recorded for that separate graph.

## Asymmetric rotation / two-anchor lessons

### Denominator-5 sparse census is bounded-empty, not a theorem

Exact finite searches in `Q(zeta30,sqrt(-11))` found no denominator-5 unit rotation in the tested coefficient boxes:

- support `<=5`, coefficient absolute value `<=3`: 18,224,832 numerators checked, 0 exact units;
- support `<=4`, coefficient absolute value `<=5`: 9,386,080 checked, 11 float-near candidates, 0 exact units;
- support `<=3`, coefficient absolute value `<=20`: 18,016,320 checked, 11 float-near candidates, 0 exact units.

Evidence: `results/unconditional-2026-09-14/rotation-census-den5/ROTATIONS.json` and `tools/hn_rotation_census.py`.

This is only a bounded sparse census. Do **not** claim denominator-5 nonexistence in the field.

### Exact two-anchor edge gluing failed for the first non-root rotation

For the 1,192 / 7,008 order-3 ring and `r=(-1+3*sqrt(-11))/10`, an exact search for oriented unit edges satisfying

`p_b - p_a = r * (p_d - p_c)`

found **0 matches**. No floating proposal was used.

Evidence: `results/unconditional-2026-09-14/two-anchor-link-search/SUMMARY.md`, Actions run `34790564465`.

This closes only this exact edge-to-edge gluing mechanism for this ring and this rotation.

## Resume here — multi-link closed-orbit network

Do not spend the next cycle on another isolated single ring or the same two-ring pivot link. The next construction should increase global compatibility by linking **three or more closed orbits**, preferably with different exact non-root rotations.

A convenient explicit infinite family already lies in `Q(sqrt(-11)) subset K2`. For rational `t`,

`r(t) = (1 - 11 t^2 + 2 t sqrt(-11)) / (1 + 11 t^2)`

has exact norm 1. Examples include:

- `t=1/3`: `(-1 + 3 sqrt(-11))/10` — the now-closed two-ring control;
- `t=1/2`: `(-7 + 4 sqrt(-11))/15`;
- `t=2/3`: `(-35 + 12 sqrt(-11))/53`.

Before use, every chosen rotation must still be exact-checked for unit norm and excluded from all 30 `zeta30` roots.

Recommended next experiment:

1. build the pinned order-3 closed ring once;
2. place orbit B using `r(1/3)` and orbit C using a genuinely different rotation such as `r(1/2)`;
3. search exact pivot placements for B and C jointly, ranking by actual inter-orbit unit edges plus sampled coloring-signature rigidity;
4. prefer configurations where C couples to **both** A and B, not merely two independent one-point leaves;
5. exact-complete the selected union over all unordered point pairs;
6. test ordinary 5-colorability first;
7. if SAT, use validated coloring diversity/local repair to test B; if whole-graph UNSAT appears, immediately obtain an independent certificate/check.

A selector composition or multi-anchor network using only literal unit edges is also valid if it attacks global compatibility more strongly than the closed two-ring D control.

## Previous checkpoint — Cycle 7 top-200 is closed D

Cycle 7 exact graph:

- 9,115 vertices;
- 81,068 unit-distance edges;
- graph SHA-256 `632ab11f24bf084221db31fec8e1eda522a18eba8d95dbd3bddf9cbcae1fe49d`;
- all 41,537,055 unordered pairs checked exactly;
- proper 5-coloring exists;
- 79 compressed validated proper 5-colorings distinguish all 9,115 vertices.

Therefore Cycle 7 is D for A and B. Do not rerun it or resume its old frontier/contact-ranking lanes.

## Closed lanes — do not repeat unchanged

- Cycle 1: full G510 pair scan — D.
- Cycle 2: 3,195-point frontier-forge induced UDG — D; exact all-pairs audited.
- Cycle 3: 760 / 4,280 — D.
- high-contact closure: 3,314 / 26,769 — D.
- full 3-contact closure: 8,915 / 78,063 — D.
- Cycle 7 top-200: 9,115 / 81,068 — D for A and B.
- closed-copy order 3 / anchor `(95,101)`: 1,192 / 7,008 — D for A and B.
- closed-copy order 6 / anchor `(45,173)`: 2,628 / 15,708 — D for A and B.
- asymmetric two-ring link using `(-1+3*sqrt(-11))/10`, pivots `(0,911)`: 2,373 / 14,178 — D for A and B.
- exact oriented-edge two-anchor gluing for that same ring/rotation — 0 matches.
- conditional support-`<=4` port-free equality-interface search — independently exhausted; historical context only unless assumptions are removed geometrically.

## Invariants

- use actual points and actual unit-distance edges for unconditional claims;
- validate every saved coloring on every claimed edge;
- a family of proper colorings separating every pair is a valid D certificate;
- UNKNOWN/timeout and heuristic failure are never proofs;
- any candidate B result requires independent confirmation;
- preserve exact coordinates, semantic `{pts,edges}` hashes, compact evidence, and frequent checkpoints;
- distinguish file hashes from semantic point/edge hashes;
- do not generalize a finite D result to an entire field or construction class.
