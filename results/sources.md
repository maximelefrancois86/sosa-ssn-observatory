# Semantic Scholar against the OpenAlex candidate corpus

Semantic Scholar harvest `2026-11-07T1353`, OpenAlex corpus of `results/scoping.md`; computed by `scripts/compare_sources.py`. Same work: equal DOI, or equal normalised title within one year.

- Distinct citing papers in Semantic Scholar: 2397; already OpenAlex candidates: 1806 (75.3 %); **not in the OpenAlex corpus: 591**
- Of these, by the strata rule (review/101): A 177, B 136, C 278
- Citation records with citation contexts: 1597 of 2905 (55.0 %)

## Per seed

| seed | citing papers in Semantic Scholar | in the OpenAlex corpus | not in it |
|---|---|---|---|
| ssn-xg-report-2011 | 197 | 124 | 73 |
| sso-2010 | 175 | 131 | 44 |
| compton-2012 | 1573 | 1263 | 310 |
| cox-2017-oosf | 102 | 36 | 66 |
| w3c-rec-2017 | not found | — | — |
| w3c-rec-2017-hal | not found | — | — |
| janowicz-2019 | 555 | 428 | 127 |
| janowicz-2018-ssrn | not found | — | — |
| haller-2019 | 278 | 208 | 70 |
| taylor-2019-revamped | 25 | 10 | 15 |

