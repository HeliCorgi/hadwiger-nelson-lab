# Handoff — Hadwiger–Nelson unconditional mainline

Last updated: 2026-09-14

## Active goal

Seek only unconditional finite planar unit-distance constructions aimed at:

- **A:** a finite planar unit-distance graph that is not 5-colorable;
- **B:** a finite 5-colorable planar unit-distance graph with a fixed distinct pair that has the same color in every proper 5-coloring;
- **C:** a concrete incomplete unconditional construction;
- **D:** a tested unconditional construction family/instance that fails its intended mechanism.

The Lean-checked `PositiveDistance` reduction means any B pair at any positive distance is enough. UNKNOWN, timeout, heuristic failure, or solver difficulty is never evidence.

## Current checkpoint — single closed-orbit controls are closed

The post-Cycle-7 mechanism uses complete exact copies of pinned G510 in finite cyclic `zeta30` orbits with the final/first seam included. Only literal exact unit-distance edges are constraints. Selected point sets are completed over **all unordered pairs** by exact arithmetic before final A/B classification.

### Order 3 / anchor `(95,101)` — D for A and B

- 1,192 vertices;
- 7,008 exact induced unit-distance edges;
- 709,836 unordered pairs checked exactly;
- semantic `{pts,edges}` SHA-256 `35898dab08d69084b0ac6323e3fccfadbcfa63d62d4cccf38fc8a430f42e28f4`;
- proper 5-coloring exists;
- 14 validated proper 5-colorings separate every distinct pair.

Evidence:

- `results/unconditional-2026-09-14/closed-copy/SUMMARY.md`
- `results/unconditional-2026-09-14/closed-copy-anchor95/SUMMARY.md`
- Actions runs `34783119580` and `34783221549`.

Do not rerun this instance unchanged.

### Order 6 / anchor `(45,173)` — D for A and B

Exact induced graph:

- **2,628 vertices**;
- **15,708 exact unit-distance edges**;
- **3,451,878 unordered pairs checked exactly**;
- exact completion added zero missed unit edges;
- completed graph SHA-256 `2275306ce8ad3d5bdb7d6c514990f08c103fa2474bfdc36a954c8abcac902bcb`.

A is closed negatively by two independent proper-5-color witnesses:

1. Actions run `34783432616`, artifact `10325667672`: sound color-name symmetry breaking on actual triangle `(0,1,5)`; attempt 3 SAT; full coloring validated on all exact edges.
2. Actions run `34783526599`, artifact `10324809446`: independent TabuCol-style search reached zero conflicts at restart 2 / iteration 389,211; full coloring validated on all exact edges.

B is also closed negatively:

- Actions run `34789803241`, artifact `10327627290`;
- targeted local repair generated **690** validated proper 5-colorings with **0 repair failures**;
- remaining unseparated pairs: **0**;
- greedy compression retained **205** colorings;
- independent certificate verifier confirms all 205 are proper on all 15,708 exact edges and all 2,628 vertex color-signatures are distinct.

Durable committed certificate:

- `results/unconditional-2026-09-14/closed-copy-anchor45-order6/WITNESSES.txt.xz.b64`
- `results/unconditional-2026-09-14/closed-copy-anchor45-order6/SEPARATION.json`
- `results/unconditional-2026-09-14/closed-copy-anchor45-order6/VERIFICATION.json`
- checker: `tools/verify_coloring_separation_certificate.py`
- raw certificate SHA-256 `5e7db802b387d53e6fa8d2090202335727bcadbb8b799a75cc4d377ca3490775`
- packed xz SHA-256 `dba0ad64c18297cb31a8eaba619a20e8719580a5cc7b7a81cc9d605ee2508d17`
- durable rebuild/verify/store Actions run `34789955622`.

**Order 6 / anchor `(45,173)` is D for both A and B. Do not rerun it unchanged.**

## Active next construction — link closed orbits

Do **not** spend the next cycle enumerating more single-anchor root-of-unity rings. Orders 3 and 6 demonstrate that a closed ring can add many real cross-copy unit edges while still retaining enough 5-coloring freedom to separate all pairs.

The pre-restart plan explicitly called for:

> place complete exact isometric copies in a finite cyclic orbit, include the last/first seam, and mix an **asymmetric 5-denominator rotation** to link the orbits.

That asymmetric linking step has not yet been implemented and is now the main construction-level target.

Preferred progression:

1. **Exact rotation census.** Find explicit non-root-of-unity `r in K2 = Q(zeta30,sqrt(-11))` with `|r|=1`, prioritizing normalized denominator 5. Save exact coefficients and independently verify `r*conj(r)=1` and `r != zeta30^k` for all 30 roots.
2. **Two-orbit linker.** Build two already-closed exact copy orbits and place the second by an exact isometry using such an asymmetric rotation/translation. Discover candidate inter-orbit unit edges only as proposals; exact-check every edge before SAT.
3. **Global objective.** Rank link placements by actual cross-orbit coupling and sampled coloring-signature rigidity, not raw contact count alone.
4. **Exact completion.** For any selected point set, run all-pairs exact unit-edge completion once before a D/B conclusion.
5. **A/B decision.** Test ordinary 5-colorability first; if SAT, generate diverse validated colorings and use residual pair repair/SAT only as needed. Any UNSAT candidate requires independent reproduction/certificate.

A multi-anchor/selector composition that links closed orbits using only actual unit edges is also acceptable if the denominator-5 rotation census does not immediately yield a usable linker.

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
- conditional support-`<=4` port-free equality-interface search — independently exhausted; historical context only unless assumptions are removed geometrically.

## Invariants

- use actual points and actual unit-distance edges for unconditional claims;
- validate every saved coloring on every claimed edge;
- a family of proper colorings separating every pair is a valid D certificate;
- UNKNOWN/timeout and heuristic failure are never proofs;
- any candidate B result requires independent confirmation;
- preserve exact coordinates, graph hashes, compact evidence, and frequent checkpoints;
- do not generalize a finite D result to an entire field or construction class.
