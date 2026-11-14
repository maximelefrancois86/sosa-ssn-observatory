// The SOSA/SSN Usage Observatory's settings of Sparklis (see VENDOR.txt), loaded first.
//
// This copy of Sparklis serves one knowledge graph only: the endpoint is always the site's
// in-browser ./sparql, and the settings that the observatory relies on (no third-party proxy,
// no logging, no URL shortener, rdfs:label for entities and concepts) cannot be changed from
// the address. Any other value in the address is replaced, and the page reloaded once; the
// query and focus of a permalink (sparklis-query, sparklis-path) are kept.
(function () {
  "use strict";
  var LABEL = "http://www.w3.org/2000/01/rdf-schema#label";
  var fixed = {
    title: "SOSA/SSN Usage Observatory",
    endpoint: new URL("../sparql", location.href).href,
    proxy_url: "", proxy: "false", logging: "false", "short-permalink": "false", lang: "en",
    entity_lexicon_select: LABEL, concept_lexicons_select: LABEL
  };
  var p = new URLSearchParams(location.search), changed = false;
  Object.keys(fixed).forEach(function (k) {
    if (p.get(k) !== fixed[k]) { p.set(k, fixed[k]); changed = true; }
  });
  if (changed) {
    location.replace(location.pathname + "?" + p.toString() + location.hash);
    throw new Error("Sparklis settings fixed by the observatory: reloading");   // stop this load
  }
})();
