# Exact four-set master implementation

Status: implemented, not yet a mathematical result.

The specialized master requested by `HANDOFF.md` is implemented on branch:

`research/exact-fourset-master`

Implementation commit:

`e83f6d44bf71322eb7725079422ae3cf9cd22306`

Tool:

`tools/exact_fourset_master.py`

Manual workflow on `main`:

`.github/workflows/exact-fourset-master.yml`

The workflow is deliberately `workflow_dispatch` only. Merely pushing code does not start a long solver run.

## Input state

The research branch starts from Run-4 checkpoint commit:

`43915f71caff21b316ba1ebcc901a758d0218ea7`

The input checkpoint is:

`checkpoints/semantic_portfree_s4.json.gz`

Expected validated pair counts before exact-cut deduplication:

- 872 upstream seed A/B fooling pairs;
- 5910 lab-generated A/B fooling pairs;
- 6782 total sound fooling-pair cuts before collapsing identical difference graphs.

The tool independently revalidates every A model against `H* ∧ C88` and every B model against `H* ∧ (c(217) != c(490))` before constructing its cut library.

## Exact search

For each unique fooling-pair difference graph `D_t`, a four-set must contain at least one edge of `D_t`.

The search chooses the sparsest difference graph as a root pivot. Every possible four-set must contain one of that pivot's edges, so root branches enumerate those edges exactly.

For a selected root pair, an uncovered cut is chosen. Every completion must contain one of its edges. Edges incident to the selected pair create a three-vertex branch; disjoint edges determine all four vertices immediately.

For a selected triple, only one vertex slot remains. An uncovered cut can therefore be hit only by an edge from the new fourth vertex to one of the three selected vertices. The tool enumerates all such fourth vertices exactly. If some cut has no edge incident to the triple, that triple is soundly pruned.

Branch-order heuristics do not remove candidates. Root-edge canonicalization only assigns each four-set to the earliest pivot edge it contains, eliminating duplicate work.

The implementation contains a built-in randomized self-test. On 400 small random instances, the edge-branching search was compared against literal enumeration of every four-set and matched the brute-force SAT/UNSAT result in every case before the code was committed.

## Results and safety boundary

Possible outputs under `results/exact-fourset-master/`:

- `CANDIDATE.json`: a four-set hits every currently known unique cut. This is not yet a semantic interface; send the support to the existing exact A/B oracle.
- `STATE.json`: resumable progress between fully exhausted pivot-root branches. A timed-out root branch is retried; timeout has no logical meaning.
- `FINAL.json`: the specialized search exhausted every pivot-root branch and found no four-set hitting all cuts.

Even if `FINAL.json` is produced, the tool labels it

`EXACT-MASTER-EXHAUSTED-REQUIRES-INDEPENDENT-VERIFY`.

Do not promote that output to a public support-`<=4` theorem until a genuinely independent implementation or exact certificate/checker reproduces the exhaustion.

If independently verified, exact master exhaustion would imply that the pinned A/B system has no port-free equality semantic interface supported on at most four vertices. It would still **not** prove `chi(R^2) >= 6`; the Hadwiger–Nelson objective still requires geometric realization / an unconditional unit-distance forcing construction.
