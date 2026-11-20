"""Research retrieval operations. Query snapshots preserve exactly what was observed."""

import base64
import copy
import json
from datetime import datetime, timezone

from .config import Config
from .identity import canonical_ref, normalize_ref, title_key, version_from_ref
from .models import PaperLookup, PaperQuery
from .providers import Providers
from .store import Store, digest
from .transport import Operation, SourceError, Transport

SOURCES = ["arxiv", "semantic_scholar", "scholar", "openalex"]
CORE = {
    "paper_ref",
    "identifiers",
    "field_provenance",
    "conflicts",
    "fetched_at",
    "entity_ref",
    "entity_type",
    "source",
}


def selected_fields(paper, fields):
    if fields is None:
        # Default excludes raw payloads but includes stable identity and useful provenance.
        return paper
    unknown = set(fields) - set(paper)
    if unknown:
        raise ValueError("Unknown/unavailable fields: " + ", ".join(sorted(unknown)))
    return {k: v for k, v in paper.items() if k in CORE or k in fields}


def error_report(source, error):
    return {
        "source": source,
        "status": (
            "unsupported"
            if error.kind == "unsupported"
            else "not_found"
            if error.kind == "not_found"
            else "failed"
        ),
        "error": error.public(),
        "fetched_count": 0,
        "upstream_has_more": None,
        "fetched_at": None,
        "cache_state": "miss",
    }


