# Handoff — P2 forcing / port-free semantic search

Last updated: 2026-09-11

## Scope

This repository continues the finite five-color forcing program inherited from `HeliCorgi/five-color-forcing-anatomy`.

Pinned upstream commit:

`d1e80998bda337d9fa721f2e96d203ae54e97fc8`

The active support-4 lane asks whether the P2 forcing system admits an equality-based semantic interface supported on at most four **non-port** vertices.

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
- computational phase changes, such as a search suddenly collapsing from many possibilities to a tiny exact interface.

Every such note must be labeled by evidence level:

1. **proved / independently verified finite statement** — exact exhaustive computation or proof certificate, preferably independently checked;
2. **exact computational observation** — exact for the stated finite sample/system, but not independently rechecked;
3. **empirical pattern** — observed in sampled colorings/search trajectories only;
4. **conjectural interpretation** — a proposed explanation or possible geometric significance.

For each recorded item include, when available:

- the precise finite statement or observation;
- why it may be interesting;
- the generating script/result path;
- solver/checker and sample size or exhaustive scope;
- independent-verification status;
- an explicit warning if it is conditional on `C88`, quotient contraction, sampled colorings, or another non-geometric assumption.

Do **not** wait for the user to ask whether something is interesting. Preserve it first, with scope clearly stated. Conversely, do not promote an empirical pattern to a theorem merely because it looks striking.

For geometric observations, also record exact coordinates/distances when practical and state explicitly whether the object is already a genuine unit-distance construction or only an abstract/conditional graph pattern.

## Verified structural results now merged to `main`

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

- The six-boundary state space collapses very asymmetrically: the 261-vertex `p` side permits only `012202` and `012203`, while the 38-vertex `q` side permits 81 states. Their intersection is the single state `012203`. This is an unusually sharp finite interface.
- Exact port-relation scanning found 20 quotient vertices forced to the same color as the port class containing 217.
- Among those forced-equal classes, there is a clean local lemma: `p` and qnode 22 are forced equal because their common neighborhood is exactly a `K4`.
- In 300 sampled 5-colorings of the quotient, the required two-color Kempe connectivity between the two ports repeatedly used the same four shortest path skeletons. This is currently an empirical structural pattern, not a theorem.
- Proof-guided color-symmetric support searches at sizes 4, 5, and 6 repeatedly produced candidates whose A/B projection overlap was only one state. These are near-separators but not certified interfaces.

Future work should add comparable observations automatically when they appear.

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
- Oracle UNSAT: write `INTERFACE.json`; this is a semantic-interface candidate and must be independently reconstructed and checked.
- Exact master UNSAT: write `FINAL.json`; this excludes all port-free equality interfaces of support `<=4` for the pinned system.
- Empty difference graph on all 391 non-port vertices: stronger terminal fooling pair, excluding port-free equality interfaces of any support.
- Timeout / decision-budget exhaustion / solver interruption: **UNKNOWN only**.

## Latest durable state — Run 4 complete

Search branch checkpoint commit:

`43915f71caff21b316ba1ebcc901a758d0218ea7`

Workflow run:

`34562068005`

Final durable counts:

- validated upstream seed fooling pairs: **872**;
- lab-generated fooling pairs: **5910**;
- total represented sound cuts: **6782**;
- Run 4 additions relative to Run 2: **2705** lab fooling pairs;
- fast candidates sent to the exact oracle in Run 4: **2705**;
- exact oracle calls in Run 4: **2705**;
- oracle UNKNOWNs: **0**;
- unresolved supports at the final checkpoint: **0**;
- no empty-difference global fooling pair;
- no oracle-UNSAT four-set / `INTERFACE.json`;
- no exact master-UNSAT / `FINAL.json`;
- final continuation state: **`MASTER-UNKNOWN`**.

Run-4 artifact id `10187878072`, digest `sha256:f32e432c7f4cc8b30ce9ddbc449e9e8b23d863ad0d83772c745ed73cb1be8bcd`.

## Specialized exact master

The bottleneck after Run 4 is whether any four vertices have six internal pair-atoms whose coverage bitsets jointly hit all 6782 known cuts.

`tools/exact_fourset_master.py` implements a standalone exact combinatorial solver for this question. It branches only on logically necessary edges from uncovered difference graphs; heuristics affect branch order, not completeness. It self-tests against brute force on small random instances. A timeout remains UNKNOWN.

The exact-master workflow is `.github/workflows/exact-fourset-master.yml`.

Interpret outcomes carefully:

- found four-set -> candidate only; send it back to the exact semantic oracle;
- exact exhaustion -> complete negative for this 6782-cut master, but independently recheck before promoting to a theorem-level README claim;
- timeout / interrupted run -> UNKNOWN.

## Secondary structural lane

The six-vertex separator result is currently the cleanest finite explanation of the conditional P2 same-color relation. It should be preserved independently of the support-4 search outcome.

If the support-4 master is eventually proved UNSAT, that result would say only that this particular **port-free equality-interface language** needs support at least five; it would not invalidate the six-vertex quotient separator proof and would not rule out other semantic observables or geometric gadget constructions.

The eventual Hadwiger–Nelson objective remains geometric: obtain an unconditional forced-mono pair at Euclidean distance at least `1/2`, or an equivalent finite 6-chromatic unit-distance construction. Conditional quotient/SAT statements are intermediate machinery only.

## Checkpoint and UNKNOWN policy

Keep these invariants:

- `iterations == len(new_pairs)` for the lab-generated portion;
- every seed and generated A/B coloring pair must validate against its defining formula;
- oracle UNKNOWN never generates a blocking clause;
- heuristic failure never modifies the exact master proof space;
- writes remain atomic and gzip integrity is checked before persistence;
- checkpoints are committed after completed guarded slices.

## Certificate policy

Any terminal result must be independently checked before being promoted to a mathematical claim.

For `INTERFACE.json`:

- preserve the exact four vertex IDs and all six equality observables;
- preserve the pinned upstream SHA;
- independently reconstruct the oracle query;
- check UNSAT with a second solver and preferably a standalone certificate/checker.

For exact master UNSAT / `FINAL.json`:

- preserve the full fooling-pair/cut library or a reduced exact covering certificate;
- provide a deterministic standalone checker for the claimed exhaustion;
- independently rerun/reconstruct the exhaustion before documenting it as a finite theorem.

For a global empty-difference fooling pair:

- independently validate both A and B colorings;
- verify identical equality pattern on all 391 non-port vertices.

Lean is appropriate only after the finite statement and certificate format stabilize.

## Resume checklist

1. Use the Run-4 checkpoint containing `5910` lab pairs + `872` seeds = `6782` cuts.
2. Confirm no terminal `FINAL.json` / `INTERFACE.json` already supersedes it.
3. Validate the checkpoint and coloring-pair invariants.
4. Prefer the specialized exact four-set master over another generic long CEGIS run.
5. If a four-set is found, return it to the exact semantic oracle.
6. If exact exhaustion is claimed, independently verify before promoting it.
7. Whenever interesting mathematical/geometric structure appears, record it proactively under the research-recording policy above.
