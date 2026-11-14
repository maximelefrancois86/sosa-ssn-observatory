// Example SPARQL queries of the observatory, on data/kg.ttl.gz (shape: slr/scripts/build_kg.py).
// The prefixes come from data/meta.json ("prefixes", written by build_kg.py), so that the IRIs
// of the queries are always those of the graph.
const ORDER = ["slr", "kg", "fabio", "cito", "mod", "dcterms", "dcat", "prov", "oa", "rdfs", "xsd", "sosa", "ssn"];
export function prefixBlock(prefixes) {
  return ORDER.filter((p) => prefixes && prefixes[p]).map((p) => `PREFIX ${p}: <${prefixes[p]}>`).join("\n");
}

export const EXAMPLES = [
  {
    title: "Works that cite the Extensions to SSN",
    query: `# Works that cite the W3C draft "Extensions to the Semantic Sensor Network Ontology"
# (a text seed, found by its URL in the full texts), with the engagement the model coded
SELECT ?work ?year ?engagement WHERE {
  ?seed slr:seedKey "cox-2020-ssn-ext" .
  ?work cito:cites ?seed .
  OPTIONAL { ?work fabio:hasPublicationYear ?year }
  OPTIONAL { ?c slr:about ?work ; slr:question slr:q-engagement ; slr:value ?engagement }
}
ORDER BY DESC(?year)`,
  },
  {
    title: "Works whose properties are feature-specific individuals",
    query: `# Modelling pattern "property individuals" (coded by an agent from excerpts):
# 'specific' = one property individual per feature (the temperature of room 1),
# 'both' = generic and feature-specific individuals; with one quotation each
SELECT ?work ?value (SAMPLE(?q) AS ?quotation) WHERE {
  ?c a slr:PatternCoding ; slr:about ?work ;
     slr:question slr:p-property_individuals ; slr:value ?value .
  FILTER (?value IN ("specific", "both"))
  OPTIONAL { ?c slr:evidence/oa:exact ?q }
}
GROUP BY ?work ?value
ORDER BY ?value`,
  },
  {
    title: "The quotations that support a code (engagement E5)",
    query: `# Each quotation the model gave for one answer: here, the works coded E5
# (a contribution to SOSA/SSN itself). Change the question and the value at will.
SELECT ?work ?agent ?quotation WHERE {
  ?c a slr:Coding ; slr:about ?work ;
     slr:question slr:q-engagement ; slr:value "E5" ;
     prov:wasAttributedTo ?agent .
  OPTIONAL { ?c slr:evidence/oa:exact ?quotation }
}
ORDER BY ?work`,
  },
  {
    title: "Terms used, by version used",
    query: `# Number of works using each term, by the version the work uses (model codes),
# with the versions that declare the term
SELECT ?version ?term (COUNT(DISTINCT ?work) AS ?works)
       (GROUP_CONCAT(DISTINCT STRAFTER(STR(?declaredBy), "artefact/"); separator=", ") AS ?declaredBy)
WHERE {
  ?v slr:about ?work ; slr:question slr:q-version_used ; slr:value ?version .
  ?work slr:usesTerm ?term .
  OPTIONAL { ?term rdfs:isDefinedBy ?declaredBy }
}
GROUP BY ?version ?term
ORDER BY ?version DESC(?works)`,
  },
  {
    title: "Namespace errors before 2023-09-21",
    query: `# Works whose SOSA/SSN names (found by script in the text) put a term in the wrong
# namespace, published before the decision of 2023-09-21 that put every SSN term
# into sosa: too (or classed "before the decision" by publication date)
SELECT ?work ?year (GROUP_CONCAT(DISTINCT ?class; separator=" · ") AS ?classes) WHERE {
  ?work slr:nameClass ?class .
  FILTER (STRSTARTS(?class, "ns-") && !CONTAINS(?class, "after the decision"))
  OPTIONAL { ?work fabio:hasPublicationYear ?y }
  BIND (xsd:integer(STR(?y)) AS ?year)
  FILTER (CONTAINS(?class, "before the decision") || ?year < 2023)
}
GROUP BY ?work ?year
ORDER BY ?year`,
  },
  {
    title: "Citation characterisation by stratum (CiTO)",
    query: `# The relation of each coded work to SOSA/SSN as a CiTO citation act,
# characterised from the engagement code, counted by stratum
SELECT ?stratum ?characterisation (COUNT(?cit) AS ?works) WHERE {
  ?cit a cito:Citation ; cito:hasCitingEntity ?work ;
       cito:hasCitationCharacterization ?characterisation .
  ?work slr:stratum ?stratum .
}
GROUP BY ?stratum ?characterisation
ORDER BY ?stratum DESC(?works)`,
  },
  {
    title: "Ontologies published that rely on SOSA/SSN",
    query: `# Artefacts (ontologies, alignments, shapes, patterns) that works publish and that
# reuse SOSA/SSN (MOD: mod:reliesOn), with the version they rely on
SELECT ?work ?artefact ?kind ?reliesOn WHERE {
  ?work slr:publishes ?artefact .
  ?artefact slr:artefactKind ?kind ; mod:reliesOn ?reliesOn .
  FILTER (?kind IN ("ontology", "alignment", "shacl-shapes", "design-pattern"))
}
ORDER BY ?kind ?work`,
  },
  {
    title: "Who coded what",
    query: `# The agents the codes are attributed to (prov:wasAttributedTo): the language model
# for the codebook, Claude Opus 5.5 agents for the modelling patterns
SELECT ?agent ?name ?kind (COUNT(DISTINCT ?work) AS ?works) (COUNT(?c) AS ?answers) WHERE {
  ?c slr:about ?work ; a ?kind ; prov:wasAttributedTo ?agent .
  OPTIONAL { ?agent rdfs:label ?name }
}
GROUP BY ?agent ?name ?kind
ORDER BY DESC(?answers)`,
  },
];

// the licence of the graph, on its dataset node
EXAMPLES.push({
  title: "The dataset and its licence",
  query: `# The knowledge graph describes itself: title, licence, date of the data
SELECT ?dataset ?title ?license ?modified WHERE {
  ?dataset a dcat:Dataset ; dcterms:title ?title ;
           dcterms:license ?license ; dcterms:modified ?modified .
}`,
});
