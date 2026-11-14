# SOSA/SSN terms by version

`w3c/sdw` at `f40b399 2026-08-31` (SSN-XG and 2017), `w3c/sdw-sosa-ssn` at `b2eb09d 2026-11-11` (2023 Edition). Computed by `scripts/term_inventory.py`; the list is `results/terms.csv`.

| version | namespace | terms | of which deprecated |
|---|---|---|---|
| sosa-ssn-2017 | `http://www.w3.org/ns/sosa/` | 36 | 0 |
| sosa-ssn-2017 | `http://www.w3.org/ns/ssn/` | 21 | 0 |
| sosa-ssn-2017 | `http://www.w3.org/ns/ssn/systems/` | 31 | 0 |
| ssn-2023 | `http://www.w3.org/ns/sosa/` | 141 | 3 |
| ssn-2023 | `http://www.w3.org/ns/ssn/` | 22 | 22 |
| ssn-xg | `http://purl.oclc.org/NET/ssnx/ssn#` | 80 | 80 |

Totals: sosa-ssn-2017 88, ssn-2023 163, ssn-xg 80.

| version | file | terms |
|---|---|---|
| sosa-ssn-2017 | `ssn/integrated/sosa.ttl` | 36 |
| sosa-ssn-2017 | `ssn/integrated/ssn-system.ttl` | 31 |
| sosa-ssn-2017 | `ssn/integrated/ssn.ttl` | 21 |
| ssn-2023 | `ssn/rdf/ontology/core/sosa-actuation.ttl` | 10 |
| ssn-2023 | `ssn/rdf/ontology/core/sosa-common.ttl` | 51 |
| ssn-2023 | `ssn/rdf/ontology/core/sosa-deprecated.ttl` | 3 |
| ssn-2023 | `ssn/rdf/ontology/core/sosa-observation.ttl` | 21 |
| ssn-2023 | `ssn/rdf/ontology/core/sosa-sampling.ttl` | 21 |
| ssn-2023 | `ssn/rdf/ontology/core/ssn-deprecated.ttl` | 22 |
| ssn-2023 | `ssn/rdf/ontology/extensions/sample-relations.ttl` | 5 |
| ssn-2023 | `ssn/rdf/ontology/extensions/sosa-oms.ttl` | 22 |
| ssn-2023 | `ssn/rdf/ontology/extensions/sosa-system.ttl` | 8 |
| ssn-xg | `ssn/integrated/ssnx.ttl` | 80 |

- Terms of 2017 still declared in 2023: 57
- Terms of 2017 no longer declared in 2023 (moved or removed): 31
- Terms of 2023 absent from 2017: 106
