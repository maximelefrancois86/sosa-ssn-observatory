# Detection of SOSA/SSN in the full texts

Full texts of S2ORC kept by `scripts/scan_s2orc.py` (shards scanned: see the last `raw/*-s2orc-scan-manifest.json`), occurrences of the namespace IRIs, prefixed names and distinctive local names of `results/search-strings.csv` in the body only; computed by `scripts/build_items.py`. Not screened.

- Full texts: 700; naming SOSA/SSN in the body (terms or names in prose): 616; with terms (IRIs, prefixed or local names): 256

| stratum | full texts | naming SOSA/SSN | with terms | share naming |
|---|---|---|---|---|
| A | 289 | 261 | 123 | 90.3 % |
| B | 198 | 171 | 41 | 86.4 % |
| C | 148 | 119 | 27 | 80.4 % |
| D | 65 | 65 | 65 | 100.0 % |

## Measured lengths (words)

| what | first quartile | median | third quartile |
|---|---|---|---|
| body of a full text | 3965 | 6224 | 9124 |
| passages of a work with occurrences | 181 | 363 | 702 |

## Full texts still to retrieve (strata A and B)

Candidates with a DOI, by whether S2ORC gives their full text (matched by DOI) and, if not, by their open-access status in OpenAlex. Candidates without a DOI are counted apart.

| stratum | S2ORC full text | open access, not in S2ORC | of which PDF text retrieved | closed or unknown | no DOI |
|---|---|---|---|---|---|
| A | 235 | 352 | 462 | 278 | 21 |
| B | 171 | 160 | 276 | 279 | 16 |

## Second source: open-access PDFs (scripts/harvest_oa_fulltext.py)

Retrieval `2026-11-11T1451, 2026-11-11T1519, 2026-11-11T1531, 2026-11-12T1332, 2026-11-12T1615, 2026-11-12T1633, 2026-11-12T1651, 2026-11-12T1653, 2026-11-12T1654, 2026-11-12T1707, 2026-11-12T1711, 2026-11-12T1733, 2026-11-12T1748, 2026-11-13T1640, 2026-11-13T1707, 2026-11-13T1804, 2026-11-14T1052`: 794 texts extracted with pdftotext; reference list found and cut in 750; paragraphs split on blank lines, no section headers (so no E1 by script). Counted apart from S2ORC.

| stratum | full texts | naming SOSA/SSN | with terms | share naming |
|---|---|---|---|---|
| A | 462 | 424 | 216 | 91.8 % |
| B | 276 | 242 | 75 | 87.7 % |
| D | 56 | 48 | 27 | 85.7 % |

| stratum D signal | texts | naming SOSA/SSN | with terms |
|---|---|---|---|
| strong | 36 | 34 | 26 |
| weak | 20 | 14 | 1 |

| what | first quartile | median | third quartile |
|---|---|---|---|
| body of a full text | 4468 | 6699 | 11634 |
| passages of a work with occurrences | 379 | 721 | 1418 |

## What S2ORC adds to stratum D

Works naming SOSA/SSN in the body that cite no seed: 65; of these, already in the stratum D of the OpenAlex full-text search (same DOI): 22; **new: 43**; new and with terms (IRIs, prefixed or local names): 43.

