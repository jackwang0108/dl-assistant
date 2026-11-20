"""Explicit REST adapters. Each call returns one upstream page plus its real progress."""

import re
from datetime import datetime, timezone
from urllib.parse import quote
from xml.etree import ElementTree as ET

from .identity import normalize_ref, version_from_ref
from .store import now
from .transport import SourceError

SS = "https://api.semanticscholar.org/graph/v1"
OA = "https://api.openalex.org"
SS_FIELDS = (
    "paperId,externalIds,title,authors,year,publicationDate,abstract,venue,"
    "citationCount,referenceCount,openAccessPdf,publicationTypes,url"
)
N = {
    "a": "http://www.w3.org/2005/Atom",
    "o": "http://a9.com/-/spec/opensearch/1.1/",
    "x": "http://arxiv.org/schemas/atom",
}


def base(source, raw, refs, **fields):
    refs = [normalize_ref(r) for r in refs if r]
    if not refs:
        raise SourceError("parse", "Upstream paper omitted all stable identifiers")
    return {"source": source, "identifiers": refs, "raw": raw, "fetched_at": now(), **fields}


def asset(url, kind, source, version=None):
    return {"url": url, "type": kind, "source": source, "version": version, "access": "not_checked"}


def ss_record(p):
    ext = p.get("externalIds") or {}
    refs = [f"s2:{p['paperId']}"] if p.get("paperId") else []
    refs += [
        f"{scheme}:{ext[k]}" for k, scheme in [("DOI", "doi"), ("ArXiv", "arxiv")] if ext.get(k)
    ]
    pdf = (p.get("openAccessPdf") or {}).get("url")
    assets = [asset(pdf, "pdf", "semantic_scholar")] if pdf else []
    if p.get("url"):
        assets.append(asset(p["url"], "landing", "semantic_scholar"))
    return base(
        "semantic_scholar",
        p,
        refs,
        title=p.get("title"),
        authors=[
            {
                "name": a.get("name"),
                "author_ref": f"s2:author:{a['authorId']}" if a.get("authorId") else None,
            }
            for a in (p.get("authors") or [])
        ],
        year=p.get("year"),
        abstract=p.get("abstract"),
        venues=[p["venue"]] if p.get("venue") else [],
        dates={
            "published": p.get("publicationDate"),
            "precision": "day" if p.get("publicationDate") else "year",
        },
        citation_count=p.get("citationCount"),
        reference_count=p.get("referenceCount"),
        publication_types=p.get("publicationTypes"),
        assets=assets,
    )


def oa_record(p):
    ids = p.get("ids") or {}
    refs = ["openalex:" + p["id"].rsplit("/", 1)[-1]] if p.get("id") else []
    doi = p.get("doi") or ids.get("doi")
    if doi:
        refs.append(normalize_ref(doi))
    words = p.get("abstract_inverted_index") or {}
    abstract = (
        " ".join(w for _, w in sorted((i, w) for w, indexes in words.items() for i in indexes))
        or None
    )
    assets = []
    for loc in p.get("locations") or [p.get("best_oa_location"), p.get("primary_location")]:
        if not loc:
            continue
        for field, kind in [("pdf_url", "pdf"), ("landing_page_url", "landing")]:
            if loc.get(field):
                assets.append(asset(loc[field], kind, "openalex"))
    return base(
        "openalex",
        p,
        refs,
        title=p.get("display_name"),
        authors=[
            {
                "name": a.get("author", {}).get("display_name"),
                "author_ref": "openalex:author:" + a["author"]["id"].rsplit("/", 1)[-1]
                if a.get("author", {}).get("id")
                else None,
            }
            for a in p.get("authorships") or []
        ],
        year=p.get("publication_year"),
        abstract=abstract,
        venues=[((p.get("primary_location") or {}).get("source") or {}).get("display_name")],
        dates={
            "published": p.get("publication_date"),
            "precision": "day" if p.get("publication_date") else "year",
        },
        language=p.get("language"),
        publication_types=[p["type"]] if p.get("type") else [],
        open_access=(p.get("open_access") or {}).get("is_oa"),
        citation_count=p.get("cited_by_count"),
        assets=assets,
    )


