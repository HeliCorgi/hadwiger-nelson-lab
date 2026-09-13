# hadwiger-nelson-lab

Computational research workspace for the Hadwiger–Nelson problem.

> This repository does **not** claim a solution of the Hadwiger–Nelson problem. The current work searches for unconditional finite unit-distance constructions that would improve the lower bound, while retaining older conditional finite results as audited components.

## Active objective — unconditional geometry first

The active target is one of:

- **A:** a finite planar unit-distance graph that is not 5-colorable; or
- **B:** a finite 5-colorable planar unit-distance graph with two fixed, distinct actual points that receive the same color in every proper 5-coloring.

For target B, **any strictly positive Euclidean distance is sufficient**. The Lean-checked `PositiveDistance` reduction shows that a positive-distance forced-equal pair can be chained to reach the usual spindle geometry, so the old `d >= 1/2` search threshold is no longer a requirement.

Conditional quotient/C88/palette results remain available as components, but they are not the active todo list unless a concrete construction removes their assumptions.

## Latest unconditional checkpoint — Cycle 7 top-200 fully closed as D

The exact Cycle 7 top-200 graph has:

- **9,115 vertices**;
- **81,068 unit-distance edges**;
- graph SHA-256 `632ab11f24bf084221db31fec8e1eda522a18eba8d95dbd3bddf9cbcae1fe49d`.

