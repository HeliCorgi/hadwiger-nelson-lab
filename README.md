# hadwiger-nelson-lab

Computational research workspace for the Hadwiger–Nelson problem.

> This repository does **not** claim a solution of the Hadwiger–Nelson problem. The current work searches for unconditional finite unit-distance constructions that would improve the lower bound, while retaining older conditional finite results as audited components.

## Active objective — unconditional geometry first

The active target is one of:

- **A:** a finite planar unit-distance graph that is not 5-colorable; or
- **B:** a finite 5-colorable planar unit-distance graph with two fixed, distinct actual points that receive the same color in every proper 5-coloring.

For target B, **any strictly positive Euclidean distance is sufficient**. The Lean-checked `PositiveDistance` reduction shows that a positive-distance forced-equal pair can be chained to reach the usual spindle geometry, so the old `d >= 1/2` search threshold is no longer a requirement.

Conditional quotient/C88/palette results remain available as components, but they are not the active todo list unless a concrete construction removes their assumptions.

## Latest unconditional checkpoint — Cycle 7 top-200 closure

Workflow run [`34750198928`](https://github.com/HeliCorgi/hadwiger-nelson-lab/actions/runs/34750198928) completed successfully from pinned upstream commit

`d1e80998bda337d9fa721f2e96d203ae54e97fc8`.

The workflow rebuilt the geometric chain from the pinned G510 data and checked semantic identity of the Cycle 3 graph rather than relying on JSON byte-for-byte identity.

Reconstruction/result:

- Cycle 3: **760 vertices / 4,280 edges**;
- Cycle 3 semantic SHA-256 over `{pts,edges}`: `6cefdd905c4ab09108ea4005e80e3b234e3b2826de759b73bd619163b9943380`;
- Cycle 4: **2,512 vertices**, adding 1,752 exact points;
- Cycle 6: **8,915 vertices / 78,063 edges**, adding 6,403 exact points;
- Cycle 7 exact candidate pool: **13,556 points**;
- tested graph after adding the entire ranked top-200 candidate set: **9,115 vertices / 81,068 edges**;
- every retained edge was checked as an exact unit-distance edge;
- CaDiCaL195 result: **SAT** in 87.778 s;
- the returned 5-coloring was independently checked against all 81,068 edges by the workflow;
- tested graph SHA-256: `632ab11f24bf084221db31fec8e1eda522a18eba8d95dbd3bddf9cbcae1fe49d`.

The producing run classifies this tested direct-extension family as **D**: adding all top-200 Cycle 7 candidates still does **not** produce a non-5-colorable unit-distance graph.

Artifact: `10315263782`, digest `sha256:17e65652d2b95eaed786720b9176825f73f07b20dfecf343fb9bd96812e3c5d2`. It contains `run/GRAPH.json`, `run/COLORING.txt`, `run/REBUILD.json`, `run/VERDICT.json`, the reconstructed Cycle 3 files, and the compact summary.

### Important scope of the D result

The successful 5-coloring closes the **direct A attempt** for this top-200 closure: this 9,115-vertex graph is 5-colorable.

It does **not** show that the graph has no fixed forced-equal pair. A 5-colorable graph can still satisfy target B. Therefore the next high-value computation is an unconditional all-pairs forcing scan on this exact 9,115-vertex graph, seeded by the verified coloring from the artifact and additional proper 5-colorings.

If every distinct point pair can be separated by at least one validated proper 5-coloring, then the top-200 graph is fully D for both A and B. If a pair survives and `G + (c(u) != c(v))` is UNSAT, it becomes a B candidate and must be independently checked.

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

The detailed historical derivation, palette gates, exact state tables, and solver-crosschecks are retained in repository results and git history. They should be pursued further only when tied to a concrete unconditional geometric construction.

## Current direction

1. Use the Cycle 7 artifact's exact `run/GRAPH.json` and verified `run/COLORING.txt` as the next checkpoint.
2. Search the 9,115-vertex graph for a fixed forced-equal pair using only actual vertices and actual unit-distance edges. Any positive port distance is eligible.
3. Accumulate validated proper 5-colorings to refine equality blocks; a small separating family is enough to prove no forced pair.
4. If an inequality query is UNSAT, treat it only as a candidate until rechecked independently; also verify the graph itself remains 5-colorable and the two points are distinct.
5. If all pairs are separated, record the top-200 family as fully D and move to a genuinely different unconditional construction mechanism rather than adding more conditional palette lemmas.

See [`HANDOFF.md`](HANDOFF.md) for the operational continuation plan and [`RESEARCH.md`](RESEARCH.md) for background.