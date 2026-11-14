# Pilot: open-access full texts that S2ORC does not give

Candidates of strata A and B with a DOI, open access in OpenAlex, without an S2ORC full text: 512; random sample of 30 (seed 20261111); locations asked to OpenAlex (`raw/2026-11-11T1440-openalex-locations.jsonl.gz`), first PDF URL downloaded once; computed by `scripts/pilot_oa_fulltext.py`, manifest `raw/2026-11-11T1440-oa-pilot-manifest.json`.

| outcome | works |
|---|---|
| pdf | 12 |
| no PDF URL | 9 |
| not a PDF | 5 |
| error | 4 |

- Text extracted: 12; reference list found and cut: 11; naming SOSA/SSN in the body: 10; with terms: 3

## Failed downloads by host

| host | works |
|---|---|
| upcommons.upc.edu | 1 |
| ink.library.smu.edu.sg | 1 |
| zenodo.org | 1 |
| www.sciencedirect.com | 1 |
| hal.science | 1 |
| www.preprints.org | 1 |
| ars.els-cdn.com | 1 |
| orca.cardiff.ac.uk | 1 |
| cris.unibo.it | 1 |

