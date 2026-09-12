# Handoff — P2 forcing / port-free semantic search

Last updated: 2026-09-12

## Scope

This repository continues the finite five-color forcing program inherited from `HeliCorgi/five-color-forcing-anatomy`.

Pinned upstream commit:

`d1e80998bda337d9fa721f2e96d203ae54e97fc8`

The support-4 lane asks whether the P2 forcing system admits an equality-based semantic interface supported on at most four **non-port** vertices.

Define:

- `A = H* ∧ C88`;
- `B = H* ∧ (c(217) != c(490))`.

`H*` is the first minimal core from `B5_MULTICORE.json`; `C88` is `C_min` from `B5_P2_LEMMA.json`.

No result in this handoff is an unconditional finite unit-distance 6-chromatic graph. Nothing here changes the known Hadwiger–Nelson lower bound.

## Research-recording policy: preserve interesting mathematics, not only wins

The user does not want to be responsible for judging whether an observed structure is mathematically interesting. Future work should therefore **proactively record potentially interesting mathematical or geometric structure** rather than only terminal solver results.

Whenever computation reveals something that looks structurally non-generic, concise, symmetric, extremal, unexpectedly rigid, or repeatedly recurring, add a short note to the README or a nearby structural-notes file and link it from the README when appropriate. Do this even when the observation does not immediately advance the Hadwiger–Nelson lower bound.

Examples worth recording include:

- unexpectedly small separators, interfaces, critical substructures, or forcing witnesses;
- exact symmetries or color-symmetric state descriptions;
- repeated Kempe-chain or path skeletons;
- forced-equality classes or other rigid relations among many vertices;
- unusually small projection/state spaces relative to the ambient graph;
- local graph-theoretic lemmas such as common-neighborhood forcing;
- geometric regularities in coordinates, distances, rotations, reflections, lattice structure, or repeated unit-distance motifs;
- near-misses that are one state / one edge / one constraint away from becoming a separator or obstruction;
- computational phase changes, including exact exhaustion of a previously heuristic search language.

Every such note must be labeled by evidence level:

1. **proved / independently verified finite statement** — exact exhaustive computation or proof certificate, preferably independently checked;
2. **exact computational observation** — exact for the stated finite system, but not independently rechecked;
3. **empirical pattern** — observed in sampled colorings/search trajectories only;
4. **conjectural interpretation** — a proposed explanation or possible geometric significance.

For each recorded item include, when available:

- the precise finite statement or observation;
- why it may be interesting;
- the generating script/result path;
- solver/checker and sample size or exhaustive scope;
- independent-verification status;
- an explicit warning if it is conditional on `C88`, quotient contraction, sampled colorings, or another non-geometric assumption.

Do **not** wait for the user to ask whether something is interesting. Preserve it first, with scope clearly stated. Conversely, do not promote an empirical pattern or a single-implementation exact result to a theorem merely because it looks striking.

For geometric observations, also record exact coordinates/distances when practical and state explicitly whether the object is already a genuine unit-distance construction or only an abstract/conditional graph pattern.

## Verified structural results already merged to `main`

### Quotient criticality

Contract the C88 equality components to obtain `Q = H*/C88`.

- `Q` has 305 vertices and 1599 edges;
- `Q` is 5-colorable;
- adding the edge between the quotient classes containing 217 and 490 makes the graph non-5-colorable;
- deleting any one vertex from that added-edge graph restores 5-colorability;
- there is no articulation point and no 2-vertex cut;
- `p`-to-`q` vertex connectivity in `Q` is 6.

Evidence: `results/quotient-critical/analysis.json` and `tools/quotient_critical.py`.

### Six-vertex color-symmetric separator proof

A minimum `p`-`q` separator in quotient-node numbering is

`S = {0, 6, 8, 9, 10, 266}`.

Deleting it leaves a 261-vertex `p` side and a 38-vertex `q` side. Of all 202 canonical equality partitions of the six boundary vertices using at most five colors:

