# Handoff — port-free support-4 semantic search

Last updated: 2026-09-11

## Scope

This handoff concerns only the current computational lane inherited from `HeliCorgi/five-color-forcing-anatomy`.

Pinned upstream commit:

`d1e80998bda337d9fa721f2e96d203ae54e97fc8`

The target question is whether the P2 forcing system admits an equality-based semantic interface supported on at most four vertices that does not use ports 217 or 490.

Define:

- `A = H* ∧ C88`;
- `B = H* ∧ (c(217) != c(490))`.

`H*` is the first core from `B5_MULTICORE.json`; `C88` is `C_min` from `B5_P2_LEMMA.json`.

## Why exact four-sets suffice

For a support `S`, the semantic state is the equality partition of colors on `S`. If the projected A-state and B-state sets are disjoint on a support of size at most three, adding arbitrary non-port vertices cannot make two previously different restrictions equal. Therefore any separator with support `<= 3` extends to one on exactly four vertices.

Consequently, exhaustion of all non-port four-sets is complete for the support-`<=4` equality-interface question.

## CEGIS formulation

There are 391 non-port vertices and 76,245 unordered non-port pairs.

For each A/B fooling pair `(alpha,beta)`, form its difference graph `D(alpha,beta)`: an edge `{u,v}` is present exactly when

`[alpha(u)=alpha(v)] != [beta(u)=beta(v)]`.

A proposed four-set survives that fooling pair iff its induced `K4` contains at least one edge of `D(alpha,beta)`. Thus the master seeks four vertices whose six internal pairs hit every accumulated difference graph.

The oracle fixes those six equality observables and asks whether an A-model and B-model can agree on all of them.

- Oracle SAT: save the A/B model pair and add its difference graph as a sound cut.
- Oracle UNSAT: save the four-set as `INTERFACE.json`; it is a semantic-interface candidate requiring independent verification and geometric translation.
- Master UNSAT: save `FINAL.json`; this excludes all port-free equality interfaces of support `<=4` for the pinned system.
- An A/B fooling pair whose difference graph is empty on all 391 non-port vertices would be stronger: it excludes port-free equality interfaces of any support.

No timeout, decision-budget exhaustion, or interrupted solver call is evidence for any of the terminal outcomes above.

## Latest durable mathematical state

Branch:

`research/semantic-interface`

Checkpoint path:

`checkpoints/semantic_portfree_s4.json.gz`

Baseline durable checkpoint commit before the hybrid continuation:

`a10e0f9`

Counts after Run 2:

- 872 validated upstream seed fooling pairs;
- 3205 new fooling pairs generated in this lab;
- 4077 represented sound cuts total;
- no empty-difference global fooling pair;
- no oracle-UNSAT four-set;
- no master-UNSAT exhaustion result.

These counts remain the conservative durable mathematical state until a later hybrid-search checkpoint commit is produced. Do not count a running or failed preflight as mathematical progress.

## Run 1 — baseline long-slice run

Workflow run: `34436888946`

Run 1 used the original three long solver stages and reached iteration 2525.

Final observed state after Run 1:

- 872 validated seed fooling pairs;
- 2525 new fooling pairs;
- 3397 total sound cuts;
- no terminal result.

Latest checkpoint commit after Run 1:

`5283a5f`

Stage-3 artifact:

- artifact id: `10157101775`
- digest: `sha256:a90421e0ec8351a896b039bc7bb9ae94cc9374b41097ac0c714448f8f270b172`

The Node.js 20 message in this run was a deprecation warning rather than a failed step.

## Run 2 — hardened guarded-slice run

Workflow run: `34493404794`

Run 2 used the revised workflow with Node-24 action majors, six guarded solver slices, atomic checkpoints, and `--checkpoint-every 1`.

Slice endpoints were:

- slice 1: 2525 -> 2669;
- slice 2: 2669 -> 2778;
- slice 3: 2778 -> 2922;
- slice 4: 2922 -> 3008;
- slice 5: 3008 -> 3131;
- slice 6: 3131 -> 3205.

Thus Run 2 added 680 sound fooling pairs and moved the total from 3397 to 4077 cuts.

No `FINAL.json` or `INTERFACE.json` was produced. The result is therefore **nonterminal**.

Run-2 artifact:

- artifact id: `10170346817`
- digest: `sha256:44021dfa60c29f76f61df23e69c24f6469fc5a4c571f8bf1975bde129e8c95c3`

### Important timeout observation

The sixth slice started at approximately `19:01:18Z`. Iteration 3205 completed at `19:44:25Z`. No later iteration completed before the outer 3000-second guard fired at approximately `19:51:18Z`.

Therefore one solver operation after iteration 3205 consumed at least several minutes without returning a completed CEGIS step. The logs do not distinguish whether that time was spent in the master solve or the oracle solve, so do not attribute the stall to either component without instrumentation.

The timeout protection behaved correctly:

- iteration 3205 had already been atomically checkpointed;
- the outer guard terminated only the active process;
- the checkpoint gzip passed the workflow integrity path and was committed as `a10e0f9`;
- the timeout was not interpreted as SAT or UNSAT.

This validates the checkpoint design, but it also shows that wall-clock slice guards alone are not enough for efficient continuation.

## Hybrid continuation implemented on 2026-09-11

The branch was first fast-forwarded to the merged `main` state at merge commit `8fac245` so that the Run-2 checkpoint, documentation, and workflow all had one common base.

The continuation architecture requested by the Run-2 handoff has now been implemented:

`fast bitset/local-search candidate generator -> exact oracle -> sound cut -> repeat`

with the original exact SAT master retained as the completeness backstop.

### Fast candidate layer

