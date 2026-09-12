# q18-side unique forbidden state core

- five common pairwise disequalities: `[[23, 57], [23, 86], [23, 159], [57, 86], [86, 159]]`
- these alone allow 9 states: `['00121', '00123', '01121', '01123', '01212', '01213', '01231', '01232', '01234']`
- unique extra state rejected by q18 side: **01232**
- full-side forbidden-state SAT checks: `{'Cadical195': False, 'Glucose4': False}`
- nearby valid control `01231` SAT checks: `{'Cadical195': True, 'Glucose4': True}`
- raw assumption core: **251 vertices**
- best inclusion-minimal core: **236 vertices / 1263 edges** (degree-desc)
- best core cross-check: forbidden CaDiCaL/Glucose=False/False; control=True/True