- 2 extend to the `p` side;
- 81 extend to the `q` side;
- exactly one extends to both: `012203`.

For this unique common boundary state, both side computations force their port to the same singleton boundary color. Therefore every proper 5-coloring of `Q` satisfies

`c(217) = c(490)`.

Discovery used CaDiCaL. An independent implementation using Glucose4 enumerated all 202 states on both sides and verified the unique intersection and same singleton port color.

Evidence:

- `results/separator-interface/analysis.json`;
- `results/separator-verify/analysis.json`;
- `tools/separator_interface.py` and the independent verification workflow.

This is a conditional six-vertex color-symmetric interface proof, not an unconditional geometric gadget.

### Independently checked SAT-level contradiction

For the normalized CNF

`COMMON ∧ A-only ∧ B-only`,

there are 1965 Boolean variables and 13,203 clauses: 12,318 common clauses, 880 C88-side clauses, and 5 `c(217) != c(490)` clauses.

Glucose4 generated an UNSAT DRUP proof. Pinned `drat-trim` commit `2e3b2dc0ecf938addbd779d42877b6ed69d9a985` converted/trimmed it to LRAT, and independent `lrat-check` accepted the LRAT proof.

The dependency cone still contains 11,018 initial clauses and 215,041 learned clauses, all 880 A-only clauses, all 5 B-only clauses, and support from all 393 graph vertices. Therefore proof trimming alone does not expose a small local explanation.

Compact evidence:

- `results/proof-lrat/PARTITION.json`;
- `results/proof-lrat/LRAT_CONE.json`;
- `tools/lrat_export.py`.

Full proof artifact: Actions artifact `10185491584` from run `34564305431`, ZIP SHA-256 `fc062d366b78700baf008ef18b8d424a30400717691c8be42f2ff153371c423f`.

## Interesting structural observations already worth preserving

These are summarized more fully in `STRUCTURAL_NOTES.md`.

- The six-boundary state space collapses very asymmetrically: the 261-vertex `p` side permits only `012202` and `012203`, while the 38-vertex `q` side permits 81 states. Their intersection is the single state `012203`.
- Exact port-relation scanning found 20 quotient vertices forced to the same color as the port class containing 217.
- Among those forced-equal classes, there is a clean local lemma: `p` and qnode 22 are forced equal because their common neighborhood is exactly a `K4`.
- In 300 sampled 5-colorings of the quotient, the required two-color Kempe connectivity between the two ports repeatedly used the same four shortest path skeletons. This is empirical, not exhaustive.
- Proof-guided color-symmetric support searches at sizes 4, 5, and 6 repeatedly produced candidates whose A/B projection overlap was only one state.
- The specialized exact master has now exhausted the support-4 difference-graph language for the current validated cut library. This is an exact computational observation pending independent reconstruction, not yet a verified finite theorem.

## Why exact four-sets suffice

For a support `S`, the semantic state is the equality partition of colors on `S`. If the projected A-state and B-state sets are disjoint on a support of size at most three, adding arbitrary non-port vertices cannot make two previously different restrictions equal.

Therefore any separator of support `<=3` extends to a separator on exactly four vertices, and exhaustion of all non-port four-sets is complete for the support-`<=4` equality-interface question.

## CEGIS / difference-graph formulation

There are 391 non-port vertices and 76,245 unordered non-port pair-atoms.

For each A/B fooling pair `(alpha,beta)`, form its difference graph `D(alpha,beta)` with edge `{u,v}` exactly when

`[alpha(u)=alpha(v)] != [beta(u)=beta(v)]`.

A four-set survives a fooling pair iff one of its six internal pairs belongs to that difference graph. Hence the master problem is a constrained hitting problem: choose four vertices so that their six pair-atoms hit every accumulated difference graph.

The semantic oracle fixes the six equality observables of a proposed four-set and asks whether A and B can agree on them.

