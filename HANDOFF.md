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

## Verified structural results now merged to `main`

Before continuing the support-4 search, preserve the following proof-level finite statements. They are useful context and must not be lost during branch conflict resolution.

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

Search branch:

`research/semantic-interface`

Checkpoint:

`checkpoints/semantic_portfree_s4.json.gz`

Latest durable checkpoint commit:

`43915f71caff21b316ba1ebcc901a758d0218ea7`

Workflow run:

`34562068005`

Run 4 completed successfully at the workflow level on 2026-09-11.

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

Run-4 artifact:

- id: `10187878072`;
- digest: `sha256:f32e432c7f4cc8b30ce9ddbc449e9e8b23d863ad0d83772c745ed73cb1be8bcd`.

This is the checkpoint to resume from. Do **not** fall back to Run-2 commit `a10e0f9` unless the Run-4 checkpoint itself fails validation.

## Run history

### Run 1

Workflow `34436888946`.

- 2525 lab fooling pairs;
- 3397 total cuts;
- checkpoint `5283a5f`;
- no terminal result.

### Run 2

Workflow `34493404794`.

Slice endpoints:

- 2525 -> 2669;
- 2669 -> 2778;
- 2778 -> 2922;
- 2922 -> 3008;
- 3008 -> 3131;
- 3131 -> 3205.

Final Run-2 state: 3205 lab pairs + 872 seeds = 4077 cuts. The sixth slice was stopped by the outer guard after iteration 3205 was already atomically checkpointed. No timeout was interpreted as logical evidence.

### Run 3

Workflow `34561883743`.

The first hybrid implementation attempted PySAT/CaDiCaL interrupt clearing. `clear_interrupt()` is unsupported in the pinned wrapper. The smoke test failed before production search; the real checkpoint remained untouched. Run 3 contributes zero mathematical progress.

### Run 4

Workflow `34562068005`, based on corrected commit `b163d55`.

The corrected implementation uses CaDiCaL decision budgets:

- `dec_budget(N)`;
- `solve_limited()`;
- `True` = SAT;
- `False` = UNSAT;
- `None` = UNKNOWN / budget exhausted;
- reset budget afterward.

The hybrid candidate path is

`fast pair-coverage bitsets + local search -> exact semantic oracle -> sound cut`.

Across Run 4, the fast layer generated 2705 usable candidates and the exact oracle resolved all 2705 as SAT, with no oracle UNKNOWNs. The run therefore added 2705 new sound cuts.

At the end, the heuristic candidate layer ceased finding a four-set that hits all current cuts within its search budget. The fallback exact SAT master then exhausted its decision budget and returned `MASTER-UNKNOWN`.

### Performance conclusion from Run 4

The bottleneck is now sharply localized:

> the current expensive question is whether **any four vertices have six internal pair-atoms whose coverage bitsets jointly hit all 6782 known cuts**.

The semantic oracle is not presently the bottleneck: every Run-4 oracle query completed SAT within budget.

## Immediate continuation — specialized exact master

Do **not** spend the next large compute budget merely repeating the same hybrid CEGIS loop from iteration 5910. First replace or supplement the generic SAT master with a specialized exact solver for the current 6782-cut combinatorial problem.

For each unordered vertex pair `{u,v}`, let

`C[u,v] = bitset of known cuts hit by that pair`.

For a four-set `{a,b,c,d}`, define

`C4 = C[a,b] | C[a,c] | C[a,d] | C[b,c] | C[b,d] | C[c,d]`.

The current exact master question is simply whether some four-set has all 6782 bits set.

Recommended exact-search requirements:

