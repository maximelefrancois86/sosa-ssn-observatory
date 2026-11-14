// The in-browser SPARQL endpoint, seen from the Sparklis page (loaded before osparklis.js).
//
// Sparklis sends its queries with XMLHttpRequest to the `endpoint` of its address, here the
// site's ./sparql. Normally the service worker ../sw.js answers them (Oxigraph on
// data/kg.ttl.gz): this script then only asks it to load the graph early and keeps it alive
// while the page is open. When no service worker controls the page (a browser without module
// service workers, a private window, a forced reload), this script answers the same requests
// itself: it replaces XMLHttpRequest for that one URL and runs the queries in ../kg-worker.js.
(function () {
  "use strict";
  var endpoint;
  try {
    var arg = new URLSearchParams(location.search).get("endpoint");
    if (!arg) return;
    endpoint = new URL(arg, location.href);
  } catch (e) { return; }
  if (endpoint.origin !== location.origin || !/\/sparql$/.test(endpoint.pathname)) return;
  var root = new URL(".", endpoint);   // the site: sw.js, kg-worker.js, data/
  var sw = navigator.serviceWorker;

  if (sw && sw.controller) {
    var ping = function (type) { if (sw.controller) sw.controller.postMessage({ type: type }); };
    ping("warm");
    setInterval(function () { ping("keepalive"); }, 20000);
    return;
  }
  // for the next visit
  if (sw) sw.register(new URL("sw.js", root).href, { type: "module", scope: root.pathname }).catch(function () {});

  var worker = null, ready = null, seq = 0, pending = {};
  function start() {
    if (ready) return ready;
    worker = new Worker(new URL("kg-worker.js", root).href, { type: "module" });
    worker.onmessage = function (e) {
      var m = e.data, p = pending[m.id];
      if (!p) return;
      delete pending[m.id];
      if (m.type === "error") p.reject(new Error(m.message)); else p.resolve(m);
    };
    worker.onerror = function (e) {
      var err = new Error("The SPARQL engine could not start (" + (e.message || "network or CDN error") + ").");
      Object.keys(pending).forEach(function (k) { pending[k].reject(err); delete pending[k]; });
      ready = null;
    };
    ready = call({ type: "load", url: new URL("data/kg.ttl.gz", root).href }).catch(function (e) { ready = null; throw e; });
    return ready;
  }
  function call(msg) {
    var id = ++seq;
    return new Promise(function (resolve, reject) {
      pending[id] = { resolve: resolve, reject: reject };
      msg.id = id;
      worker.postMessage(msg);
    });
  }
  function run(query, accept) {
    var format = /sparql-results\+xml|application\/xml|text\/xml/.test(accept || "") ? "xml" : "json";
    if (/text\/turtle/.test(accept || "")) format = "turtle";
    return start().then(function () { return call({ type: "query", query: query, format: format }); });
  }

  function isEndpoint(u) {
    try { var x = new URL(u, location.href); return x.origin === endpoint.origin && x.pathname === endpoint.pathname; }
    catch (e) { return false; }
  }
  var Real = window.XMLHttpRequest;
  function set(xhr, k, v) { Object.defineProperty(xhr, k, { value: v, configurable: true, writable: true }); }
  function fire(xhr, type) { xhr.dispatchEvent(new Event(type)); }
  class EndpointXHR extends Real {
    open(method, url) {
      if (!isEndpoint(url)) { this._local = null; return super.open.apply(this, arguments); }
      this._local = { method: String(method).toUpperCase(), url: new URL(url, location.href), headers: {}, out: {} };
      set(this, "readyState", 1);
      fire(this, "readystatechange");
    }
    setRequestHeader(k, v) {
      if (!this._local) return super.setRequestHeader(k, v);
      this._local.headers[String(k).toLowerCase()] = v;
    }
    getResponseHeader(k) {
      if (!this._local) return super.getResponseHeader(k);
      return this._local.out[String(k).toLowerCase()] || null;
    }
    getAllResponseHeaders() {
      if (!this._local) return super.getAllResponseHeaders();
      var o = this._local.out;
      return Object.keys(o).map(function (k) { return k + ": " + o[k] + "\r\n"; }).join("");
    }
    abort() {
      if (!this._local) return super.abort();
      this._local.aborted = true;
    }
    send(body) {
      if (!this._local) return super.send(body);
      var L = this._local, xhr = this, query = null;
      if (L.method === "GET") query = L.url.searchParams.get("query");
      else if (typeof body === "string") {
        query = /sparql-query/.test(L.headers["content-type"] || "") ? body : new URLSearchParams(body).get("query");
      } else if (body && typeof body.get === "function") query = body.get("query");
      fire(xhr, "loadstart");
      var done = function (status, text, type) {
        if (L.aborted) return;
        L.out = { "content-type": type + "; charset=utf-8" };
        set(xhr, "status", status);
        set(xhr, "statusText", status === 200 ? "OK" : "Bad Request");
        set(xhr, "responseURL", L.url.href);
        set(xhr, "responseText", text);
        set(xhr, "response", text);
        var xml = null;
        if (/xml/.test(type)) {
          xml = new DOMParser().parseFromString(text, "application/xml");
          if (xml.getElementsByTagName("parsererror").length) xml = null;
        }
        set(xhr, "responseXML", xml);
        set(xhr, "readyState", 2); fire(xhr, "readystatechange");
        set(xhr, "readyState", 3); fire(xhr, "readystatechange");
        set(xhr, "readyState", 4); fire(xhr, "readystatechange");
        fire(xhr, "load"); fire(xhr, "loadend");
      };
      if (!query) { setTimeout(function () { done(400, "No query.\n", "text/plain"); }, 0); return; }
      run(query, L.headers.accept).then(function (r) { done(200, r.text, r.type); },
        function (err) { done(400, String(err && err.message ? err.message : err) + "\n", "text/plain"); });
    }
  }
  window.XMLHttpRequest = EndpointXHR;
  start().catch(function () {});   // load the graph while Sparklis starts
})();
