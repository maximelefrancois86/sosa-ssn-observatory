# Stratum D: works found by the full-text search of OpenAlex

Full-text harvest `2026-11-07T1627` (282 queries, strings of `results/search-strings.csv`: namespace IRIs under several spellings, prefixed names; no local names), against the OpenAlex candidate corpus of `results/scoping.md` and the last Semantic Scholar harvest; computed by `scripts/stratum_d.py`. **Not screened**: the precision of the search is not measured yet.

- Distinct works found: **856**; truncated queries: 0
- Already OpenAlex candidates: 213 — A 150 of 886 (16.9 %), B 28 of 626 (4.5 %), C 35 of 792 (4.4 %)
- Not OpenAlex candidates but citing a seed according to Semantic Scholar: 28
- **Stratum D (cites no seed in either source): 615**, by signal (rule in the script, precision to measure): strong 104, weak 468, early 43

## Stratum D by what was found

| found by | works |
|---|---|
| prefixed names only | 549 |
| namespace IRI only | 43 |
| both | 23 |

## Stratum D by OpenAlex type

| type | works |
|---|---|
| article | 348 |
| conference-paper | 76 |
| dissertation | 59 |
| preprint | 47 |
| review | 26 |
| report | 16 |
| book | 14 |
| book-chapter | 13 |
| other | 6 |
| paratext | 3 |
| dataset | 3 |
| software | 2 |
| conference-abstract | 1 |
| study-registration | 1 |

## Stratum D: signal against a Semantic Web term in title, abstract or keywords

A crude indicator of relevance (ontology, semantic, RDF, OWL, linked data, knowledge graph, SPARQL), not a screening decision.

| signal | with a term | without | share with |
|---|---|---|---|
| strong | 80 | 24 | 76.9 % |
| weak | 79 | 389 | 16.9 % |
| early | 2 | 41 | 4.7 % |

## Strong signals of stratum D by year

| year | works |
|---|---|
| 2011 | 4 |
| 2012 | 3 |
| 2013 | 2 |
| 2014 | 1 |
| 2015 | 5 |
| 2016 | 4 |
| 2017 | 2 |
| 2018 | 15 |
| 2019 | 8 |
| 2020 | 12 |
| 2021 | 9 |
| 2022 | 4 |
| 2023 | 10 |
| 2024 | 10 |
| 2025 | 9 |
| 2026 | 6 |

## Strings with the most works (40 first)

| string | works | OpenAlex candidates | citing per Semantic Scholar | stratum D | stratum D, strong |
|---|---|---|---|---|---|
| `sosa:Sensor` | 171 | 90 | 10 | 71 | 22 |
| `ssn:Sensor` | 138 | 29 | 4 | 105 | 9 |
| `ssn:System` | 137 | 12 | 4 | 121 | 8 |
| `w3.org/ns/sosa` | 87 | 45 | 3 | 39 | 39 |
| `w3.org/ns/ssn` | 57 | 29 | 3 | 25 | 25 |
| `ssn:Condition` | 53 | 0 | 0 | 53 | 1 |
| `sosa:Observation` | 45 | 32 | 2 | 11 | 9 |
| `purl.oclc.org/NET/ssnx/ssn` | 40 | 18 | 3 | 19 | 19 |
| `ssn:Observation` | 38 | 17 | 2 | 19 | 9 |
| `ssn:Sensitivity` | 28 | 0 | 0 | 28 | 1 |
| `sosa:System` | 25 | 1 | 1 | 23 | 0 |
| `ssn:Input` | 22 | 1 | 1 | 20 | 2 |
| `ssn:Output` | 20 | 1 | 1 | 18 | 1 |
| `ssn:Platform` | 20 | 2 | 0 | 18 | 4 |
| `sosa:resultTime` | 18 | 13 | 0 | 5 | 5 |
| `sosa:madeBySensor` | 17 | 10 | 1 | 6 | 6 |
| `sosa:hasSimpleResult` | 14 | 11 | 0 | 3 | 3 |
| `ssn:Device` | 14 | 3 | 0 | 11 | 4 |
| `sosa:hasResult` | 13 | 8 | 1 | 4 | 4 |
| `sosa:observes` | 13 | 5 | 0 | 8 | 2 |
| `ssn:Property` | 12 | 5 | 0 | 7 | 4 |
| `sosa:observedProperty` | 10 | 8 | 0 | 2 | 2 |
| `ssn:FeatureOfInterest` | 10 | 6 | 1 | 3 | 3 |
| `ssn:featureOfInterest` | 10 | 6 | 1 | 3 | 3 |
| `ssn:Process` | 10 | 1 | 0 | 9 | 0 |
| `ssn:Sensing` | 10 | 1 | 0 | 9 | 2 |
| `ssn:Stimulus` | 10 | 3 | 1 | 6 | 1 |
| `sosa:Platform` | 9 | 4 | 0 | 5 | 4 |
| `sosa:Procedure` | 9 | 5 | 0 | 4 | 4 |
| `ssn:Frequency` | 9 | 0 | 0 | 9 | 1 |
| `ssn:hasValue` | 9 | 5 | 0 | 4 | 4 |
| `sosa:Actuator` | 8 | 4 | 0 | 4 | 3 |
| `sosa:FeatureOfInterest` | 8 | 6 | 0 | 2 | 2 |
| `sosa:hosts` | 8 | 3 | 0 | 5 | 1 |
| `sosa:ObservableProperty` | 8 | 5 | 1 | 2 | 2 |
| `ssn:detects` | 8 | 1 | 0 | 7 | 0 |
| `ssn:observedBy` | 8 | 5 | 0 | 3 | 3 |
| `ssn:observes` | 8 | 6 | 0 | 2 | 0 |
| `ssn:SensorOutput` | 8 | 6 | 0 | 2 | 2 |
| `w3.org/ns/ssn/systems` | 7 | 5 | 0 | 2 | 2 |

## Prefixed names that only the 2023 Edition declares, found by the search

Leads for the usage report (pilotage usage/301), not evidence: a `sosa:` name found in a work published before 2023 is more likely a term of `ssn:` written with the wrong prefix (error S1 of the codebook).

| string | works | years |
|---|---|---|
| `sosa:classification` | 2 | 2023, 2024 |
| `sosa:Deployment` | 3 | 2020, 2021, 2025 |
| `sosa:hasMember` | 1 | 2021 |
| `sosa:originated` | 1 | 2011 |
| `sosa:parameter` | 4 | 2001, 2001, 2001, 2001 |
| `sosa:Property` | 3 | 2020, 2021, 2023 |
| `sosa:size` | 2 | 2015, 2021 |
| `sosa:System` | 25 | 1940, 1996, 2007, 2009, 2010, 2011, 2011, 2011, 2012, 2016, 2016, 2019, 2020, 2020, 2020, 2020, 2022, 2023, 2025, 2025, 2026, 2026, 2026, 2026, 2026 |

Prefixed names searched: 254, of which 158 found nothing.