For every one of the 76,245 non-port pair-atoms, the code stores a bitset of accumulated fooling-pair cuts hit by that atom. A four-set can therefore be scored by OR-ing the six bitsets of its `K4` edges and counting uncovered cuts.

A restart/local-improvement search changes one support vertex at a time and looks for a four-set whose six edges hit all currently known cuts. This layer is only a candidate generator:

- finding a zero-uncovered four-set is useful, but it is still sent to the exact semantic oracle;
- failing to find one has no mathematical meaning;
- heuristic failure can never be promoted to master UNSAT.

Only the unchanged exact SAT master returning `UNSAT` may certify exhaustion of all support-`<=4` equality interfaces.

### Instrumentation and UNKNOWN handling

The v3 checkpoint format adds:

- `unresolved_supports`;
- `last_support`;
- counts of master/oracle calls and UNKNOWNs;
- maximum observed wall time for master and oracle calls;
- the existing complete list of newly generated fooling pairs.

A support whose oracle solve is UNKNOWN is stored for retry and is **not** blocked by a clause. The fast layer avoids immediately cycling back to unresolved supports, while an exact-master proposal for an unresolved support is retried with a larger budget. This preserves completeness.

### Run 3 — failed preflight, no mathematical progress

Workflow run: `34561883743`

Initial hybrid commit: `bcc82a0`.

The first implementation attempted wall-clock interruption through PySAT's CaDiCaL wrapper. The smoke test failed before preflight/search with:

`NotImplementedError: Limited solve is currently unsupported by CaDiCaL.`

The exception arose at `clear_interrupt()` for `python-sat==1.9.dev7`. No search slice started and the real checkpoint was not modified. Run 3 therefore contributes **zero** new fooling pairs and no mathematical result.

Run-3 artifact id: `10184599980`; it contains the pre-existing checkpoint state and is not a newer mathematical checkpoint.

### Corrected decision-budget implementation

Correction commit:

`b163d55edea3ceddd333b48fa3ddb4f5d92ef414`

Rather than relying on the unsupported interrupt-clear path, the solver now uses CaDiCaL decision budgets:

- set `dec_budget(N)`;
- call `solve_limited()`;
- `True` = SAT, `False` = UNSAT, `None` = UNKNOWN/budget exhausted;
- reset the budget after the call.

The production starting budget is 2,000,000 decisions and unresolved supports may be retried up to a 16,000,000-decision cap. Wall-clock time is still measured for diagnostics. The outer GNU timeout remains an independent hard safety guard.

This distinction is important: budget exhaustion is recorded as UNKNOWN and is never interpreted as UNSAT.

### Run 4 — current continuation

Workflow run: `34562068005`

Run 4 is based on correction commit `b163d55`.

Verified before the production search step:

- Node-24 action setup succeeded;
- dependency installation succeeded;
- CaDiCaL decision-budget smoke test succeeded;
- a copied Run-2 checkpoint passed the v2 -> v3 compatibility preflight;
- the real production checkpoint was not modified by the preflight;
- the guarded hybrid production step started from iteration 3205 / 4077 cuts.

At the time of this handoff update, Run 4 is in progress. Until a hybrid slice commits a newer checkpoint or writes `FINAL.json` / `INTERFACE.json`, the conservative durable mathematical state remains the Run-2 counts above.

## Performance interpretation

The exact CEGIS search remained productive through Run 2, but individual solve times became highly variable and the accumulated master constraints became expensive.

The hybrid layer is intended to move most routine candidate generation out of the large exact SAT master. The exact master is still periodically/fallback invoked, specifically so the completeness claim remains anchored to an exact solver result rather than to the heuristic search.

The decision budget is a computational control, not a logical assumption. If it is exhausted, the query remains unresolved.

## Timeout policy

The current workflow uses:

1. Node-24 GitHub Action majors (`checkout@v7`, `setup-python@v7`, `upload-artifact@v7`);
2. six guarded internal solver slices;
3. an outer GNU `timeout` guard per slice;
4. `--checkpoint-every 1`;
5. atomic gzip checkpoint writes (`temp -> os.replace`);
6. gzip integrity validation before persistence;
7. commit/push after every completed slice;
8. decision-budget exhaustion and timeout exit codes treated as continuation states only;
9. a preflight on a copied checkpoint before production search.

The production checkpoint is therefore not used as a test scratch file.

## Certificate policy

Any terminal result must be independently checked before being promoted to a mathematical claim.

For an interface candidate, preserve the exact four vertex IDs, all six equality atoms, pinned upstream SHA, and an independently reconstructed UNSAT query. Prefer a second SAT solver and then a small standalone certificate/checker.

For master UNSAT, preserve the complete fooling-pair library or an independently checkable reduced covering certificate. The gzip checkpoint is sufficient to resume computation but should not by itself be treated as a publication-grade UNSAT certificate.

Lean should be used only after the finite combinatorial statement and its certificate format have stabilized. Formalizing a moving SAT search state would add little value.

## Immediate continuation

If Run 4 has produced a committed checkpoint after this document was written, use that newer checkpoint rather than `a10e0f9`.

Otherwise resume from `a10e0f9` / `checkpoints/semantic_portfree_s4.json.gz` with the corrected hybrid code at or after `b163d55`.

Do not regenerate the 3205 lab fooling pairs unless checkpoint validation fails. Do not permanently block any support solely because of UNKNOWN, decision-budget exhaustion, or wall-clock timeout.

On a terminal result:

1. stop ordinary search;
2. independently rebuild and verify the decisive SAT/UNSAT query;
3. preserve the exact finite certificate data;
4. only then update the public mathematical claim or begin Lean formalization.
