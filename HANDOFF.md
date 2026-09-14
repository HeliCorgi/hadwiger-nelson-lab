# Handoff — Hadwiger–Nelson unconditional mainline

Last updated: 2026-09-14

## Active goal

Seek only unconditional finite planar unit-distance constructions aimed at:

- **A:** a finite planar unit-distance graph that is not 5-colorable;
- **B:** a finite 5-colorable planar unit-distance graph with a fixed distinct pair that has the same color in every proper 5-coloring;
- **C:** a concrete incomplete unconditional construction;
- **D:** a tested unconditional construction/instance that fails its intended mechanism.

The Lean-checked `PositiveDistance` reduction means any B pair at any positive distance is enough. UNKNOWN, timeout, heuristic failure, solver difficulty, or failure of a restricted coloring family is never evidence.

## Current checkpoint — p1q7 commuting cube is NOT_A; B is active

The current construction starts from the exact 1,192-vertex / 7,008-edge order-3 G510 closed ring and exact non-root unit rotations

`r(t) = (1 - 11 t^2 + 2 t sqrt(-11)) / (1 + 11 t^2)`.

Use one exact common center and three commuting affine generators:

- `T1 = r(1/3) = (-1+3 sqrt(-11))/10`;
- `T2 = r(1/5) = (7+5 sqrt(-11))/18`;
- `T3 = r(1/7) = (19+7 sqrt(-11))/30`.

A 10-rotation geometry portfolio selected `T3=r(1/7)`: base↔T3(base) had 50 exact unit edges and the 8-copy Boolean cube had 1,703 newly discovered exact cross edges, best on both ranking measures in that portfolio.

### Exact p1q7 cube

The selected 8-orbit cube was all-pairs exact-completed:

- **9,369 vertices**;
- **57,488 exact induced unit-distance edges**;
- **43,884,396 unordered pairs checked exactly**;
- exact completion added **0** missed unit edges.

The cube decomposes as a lower commuting square and its `T3` image:

- each square: 4,742 vertices / 28,459 exact edges;
- the two squares share **115 exact geometric vertices**;
- union of the two square-internal edge sets: 56,602 edges;
- remaining exact inter-layer edges: **886**.

Dropping the 886 inter-layer edges gives an overlap-only two-square graph that is 5-colorable. Among the previously saved 223 validated square witnesses, lower witness 89 admits an upper-square coloring agreeing on all 115 shared vertices; that merged overlap-only coloring has 106 conflicts when all 886 inter-layer edges are restored.

### A is closed negatively: validated proper 5-coloring exists

For fixed lower witness 89, exact weighted MaxSAT over the upper square found that the **minimum possible number of full-cube conflicts is 19** under that fixed lower coloring.

Starting from that exact-optimal 19-conflict seed, `tools/hn_seeded_tabucol.py` reached conflict 0 at:

- restart 0;
- iteration **38,915**.

The resulting 9,369-entry coloring was validated on **all 57,488 exact edges**. Therefore the p1q7 cube is definitively **NOT_A**.

Source Actions run: `34832204007`, artifact `p1q7-interface-maxsat-34832204007`. The durable B workflow re-imports and independently revalidates this coloring against a freshly rebuilt/all-pairs-completed graph before using it. Coloring text SHA-256 observed from the artifact:

`a7124d31de62f7acfa587c8f5a4aadc1a78ae89b4d7d8ffddde6e57699119da2`.

### Finite interface rigidity results — not whole-graph UNSAT evidence

The square's 223 compressed validated witnesses were tested as possible lower-layer colorings. For each fixed lower witness, the upper square was solved with:

- all 115 shared-vertex color equalities;
- all 886 inter-layer edges, which become unary forbidden colors when the lower coloring is fixed.

All **223/223** constrained upper-square instances were UNSAT. This proves only that the saved finite lower-witness family contains no full-cube coloring; it does **not** prove whole-cube UNSAT, and indeed the separate 19-conflict repair above found a full proper coloring outside that finite family.

