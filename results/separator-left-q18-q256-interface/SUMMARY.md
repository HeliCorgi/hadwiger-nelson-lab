# q18 != q256 recursive interface

- separator: `[23, 35, 57, 86, 159]` (minimum cut 5)
- side sizes: q18=260, q256=1
- q256 neighborhood exactly separator: **True**
- q18-side extendable states: **8**
- q256-side extendable states: **26**
- intersection: **7** states: `['00121', '00123', '01121', '01123', '01212', '01213', '01231']`
- all intersection states force q18!=q256: **True**
- CaDiCaL/Glucose exact agreement: **True**
- separator induced edges: `[[23, 159], [57, 86]]`

Human-readable refinement: the eight q18-side states satisfy five common disequalities. Those five pairwise relations alone permit exactly nine canonical states, and the q18 side excludes exactly one extra state, `01232`. The state `01234` extends on the q18 side but cannot extend through singleton q256 because its five neighbors use all five colors. In each of the seven common states, q18 can use only colors already present on the separator while q256 can use only missing separator colors, so the endpoints are necessarily distinct.

Workflow run: `34699489848`. Artifact id: `10299328248`. Artifact SHA-256: `f022abe24eee259e8095174a5d2598ddf71378996fdf9c8e0b681f9e9bc45448`.