- Oracle SAT: preserve the A/B models and add their difference graph as another sound cut.
- Oracle UNSAT: semantic-interface candidate; independently reconstruct and check it.
- Exact master exhaustion: no four-set hits all current validated difference cuts; if the cut library is sound, that excludes a support-4 separator for this language, but the producing exhaustive implementation must still be independently checked before theorem promotion.
- Empty difference graph on all 391 non-port vertices: stronger terminal fooling pair, excluding port-free equality interfaces of any support.
- Timeout / decision-budget exhaustion / solver interruption: **UNKNOWN only**.

## Current durable terminal state — exact CEGIS v2

Workflow run:

`34683854626`

Actions artifact:

- id: `10298170797`;
- ZIP SHA-256: `33be9aa4456a8fb293811c39b5a4bf58574d9a34c9f8bbc812b5091a7fb96d29`;
- size: 1,669,158 bytes.

The uploaded artifact copy was checked against that SHA-256 and matched exactly.

Final durable counts:

- validated upstream seed fooling pairs: **872**;
- lab-generated fooling pairs: **6139**;
- total validated fooling pairs before cut deduplication: **7011**;
- unique difference-graph cuts: **7008**;
- duplicate difference cuts: **3**;
- non-port vertices: **391**;
- pair-atoms: **76,245**;
- fixed pivot cut source: `checkpoint:5191`;
- fixed pivot root count: **23,440**;
- completed pivot roots: **23,440 / 23,440**;
- final exact-master state: `EXACT-MASTER-EXHAUSTED-REQUIRES-INDEPENDENT-VERIFY`.

Hashes:

- final cut library: `a58cb579f1fa725107ef10a776b290c089a8ff0cfc12dc4d75fa1fe82ba5ccfa`;
- fixed root order: `f72cdbf49f6a06929ebae1efe58b795b466c1ef4bd5bfa2f923ee6b3029532a7`.

Compact evidence:

- `results/exact-cegis-loop/MASTER_FINAL.json`;
- `results/exact-cegis-loop/STATUS.md`;
- `results/exact-cegis-loop/master-current/STATE.json`;
- `results/exact-cegis-loop/master-current/ROOT_ORDER.json`;
- `checkpoints/semantic_portfree_s4.json.gz`.

The final checkpoint still carries status `RUNNING-AFTER-EXACT-MASTER-CUT` because that field describes the semantic-pair CEGIS checkpoint format, not the separate exact-master terminal state. **Do not use the checkpoint status alone to decide whether the support-4 master is unfinished.** The authoritative master status is the `MASTER_FINAL.json` / `STATE.json` terminal value above.

### New semantic witnesses found during the terminal run

The v2 run found two additional four-set master candidates. Both were rejected as interfaces by two semantic SAT solvers and therefore generated new sound cuts:

1. support `{318,394,399,444}` at root rank `10484`; CaDiCaL195 SAT and Glucose4 SAT; appended as lab pair 6138;
2. support `{4,301,402,464}` at root rank `21442`; CaDiCaL195 SAT and Glucose4 SAT; appended as lab pair 6139.

Evidence is retained under `results/exact-cegis-loop/history/`.

### Monotone-resume behavior was exercised successfully

The v2 master stores a fixed root order and verifies prefix compatibility of the ordered unique-cut library. If new cuts are appended, already completed roots remain impossible because the master constraints only strengthen. The root that produced the candidate is retried.

The production run demonstrated this twice:

- legacy state upgraded and resumed from root **4833**, not 0;
- after the first new cut, `resume-monotone-prefix-v2` restarted at root **10484**, not 0;
- after the second new cut, `resume-monotone-prefix-v2` restarted at root **21442**, not 0;
- search then reached **23440 / 23440**.

The preflight also passed the original 400 randomized exact-vs-brute-force tests and a monotone-resume extension self-test. These tests support implementation confidence but do not substitute for an independent full-size verifier.

