# Handoff — port-free support-4 semantic search

Last updated: 2026-09-10

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

## Run 1 checkpoint

Workflow run: `34436888946`

All three original stages completed successfully. The apparent Node.js message in the logs is a deprecation warning, not a failed step.

Final observed state:

- 872 validated seed fooling pairs loaded from the upstream handoff;
- 2525 new fooling pairs generated in this lab;
- 3397 sound cuts represented in total;
- no empty-difference global fooling pair;
- no oracle-UNSAT four-set;
- no master-UNSAT exhaustion result;
- checkpoint status: time-slice complete.

Latest checkpoint commit after Run 1:

`5283a5f`

Checkpoint path:

`checkpoints/semantic_portfree_s4.json.gz`

Stage-3 artifact:

- artifact id: `10157101775`
- digest: `sha256:a90421e0ec8351a896b039bc7bb9ae94cc9374b41097ac0c714448f8f270b172`

The artifact is auxiliary; the committed gzip checkpoint is the primary continuation state.

## Performance observation

The search remained productive throughout Run 1, but candidate generation became progressively more expensive. In stage 1 the run reached iteration 1414; stage 2 reached 1999; stage 3 reached 2525. This is consistent with a master problem that gets harder as more difference-graph hitting constraints accumulate.

The current exact SAT master remains valid. If throughput degrades further, the next implementation target should be a specialized bitset/local-search candidate generator for the four-vertex hitting problem, while retaining exact SAT as the final exhaustion oracle. A heuristic generator may produce candidates but must never be used to claim master UNSAT.

## Timeout policy after Run 1

The original workflow used ~200-minute solver slices inside 220-minute jobs. It completed, but that leaves an unnecessarily large exposure to a single slow SAT call and used action versions that emitted Node.js 20 deprecation warnings.

The revised workflow uses:

1. Node-24 GitHub Action majors (`checkout@v7`, `setup-python@v7`, `upload-artifact@v7`);
2. shorter solver slices with an outer OS-level timeout guard;
3. `--checkpoint-every 1`, so every completed CEGIS iteration is durable before substantial additional work;
4. an atomic gzip checkpoint (`write temp -> os.replace`), so interruption cannot leave a partially written checkpoint;
5. checkpoint validation before commit;
6. a commit/push after every slice, so loss of the runner VM only loses at most the currently active iteration/slice;
7. timeout exit codes treated as continuation states, never as mathematical results.

If a candidate repeatedly consumes the hard timeout, do not block it permanently as that would make eventual exhaustion unsound. Instead isolate it for a separately certified solver run or add a sound per-call interruption mechanism that returns UNKNOWN and records the unresolved support.

## Certificate policy

Any terminal result must be independently checked before being promoted to a mathematical claim.

For an interface candidate, preserve the exact four vertex IDs, all six equality atoms, pinned upstream SHA, and an independently reconstructed UNSAT query. Prefer a second SAT solver and then a small standalone certificate/checker.

For master UNSAT, preserve the complete fooling-pair library or an independently checkable reduced covering certificate. The current gzip checkpoint is sufficient to resume computation but should not by itself be treated as a publication-grade UNSAT certificate.

Lean should be used only after the finite combinatorial statement and its certificate format have stabilized. Formalizing a moving SAT search state would add little value.

## Immediate continuation

Continue from `checkpoints/semantic_portfree_s4.json.gz` on branch `research/semantic-interface` using the revised workflow. If the exact master continues to slow substantially before reaching a terminal state, implement a specialized four-set candidate finder over the accumulated difference-graph bitsets, with the exact SAT master retained as the completeness backstop.
