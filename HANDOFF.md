# Handoff — Hadwiger–Nelson unconditional mainline

Last updated: 2026-09-14

## Active goal

Prioritize only unconditional finite unit-distance constructions aimed at:

- **A:** a finite planar unit-distance graph that is not 5-colorable;
- **B:** a finite 5-colorable planar unit-distance graph with a fixed distinct pair that has the same color in every proper 5-coloring;
- **C:** a concrete incomplete unconditional construction;
- **D:** a tested unconditional construction family/instance that fails its intended mechanism.

The Lean-checked `PositiveDistance` reduction means any B pair at any distance `d>0` is enough. Do not restore the old `d >= 1/2` filter.

Conditional C88/quotient/palette work is historical context unless a concrete construction removes the assumptions.

## Current checkpoint — closed cyclic multi-copy continuation

Cycle 7 is closed. The active lane is now a genuinely different **closed cyclic multi-copy assembly** using complete exact copies of pinned G510. For an anchor pair `(a,b)`, copy `i` is placed by an exact finite-order `zeta30` isometry so its `b` anchor is identified with the next copy's `a` anchor, including the final/first seam. Only actual exact unit-distance edges are coloring constraints.

Implementation:

- `tools/hn_closed_copy_assembly.py` — finite order/anchor portfolio, exact-checks every screening edge, ranks SAT candidates by sampled 5-coloring signature rigidity;
- `tools/hn_closed_copy_direct.py` — reproducible one-candidate builder;
- `tools/hn_exact_complete_io.py` + `tools/hn_exact_completion.cpp` — selected-point all-pairs exact induced completion, no float prefilter;
- `tools/hn_probe_completed_graph.py` — ordinary 5-colorability, diverse proper-coloring signatures, and residual direct pair-inequality SAT;
- `tools/hn_symmetry_sat_probe.py` — sound whole-graph color-symmetry breaking using an actual triangle; use only for ordinary 5-colorability, not as a shortcut for pair forcing;
- `tools/hn_tabucol.py` — validated heuristic 5-color witness search; failure is non-evidence;
- `tools/hn_local_pair_separation.py` — targeted local-repair separation for residual same-signature pairs; every success is a full validated proper coloring, failure is non-evidence.

### Closed-copy portfolio run

Actions run `34783221549`, artifact `10324734261`:

- 36 geometric candidates screened: orders 3 and 6, 18 anchors each;
- top two candidates per order sent to limited SAT screening;
- order 3 `(95,101)`: SAT, 1,192 vertices, 789 added exact cross-copy edges;
- order 3 `(44,192)`: SAT, 1,180 vertices, 720 added exact cross-copy edges;
- order 6 `(45,173)`: UNKNOWN under the limited screening budget — non-evidence;
- order 6 `(95,101)`: UNKNOWN under the limited screening budget — non-evidence.

The selector chose the strongest candidate with an actual SAT result, order 3 / anchor `(95,101)`.

### Exact order-3 control is D for both A and B

The selected `(95,101)` order-3 graph was also run independently in Actions run `34783119580`, artifact `10324729119`.

Exact graph:

- **1,192 vertices**;
- **7,008 exact induced unit-distance edges**;
- **709,836** unordered point pairs checked exactly;
- final exact completion added zero missed unit edges to the screening graph;
- semantic SHA-256 of `{pts,edges}`: `35898dab08d69084b0ac6323e3fccfadbcfa63d62d4cccf38fc8a430f42e28f4`.

CaDiCaL195 found a proper 5-coloring, so it is not A. A family of **14 validated proper 5-colorings** separates every distinct vertex pair, so it has no B pair either.

**Order 3 / anchor `(95,101)` is D for both A and B. Do not rerun it unchanged.**

Evidence:

- `results/unconditional-2026-09-14/closed-copy/SUMMARY.md`
- `results/unconditional-2026-09-14/closed-copy/GEOMETRY.json`
- `results/unconditional-2026-09-14/closed-copy/PROBE.json`
- `results/unconditional-2026-09-14/closed-copy-anchor95/SUMMARY.md`

### Exact order-6 control: NOT_A; B scan active

The order-6 / anchor `(45,173)` graph is now fully exact-completed:

- **2,628 vertices**;
- **15,708 exact induced unit-distance edges**;
- **3,451,878** unordered point pairs checked exactly;
- final completion added zero missed unit edges;
- completed graph SHA-256 `2275306ce8ad3d5bdb7d6c514990f08c103fa2474bfdc36a954c8abcac902bcb`.

The earlier generic probe run `34783286450` was cancelled while solving after geometry completion; this cancellation is non-evidence.

Ordinary 5-colorability is nevertheless settled positively by two independent witness routes:

1. Actions run `34783432616`, artifact `10325667672`: sound triangle color-symmetry breaking on actual triangle `(0,1,5)`; attempts 0–2 UNKNOWN, attempt 3 SAT; full returned coloring validated on all 15,708 exact edges.
2. Actions run `34783526599`, artifact `10324809446`: TabuCol-style local search reached zero conflicts at restart 2 / iteration 389,211; full returned coloring validated on all exact edges.

Therefore **order 6 / anchor `(45,173)` is NOT_A**. Do not spend more work on whole-graph UNSAT for this instance.

