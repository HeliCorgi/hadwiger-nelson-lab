# Closed cyclic multi-copy order 6 / anchor (45,173) — D for A and B

This concrete exact graph is closed. Do not rerun it unchanged.

## Exact graph

- vertices: **2,628**;
- exact induced unit-distance edges: **15,708**;
- inherited-copy edges before cross-copy completion: **13,938**;
- additional exact cross-copy edges: **1,770**;
- all unordered point pairs checked exactly: **3,451,878**;
- final exact completion added **0** missed edges;
- completed graph SHA-256: `2275306ce8ad3d5bdb7d6c514990f08c103fa2474bfdc36a954c8abcac902bcb`.

## A: closed — graph is 5-colorable

Two independent witness routes established ordinary 5-colorability:

- Actions run `34783432616`, artifact `10325667672`: sound color-symmetry breaking on the actual triangle `(0,1,5)`; attempts 0–2 were UNKNOWN, attempt 3 returned SAT; the full coloring was validated on all 15,708 exact edges.
- Actions run `34783526599`, artifact `10324809446`: independent TabuCol-style search reached zero conflicts at restart 2 / iteration 389,211; the returned full coloring was again validated on all exact edges.

Therefore this graph is **not A**.

The earlier generic run `34783286450` was cancelled while solving after exact geometry completion. That cancellation is non-evidence and is superseded for ordinary 5-colorability by the two validated witnesses above.

## B: closed — no forced same-color pair

Actions run `34789803241`, artifact `10327627290`, used targeted local repair only to generate additional proper 5-colorings. Every successful coloring was validated on every exact edge; repair failure or timeout would have been treated as non-evidence.

Result:

- generated validated proper 5-colorings: **690**;
- repair failures: **0**;
- remaining unseparated vertex pairs: **0**;
- greedy compressed witness family: **205** colorings.

The compressed family was then independently checked by `tools/verify_coloring_separation_certificate.py`:

- all **205** colorings are proper on all **15,708** exact edges;
- the **2,628** vertices have **2,628 distinct color-signatures**;
- remaining unseparated pairs: **0**.

Hence every distinct vertex pair is differently colored by at least one proper 5-coloring. There is no B pair in this graph.

**Order 6 / anchor `(45,173)` is D for both A and B.**

## Durable certificate

Committed evidence:

- `COLORING.txt` — one independently validated proper 5-coloring;
- `WITNESSES.txt.xz.b64` — base64/xz packed 205-coloring separation certificate;
- `SEPARATION.json` — generation/compression metadata;
- `VERIFICATION.json` — independent certificate verification result;
- `tools/verify_coloring_separation_certificate.py` — checker.

Hashes:

- raw 205-coloring certificate SHA-256: `5e7db802b387d53e6fa8d2090202335727bcadbb8b799a75cc4d377ca3490775`;
- xz-compressed certificate SHA-256: `dba0ad64c18297cb31a8eaba619a20e8719580a5cc7b7a81cc9d605ee2508d17`.

The durable-certificate rebuild/verification/store workflow completed in Actions run `34789955622` and committed the certificate files to `main`.