class Service:
    def __init__(self, config=None, transport=None):
        self.config = config or Config.from_env()
        self.store = Store(self.config.cache_dir)
        self.providers = Providers(transport or Transport(), self.config.keys)

    def get_capabilities(self):
        return {
            "api_version": 2,
            "sources": self.providers.capabilities(),
            "cache_policies": ["prefer", "refresh", "only"],
            "query_ids": "Local cache identifiers; use stable paper refs across machines.",
            "related_methods": [
                "shared_references",
                "shared_citations",
                "provider_recommendations",
            ],
            "entity_hints": "Author affiliation/topic hints are evidence, not guaranteed filters.",
            "ordering": "Provider order within each task; combined order is not a global relevance ranking.",
        }

    def resolve_papers(self, inputs, sources=None, budget=None):
        op = Operation(budget)
        sources = self._sources(sources)
        output = []
        for inp in inputs:
            lookup = inp if isinstance(inp, PaperLookup) else PaperLookup.model_validate(inp)
            reports, candidates = [], []
            if lookup.identifier:
                try:
                    ref = normalize_ref(lookup.identifier)
                except ValueError as exc:
                    output.append(
                        {"input": lookup.model_dump(), "status": "invalid", "error": str(exc)}
                    )
                    continue
                # Local observations are candidates only if a matching alias was observed.
                version = version_from_ref(lookup.identifier)
                cached = self.store.paper(ref, version=version)
                if cached:
                    candidates.append(cached)
                for source in sources:
                    if not self.providers.enabled(source):
                        reports.append({"source": source, "status": "disabled"})
                        continue
                    try:
                        if version and source != "arxiv":
                            raise SourceError(
                                "unsupported",
                                "Exact arXiv revision resolution requires arxiv source",
                            )
                        if op.items >= op.budget.max_items:
                            raise SourceError("budget", "Item budget reached")
                        records = self.providers.resolve(
                            source, ref, op, version_from_ref(lookup.identifier)
                        )
                        op.items += len(records)
                        accepted = [
                            r
                            for r in records
                            if ref in r["identifiers"]
                            and (not version or r.get("version") == version)
                        ]
                        for r in accepted:
                            self.store.save_record(r)
                            candidates.append(self.store.paper(ref))
                        reports.append(
                            {
                                "source": source,
                                "status": "ok",
                                "matched": len(accepted),
                                "fetched_count": len(records),
                            }
                        )
                    except SourceError as exc:
                        reports.append(error_report(source, exc))
                matched = self.store.paper(ref, version=version)
                output.append(
                    {
                        "input": lookup.model_dump(),
                        "status": "confirmed" if matched else self._absence(reports),
                        "paper": matched,
                        "source_reports": reports,
                        "evidence": ["Exact normalized external identifier"] if matched else [],
                    }
                )
            else:
                for source in sources:
                    if not self.providers.enabled(source):
                        reports.append({"source": source, "status": "disabled"})
                        continue
                    try:
                        remaining = op.budget.max_items - op.items
                        if remaining <= 0:
                            raise SourceError("budget", "Item budget reached")
                        records, _, more, limits, actual = self.providers.search(
                            {"source": source, "text": lookup.title, "syntax": "text"},
                            min(5, remaining),
                            op,
                        )
                        op.items += len(records)
                        for r in records:
                            self.store.save_record(r)
                            candidates.append(self.store.paper(canonical_ref(r["identifiers"])))
                        reports.append(
                            {
                                "source": source,
                                "status": "ok",
                                "upstream_has_more": more,
                                "limitations": limits,
                                "actual_query": actual,
                            }
                        )
                    except SourceError as exc:
                        reports.append(error_report(source, exc))
                candidates = self._dedup(candidates)
                for candidate in candidates:
                    candidate["match_evidence"] = {
                        "title_exact_normalized": title_key(candidate.get("title") or "")
                        == title_key(lookup.title),
                        "year_matches": candidate.get("year") == lookup.year
                        if lookup.year
                        else None,
                        "requested_authors": lookup.authors,
                        "authors_observed": candidate.get("authors"),
                    }
                output.append(
                    {
                        "input": lookup.model_dump(),
                        "status": "ambiguous" if candidates else self._absence(reports),
                        "candidates": candidates,
                        "source_reports": reports,
                        "limitations": [
                            "Title search yields candidates; no automatic external-ID binding."
                        ],
                    }
                )
        return {"results": output, "usage": op.usage()}

    @staticmethod
    def _absence(reports):
        return (
            "not_found"
            if any(r["status"] in ("ok", "not_found") for r in reports)
            and not any(r["status"] == "failed" for r in reports)
            else "unavailable"
        )

    @staticmethod
    def _sources(sources):
        if sources is not None and (not sources or set(sources) - set(SOURCES)):
            raise ValueError("sources must be a nonempty list of supported sources")
        return list(dict.fromkeys(sources or SOURCES))

    @staticmethod
    def _dedup(items):
        result = []
        for item in items:
            aliases = set(item.get("identifiers", []))
            matches = [
                i
                for i, old in enumerate(result)
                if aliases.intersection(old.get("identifiers", []))
            ]
            if not matches:
                result.append(copy.deepcopy(item))
            else:
                i = matches[0]
                old = result[i]
                evidence = old.get("relation_evidence", []) + item.get("relation_evidence", [])
                combined = {**old, **item, "identifiers": sorted(set(old["identifiers"]) | aliases)}
                for other in reversed(matches[1:]):
                    popped = result.pop(other)
                    combined["identifiers"] = sorted(
                        set(combined["identifiers"]) | set(popped["identifiers"])
                    )
                    evidence += popped.get("relation_evidence", [])
                combined["paper_ref"] = canonical_ref(combined["identifiers"])
                if evidence:
                    combined["relation_evidence"] = list({digest(e): e for e in evidence}.values())
                result[i] = combined
        return result

    def get_papers(
        self, paper_refs, fields=None, view="normalized", cache="prefer", budget=None, _op=None
    ):
        if not paper_refs:
            raise ValueError("paper_refs cannot be empty")
        op, results = _op or Operation(budget), []
        for value in paper_refs:
            try:
                ref = normalize_ref(value)
            except ValueError as exc:
                results.append(
                    {"requested_ref": value, "status": "invalid", "paper": None, "error": str(exc)}
                )
                continue
            version = version_from_ref(value)
            current = self.store.paper(ref, view, version)
            fresh = (
                current is not None
                and cache == "prefer"
                and (
                    datetime.now(timezone.utc)
                    - datetime.fromisoformat(max(r["fetched_at"] for r in self.store.records(ref)))
                ).total_seconds()
                < 86400
            )
            reports = []
            if cache != "only" and (cache == "refresh" or not fresh):
                for source in (
                    ["arxiv"]
                    if version and ref.startswith("arxiv:")
                    else self._preferred_sources(ref)
                ):
                    try:
                        if op.items >= op.budget.max_items:
                            raise SourceError("budget", "Item budget reached")
                        for record in self.providers.resolve(
                            source, ref, op, version_from_ref(value)
                        ):
                            op.items += 1
                            if ref in record["identifiers"]:
                                self.store.save_record(record)
                        reports.append({"source": source, "status": "ok"})
                    except SourceError as exc:
                        reports.append(error_report(source, exc))
                current = self.store.paper(ref, view, version)
            results.append(
                {
                    "requested_ref": ref,
                    "status": ("partial" if any(r["status"] == "failed" for r in reports) else "ok")
                    if current
                    else ("cache_miss" if cache == "only" else self._absence(reports)),
                    "paper": selected_fields(current, fields) if current else None,
                    "source_reports": reports,
                    "cache_state": ("hit" if current else "miss")
                    if fresh or cache == "only"
                    else "refreshed",
                    "limitations": ["Refresh failure may leave older observations available."]
                    if any(r["status"] == "failed" for r in reports) and current
                    else [],
                }
            )
        return {"results": results, "usage": op.usage()}

    @staticmethod
    def _preferred_sources(ref):
        scheme = ref.split(":", 1)[0]
        return {
            "arxiv": ["arxiv", "semantic_scholar"],
            "doi": ["semantic_scholar", "openalex"],
            "s2": ["semantic_scholar"],
            "openalex": ["openalex"],
            "scholar": [],
            "scholar_cites": [],
            "url": ["semantic_scholar"],
        }[scheme]

    def search_papers(self, queries, filters=None, sort="relevance", budget=None, cache="prefer"):
        if not queries:
            raise ValueError("queries cannot be empty")
        tasks = []
        for query in queries:
            q = query if isinstance(query, PaperQuery) else PaperQuery.model_validate(query)
            for source in self._sources(q.sources):
                tasks.append(
                    {
                        "kind": "search",
                        "source": source,
                        "text": q.text,
                        "syntax": q.syntax,
                        "filters": filters.model_dump(mode="json") if filters else None,
                        "sort": sort,
                    }
                )
        return self._query({"kind": "search", "tasks": tasks}, budget, cache)

    def _relation_tasks(self, paper_ref, kind, sources):
        ref = normalize_ref(paper_ref)
        observed = self.store.paper(ref)
        aliases = observed["identifiers"] if observed else [ref]
        tasks = []
        for source in self._sources(sources or ["semantic_scholar", "openalex", "scholar"]):
            schemes = {
                "semantic_scholar": ["s2", "doi", "arxiv"],
                "openalex": ["openalex"],
                "scholar": ["scholar_cites"],
                "arxiv": [],
            }[source]
            resolved = next(
                (a for scheme in schemes for a in aliases if a.startswith(scheme + ":")), ref
            )
            tasks.append(
                {"kind": kind, "source": source, "paper_ref": ref, "resolved_ref": resolved}
            )
        return tasks

    def relation(self, paper_ref, kind, sources=None, filters=None, budget=None, cache="prefer"):
        tasks = self._relation_tasks(paper_ref, kind, sources)
        # Filtering a citation endpoint is different from filtering a search endpoint.
        # Explicit local filtering is not a promise of exhaustive filtered retrieval.
        if filters and filters.model_dump(exclude_defaults=True):
            raise ValueError(
                "Citation filters are not supported yet; inspect/export candidates instead"
            )
        return self._query({"kind": kind, "tasks": tasks}, budget, cache)

    def search_entities(
        self, name, entity, sources=None, affiliation=None, topic=None, country=None, budget=None
    ):
        tasks = [
            {
                "kind": "entity_search",
                "entity": entity,
                "source": source,
                "text": name,
                "country": country,
            }
            for source in self._sources(
                sources
                or (["semantic_scholar", "openalex"] if entity == "author" else ["openalex"])
            )
        ]
        result = self._query(
            {
                "kind": "entity_search",
                "tasks": tasks,
                "hints": {"affiliation": affiliation, "topic": topic},
            },
            budget,
            "refresh",
        )
        if affiliation or topic:
            result["coverage"]["limitations"].append(
                "Affiliation/topic are disambiguation hints, not enforced filters."
            )
        return result

    def get_entity_papers(
        self, entity_ref, filters=None, sort="relevance", budget=None, cache="prefer"
    ):
        parts = entity_ref.split(":")
        if (
            len(parts) != 3
            or parts[0] not in ("s2", "openalex")
            or parts[1] not in ("author", "institution")
        ):
            raise ValueError("Use an entity_ref returned by search_authors/search_institutions")
        if parts[0] == "s2" and parts[1] != "author":
            raise ValueError("Semantic Scholar has no institution entity endpoint")
        if parts[0] == "s2" and (
            sort != "relevance" or filters and filters.model_dump(exclude_defaults=True)
        ):
            raise ValueError(
                "SS author papers cannot enforce these filters/sort; use an OpenAlex entity"
            )
        task = {
            "kind": "entity_papers",
            "source": "semantic_scholar" if parts[0] == "s2" else "openalex",
            "entity_ref": entity_ref,
            "sort": sort,
            "filters": filters.model_dump(mode="json") if filters else None,
        }
        return self._query({"kind": "entity_papers", "tasks": [task]}, budget, cache)

    def _query(self, spec, budget, cache):
        spec = {**spec, "source_capabilities": self.providers.capabilities()}
        cached = self.store.cached_snapshot(spec)
        if cache != "refresh" and cached:
            result = self._page(cached, 0, 20)
            result["cache_state"] = "hit"
            return result
        if cache == "only":
            return {
                "status": "cache_miss",
                "items": [],
                "query_id": None,
                "snapshot_id": None,
                "coverage": {"limitations": ["No unexpired cached query."]},
                "usage": Operation(budget).usage(),
            }
        snapshot = self._execute(spec, copy.deepcopy(spec["tasks"]), [], Operation(budget))
        return self._page(snapshot, 0, 20)

    def _execute(self, spec, tasks, items, op, query_id=None, selection=None):
        items = copy.deepcopy(items)
        for index, task in enumerate(tasks):
            if selection is not None and index not in selection:
                continue
            source = task["source"]
            if not self.providers.enabled(source):
                task["report"] = {
                    "source": source,
                    "status": "disabled",
                    "fetched_count": 0,
                    "upstream_has_more": None,
                    "missing_config": ["SERPAPI_KEY"],
                }
                continue
            remaining = op.budget.max_items - op.items
            if remaining <= 0:
                task["report"] = error_report(source, SourceError("budget", "Item budget reached"))
                continue
            size = min(20, remaining, max(1, op.budget.max_items // max(1, len(tasks))))
            try:
                kind = task["kind"]
                if kind == "search":
                    records, offset, more, limits, actual = self.providers.search(task, size, op)
                elif kind in ("citations", "references"):
                    records, offset, more, limits, actual = self.providers.relation(task, size, op)
                elif kind == "entity_search":
                    records, offset, more, limits, actual = self.providers.entity_search(
                        task, size, op
                    )
                elif kind == "entity_papers":
                    records, offset, more, limits, actual = self.providers.entity_papers(
                        task, size, op
                    )
                elif kind == "recommendations":
                    records = self.providers.recommendations(task["paper_ref"], size, op)
                    offset, more, limits, actual = (
                        None,
                        None,
                        [],
                        {"paper_ref": task["paper_ref"], "pool": "all-cs"},
                    )
                else:
                    raise ValueError("Unknown task kind")
                if len(records) > size:
                    raise SourceError(
                        "parse", "Upstream exceeded requested page size; progress not advanced"
                    )
                op.items += len(records)
                for record in records:
                    if kind == "entity_search":
                        item = record
                        if not any(old.get("entity_ref") == item["entity_ref"] for old in items):
                            items.append(item)
                    else:
                        self.store.save_record(record)
                        item = self.store.paper(canonical_ref(record["identifiers"]))
                        if kind in ("citations", "references", "recommendations"):
                            item["relation_evidence"] = [
                                {
                                    "source": source,
                                    "relation": kind,
                                    "seed_ref": task["paper_ref"],
                                    "fetched_at": record["fetched_at"],
                                }
                            ]
                        items = self._dedup(items + [item])
                task["offset"] = offset
                task["done"] = more is False or kind == "recommendations"
                task["report"] = {
                    "source": source,
                    "status": "partial" if limits else "ok",
                    "actual_query": actual,
                    "fetched_count": len(records),
                    "upstream_has_more": more,
                    "limitations": limits,
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                    "cache_state": "miss",
                }
            except SourceError as exc:
                task["report"] = error_report(source, exc)
            except (ValueError, KeyError, TypeError):
                task["report"] = error_report(
                    source, SourceError("parse", "Malformed upstream record")
                )
        all_items = items
        if spec["kind"] == "related" and spec["match"] == "all":
            items = [
                item
                for item in items
                if set(spec["paper_refs"])
                <= {e["seed_ref"] for e in item.get("relation_evidence", [])}
            ]
        return self.store.snapshot(
            {
                "spec": spec,
                "tasks": tasks,
                "items": items,
                "all_items": all_items,
                "usage": op.usage(),
            },
            query_id,
        )

    @staticmethod
    def _cursor(snapshot, index):
        return base64.urlsafe_b64encode(
            json.dumps([snapshot["snapshot_id"], index]).encode()
        ).decode()

    def _page(self, snapshot, offset, page_size, fields=None):
        reports = [
            task.get(
                "report", {"source": task["source"], "status": "not_run", "upstream_has_more": None}
            )
            for task in snapshot["tasks"]
        ]
        more = [r.get("upstream_has_more") for r in reports]
        upstream = True if True in more else (None if None in more else False)
        items = snapshot["items"][offset : offset + page_size]
        if fields is not None:
            items = [selected_fields(item, fields) for item in items]
        limitations = list(
            dict.fromkeys(note for r in reports for note in r.get("limitations", []))
        )
        if any(r["status"] not in ("ok",) for r in reports):
            limitations.append(
                "Some sources/conditions were incomplete, unsupported or unavailable; inspect source_reports."
            )
        limitations.append("Local completion does not establish exhaustive literature coverage.")
        next_offset = offset + len(items)
        return {
            "query_id": snapshot["query_id"],
            "snapshot_id": snapshot["snapshot_id"],
            "created_at": snapshot["created_at"],
            "items": items,
            "next_cursor": self._cursor(snapshot, next_offset)
            if next_offset < len(snapshot["items"])
            else None,
            "source_reports": reports,
            "coverage": {
                "local_has_more": next_offset < len(snapshot["items"]),
                "upstream_has_more": upstream,
                "truncated": upstream is not False or bool(limitations[:-1]),
                "limitations": limitations,
            },
            "usage": snapshot["usage"],
            "ordering": "Provider/task order; not a globally comparable relevance score.",
        }

    def get_query_results(self, query_id, cursor=None, page_size=20, fields=None):
        if not 1 <= page_size <= 200:
            raise ValueError("page_size must be between 1 and 200")
        snapshot = self.store.get_snapshot(query_id)
        offset = 0
        if cursor:
            try:
                sid, offset = json.loads(base64.urlsafe_b64decode(cursor).decode())
                if (
                    not isinstance(sid, str)
                    or not isinstance(offset, int)
                    or isinstance(offset, bool)
                    or offset < 0
                ):
                    raise ValueError()
                frozen = self.store.get_snapshot(sid)
                if frozen["query_id"] != snapshot["query_id"]:
                    raise ValueError()
                snapshot = frozen
            except (ValueError, TypeError, UnicodeError, json.JSONDecodeError):
                raise ValueError("Invalid cursor or cursor belongs to another query") from None
        return self._page(snapshot, offset, page_size, fields)

    def extend_query(self, query_id, action, queries=None, sources=None, budget=None):
        old = self.store.get_snapshot(query_id)
        tasks = copy.deepcopy(old["tasks"])
        spec = copy.deepcopy(old["spec"])
        if queries and action != "add_queries":
            raise ValueError("queries is only valid for add_queries")
        if action == "fetch_more":
            selection = [
                i
                for i, t in enumerate(tasks)
                if not t.get("done") and t.get("report", {}).get("status") in ("ok", "partial")
            ]
        elif action == "retry_failed":
            selection = [
                i
                for i, t in enumerate(tasks)
                if t.get("report", {}).get("status") == "failed"
                and (not sources or t["source"] in sources)
            ]
        elif action == "add_queries":
            if spec["kind"] != "search" or not queries:
                raise ValueError("add_queries requires a paper search and nonempty queries")
            additions = []
            for q in queries:
                q = q if isinstance(q, PaperQuery) else PaperQuery.model_validate(q)
                for source in self._sources(q.sources):
                    additions.append(
                        {**spec["tasks"][0], "source": source, "text": q.text, "syntax": q.syntax}
                    )
            selection = list(range(len(tasks), len(tasks) + len(additions)))
            tasks += copy.deepcopy(additions)
            spec["tasks"] += additions
        elif action == "refresh":
            tasks = copy.deepcopy(spec["tasks"])
            selection = list(range(len(tasks)))
        else:
            raise ValueError("Unknown extension action")
        if sources:
            self._sources(sources)
            if action not in ("retry_failed", "fetch_more"):
                raise ValueError("sources is only valid for retry_failed/fetch_more")
            selection = [i for i in selection if tasks[i]["source"] in sources]
        snapshot = self._execute(
            spec,
            tasks,
            [] if action == "refresh" else old.get("all_items", old["items"]),
            Operation(budget),
            old["query_id"],
            selection,
        )
        oldmap = {i.get("paper_ref", i.get("entity_ref")): i for i in old["items"]}
        newmap = {i.get("paper_ref", i.get("entity_ref")): i for i in snapshot["items"]}
        result = self._page(snapshot, 0, 20)
        result["changes"] = {
            "newly_matched": sorted(set(newmap) - set(oldmap)),
            "no_longer_observed": sorted(set(oldmap) - set(newmap)) if action == "refresh" else [],
            "changed": [
                r
                for r in oldmap.keys() & newmap.keys()
                if self._content(oldmap[r]) != self._content(newmap[r])
            ],
            "basis_snapshot_id": old["snapshot_id"],
        }
        return result

    @staticmethod
    def _content(value):
        return digest(
            {
                k: v
                for k, v in value.items()
                if k not in ("fetched_at", "field_provenance", "relation_evidence")
            }
        )

    def find_related_papers(self, paper_refs, method, match="all", sources=None, budget=None):
        if not paper_refs:
            raise ValueError("paper_refs cannot be empty")
        refs = list(dict.fromkeys(normalize_ref(r) for r in paper_refs))
        if method == "provider_recommendations":
            if sources and sources != ["semantic_scholar"]:
                raise ValueError("Provider recommendations currently support Semantic Scholar only")
            tasks = [
                {"kind": "recommendations", "source": "semantic_scholar", "paper_ref": ref}
                for ref in refs
            ]
        else:
            if method not in ("shared_references", "shared_citations"):
                raise ValueError("Unsupported related-paper method")
            kind = "references" if method == "shared_references" else "citations"
            tasks = [t for ref in refs for t in self._relation_tasks(ref, kind, sources)]
        spec = {
            "kind": "related",
            "method": method,
            "match": match,
            "paper_refs": refs,
            "tasks": tasks,
        }
        result = self._query(spec, budget, "refresh")
        result["coverage"]["limitations"].append(
            "Relatedness is not evidence of scientific agreement or novelty."
        )
        return result

    def export_records(self, query_id=None, paper_refs=None, format="json", fields=None):
        if bool(query_id) == bool(paper_refs):
            raise ValueError("Provide query_id or nonempty paper_refs, not both")
        snapshot = self.store.get_snapshot(query_id) if query_id else None
        missing = []
        if snapshot:
            records = snapshot["items"]
        else:
            records = []
            for ref in paper_refs:
                record = self.store.paper(normalize_ref(ref))
                if record:
                    records.append(record)
                else:
                    missing.append({"paper_ref": ref, "reason": "not_in_cache"})
        records = [selected_fields(r, fields) for r in records]
        coverage = self._page(snapshot, 0, 20)["coverage"] if snapshot else None
        if format == "json":
            content = json.dumps(
                {
                    "records": records,
                    "missing": missing,
                    "spec": snapshot["spec"] if snapshot else None,
                    "source_reports": [t.get("report") for t in snapshot["tasks"]]
                    if snapshot
                    else [],
                    "snapshot_id": snapshot["snapshot_id"] if snapshot else None,
                    "coverage": coverage,
                },
                ensure_ascii=False,
                indent=2,
            )
        elif format == "markdown":
            content = "\n".join(
                f"- {r.get('title') or r.get('name') or 'Unknown title'} "
                f"[{r.get('paper_ref') or r.get('entity_ref')}]"
                for r in records
            )
        elif format == "bibtex":
            entries = []
            for r in records:
                if "paper_ref" not in r:
                    missing.append({"entity_ref": r.get("entity_ref"), "reason": "not_a_paper"})
                    continue

                def esc(text):
                    return (
                        str(text)
                        .replace("\\", "\\textbackslash{}")
                        .replace("{", "\\{")
                        .replace("}", "\\}")
                        .replace("\n", " ")
                    )

                values = {
                    "title": r.get("title"),
                    "year": r.get("year"),
                    "author": " and ".join(
                        a["name"] for a in r.get("authors") or [] if a.get("name")
                    )
                    or None,
                    "doi": next((i[4:] for i in r["identifiers"] if i.startswith("doi:")), None),
                }
                absent = [k for k in ("title", "year", "author") if not values[k]]
                if absent:
                    missing.append({"paper_ref": r["paper_ref"], "missing_fields": absent})
                key = "paper" + digest(r["paper_ref"])[:12]
                entries.append(
                    "@misc{"
                    + key
                    + ",\n"
                    + ",\n".join(
                        "  " + k + " = {" + esc(v) + "}" for k, v in values.items() if v is not None
                    )
                    + "\n}"
                )
            content = "\n\n".join(entries)
        else:
            raise ValueError("Unsupported export format")
        return {
            "format": format,
            "content": content,
            "count": len(records),
            "missing": missing,
            "snapshot_id": snapshot["snapshot_id"] if snapshot else None,
            "coverage": coverage,
        }
