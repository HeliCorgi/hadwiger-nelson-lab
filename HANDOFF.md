# Handoff — Hadwiger–Nelson unconditional mainline

Last updated: 2026-09-14

## Active goal

Seek only unconditional finite planar unit-distance constructions aimed at:

- **A:** a finite planar unit-distance graph that is not 5-colorable;
- **B:** a finite 5-colorable planar unit-distance graph with a fixed distinct pair that has the same color in every proper 5-coloring;
- **C:** a concrete incomplete unconditional construction;
- **D:** a tested unconditional construction/instance that fails its intended mechanism.

The Lean-checked `PositiveDistance` reduction means any B pair at any positive distance is enough. UNKNOWN, timeout, heuristic failure, solver difficulty, or failure of a restricted coloring family is never evidence.

## Current checkpoint — commuting four-orbit square is closed D

The current construction family starts from the exact 1,192-vertex / 7,008-edge order-3 G510 closed ring and applies exact non-root unit rotations from

`r(t) = (1 - 11 t^2 + 2 t sqrt(-11)) / (1 + 11 t^2)`.

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

A restricted compatibility test was nevertheless significantly harder than previous controls: all **119** compressed A+B witnesses times all **120** global color permutations on the exact `T2` image C+D were tested (14,280 assignments total), and none colored the completed square. This is **not** an UNSAT proof; it only shows that the simple two-block lifted witness family is exhausted.

Evidence: `results/unconditional-2026-09-14/commuting-square-lifted-color/SUMMARY.md`, run `34825370811`.

**The fixed commuting square is D for both A and B. Do not rerun it unchanged.**

## Resume here — commuting cube / center portfolio

The next mechanism should preserve the square's structural replication but add a third independent exact rotation around the same center, producing up to **8 commuting orbit copies**.

Preferred progression:

1. keep `T1=r(1/3)` and the exact center fixed by the established `(0,911)` A->B placement;
2. keep `T2=r(1/5)` as the second generator;
3. geometry-scan a portfolio of distinct `r(t)` values for a third generator `T3`, using the same center so all three affine maps commute exactly;
4. rank `T3` by literal exact unit coupling between the base ring and `T3(base)`, plus extra diagonal couplings to `T1(base)` / `T2(base)`; do not rank by float contacts alone;
5. build the full Boolean orbit cube `{T1^e1 T2^e2 T3^e3(A): ei in {0,1}}`, deduplicate exact points, and discover only exact unit edges;
6. all-pairs exact-complete the selected cube once before any D/B conclusion;
7. test ordinary 5-colorability; if SAT, run pair separation; if UNSAT/UNKNOWN, obtain independent evidence before classification.

If the 8-orbit cube is still D, vary the common center (derived from alternative exact T1 pivot alignments) before adding more dimensions. The lesson from the three-orbit lane is that weak one-sided attachments do not sufficiently constrain global color compatibility.

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
