#!/usr/bin/env python3
"""Merge search/*.json into pool.json, retaining provenance and conflicts.

Usage: python3 merge_pool.py <survey-directory>
Only shared arXiv IDs, DOIs or exact URLs establish identity. Titles suggest
manual review only. Uses the standard library; malformed inputs never replace
an existing pool.json. Query execution coverage is retained, not inferred from
the newest publication found.
"""
import json
import os
import re
import sys
import tempfile
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


def norm_arxiv(value):
    if not value:
        return None
    value = re.sub(r"^(arxiv:\s*|https?://arxiv\.org/(abs|pdf)/)", "", value.strip(), flags=re.I)
    value = re.sub(r"\.pdf$", "", value, flags=re.I)
    return re.sub(r"v\d+$", "", value, flags=re.I) or None


def norm_doi(value):
    if not value:
        return None
    return re.sub(r"^(doi:\s*|https?://(dx\.)?doi\.org/)", "", value.strip().lower()) or None


def norm_title(value):
    if not value:
        return None
    text = unicodedata.normalize("NFKC", value).casefold()
    return " ".join("".join(c if c.isalnum() else " " for c in text).split()) or None


def identity_keys(paper):
    keys = set()
    for kind, normalizer in (("arxiv", norm_arxiv), ("doi", norm_doi)):
        if paper.get(kind):
            keys.add((kind, normalizer(paper[kind])))
    url = paper.get("url")
    if url:
        url = url.strip()
        if re.match(r"https?://arxiv\.org/(abs|pdf)/", url, re.I):
            keys.add(("arxiv", norm_arxiv(url)))
        elif re.match(r"https?://(dx\.)?doi\.org/", url, re.I):
            keys.add(("doi", norm_doi(url)))
        else:
            keys.add(("url", url))
    return keys


def read_records(files):
    records, requests, group_stats = [], [], {}
    for path in files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("top level must be an object")
            group = data.get("query_group") or path.stem
            if not isinstance(group, str):
                raise ValueError("query_group must be a string")
            calls = data.get("requests", [])
            if not isinstance(calls, list) or any(not isinstance(c, dict) for c in calls):
                raise ValueError("requests must be a list of objects")
            requests.append({"file": path.name, "query_group": group,
                             "requests": calls, "coverage_known": bool(calls)})
            stats = group_stats.setdefault(group, {"included": 0, "excluded": 0, "pending": 0})
            for decision in ("included", "excluded", "pending"):
                papers = data.get(decision, [])
                if not isinstance(papers, list):
                    raise ValueError(f"{decision} must be an array")
                for index, paper in enumerate(papers):
                    if not isinstance(paper, dict):
                        raise ValueError(f"{decision}[{index}] must be an object")
                    for field in ("arxiv", "doi", "url", "title"):
                        if paper.get(field) is not None and not isinstance(paper[field], str):
                            raise ValueError(f"{decision}[{index}].{field} must be a string or null")
                    if not any(paper.get(k) and paper[k].strip() for k in ("arxiv", "doi", "url", "title")):
                        raise ValueError(f"{decision}[{index}] has no usable identity or title")
                    stats[decision] += 1
                    records.append({"query_group": group, "file": path.name,
                                    "decision": decision, "index": index, "record": paper})
        except (ValueError, UnicodeError) as exc:
            raise ValueError(f"{path}: {exc}") from exc
    return records, requests, group_stats