Additional restricted tests also failed (e.g. simple lifted witness/permutation families). Keep them only as structural diagnostics.

### B classification is currently active

A proper coloring exists, so the only remaining question for this fixed p1q7 cube is B.

Primary run:

- Actions `34833122000` — direct targeted pair separation from the validated full-cube coloring; rebuilds and exact-completes the cube again, revalidates the imported coloring on all edges, then runs `hn_local_pair_separation.py`.

Parallel rigorous/heuristic-positive lanes:

- Actions `34833385320` — Kempe-swap separation. Every accepted coloring is automatically proper and is still revalidated on all exact edges; if signatures become unique, this is a direct D certificate for B.
- Actions `34833276186` — perturb-and-repair diversification followed by targeted residual pair separation.

Classify B as D **only** when a validated coloring family has `remaining_pairs=0`. Any residual/timeout/failure is non-evidence and may instead motivate exact SAT checks on remaining candidate pairs.

### Useful failed/diagnostic p1q7 searches

- independent random TabuCol before a proper seed was known: no witness within budget; best conflict 71. Non-evidence.
- frozen-boundary LNS from the older 106-conflict interface seed:
  - radius 0: 186 free vertices, CaDiCaL + Glucose local UNSAT;
  - radius 1: 1,881 free vertices, CaDiCaL + Glucose local UNSAT;
  these are only local frozen-boundary statements.
- core-guided relaxation from the same seed produced 40 consecutive assumption-UNSAT cores, releasing 186 → 5,786 vertices, then stopped at its round limit with status UNKNOWN. Non-evidence globally.

These diagnostics are superseded for A by the validated proper coloring but remain useful for understanding the cube's unusually constrained 5-coloring space.

## Previous checkpoint — commuting four-orbit square is closed D

### Three-orbit controls are closed

#### `r(1/2)` fast control — D for A and B

- 3,564 vertices / 21,193 exact induced unit edges;
- all 6,349,266 unordered pairs checked exactly; completion added 0 edges;
- C couples to A by 2 exact edges and to B by 5;
- proper 5-coloring exists;
- local separation generated 609 validated colorings, compressed to 145, with remaining pairs 0.

Evidence: `results/unconditional-2026-09-14/three-orbit-network-fast/SUMMARY.md`.

A wider 288-placement `r(1/2)` geometry census found 60 two-sided placements but `max min(C->A,C->B)=3`; do not repeat that pivot lane unchanged.

#### Rotation portfolio and `r(1/5)` winner — D for A and B

An 8-rotation geometry portfolio found the best tested weak-side coupling at

`r(1/5) = (7 + 5 sqrt(-11))/18`.

The selected 72-placement candidate used `(dst,src)=(583,553)`:

- C->A = 23, C->B = 7, 28 new cross edges;
- exact completed graph: **3,562 vertices / 21,211 edges**;
- all 6,342,141 unordered pairs checked exactly; completion added 0 edges;
- SAT, hence not A;
- 585 validated proper 5-colorings generated, compressed to 159;
- remaining unseparated pairs: 0; repair failures: 0.

Therefore this candidate is D for both A and B.

Evidence: `results/unconditional-2026-09-14/three-orbit-p1q5/SUMMARY.md`.

A wider 288-placement `r(1/5)` census found 89 two-sided placements but the weak-side maximum stayed **7**. Its most balanced selected placement was 7/8. Do not keep expanding the same three-orbit pivot search without changing mechanism.

### Exact commuting four-orbit square — D for A and B

Use two affine rotations about the same exact center:

- `T1` uses `r1=r(1/3)=(-1+3 sqrt(-11))/10` and the established `(dst,src)=(0,911)` shift;
- `T2` uses `r2=r(1/5)=(7+5 sqrt(-11))/18`;
- choose `s2=(1-r2)(1-r1)^(-1)s1`, computed exactly in `Q(sqrt(-11))`;
- verify `T1*T2 = T2*T1` exactly.

