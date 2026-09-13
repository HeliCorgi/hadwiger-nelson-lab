# Handoff — Hadwiger–Nelson main target / unconditional geometry

Last updated: 2026-09-13

## USER OVERRIDE — this section supersedes older priorities

The active goal is an actual Hadwiger–Nelson lower-bound improvement, not further compression of conditional palette/C88/quotient statements.

Only prioritize work that directly seeks one of:

- **A:** a finite planar unit-distance graph that is not 5-colorable;
- **B:** a finite 5-colorable planar unit-distance graph containing a fixed pair of distinct actual points forced to the same color in every proper 5-coloring;
- **C:** a concrete incomplete unconditional construction toward A or B, with the unchecked part stated explicitly;
- **D:** a tested unconditional family that fails the intended A/B mechanism.

The Lean-checked `PositiveDistance` bridge removes the old `d >= 1/2` search threshold: **any fixed forced-equal pair at any Euclidean distance `d>0` is enough** after chaining. Do not reject a forcing candidate because its distance is small.

Do not return to conditional palette/C88/quotient/proof-compression/Lean-only work unless a specific construction explains how it removes the conditional assumptions.

## Latest checkpoint — Cycle 7 top-200 direct extension

Workflow run:

- https://github.com/HeliCorgi/hadwiger-nelson-lab/actions/runs/34750198928
- status: **success**
- head commit used by the run: `afc203994e861cd945242f16b71896b3cf5f6313`
- pinned upstream: `d1e80998bda337d9fa721f2e96d203ae54e97fc8`

Artifact:

- id: `10315263782`
- name: `hn-cycle7-top200-v2-34750198928`
- digest: `sha256:17e65652d2b95eaed786720b9176825f73f07b20dfecf343fb9bd96812e3c5d2`
- important files: `run/GRAPH.json`, `run/COLORING.txt`, `run/REBUILD.json`, `run/VERDICT.json`, plus reconstructed Cycle 3 files.

### Exact reconstruction chain

The successful run rebuilt everything from the pinned upstream G510 data.

1. **Cycle 3**
   - 760 vertices / 4,280 edges;
   - semantic SHA-256 over canonical JSON `{pts,edges}`:
     `6cefdd905c4ab09108ea4005e80e3b234e3b2826de759b73bd619163b9943380`;
   - this semantic hash replaced the earlier incorrect byte-for-byte `GRAPH.json` hash gate.
2. **Cycle 4**
   - 2,512 vertices;
   - 2,543 float proposals;
   - 1,752 retained exact new points.
3. **Cycle 6**
   - 8,915 vertices / 78,063 edges;
   - 9,302 float proposals;
   - 6,403 retained exact new points.
4. **Cycle 7 candidate pool**
   - 15,216,277 base pairs within floating radius 2 used for proposal generation;
   - 13,556 float proposals after multiplicity/contact filtering;
   - all 13,556 reconstructed as distinct exact candidates in this run.
5. **Top-200 test graph**
   - Cycle 6 plus the first 200 ranked exact candidates;
   - 9,115 vertices / 81,068 induced unit edges according to `induced_edges`;
   - every retained edge is verified exactly with `unit_modulus`;
   - graph SHA-256: `632ab11f24bf084221db31fec8e1eda522a18eba8d95dbd3bddf9cbcae1fe49d`.

### SAT result

CaDiCaL195 returned **SAT** in 87.778 seconds. The returned coloring was checked against all 81,068 saved edges and written to `run/COLORING.txt` as one 9,115-digit color string.

Producing verdict:

- `cadical195 = SAT`;
- `proper_5_coloring_verified = true`;
- producing classification: `D`;
- conclusion: `Entire top-200 Cycle7 candidate family remains 5-colorable.`

Total rebuild+SAT time recorded by the workflow: 122.886 seconds.

## Precise scope of the Cycle 7 result