def build_pool(files):
    records, requests, group_stats = read_records(files)
    parent = list(range(len(records)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    owners = {}
    keys = [identity_keys(r["record"]) for r in records]
    for i, identifiers in enumerate(keys):
        for key in identifiers:
            if key in owners:
                parent[find(i)] = find(owners[key])
            else:
                owners[key] = i
    components = defaultdict(list)
    for i in range(len(records)):
        components[find(i)].append(i)

    # Contradictory strong identifiers require review, not an arbitrary merge.
    groups, identity_conflicts = [], []
    for indices in components.values():
        identifiers = set().union(*(keys[i] for i in indices))
        conflict = any(len({v for k, v in identifiers if k == kind}) > 1
                       for kind in ("arxiv", "doi"))
        if conflict:
            identity_conflicts.append({"observation_indices": indices,
                                       "identifiers": [list(k) for k in sorted(identifiers)]})
            groups.extend([[i] for i in indices])
        else:
            groups.append(indices)
    groups.sort(key=lambda group: group[0])
    items, title_groups = [], defaultdict(list)
    conflicted = {i for c in identity_conflicts for i in c["observation_indices"]}
    for number, indices in enumerate(groups, 1):
        observations = [records[i] for i in indices]
        item = {"pool_id": f"p{number:05d}", "source_groups": [],
                "identifiers": [list(k) for k in sorted(set().union(*(keys[i] for i in indices)))],
                "observations": observations, "field_conflicts": [], "citation_observations": []}
        values = defaultdict(list)
        for obs in observations:
            paper = obs["record"]
            if obs["query_group"] not in item["source_groups"]:
                item["source_groups"].append(obs["query_group"])
            for field, value in paper.items():
                if field in ("source_groups", "citations"):
                    continue
                if value is not None and value != "" and value != [] and value not in values[field]:
                    values[field].append(value)
            if paper.get("citations") is not None:
                item["citation_observations"].append({
                    "value": paper["citations"], "source": paper.get("source"),
                    "observed_at": paper.get("observed_at"), "file": obs["file"],
                    "query_group": obs["query_group"]})
        for field, alternatives in values.items():
            if field in item:
                continue
            # Identifier formatting differences are retained in observations.
            if field in ("arxiv", "doi"):
                normalized = [v for k, v in item["identifiers"] if k == field]
                item[field] = normalized[0] if normalized else None
            elif len(alternatives) == 1:
                item[field] = alternatives[0]
            else:
                item[field] = None
                item["field_conflicts"].append({"field": field, "values": alternatives})
        item["citations"] = None  # No cross-provider maximum or unlabelled count.
        decisions = {o["decision"] for o in observations}
        item["decision_conflict"] = len(decisions) > 1
        item["identity_conflict"] = any(i in conflicted for i in indices)
        item["decision"] = ("pending" if item["decision_conflict"] or item["identity_conflict"]
                            else next(iter(decisions)))
        items.append(item)
        for title in {norm_title(o["record"].get("title")) for o in observations} - {None}:
            title_groups[title].append(item["pool_id"])
    papers = [p for p in items if p["decision"] == "included"]
    excluded = [p for p in items if p["decision"] == "excluded"]
    pending = [p for p in items if p["decision"] == "pending"]
    years = Counter(str(p["year"]) for p in papers if p.get("year"))
    dates = [str(o["record"]["published"]) for o in records if o["record"].get("published")]
    return {"schema_version": 2, "merged_from": [p.name for p in files],
            "stats": {"per_group": group_stats,
                      "included_before_dedup": sum(g["included"] for g in group_stats.values()),
                      "after_dedup": len(papers), "excluded_count": len(excluded),
                      "pending_count": len(pending), "total_records": len(records),
                      "year_distribution": dict(sorted(years.items())),
                      "latest_published": max(dates) if dates else None},
            "requests": requests, "papers": papers, "excluded": excluded, "pending": pending,
            "identity_conflicts": identity_conflicts,
            "possible_duplicates": [{"normalized_title": t, "pool_ids": ids}
                                    for t, ids in title_groups.items() if len(ids) > 1]}


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    survey_dir = Path(sys.argv[1])
    files = sorted((survey_dir / "search").glob("*.json"))
    if not files:
        sys.exit(f"错误：{survey_dir / 'search'} 下没有检索 JSON")
    try:
        output = build_pool(files)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=survey_dir,
                                         prefix=".pool-", suffix=".json", delete=False) as stream:
            temporary = Path(stream.name)
            try:
                json.dump(output, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
            except BaseException:
                temporary.unlink(missing_ok=True)
                raise
        try:
            os.replace(temporary, survey_dir / "pool.json")
        finally:
            temporary.unlink(missing_ok=True)
    except (ValueError, OSError) as exc:
        sys.exit(f"错误：{exc}")
    stats = output["stats"]
    print(f"pool.json 已写入 {survey_dir / 'pool.json'}")
    print(f"合并前纳入记录 {stats['included_before_dedup']}；合并后纳入 {stats['after_dedup']}，"
          f"排除 {stats['excluded_count']}，待核查 {stats['pending_count']}")
    print(f"最新命中文献日期：{stats['latest_published'] or '未知'}（不代表检索覆盖完整）")
    print("来源完整性请核对 requests；身份、字段和纳排冲突须人工核查。")


if __name__ == "__main__":
    main()
