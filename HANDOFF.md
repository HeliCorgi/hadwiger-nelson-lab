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

No timeout or interrupted solver call is evidence for any of the terminal outcomes above.

## Latest durable state

Branch:

`research/semantic-interface`

Checkpoint path:

`checkpoints/semantic_portfree_s4.json.gz`

Latest durable checkpoint commit:

`a10e0f9`

Current counts after Run 2:

- 872 validated upstream seed fooling pairs;
- 3205 new fooling pairs generated in this lab;
- 4077 represented sound cuts total;
- no empty-difference global fooling pair;
- no oracle-UNSAT four-set;
- no master-UNSAT exhaustion result.

This is the state from which the next continuation must resume.

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

## Performance interpretation

The exact CEGIS search remains productive, but individual solve times are highly variable and the accumulated master constraints are becoming expensive.

Run 2 generated 680 new cuts in roughly six 45-minute internal windows. The last slice generated only 74 completed new cuts and ended while another solver operation was still active. Re-running the exact same workflow is sound, but it is increasingly compute-inefficient.

The combinatorial master can be restated cleanly: find a 4-set `S` such that for every accumulated difference graph `D_t`, at least one of the six pairs in `K4[S]` lies in `D_t`. This suggests separating candidate generation from certificate production.

## Recommended next implementation

Before another large continuation run, prefer the following order.

1. Add timing/instrumentation around `master.solve()` and `oracle_for_support()` so future stalls are attributable.
2. Add a sound per-query interruption path. A timed-out query must return `UNKNOWN` and be recorded for retry; it must never be converted into SAT, UNSAT, or a permanent blocking clause.
3. Implement a specialized bitset/local-search four-set candidate generator over the 4077 accumulated difference graphs. This may be heuristic for finding candidates quickly.
4. Retain exact SAT as the completeness backstop. Only exact master UNSAT may support the claim that support `<=4` has been exhausted.
5. If a small set of supports repeatedly time out in the oracle, place them in a separate unresolved queue and solve them independently with longer budgets / a second solver rather than silently skipping them.

A useful architecture is therefore:

`fast candidate generator -> exact oracle -> sound cut -> repeat`,

with the current exact SAT master periodically invoked as the exhaustion checker.

Do **not** permanently discard a four-set merely because one solver invocation timed out; doing so would destroy completeness.

## Timeout policy

The current workflow uses:

1. Node-24 GitHub Action majors (`checkout@v7`, `setup-python@v7`, `upload-artifact@v7`);
2. six short internal solver slices;
3. an outer GNU `timeout` guard per slice;
4. `--checkpoint-every 1`;
5. atomic gzip checkpoint writes (`temp -> os.replace`);
6. gzip integrity validation before persistence;
7. commit/push after every completed slice;
8. timeout exit codes treated as continuation states only.

Run 2 demonstrated that this is safe against loss of completed work. The next engineering improvement should be per-query interruption rather than simply making the outer timeout longer.

## Certificate policy

Any terminal result must be independently checked before being promoted to a mathematical claim.

For an interface candidate, preserve the exact four vertex IDs, all six equality atoms, pinned upstream SHA, and an independently reconstructed UNSAT query. Prefer a second SAT solver and then a small standalone certificate/checker.

For master UNSAT, preserve the complete fooling-pair library or an independently checkable reduced covering certificate. The current gzip checkpoint is sufficient to resume computation but should not by itself be treated as a publication-grade UNSAT certificate.

Lean should be used only after the finite combinatorial statement and its certificate format have stabilized. Formalizing a moving SAT search state would add little value.

## Immediate continuation

Resume from commit `a10e0f9` / `checkpoints/semantic_portfree_s4.json.gz`.

Do not restart from Run-1 artifacts or regenerate the 3205 lab fooling pairs unless checkpoint validation fails.

Preferred next step is **instrumentation + per-query UNKNOWN handling + faster four-set candidate generation**, followed by another guarded Actions run. If no code changes are made, the existing workflow can still be rerun soundly from iteration 3205, but expect diminishing throughput and possible repeated long single-query stalls.
