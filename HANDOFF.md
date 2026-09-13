# Handoff — Hadwiger–Nelson unconditional mainline

Last updated: 2026-09-13

## Active goal

Prioritize only unconditional finite unit-distance constructions aimed at:

- **A:** a finite planar unit-distance graph that is not 5-colorable;
- **B:** a finite 5-colorable planar unit-distance graph with a fixed distinct pair that has the same color in every proper 5-coloring;
- **C:** a concrete incomplete unconditional construction;
- **D:** a tested unconditional construction family that fails its intended mechanism.

The Lean-checked `PositiveDistance` reduction means any B pair at any distance `d>0` is enough. Do not restore the old `d >= 1/2` filter.

Conditional C88/quotient/palette work is historical context unless a concrete construction removes the assumptions.

## Current checkpoint — Cycle 7 top-200 is closed

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

Do not rerun Cycle 7 top-200. It is closed.

Start a genuinely different unconditional construction mechanism. Prefer mechanisms that attack global 5-coloring freedom rather than:

- killing one current coloring at a time;
- another open G510 frontier chain;
- adding more points only because they have high contact count;
- collecting more conditional palette lemmas.

Promising next directions:

1. multi-copy or selector compositions that turn a disjunctive monochromatic relation into a fixed relation using only actual unit edges;
2. cycle-closing or multi-anchor copy placement;
3. direct non-5-colorable searches over a new exact geometry host;
4. portfolio-optimized extensions with a genuinely new objective, not the previous contact ranking.

For each new candidate:

1. save exact coordinates and graph hash;
2. audit the induced unit-edge set once;
3. test ordinary 5-colorability first;
4. if SAT, generate diverse validated colorings before pair-by-pair SAT;
5. if all signatures become unique, record D;
6. if a pair-inequality query is UNSAT, independently reproduce it before claiming B;
7. if the whole graph is non-5-colorable, treat it immediately as an A candidate.

## Closed lanes — do not repeat unchanged

- Cycle 1: full G510 pair scan — D.
- Cycle 2: 3,195-point frontier-forge induced UDG — D; exact all-pairs audited.
- Cycle 3: 760 / 4,280 — D.
- high-contact closure: 3,314 / 26,769 — D.
- full 3-contact closure: 8,915 / 78,063 — D.
- Cycle 7 top-200: 9,115 / 81,068 — D for A and B.
- conditional support-`<=4` port-free equality-interface search — independently exhausted.

## Invariants

- use actual points and actual unit-distance edges for unconditional claims;
- validate every saved coloring on every claimed edge;
- a family of proper colorings separating every pair is a valid D certificate;
- UNKNOWN/timeout and heuristic failure are never proofs;
- any candidate B result requires independent confirmation;
- preserve exact hashes, compact evidence, and frequent checkpoints;
- do not generalize a finite D result to an entire field or construction class.
