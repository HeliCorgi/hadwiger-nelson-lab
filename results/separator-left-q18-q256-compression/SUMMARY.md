# q18 != q256 recursive interface compression

- separator: `[23, 35, 57, 86, 159]` (minimum cut 5)
- side sizes: 260 / 1
- q18-side states: **8**: `[('00121', [0]), ('00123', [0, 3]), ('01121', [0]), ('01123', [0, 3]), ('01212', [0]), ('01213', [0, 3]), ('01231', [0, 1]), ('01234', [0, 3, 4])]`
- intersection states: **7**: `['00121', '00123', '01121', '01123', '01212', '01213', '01231']`
- q18-side states excluded by q256 side: `[{'state': '01234', 'endpoint_colors': [0, 3, 4]}]`
- q256 degree: **5**; neighborhood exactly separator: **True**
- q18 always uses an already-used boundary color on intersection: **True**
- q256 options are exactly the missing boundary colors: **True**
- endpoint option sets always disjoint: **True**
- solver cross-check: Cadical195 and Glucose4 enumerations identical