1. **Reuse the packed coverage representation.** Avoid rebuilding the original large SAT master merely to rediscover pair coverage.
2. **Apply only sound reductions.** Safe examples include pair-coverage dominance and exact upper-bound pruning. Every reduction must preserve the existence/nonexistence of a four-set.
3. **Use exact branch-and-bound / meet-in-the-middle as the primary candidate.** Precompute pair or triple coverage summaries and prune only when the maximum possible remaining coverage cannot reach all cuts.
4. **Keep the semantic oracle boundary unchanged.** If the exact combinatorial master finds a four-set, send it to the existing A/B oracle. A master candidate is not itself an interface.
5. **Treat inability to finish as UNKNOWN.** A wall-clock timeout or resource cap must not be reported as exhaustion.
6. **If the specialized master proves no four-set exists, retain an independently checkable exhaustion certificate or deterministic reconstruction/checker.** Only then promote the result to support-`<=4` exclusion.

A useful implementation sequence is:

- add a standalone tool, e.g. `tools/exact_fourset_master.py`, that reads the Run-4 checkpoint and constructs exactly the same 6782 cut-coverage bitsets;
- verify on random four-sets that its coverage score exactly matches the existing hybrid code;
- implement deterministic exact search with progress counters/checkpointing;
- test it first against prefixes of the cut library where surviving four-sets are known to exist;
- run it on all 6782 cuts;
- if SAT, feed the resulting support immediately to the semantic oracle and continue CEGIS from 5910;
- if exact UNSAT, stop normal search and independently certify exhaustion.

## Secondary structural lane

The six-vertex separator result is currently the cleanest finite explanation of the conditional P2 same-color relation. It should be preserved independently of the support-4 search outcome.

If the support-4 master is eventually proved UNSAT, that result would say only that this particular **port-free equality-interface language** needs support at least five; it would not invalidate the six-vertex quotient separator proof and would not rule out other semantic observables or geometric gadget constructions.

The eventual Hadwiger–Nelson objective remains geometric: obtain an unconditional forced-mono pair at Euclidean distance at least `1/2`, or an equivalent finite 6-chromatic unit-distance construction. Conditional quotient/SAT statements are intermediate machinery only.

## Checkpoint and UNKNOWN policy

The v3 checkpoint contains the complete generated fooling-pair library plus instrumentation fields including `unresolved_supports`, `last_support`, master/oracle call counts, UNKNOWN counts, and maximum observed solve times.

Keep these invariants:

- `iterations == len(new_pairs)` for the lab-generated portion;
- every seed and generated A/B coloring pair must validate against its defining formula;
- oracle UNKNOWN never generates a blocking clause;
- heuristic failure never modifies the exact master proof space;
- writes remain atomic (`temp -> os.replace`) and gzip integrity is checked before persistence;
- checkpoints are committed after completed guarded slices.

## Certificate policy

Any terminal result must be independently checked before being promoted to a mathematical claim.

For `INTERFACE.json`:

- preserve the exact four vertex IDs;
- preserve all six equality observables;
- preserve the pinned upstream SHA;
- independently reconstruct the oracle query;
- check UNSAT with a second solver and preferably a standalone certificate/checker;
- only after that begin geometric interpretation.

For exact master UNSAT / `FINAL.json`:

- preserve the full fooling-pair/cut library or a reduced exact covering certificate;
- provide a deterministic standalone checker for the claimed exhaustion;
- independently rerun/reconstruct the exhaustion before documenting it as a finite theorem.

For a global empty-difference fooling pair:

- independently validate both A and B colorings;
- verify identical equality pattern on all 391 non-port vertices.

Lean is appropriate only after the finite statement and certificate format stabilize. Do not formalize a moving heuristic search state.

## Resume checklist

When continuing from this handoff:

1. use checkpoint commit `43915f71caff21b316ba1ebcc901a758d0218ea7`;
2. confirm `5910` lab pairs + `872` seeds = `6782` cuts;
3. confirm no `FINAL.json` / `INTERFACE.json` is present;
4. validate the checkpoint gzip and historical invariant;
5. implement/test the specialized exact four-set master before launching another long generic CEGIS run;
6. on a found four-set, return to the exact semantic oracle;
7. on any terminal result, stop and independently verify before making a stronger mathematical claim.