This closes the **direct A attempt** for the top-200 closure. Adding all 200 selected candidates does not produce a non-5-colorable graph.

It does **not** yet close target B. A graph can be 5-colorable while still containing a fixed pair forced equal in all 5-colorings.

Therefore do not write “Cycle 7 has no forcing pair” yet. The correct current status is:

> **Cycle 7 top-200: D for direct non-5-colorability; B status untested on the final 9,115-vertex graph.**

Also distinguish two geometry checks:

- `hn_cycle7_top200_rebuild.py::induced_edges` uses a floating `|r^2-1|<1e-7` prefilter, then exact `unit_modulus` on every retained candidate and asserts no false positives;
- it does not constitute a completely float-free enumeration of all 41,537,055 point pairs.

Before theorem-level claims about the *full induced* 9,115-point unit-distance graph, perform one independent exact all-pairs audit or another argument that proves no unit edge can be missed by the floating prefilter. After that audit, gate future work by the audited graph SHA instead of repeating the expensive geometry check every scan.

## Resume here — next computation

### Step 1: recover and pin the successful artifact

Download artifact `10315263782`. Verify:

- `run/GRAPH.json` SHA-256 equals
  `632ab11f24bf084221db31fec8e1eda522a18eba8d95dbd3bddf9cbcae1fe49d`;
- `run/GRAPH.json` has 9,115 points and 81,068 edges;
- `run/COLORING.txt` has exactly 9,115 color digits in `0..4`;
- the coloring is proper on every saved edge.

`COLORING.txt` is a raw digit string, not the JSON seed format expected by `hn_unconditional_scan.py`. If using that scanner, wrap it into a seed-model JSON such as

```json
{"models":{"cycle7_top200_sat":[0,1,1,4]}}
```

with the full 9,115-entry integer list substituted for the toy four-entry example.

### Step 2: independently audit induced unit edges once

Preferred: write/use an exact or rigorously bounded all-pairs checker over all **41,537,055** point pairs.

Requirements:

- exact point distinctness;
- every saved edge has squared distance exactly 1;
- no omitted pair has squared distance exactly 1;
- save a compact geometry audit with graph SHA and exact pair count.

Do this once. Subsequent coloring scans should trust only the audited graph SHA, not rerun the all-pairs geometry audit on every attempt.

### Step 3: test target B on the 9,115-vertex graph

Use only actual vertices and actual unit-distance edges. No C88, quotient, palette assumptions, or prescribed same-color relations.

Recommended strategy:

1. Start from the verified 5-coloring in the artifact.
2. Generate diverse additional proper 5-colorings using SAT, Kempe exchanges, local repair, or a mixture.
3. Maintain equality blocks/signatures: each new validated coloring splits vertices that receive different colors.
4. If all blocks become singletons, every distinct vertex pair has a separating proper 5-coloring; record **D for B** as well.
5. If a pair `(u,v)` survives, solve `G` with `c(u) != c(v)` using color-label symmetry only where logically valid.
6. SAT gives another separating witness and refines the blocks.
7. UNSAT gives only a **B candidate** until independently checked with another solver/certificate.
8. Before promotion to B, verify ordinary `G` is SAT, `u != v` as exact points, and the Euclidean distance is strictly positive. Any positive distance is acceptable.

Do not interpret timeout/UNKNOWN as forcing.

### Step 4: branch on the outcome

If all pairs are separated:

- classify the Cycle 7 top-200 family as fully **D** for both A and B;
- preserve the small separating coloring family;
- stop adding more points by the same top-ranked contact heuristic unless a new mechanism is identified;
- move to a genuinely different unconditional construction family.

If a fixed pair is inequality-UNSAT:

- save the pair and exact distance immediately;
- independently verify graph SAT and pair-inequality UNSAT;
- preserve proof/certificate artifacts;
- this is the highest-priority lane because `PositiveDistance` turns any such `d>0` pair into a finite non-5-colorable unit-distance construction.