def scholar_record(p):
    links = p.get("inline_links") or {}
    citing = links.get("cited_by") or {}
    refs = [f"scholar:{p['result_id']}"] if p.get("result_id") else []
    if citing.get("cites_id"):
        refs.append(f"scholar_cites:{citing['cites_id']}")
    cluster = (links.get("versions") or {}).get("cluster_id")
    if cluster:
        refs.append(f"scholar_cites:{cluster}")
    assets = [
        asset(r["link"], "pdf", "scholar")
        for r in p.get("resources", [])
        if r.get("file_format", "").upper() == "PDF" and r.get("link")
    ]
    if p.get("link"):
        assets.append(asset(p["link"], "landing", "scholar"))
    info = p.get("publication_info") or {}
    years = re.findall(r"\b(?:18|19|20)\d{2}\b", info.get("summary", ""))
    return base(
        "scholar",
        p,
        refs,
        title=p.get("title"),
        authors=[{"name": a.get("name"), "author_ref": None} for a in info.get("authors", [])],
        year=int(years[-1]) if years else None,
        snippet=p.get("snippet"),
        publication_summary=info.get("summary"),
        citation_count=citing.get("total"),
        assets=assets,
    )


def arxiv_records(text):
    try:
        tree = ET.fromstring(text)
    except ET.ParseError:
        raise SourceError("parse", "arXiv returned invalid Atom XML") from None
    if tree.tag != "{http://www.w3.org/2005/Atom}feed":
        raise SourceError("parse", "arXiv did not return an Atom feed")
    records = []
    for entry in tree.findall("a:entry", N):
        value = entry.findtext("a:id", "", N)
        if "/errors" in value:
            raise SourceError("invalid_request", "arXiv rejected the query")
        if "/abs/" not in value:
            raise SourceError("parse", "arXiv entry omitted its identifier")
        ident = value.split("/abs/")[-1]
        refs = ["arxiv:" + ident]
        doi = entry.findtext("x:doi", "", N)
        if doi:
            refs.append("doi:" + doi)
        published = entry.findtext("a:published", None, N)
        version = version_from_ref(ident)
        assets = [
            asset(f"https://arxiv.org/abs/{ident}", "landing", "arxiv", version),
            asset(f"https://arxiv.org/pdf/{ident}", "pdf", "arxiv", version),
            asset(f"https://arxiv.org/src/{ident}", "source", "arxiv", version),
        ]
        records.append(
            base(
                "arxiv",
                {"atom_entry": ET.tostring(entry, encoding="unicode")},
                refs,
                title=" ".join(entry.findtext("a:title", "", N).split()),
                authors=[
                    {"name": a.findtext("a:name", "", N), "author_ref": None}
                    for a in entry.findall("a:author", N)
                ],
                year=int(published[:4]) if published else None,
                abstract=entry.findtext("a:summary", None, N),
                dates={
                    "first_submitted": published,
                    "updated": entry.findtext("a:updated", None, N),
                    "precision": "timestamp",
                },
                version=version,
                categories=[c.get("term") for c in entry.findall("a:category", N)],
                venues=[entry.findtext("x:journal_ref", "", N)] or [],
                open_access=True,
                assets=assets,
            )
        )
    total = tree.findtext("o:totalResults", None, N)
    return records, int(total) if total is not None else None


