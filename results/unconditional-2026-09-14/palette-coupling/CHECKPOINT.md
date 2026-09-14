# Coupled palette-center checkpoint

Updated 2026-09-15 JST.

This file records the current unconditional A-search mainline after the p1q7 cube itself was closed NOT_A. All positive colorings below were validated on every saved exact unit edge. Heuristic failure, restricted-family failure, and fixed-base positive MaxSAT optima are non-evidence.

## Closed NOT_A layers

- all400 center layer: 9,769 vertices / 61,404 edges; 400 centers / 400 center-center edges; fixed-base optimum 24; validated repair at 774,067 iterations.
- adaptive95: 9,464 / 58,416; 95 centers / 56 center edges; fixed-base 22; validated repair at 83,808 iterations.
- adaptive119: 9,488 / 58,676; 119 centers / 72 center edges; fixed-base 14; validated repair at 436,973 iterations. It is a subgraph of all400 and therefore A-redundant.
- top1200 58-center four-chromatic core: center core 58 vertices / 127 edges, chi=4; p1q7+core has 9,427 / 58,016, semantic SHA `63698c709736b0ad472f33b8145919b1d719dcccc2a91a5c7aa2ce70758ebd97`; seed conflict 2 repaired in 1,375 iterations.
- all1200 center layer: **10,569 vertices / 68,754 edges**, 1,200 centers / 2,550 center-center edges; semantic SHA `1815aadc36704487c05d24f0c607610afb7644037793e3174187ecfa38f79e58`; fixed-base optimum 50; validated proper 5-coloring after **694,847** repair iterations. Actions `34887160185`.
- 72-direction fresh conflict-edge layer after all1200: 10,575 / 68,789, fixed-coloring optimum 3, semantic SHA `bb6346e9d102eeb8b4eb6e798636a01f472d9f03412d0a30e8d18e92ed15b7c2`; repaired in 112 iterations. Actions `34895023197`.
- one further 72-direction coupled CEGIS round: 10,577 / 68,798, seed conflict 1, semantic SHA `b9e730f437a810154f65ba28570e20e12fc4a2425dda2882c12d311940463081`; repaired in 5 iterations. The next exact bounded scan had zero forced-singleton conflict edges in the 72-direction language. Actions `34895252857`.

## Exact center-graph/list facts

Top1200 center graph:

- 1,200 vertices / 2,550 exact unit edges;
- largest component 1,003 / 2,391;
- 337 center triangles;
- independently confirmed with CaDiCaL: 3-color UNSAT and 4-color SAT, hence **chi=4**. Actions `34886911698`.

Under the validated all1200 proper base coloring, every center allowed list has size at most 3:

- size 1: 456 centers;
- size 2: 642;
- size 3: 102.

Nevertheless the center list CSP is proper-colorable. Thus `chi(center)=4` and even `|L(v)|<=3` everywhere are insufficient; list alignment matters.

Exact fixed-base RC2 analysis over all 1,200 centers tested every common three-color palette T. Best T is `{0,2,3}`, but **at least 312 centers must be assigned outside T** in any proper center list-coloring. Other palettes require 315--377 outside assignments. So there is no small 1--few escape-valve route to a common three-color palette for this fixed base. Actions `34895895770`.

For the 58-center four-chromatic core, an independent weighted list-coloring calculation similarly needs at least **15** outside-palette centers for its best common three-color palette.

## Direction-language boundary

The original direction dictionary from the first 1,192 p1q7 vertices has only 72 directed unit vectors. After the final 72-direction CEGIS escape:

- fresh p+d candidates: 613,006;
- forced-singleton candidates: 228;
- direct killers: 9;
- same-forced-color fresh unit conflict edges: **0**.

This is only exhaustion of that bounded 72-direction language.

Using all exact p1q7 base edges among the first 9,369 vertices yields **494 directed unit vectors**. In that wider language, for the same validated escape coloring:

- fresh candidates: **4,344,706**;
- known color-count histogram: 1: 4,258,590; 2: 69,492; 3: 12,800; 4: 3,466; 5: 358;
- direct killers: **358**;
- forced-singleton candidates: **3,466**;
- same-forced-color fresh unit conflict edges: **310** on 538 endpoints.

This 494-direction pressure is highly recurrent across the three most recent validated base colorings: all **358** direct killers are common to all three; **308/310** conflict edges are common to all three; for those 308 edges, the forced missing-color label itself agrees across all three colorings.

## Active strongest test

Workflow `hn-palette-wide494`, Actions **`34895797863`**, builds a true supergraph of the current 10,577-vertex graph by adding all 358 direct killers plus all 538 endpoints of the 310 forced-missing-color conflict edges (expected up to 896 fresh centers), then exact-checks every added-center relation. It runs unrestricted repair and full exact 5-color SAT with both CaDiCaL195 and Glucose4.

This is currently the strongest nonredundant A test. A validated coloring closes it NOT_A. Solver difficulty/timeout is non-evidence. If both exact solvers report UNSAT, treat it only as an A candidate until the repository's independent geometry/completion/proof confirmation protocol is completed.