The producing workflow run [`34750198928`](https://github.com/HeliCorgi/hadwiger-nelson-lab/actions/runs/34750198928) rebuilt the chain from pinned upstream commit `d1e80998bda337d9fa721f2e96d203ae54e97fc8` and found a proper 5-coloring with CaDiCaL195. This already closed the direct A attempt.

The subsequent target-B scan is now also complete.

### Independent exact geometry audit

`tools/hn_exact_completion.cpp` was run over **all 41,537,055 unordered point pairs** with no floating-point prefilter. It found exactly **81,068** unit-distance pairs.

That exact edge set equals the saved graph edge set:

- omitted unit edges: **0**;
- spurious saved edges: **0**.

Therefore the coloring conclusion below applies to the full induced unit-distance graph on these 9,115 exact points, not merely to a saved subgraph.

### Fixed-pair scan result

A regenerated family of **456 validated proper 5-colorings** was used to refine vertex color signatures. A greedy compression retained **79 colorings** while keeping all 9,115 vertex signatures distinct.

Hence for every distinct pair `u != v`, at least one proper 5-coloring satisfies `c(u) != c(v)`.

> **The Cycle 7 top-200 graph contains no distinct fixed forced-equal pair.**

Thus this tested graph is **D for both A and B**.

Evidence:

- [`results/unconditional-2026-09-13/cycle7-top200-pair-scan/SUMMARY.md`](results/unconditional-2026-09-13/cycle7-top200-pair-scan/SUMMARY.md)
- `results/unconditional-2026-09-13/cycle7-top200-pair-scan/SEPARATION_CERT.json` when present in the checkpoint bundle
- [`tools/verify_cycle7_top200_separation.py`](tools/verify_cycle7_top200_separation.py)
- [`tools/hn_exact_completion.cpp`](tools/hn_exact_completion.cpp)

The final hard pairs are also a useful solver lesson. Generic SAT on `(9,2282)` and `(395,1098)` ran for 90 minutes and was cancelled without a result, but both were later separated quickly by local list-coloring repairs. Timeout/UNKNOWN was correctly not treated as forcing evidence.

### Scope

This closes only the tested **Cycle 7 top-200** construction. It does not rule out:

- other subsets of the 13,556 Cycle 7 exact candidates;
- different candidate-ranking objectives;
- extensions using a genuinely different forcing mechanism;
- unrelated finite unit-distance constructions.

Repeatedly adding more points by the same contact-ranked closure heuristic is no longer the preferred next move unless a new mechanism explains why the previous color-space flexibility should disappear.

## Result-recording policy

Whenever a search produces a lemma-like or theorem-like statement, preserve:

- the exact statement and scope;
- the generating code and compact result/certificate path;
- exact geometry information where relevant;
- solver/checker identity and independent-check status;
- an explicit distinction between A/B/C/D status;
- all conditionality and all unchecked steps.

Heuristic failure is never proof, solver UNKNOWN is never treated as forcing, and a candidate forcing pair is not promoted to B until ordinary 5-colorability and inequality-UNSAT have independent checks.

Large reproducible traces should normally remain GitHub Actions artifacts rather than Git blobs. Keep regeneration code, compact metadata, hashes/artifact IDs, and human-readable conclusions in the repository.

## Historical conditional finite results

The repository also contains a substantial audited conditional forcing program inherited from [`HeliCorgi/five-color-forcing-anatomy`](https://github.com/HeliCorgi/five-color-forcing-anatomy). These results remain useful research components but do not themselves improve the Hadwiger–Nelson lower bound.

### Critical quotient and six-vertex interface

For `Q = H*/C88`:

- `Q` has **305 vertices / 1,599 edges** and is 5-colorable;
- `Q + pq` is not 5-colorable and is vertex-critical under single-vertex deletion;
- a minimum `p`–`q` separator has six vertices;
- exact boundary-state enumeration leaves one globally compatible state and forces the two ports to the same color.

Evidence includes:

- [`results/quotient-critical/analysis.json`](results/quotient-critical/analysis.json)
- [`results/separator-interface/analysis.json`](results/separator-interface/analysis.json)
- [`results/separator-verify/analysis.json`](results/separator-verify/analysis.json)
- [`results/proof-lrat/`](results/proof-lrat/)

This is a conditional finite statement, not an actual planar unit-distance forcing gadget.

### Closed support-`<=4` equality-interface lane

For the pinned conditional A/B system, the port-free equality-observable search on supports of size at most four was independently exhausted:

- 7,011 validated A/B witness pairs;
- 7,008 unique difference cuts;
- all 23,440 producing roots exhausted;
- an independent implementation checked all **9,810,580** increasing first triples and found no surviving four-set.

Finite conclusion:

> **For the pinned A/B system, no port-free equality semantic interface supported on at most four vertices exists.**

Evidence:

- [`results/exact-cegis-loop/MASTER_FINAL.json`](results/exact-cegis-loop/MASTER_FINAL.json)
- [`results/independent-fourset-verify/RECONSTRUCTION.json`](results/independent-fourset-verify/RECONSTRUCTION.json)
- [`results/independent-fourset-verify/VERIFICATION.json`](results/independent-fourset-verify/VERIFICATION.json)
- [`results/independent-fourset-verify/SUMMARY.md`](results/independent-fourset-verify/SUMMARY.md)

Do not restart this support-4 lane as unfinished work.

### Human-readable palette/interface decomposition

The conditional 261-qnode side of the six-vertex separator has a hierarchical explanation via the forced equalities

- `q5=q6`;
- `q0=q10`;
- `q8=q9`.

The detailed historical derivation, palette gates, exact state tables, and solver cross-checks are retained in repository results and git history. They should be pursued further only when tied to a concrete unconditional geometric construction.

## Current direction

1. Treat the Cycle 7 top-200 graph as a closed **D** lane for both A and B; do not rescan it for a fixed pair.
2. Preserve the exact-audit hash and the separating-coloring certificate/checker.
3. Move to a genuinely different unconditional construction mechanism rather than another open-ended contact-ranked closure of the same graph.
4. Prefer constructions whose objective attacks **global 5-coloring freedom**, not one witness coloring at a time.
5. For any new candidate graph, first test ordinary 5-colorability, then use a diverse validated coloring portfolio before spending long SAT runs on individual pairs.
6. Any inequality UNSAT is only a B candidate until independently reproduced/certified. Any actual non-5-colorable UDG is already an A candidate and takes priority.

See [`HANDOFF.md`](HANDOFF.md) for the operational continuation plan and [`RESEARCH.md`](RESEARCH.md) for background.