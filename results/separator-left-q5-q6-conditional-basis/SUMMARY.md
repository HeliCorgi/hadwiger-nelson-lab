# q5=q6 conditional palette basis

- K4 anchors: `[0, 4, 8, 21]`; clique=True
- q6 direct edges to K4 anchors: `{'0': True, '4': False, '8': False, '21': True}`
- extra boundary vertices: `[17, 30, 59, 68, 105, 223]`

## q6_equals_q4
- minimum number of extra vertices that must avoid the fifth color: **6**
- all minimum bases: `[[17, 30, 59, 68, 105, 223]]`
- all six constraints UNSAT in both solvers: **True**

## q6_equals_q8
- minimum number of extra vertices that must avoid the fifth color: **1**
- all minimum bases: `[[17]]`
- all six constraints UNSAT in both solvers: **True**

- solver cross-check: CaDiCaL195 and Glucose4 found identical minimum-cardinality fifth-color-ban bases. Rescue witnesses are recorded separately for each solver.