B is still active. Two independent colorings leave residual same-signature pairs. The active workflow is:

- `.github/workflows/hn-closed-copy-anchor45-order6-separation.yml`
- tool: `tools/hn_local_pair_separation.py`

It targets a residual pair `(u,v)` by fixing `u` to its current color and `v` to one chosen different color (WLOG by global color permutation), then locally repairing the rest. Successful full colorings refine the residual blocks. Timeout/repair failure has no logical meaning.

Evidence checkpoint:

- `results/unconditional-2026-09-14/closed-copy-anchor45-order6/SUMMARY.md`

## Previous checkpoint — Cycle 7 top-200 is closed

Exact graph:

- 9,115 vertices;
- 81,068 unit-distance edges;
- graph SHA-256 `632ab11f24bf084221db31fec8e1eda522a18eba8d95dbd3bddf9cbcae1fe49d`;
- producing Actions run: https://github.com/HeliCorgi/hadwiger-nelson-lab/actions/runs/34750198928
- artifact id: `10315263782`.

The producing run found a proper 5-coloring, so the direct A attempt is D.

### Exact geometry audit

`tools/hn_exact_completion.cpp` was run over all **41,537,055** unordered point pairs with no floating prefilter.

Result:

- exact unit pairs: 81,068;
- saved edges: 81,068;
- omitted unit edges: 0;
- spurious saved edges: 0.

Thus the saved graph is the full induced unit-distance graph on these points.

### Pair scan

A regenerated family of 456 validated proper 5-colorings separated every distinct vertex pair. Greedy compression retained 79 colorings while keeping all 9,115 vertex color-signatures distinct.

Therefore this graph has no distinct pair that is same-colored in every proper 5-coloring.

**Cycle 7 top-200 is D for both A and B.**

Evidence:

- `results/unconditional-2026-09-13/cycle7-top200-pair-scan/SUMMARY.md`
- `tools/verify_cycle7_top200_separation.py`
- `tools/hn_exact_completion.cpp`

### Hard-pair lesson

Run `34754212424` tested the final two difficult pairs with CaDiCaL and Glucose. All four jobs ran about 90 minutes and were cancelled without SAT/UNSAT output. This was not evidence for B.

Both pairs were subsequently separated by local list-coloring repair:

- `(9,2282)`: radius-3 repair around 2282; 200 changed vertices;
- `(395,1098)`: radius-3 repair around 1098; 59 changed vertices.

The regenerated separation pass then ended with three further residual pairs, all also separated:

- `(327,6016)`: one-vertex recolor;
- `(403,5111)`: radius-1 local repair;
- `(500,897)`: radius-4 local repair; 322 changed vertices.

Every resulting full coloring was validated on all 81,068 exact edges.

Operational lesson: **timeout/UNKNOWN is never pair evidence**. For future hard pairs, try phase-guided or local list-coloring repair before long generic SAT runs.

## Resume here

1. Finish the exact order-6 `(45,173)` B scan. If targeted local repair separates every pair, record this concrete graph D for A/B. If residual pairs remain, use direct pair-inequality SAT only on those pairs; any UNSAT needs independent reproduction before B.
2. Do not spend the next cycle merely enumerating more single-anchor root-of-unity rings. The intended next mechanism is to **link closed orbits**, e.g. multi-anchor / selector compositions or an asymmetric non-root-of-unity exact rotation, so global compatibility is attacked more strongly than in the order-3 D instance.
3. In particular, the pre-restart plan called for mixing an **asymmetric 5-denominator rotation** between closed orbits. That part has not yet been implemented; it is the next construction-level target once the order-6 B control is classified.
4. Preserve exact coordinates, semantic graph hashes, all-pairs completion audits, and compact coloring witnesses for every completed candidate.

For each new candidate:

1. save exact coordinates and graph hash;
2. audit the induced unit-edge set once;
3. test ordinary 5-colorability first;
4. if SAT, generate diverse validated colorings before pair-by-pair SAT;
5. if all signatures become unique, record D;
6. if a pair-inequality query is UNSAT, independently reproduce it before claiming B;
7. if the whole graph is non-5-colorable, treat it immediately as an A candidate and obtain an independent certificate/check.

## Closed lanes — do not repeat unchanged

- Cycle 1: full G510 pair scan — D.
- Cycle 2: 3,195-point frontier-forge induced UDG — D; exact all-pairs audited.
- Cycle 3: 760 / 4,280 — D.
- high-contact closure: 3,314 / 26,769 — D.
- full 3-contact closure: 8,915 / 78,063 — D.
- Cycle 7 top-200: 9,115 / 81,068 — D for A and B.
- closed-copy order 3 / anchor `(95,101)`: 1,192 / 7,008 — D for A and B.
- conditional support-`<=4` port-free equality-interface search — independently exhausted.

## Invariants

- use actual points and actual unit-distance edges for unconditional claims;
- validate every saved coloring on every claimed edge;
- a family of proper colorings separating every pair is a valid D certificate;
- UNKNOWN/timeout and heuristic failure are never proofs;
- any candidate B result requires independent confirmation;
- preserve exact hashes, compact evidence, and frequent checkpoints;
- do not generalize a finite D result to an entire field or construction class.
