# Codebook (version 1)

One row per included work. Every coded value comes with its evidence: a page or section
of the work, an IRI, or a repository URL. `unknown` is a value; a blank is an error. A
value marked *(script)* is filled by a script of this repository, from the full text or
from an artefact, and checked by a person on a sample.

## Provenance of every value

The review application (protocol § 5) records, for each value coded by a reader:
`recommended` (the value proposed), `recommended_by` (`script` or `model`, with the
script or model version, the prompt and the date), `decision` (the value kept),
`reader` (an identifier; editors of SOSA/SSN are marked as such), `decided_at`, and
`seconds` (the time spent on the passage). A value without a reader's decision is a
recommendation, never a result.

## Bibliographic (filled from the harvest)

`openalex`, `doi`, `title`, `year`, `type`, `venue`, `publisher`, `authors`, `countries`,
`seeds` (the seeds the work cites), `stratum` (A to D), `venue_flag` (*(script)*,
`results/venue-risk.md`).

## Study type

`study_type`: `primary` (the work proposes or applies something) or `secondary` (survey,
review, mapping study). Secondary studies are coded for engagement and version only.

## Engagement (RQ2), one value, the deepest that applies

| code | meaning |
|---|---|
| E0 | not about SOSA/SSN: the citation supports another point, or is a list of ontologies |
| E1 | mention: SOSA/SSN is named in the background or related work, without further use |
| E2 | discussion: SOSA/SSN is described, compared, evaluated or criticised |
| E3 | data: the work describes data (dataset, knowledge graph, stream, application) with SOSA/SSN terms |
| E4 | ontology reuse: an ontology imports, specialises or aligns SOSA/SSN terms |
| E5 | contribution: an extension, pattern, alignment or tool proposed for SOSA/SSN itself |

`engagement_also`: the other codes that apply (several values allowed).
`engagement_basis`: `script` (no occurrence outside the reference list: E0 or E1),
`passages`, `full text`, `abstract` (full text not obtained).

## Version (RQ3)

- `version_cited`: from the seeds cited (filled automatically).
- `version_used`: `ssn-xg` (`purl.oclc.org/NET/ssnx/ssn`), `sosa-ssn-2017`
  (`www.w3.org/ns/sosa/`, `www.w3.org/ns/ssn/`), `ssn-2023` (a term or module of the 2023
  Edition), `mixed`, `unknown`.
- `version_evidence`: namespace IRI, term name, or statement in the text.

## Coverage (RQ4)

- `modules`: SOSA core (observation, actuation, sampling), SSN, SSN System (capabilities,
  deployment), the 2023 extensions (sosa:Execution, observation collections, sample
  relations, OMS, systems), the alignments (DUL, BFO, IDO, OBOE, PROV, SAREF, OGC
  SensorThings…).
- `terms`: the SOSA/SSN terms the work uses, as prefixed names (*(script)* when an artefact
  or the full text gives them).

## Modelling (RQ5)

- `extensions` (RQ5a): one entry per term the work defines on top of SOSA/SSN: the new
  term, the SOSA/SSN term it builds on, and how (`subClassOf`, `subPropertyOf`,
  `instanceOf` for terms whose extension point is an instance, such as properties as
  instances of `sosa:Property`, `equivalentTo`, `alignment`). Counted per SOSA/SSN term:
  how many works extend `sosa:System`, `sosa:Property`, `sosa:Procedure`…
- `result_pattern` (RQ5b), several values allowed: `simple-literal` (`sosa:hasSimpleResult`),
  `quantity-value` (QUDT, OM, schema.org), `custom-result-class`, `structured` (array,
  matrix, table, RDF list, JSON literal, RDF Data Cube), `by-reference` (image, file or
  stream given by its IRI), `time-series`, `coverage`, `nested` (observation or
  collection as result), `none`, `unknown`.
- `value_properties`, several values allowed: `unit` (with the vocabulary: QUDT, OM, UCUM
  literal…), `uncertainty`, `quality` (including `sosa:resultQuality`), `time`
  (phenomenon and result time, with OWL-Time or literals), `none`.

## Correctness (RQ6)

- `errors`: one entry per error found, with its category and code, the term involved and
  the evidence.

| code | category | meaning |
|---|---|---|
| S1 | syntactic | wrong or mixed namespace IRI (a SOSA term in `ssn:`, `https`, missing `/` or `#`) |
| S2 | syntactic | a term that no version declares |
| S3 | syntactic | misspelt name (case, plural, typo) |
| M1 | semantic | domain or range violated |
| M2 | semantic | class used as an individual, or the converse |
| M3 | semantic | a term used against its definition |
| M4 | semantic | a deprecated or superseded term, for the version the work claims |
| G1 | structural | an observation, actuation or sampling without a link that its pattern expects (feature of interest, property, result, procedure) |
| G2 | structural | a link attached to the wrong node (a result on the sensor, a property on the platform…) |
| G3 | structural | another departure from the patterns of the specification, described |

- `correctness_basis`: `artefact` (*(script)*), `text and figures`, `none` (nothing to judge).

## Domain and companions (RQ7)

- `domain`, from a closed list fixed before screening and kept coarse so that it stays
  stable: environment and earth observation, agriculture and food, buildings, cities and
  mobility, energy, manufacturing and industry, health, water and oceans, robotics and
  autonomous systems, generic IoT and Web of Things, science and laboratories, other.
- `subdomain`: free text, grouped into a second-level list after the calibration sample;
  the breadth of the applications is recorded here, not in `domain`.
- `companions`: the other vocabularies used with SOSA/SSN.

## Associated artefacts (RQ8)

- `artefacts`: one entry per artefact the work publishes: its kind (`ontology`,
  `dataset`, `alignment`, `shacl-shapes`, `jsonld-context`, `json-schema`,
  `sparql-queries`, `mapping`, `design-pattern`, `software`), its IRI or URL, and
  `resolves` (`yes`, `no`, with the date of the check, *(script)*).

## Gaps (RQ9)

- `gaps`: free text, then coded thematically (unmet requirement, modelling difficulty,
  extension proposed, criticism of the axiomatisation, tooling).