## Closed / do-not-repeat lanes

### Support-`<=4` port-free equality interface search

For the pinned conditional A/B system, this lane is independently exhausted:

- 7,011 validated A/B witness records;
- 7,008 unique difference cuts;
- 23,440 / 23,440 producing roots exhausted;
- independent verifier exhausted 9,810,580 / 9,810,580 increasing first triples;
- cut-library SHA-256:
  `a58cb579f1fa725107ef10a776b290c089a8ff0cfc12dc4d75fa1fe82ba5ccfa`.

Finite conditional conclusion:

> For the pinned A/B system, no port-free equality semantic interface supported on at most four vertices exists.

Do not restart this as unfinished work.

### Old distance threshold

Do not restore `d >= 1/2` as a search filter. `PositiveDistance` supersedes it. Any unconditional forced-equal pair at any `d>0` is enough.

### Conditional palette/proof-compression queue

The older q5/q6, q0/q10, q8/q9 palette/interface decomposition remains valid historical finite work, but it is not the active priority. Do not spend a cycle shrinking proof trees, adding palette clauses, increasing semantic support, or Lean-formalizing another conditional leaf unless it participates in a stated unconditional composition.

## Historical conditional backbone — context only

The repository inherited a conditional forcing system from `HeliCorgi/five-color-forcing-anatomy` at upstream commit

`d1e80998bda337d9fa721f2e96d203ae54e97fc8`.

Its main formulas were

- `A = H* ∧ C88`;
- `B = H* ∧ (c(217) != c(490))`.

For the quotient `Q = H*/C88`:

- 305 vertices / 1,599 edges;
- `Q` is 5-colorable;
- `Q + pq` is not 5-colorable and is vertex-critical under single-vertex deletion;
- no articulation point or 2-vertex cut;
- `p`–`q` vertex connectivity is 6.

A minimum six-vertex separator leaves exactly one globally compatible canonical boundary state, which forces the two conditional ports to the same color. The contradiction also has an independently checked LRAT proof.

The 261-qnode side was later compressed into a hierarchical palette/interface explanation through the forced equalities

- `q5=q6`;
- `q0=q10`;
- `q8=q9`.

Detailed evidence remains under:

- `results/quotient-critical/`;
- `results/separator-interface/`;
- `results/separator-verify/`;
- `results/proof-lrat/`;
- `results/separator-left-*`.

These statements are conditional and non-geometric. They do not imply `chi(R^2) >= 6` by themselves.

## Evidence/checkpoint invariants

Preserve these rules in every future cycle:

- use actual points and actual unit-distance edges for unconditional claims;
- save exact coordinates and graph hashes;
- every saved coloring must be validated on every edge of the graph being claimed;
- a small family of proper colorings separating every pair is a valid D certificate for fixed-pair forcing;
- solver UNKNOWN/timeout is never forcing evidence;
- heuristic failure is never proof;
- a candidate inequality-UNSAT must be independently rechecked before B promotion;
- if an unconditional graph itself is non-5-colorable, that is already an A candidate and is higher priority than extracting a forcing pair;
- report the tested family precisely; do not generalize a finite sample D to an entire algebraic field or construction class;
- preserve intermediate checkpoints frequently so a token/runtime cutoff does not erase progress.

## Workflow reliability notes

Three Cycle 7 top-200 workflow attempts occurred:

1. run `34749793473` failed before mathematics because `tools/hn_circle_closure.py` was missing from `main`;
2. run `34749991118` successfully rebuilt the 760/4,280 Cycle 3 graph but failed an inappropriate whole-file JSON SHA check even though the semantic `{pts,edges}` graph matched;
3. run `34750198928` replaced the byte hash with semantic graph hashing and completed successfully through the 9,115-vertex SAT test.

Do not reintroduce whole-JSON byte identity as a graph-identity requirement when metadata or serialization can differ. Use canonical semantic hashes for mathematical objects.