Copies are `A`, `B=T1(A)`, `C=T2(A)`, `D=T1*T2(A)`. This gives a closed orbit-level square rather than a leaf attachment.

Exact completed graph:

- **4,742 vertices**;
- **28,459 exact induced unit-distance edges**;
- **11,240,911 unordered pairs checked exactly**;
- exact completion added **0** missed unit edges;
- semantic `{pts,edges}` SHA-256 `d9a7f4cfe3341e783ce249c3284aecf175babf9190508c0e88eab3fb8e035935`.

Cross-orbit exact unit edges:

- AB = 162;
- AC = 49;
- AD = 2;
- BC = 4;
- BD = 49;
- CD = 162;
- total newly discovered cross edges = 427.

A is closed negatively by two independent routes:

1. sound triangle-symmetry SAT on the all-pairs-completed graph returned SAT;
2. independent TabuCol reached conflict 0 at restart 0 / iteration 1,073,587 and the full coloring was validated on all 28,459 edges.

B is also closed negatively:

- Actions run `34825053279`;
- targeted local repair generated **901** validated proper 5-colorings;
- repair failures: **0**;
- remaining unseparated pairs: **0**;
- greedy compression retained **223** colorings;
- every retained coloring was validated on every exact edge.

Evidence:

- `results/unconditional-2026-09-14/commuting-square-control/SUMMARY.md`
- `results/unconditional-2026-09-14/commuting-square-control/SEPARATION.json`
- Actions artifact `10340406367`.

**The fixed commuting square is D for both A and B. Do not rerun it unchanged.**

## Earlier closed controls — do not repeat unchanged

- Cycle 1: full G510 pair scan — D.
- Cycle 2: 3,195-point frontier-forge induced UDG — D; exact all-pairs audited.
- Cycle 3: 760 / 4,280 — D.
- high-contact closure: 3,314 / 26,769 — D.
- full 3-contact closure: 8,915 / 78,063 — D.
- Cycle 7 top-200: 9,115 / 81,068 — D for A and B; 79 compressed validated colorings distinguish all 9,115 vertices.
- closed-copy order 3 / anchor `(95,101)`: 1,192 / 7,008 — D for A and B.
- closed-copy order 6 / anchor `(45,173)`: 2,628 / 15,708 — D for A and B; 205 compressed separation witnesses.
- asymmetric two-ring link `r(1/3)`, pivots `(0,911)`: 2,373 / 14,178 — D for A and B; 119 compressed separation witnesses.
- exact oriented-edge two-anchor gluing for that ring/rotation — 0 matches.
- three-orbit `r(1/2)` and `r(1/5)` controls above — D for A and B.
- fixed commuting four-orbit square above — D for A and B.
- conditional support-`<=4` port-free equality-interface search — historical only unless assumptions are removed geometrically.

## Rotation-census boundary

Sparse denominator-5 numerator searches were bounded-empty in the tested boxes; this is not a field-wide nonexistence theorem. The rational Cayley family in `Q(sqrt(-11))` supplies explicit usable exact non-root unit rotations independently of that sparse census.

## Invariants

- use actual points and literal unit-distance edges for unconditional claims;
- validate every saved coloring on every claimed edge;
- a family of proper colorings separating every vertex pair is a valid D certificate for B;
- UNKNOWN/timeout/heuristic failure/restricted-family failure are never proofs;
- any candidate A or B result requires independent confirmation;
- exact-complete every selected point set over all unordered pairs before a final D/B conclusion;
- preserve exact coordinates, semantic `{pts,edges}` hashes, compact evidence, and frequent checkpoints;
- distinguish file hashes from semantic point/edge hashes;
- do not generalize a finite D result to an entire field or construction class.