## Run-4 historical counter correction

Run `34562068005` ended with 5910 lab pairs and 6782 total represented cuts. It added **2705** sound cuts relative to Run 2, and made **2705** exact oracle calls with zero oracle UNKNOWNs.

However the checkpoint field `fast_candidates` is **2702**, not 2705. The three-count discrepancy means it is incorrect to state that all 2705 oracle calls came from the fast candidate layer without tracing the source path. Preserve the counters separately:

- Run-4 sound cuts added: **2705**;
- exact oracle calls: **2705**;
- `fast_candidates`: **2702**.

Earlier README/HANDOFF wording equating them was wrong and has been corrected.

Run-4 artifact id `10187878072`, digest `sha256:f32e432c7f4cc8b30ce9ddbc449e9e8b23d863ad0d83772c745ed73cb1be8bcd`.

## Interpretation of the support-4 exhaustion

The producing exact master states:

> No four-set of the 391 non-port vertices hits every validated unique difference-graph cut in the final library.

If independently verified, the logical consequence is:

> For the pinned A/B system, no port-free equality semantic interface supported on at most four vertices exists.

This would mean only that this particular **port-free equality observable language** requires support at least five. It does not invalidate the six-vertex quotient separator proof, does not rule out support-5 equality interfaces, does not rule out other semantic observables, and does not provide an unconditional geometric forcing gadget.

The six-vertex separator result remains the cleanest verified finite explanation of the conditional P2 same-color relation.

## Checkpoint and UNKNOWN policy

Keep these invariants:

- `iterations == len(new_pairs)` for the lab-generated portion;
- every seed and generated A/B coloring pair must validate against its defining formula;
- oracle UNKNOWN never generates a blocking cut;
- heuristic failure never modifies the exact master proof space;
- writes remain atomic and gzip integrity is checked before persistence;
- completed exact root branches are reusable after verified monotone cut extension, but only when root order and cut-prefix checks pass;
- if any compatibility check fails, fall back to a fresh exact search rather than assuming resume safety.

## Certificate / independent-verification policy

Any terminal result must be independently checked before being promoted to a mathematical claim.

For an oracle-UNSAT semantic interface:

- preserve the exact vertex IDs and equality observables;
- preserve the pinned upstream SHA;
- independently reconstruct the oracle query;
- check UNSAT with a second solver and preferably a standalone certificate/checker.

For the current exact-master exhaustion:

- reconstruct the complete final cut library independently from the validated seed and generated fooling pairs;
- independently validate every A model against `A` and every B model against `B`;
- verify the 7008 unique difference cuts and their digest/counts;
- use a materially different exhaustive decomposition, preferably not the same root-edge recursion;
- or generate a proof-tree/certificate whose leaves carry explicit blocking cuts and check that certificate with a small standalone verifier;
- only after agreement promote support-`<=4` nonexistence into the verified result log.

A generic SAT encoding of the four-set hitting problem is acceptable as a secondary independent backstop, but a structurally different combinatorial checker is preferable.

Lean is appropriate only after the finite statement and certificate format stabilize.

## Resume / next-work checklist

1. **Do not rerun the same support-4 exact master merely to continue it; it already reached 23440/23440.**
2. Treat `results/exact-cegis-loop/MASTER_FINAL.json` as an exact computational observation pending independent verification.
3. Build an independent final-cut reconstruction/checker from the 6139 generated pairs + 872 seeds.
4. Validate the reconstructed library has 7011 pairs before dedup and 7008 unique difference cuts.
5. Reprove no four-set hits all cuts using a materially different exhaustive decomposition or a standalone proof certificate.
6. If independent verification succeeds, update README from “exact computational observation” to “independently verified finite statement.”
7. Then choose the next mathematical lane: support-5/other semantic observables, human proof of the six-boundary quotient interface, or direct geometric forcing work.
8. Whenever interesting mathematical/geometric structure appears, record it proactively under the research-recording policy above.