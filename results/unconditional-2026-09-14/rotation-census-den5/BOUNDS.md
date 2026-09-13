# Denominator-5 exact rotation census — bounded boxes tried

Target: normalized `r = (a + b*sqrt(-11))/5` in `K2 = Q(zeta30,sqrt(-11))` with exact `r*conj(r)=1`, excluding all `zeta30^k`.

These are **finite bounded searches only**. Empty results do not imply nonexistence elsewhere in K2.

| sparse support bound | coefficient magnitude bound | numerators checked | float-near `|numerator|^2≈25` | exact unit candidates |
|---:|---:|---:|---:|---:|
| 4 | 3 | 1,242,048 | 0 | 0 |
| 5 | 3 | 18,224,832 | 0 | 0 |
| 4 | 5 | 9,386,080 | 11 | 0 |
| 3 | 20 | 18,016,320 | 11 | 0 |

The boxes overlap, so the row counts must not be summed as a unique-candidate count.

All float-near proposals were subjected to exact K2 arithmetic. None satisfied exact unit modulus. The active construction therefore does not keep expanding this brute-force box; it uses the explicit exact non-root rotation

`(-1 + 3*sqrt(-11))/10`,

whose exact squared modulus is `(1 + 99)/100 = 1`, to test asymmetric links between already-closed copy orbits.