class Providers:
    def __init__(self, transport, keys):
        self.http, self.keys = transport, keys

    def enabled(self, source):
        return source != "scholar" or bool(self.keys.get("scholar"))

    def capabilities(self):
        return {
            "arxiv": {
                "enabled": True,
                "operations": ["search", "resolve"],
                "dates": ["first_submitted", "updated"],
                "filters": ["categories"],
                "sorts": ["relevance", "date_desc", "date_asc"],
                "native_query": True,
            },
            "semantic_scholar": {
                "enabled": True,
                "authenticated": bool(self.keys.get("semantic_scholar")),
                "operations": [
                    "search",
                    "resolve",
                    "citations",
                    "references",
                    "authors",
                    "entity_papers",
                    "recommendations",
                ],
                "dates": ["published"],
                "filters": ["venues", "publication_types", "open_access"],
                "sorts": ["relevance"],
                "native_query": False,
            },
            "scholar": {
                "enabled": self.enabled("scholar"),
                "missing_config": [] if self.enabled("scholar") else ["SERPAPI_KEY"],
                "operations": ["search", "citations"],
                "dates": ["published_year"],
                "filters": [],
                "sorts": ["relevance"],
                "native_query": True,
            },
            "openalex": {
                "enabled": True,
                "authenticated": bool(self.keys.get("openalex")),
                "operations": [
                    "search",
                    "resolve",
                    "citations",
                    "references",
                    "authors",
                    "institutions",
                    "entity_papers",
                ],
                "dates": ["published"],
                "filters": ["publication_types", "languages", "open_access"],
                "sorts": ["relevance", "date_desc", "date_asc", "citations_desc"],
                "native_query": False,
            },
        }

    def _ss(self, path, params, op):
        headers = (
            {"x-api-key": self.keys["semantic_scholar"]}
            if self.keys.get("semantic_scholar")
            else {}
        )
        return self.http.json("semantic_scholar", SS + path, op, params=params, headers=headers)

    def _oa(self, path, params, op):
        params = dict(params)
        if self.keys.get("openalex"):
            params["api_key"] = self.keys["openalex"]
        return self.http.json("openalex", OA + path, op, params=params)

    def _gs(self, params, op):
        if not self.enabled("scholar"):
            raise SourceError("configuration", "SERPAPI_KEY is not configured")
        return self.http.json(
            "scholar",
            "https://serpapi.com/search",
            op,
            params={"engine": "google_scholar", "api_key": self.keys["scholar"], **params},
        )

    def filter_params(self, source, filters, sort, syntax):
        cap = self.capabilities()[source]
        unsupported, limits = [], []
        params = {}
        f = filters or {}
        if syntax == "source_native" and not cap["native_query"]:
            unsupported.append("source_native")
        if sort not in cap["sorts"]:
            unsupported.append("sort:" + sort)
        for name in ("venues", "publication_types", "categories", "languages", "open_access"):
            if f.get(name) is not None and name not in cap["filters"]:
                unsupported.append(name)
        d = f.get("date_range")
        if d:
            dtype = d["date_type"]
            if dtype not in cap["dates"]:
                unsupported.append("date_type:" + dtype)
            if source == "scholar" and dtype == "published":
                # Scholar can only filter years: never advertise exact date enforcement.
                unsupported = [x for x in unsupported if x != "date_type:published"]
                for bound, full in [("start", "-01-01"), ("end", "-12-31")]:
                    if d.get(bound) and not d[bound].endswith(full):
                        unsupported.append("day_precision")
        if unsupported and f.get("unsupported", "error") == "error":
            raise SourceError("unsupported", "Unsupported conditions: " + ", ".join(unsupported))
        if unsupported:
            limits += ["Not enforced: " + v for v in unsupported]
        if source == "semantic_scholar":
            if d and d["date_type"] == "published":
                params["publicationDateOrYear"] = f"{d.get('start') or ''}:{d.get('end') or ''}"
                limits.append(
                    "Upstream may include year-only records; precise publication dates can be unknown."
                )
            if f.get("venues"):
                params["venue"] = ",".join(f["venues"])
            if f.get("publication_types"):
                params["publicationTypes"] = ",".join(f["publication_types"])
            if f.get("open_access") is True:
                params["openAccessPdf"] = ""
            elif f.get("open_access") is False:
                if f.get("unsupported", "error") == "error":
                    raise SourceError("unsupported", "SS cannot enforce closed-access-only")
                limits.append("Not enforced: closed-access-only")
        if source == "scholar" and d and d["date_type"] == "published":
            if d.get("start"):
                params["as_ylo"] = d["start"][:4]
            if d.get("end"):
                params["as_yhi"] = d["end"][:4]
        if source == "openalex":
            parts = []
            if d and d["date_type"] == "published":
                for bound, key in [
                    ("start", "from_publication_date"),
                    ("end", "to_publication_date"),
                ]:
                    if d.get(bound):
                        parts.append(key + ":" + d[bound])
            for name, key in [("publication_types", "type"), ("languages", "language")]:
                if f.get(name):
                    parts.append(key + ":" + "|".join(f[name]))
            if f.get("open_access") is not None:
                parts.append("open_access.is_oa:" + str(f["open_access"]).lower())
            if parts:
                params["filter"] = ",".join(parts)
            if sort != "relevance" and sort in cap["sorts"]:
                params["sort"] = {
                    "date_desc": "publication_date:desc",
                    "date_asc": "publication_date:asc",
                    "citations_desc": "cited_by_count:desc",
                }[sort]
        return params, limits

    def search(self, task, size, op):
        s, text = task["source"], task["text"]
        params, limits = self.filter_params(
            s, task.get("filters"), task.get("sort", "relevance"), task.get("syntax", "text")
        )
        offset = task.get("offset", 0)
        if s == "arxiv":
            if task.get("syntax") != "source_native":
                terms = re.findall(r'"([^"]+)"|(\S+)', text)
                text = " AND ".join('all:"' + (a or b).replace('"', "") + '"' for a, b in terms)
            f = task.get("filters") or {}
            if f.get("categories"):
                text = f"({text}) AND (" + " OR ".join("cat:" + c for c in f["categories"]) + ")"
            d = f.get("date_range")
            if d and d["date_type"] in ("first_submitted", "updated"):
                start = (d.get("start") or "1991-01-01").replace("-", "") + "0000"
                end = (d.get("end") or datetime.now(timezone.utc).date().isoformat()).replace(
                    "-", ""
                ) + "2359"
                key = "submittedDate" if d["date_type"] == "first_submitted" else "lastUpdatedDate"
                text = f"({text}) AND {key}:[{start} TO {end}]"
            sort = task.get("sort", "relevance")
            params = {
                "search_query": text,
                "start": offset,
                "max_results": size,
                "sortBy": "relevance"
                if sort == "relevance"
                else ("lastUpdatedDate" if d and d["date_type"] == "updated" else "submittedDate"),
                "sortOrder": "ascending" if sort == "date_asc" else "descending",
            }
            response = self.http.request(s, "https://export.arxiv.org/api/query", op, params=params)
            records, total = arxiv_records(response.text)
            more = (
                offset + len(records) < total
                if total is not None
                else (None if len(records) == size else False)
            )
            return records, offset + len(records), more, limits, params
        if s == "semantic_scholar":
            params.update(query=text, limit=min(size, 100), offset=offset, fields=SS_FIELDS)
            data = self._ss("/paper/search", params, op)
            return self.ss_page(data, params, limits)
        if s == "scholar":
            params.update(q=text, start=offset, num=min(size, 20))
            data = self._gs(params, op)
            raw = data.get("organic_results", [])
            records = [scholar_record(p) for p in raw]
            more = bool((data.get("serpapi_pagination") or {}).get("next"))
            return records, offset + len(raw), more, limits, params
        params.update(search=text, per_page=min(size, 200), cursor=task.get("offset") or "*")
        data = self._oa("/works", params, op)
        return self.oa_page(data, params, limits)

    @staticmethod
    def ss_page(data, params, limits=None):
        records = [ss_record(p) for p in data.get("data", [])]
        return records, data.get("next"), data.get("next") is not None, limits or [], params

    @staticmethod
    def oa_page(data, params, limits=None, entity=None):
        records = [
            oa_record(p) if entity is None else oa_entity(p, entity)
            for p in data.get("results", [])
        ]
        cursor = (data.get("meta") or {}).get("next_cursor")
        return records, cursor, bool(cursor) and bool(records), limits or [], params

    def resolve(self, source, ref, op, version=None):
        scheme, ident = ref.split(":", 1)
        if source == "arxiv" and scheme == "arxiv":
            response = self.http.request(
                source,
                "https://export.arxiv.org/api/query",
                op,
                params={"id_list": ident + (version or ""), "max_results": 1},
            )
            records, _ = arxiv_records(response.text)
            return records
        if source == "semantic_scholar" and scheme in ("s2", "arxiv", "doi", "url"):
            key = {"s2": "", "arxiv": "ARXIV:", "doi": "DOI:", "url": "URL:"}[scheme] + ident
            record = ss_record(self._ss("/paper/" + quote(key, safe=""), {"fields": SS_FIELDS}, op))
            if scheme == "url":
                record["identifiers"].append(ref)
                record["resolution_evidence"] = "Exact provider URL lookup"
            return [record]
        if source == "openalex" and scheme in ("doi", "openalex"):
            key = "https://doi.org/" + ident if scheme == "doi" else ident
            return [oa_record(self._oa("/works/" + quote(key, safe=""), {}, op))]
        raise SourceError("unsupported", f"{source} cannot directly resolve {scheme}")

    def relation(self, task, size, op):
        source, relation = task["source"], task["kind"]
        ref = task["resolved_ref"]
        scheme, ident = ref.split(":", 1)
        if source == "semantic_scholar":
            key = {"s2": "", "arxiv": "ARXIV:", "doi": "DOI:"}.get(scheme)
            if key is None:
                raise SourceError("unsupported", "SS needs s2, arxiv or DOI identifier")
            params = {
                "fields": SS_FIELDS,
                "offset": task.get("offset", 0),
                "limit": min(size, 1000),
            }
            data = self._ss("/paper/" + quote(key + ident, safe="") + "/" + relation, params, op)
            field = "citingPaper" if relation == "citations" else "citedPaper"
            normalized = {**data, "data": [r[field] for r in data.get("data", []) if r.get(field)]}
            omitted = len(data.get("data", [])) - len(normalized["data"])
            limitations = [f"{omitted} citation endpoints were unavailable"] if omitted else []
            return self.ss_page(normalized, params, limitations)
        if source == "scholar" and relation == "citations" and scheme == "scholar_cites":
            params = {"cites": ident, "start": task.get("offset", 0), "num": min(size, 20)}
            data = self._gs(params, op)
            raw = data.get("organic_results", [])
            return (
                [scholar_record(p) for p in raw],
                params["start"] + len(raw),
                bool((data.get("serpapi_pagination") or {}).get("next")),
                [],
                params,
            )
        if source == "openalex" and scheme == "openalex":
            params = {
                "filter": ("cites:" if relation == "citations" else "cited_by:") + ident,
                "cursor": task.get("offset") or "*",
                "per_page": min(size, 200),
            }
            data = self._oa("/works", params, op)
            return self.oa_page(data, params)
        raise SourceError("unsupported", "No confirmed identifier for this citation source")

    def entity_search(self, task, size, op):
        source, entity = task["source"], task["entity"]
        if source == "semantic_scholar" and entity == "author":
            params = {
                "query": task["text"],
                "limit": min(size, 100),
                "offset": task.get("offset", 0),
                "fields": "name,affiliations,homepage,paperCount,citationCount",
            }
            data = self._ss("/author/search", params, op)
            items = [
                {
                    "entity_ref": "s2:author:" + r["authorId"],
                    "entity_type": "author",
                    "name": r.get("name"),
                    "affiliations": r.get("affiliations"),
                    "source": source,
                    "raw": r,
                }
                for r in data.get("data", [])
            ]
            return items, data.get("next"), data.get("next") is not None, [], params
        if source == "openalex":
            params = {
                "search": task["text"],
                "per_page": min(size, 200),
                "cursor": task.get("offset") or "*",
            }
            if entity == "institution" and task.get("country"):
                params["filter"] = "country_code:" + task["country"].upper()
            data = self._oa("/" + ("authors" if entity == "author" else "institutions"), params, op)
            return self.oa_page(data, params, entity=entity)
        raise SourceError("unsupported", "Entity search not supported by this source")

    def entity_papers(self, task, size, op):
        source, entity, ident = task["entity_ref"].split(":", 2)
        params, limits = self.filter_params(
            task["source"], task.get("filters"), task.get("sort", "relevance"), "text"
        )
        if source == "s2" and entity == "author":
            params.update(fields=SS_FIELDS, offset=task.get("offset", 0), limit=min(size, 1000))
            data = self._ss("/author/" + quote(ident, safe="") + "/papers", params, op)
            # Author-paper endpoint does not enforce relevance-search filters.
            return self.ss_page(data, params, limits)
        if source == "openalex" and entity in ("author", "institution"):
            extra = ("author.id:" if entity == "author" else "institutions.id:") + ident
            params["filter"] = ",".join(x for x in [params.get("filter"), extra] if x)
            params.update(per_page=min(size, 200), cursor=task.get("offset") or "*")
            data = self._oa("/works", params, op)
            return self.oa_page(data, params, limits)
        raise SourceError("unsupported", "Unsupported entity identifier")

    def recommendations(self, ref, size, op):
        scheme, ident = ref.split(":", 1)
        prefix = {"s2": "", "arxiv": "ARXIV:", "doi": "DOI:"}.get(scheme)
        if prefix is None:
            raise SourceError("unsupported", "Recommendations require s2, arxiv or DOI")
        headers = (
            {"x-api-key": self.keys["semantic_scholar"]}
            if self.keys.get("semantic_scholar")
            else {}
        )
        data = self.http.json(
            "semantic_scholar",
            "https://api.semanticscholar.org/recommendations/v1/papers/forpaper/"
            + quote(prefix + ident, safe=""),
            op,
            params={"fields": SS_FIELDS, "limit": min(size, 100), "from": "all-cs"},
            headers=headers,
        )
        return [ss_record(p) for p in data.get("recommendedPapers", [])]


def oa_entity(p, entity):
    return {
        "entity_ref": f"openalex:{entity}:" + p["id"].rsplit("/", 1)[-1],
        "entity_type": entity,
        "name": p.get("display_name"),
        "source": "openalex",
        "country": p.get("country_code"),
        "ror": p.get("ror"),
        "orcid": p.get("orcid"),
        "affiliations": p.get("last_known_institutions"),
        "works_count": p.get("works_count"),
        "raw": p,
    }
