#!/usr/bin/env python3
"""合并 literature-survey 的 search/*.json 检索结果，去重成 pool.json。

用法:
    python3 merge_pool.py <调研目录>

读 <调研目录>/search/*.json（每个检索子 agent 一份），按 arXiv ID → DOI →
归一化标题 三级键去重合并，写 <调研目录>/pool.json，并向 stdout 打印统计
（各组命中、合并前后篇数、年份分布、扫新覆盖），供 Step2 结果汇报直接使用。

只依赖标准库。任一 json 解析失败会指出具体文件并以非零码退出。
"""

import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path


def norm_arxiv(value):
    """归一化 arXiv ID：去前缀、去 .pdf、去版本号（v1/v2 视为同一工作）。"""
    if not value:
        return None
    v = str(value).strip()
    v = re.sub(r"^(arxiv:|https?://arxiv\.org/(abs|pdf)/)", "", v, flags=re.I)
    v = re.sub(r"\.pdf$", "", v, flags=re.I)
    v = re.sub(r"v\d+$", "", v.strip())
    return v or None


def norm_doi(value):
    if not value:
        return None
    v = str(value).strip().lower()
    v = re.sub(r"^(doi:|https?://(dx\.)?doi\.org/)", "", v, flags=re.I)
    return v or None


def norm_title(value):
    """标题归一化：NFKC + 小写 + 非字母数字折叠成单空格。"""
    if not value:
        return None
    t = unicodedata.normalize("NFKC", str(value)).lower()
    t = re.sub(r"[^a-z0-9一-鿿]+", " ", t)
    return t.strip() or None


def dedup_key(paper):
    return (
        norm_arxiv(paper.get("arxiv"))
        or norm_doi(paper.get("doi"))
        or norm_title(paper.get("title"))
    )


def merge_into(existing, incoming, group):
    """同一条目被多组检索命中：并 source_groups，补空字段，引用数取大。"""
    if group not in existing["source_groups"]:
        existing["source_groups"].append(group)
    for field, value in incoming.items():
        if field in ("citations", "source_groups"):
            continue
        if not existing.get(field) and value:
            existing[field] = value
    try:
        existing["citations"] = max(
            existing.get("citations") or 0, incoming.get("citations") or 0
        ) or None
    except TypeError:
        pass


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    survey_dir = Path(sys.argv[1])
    search_dir = survey_dir / "search"
    files = sorted(search_dir.glob("*.json"))
    if not files:
        sys.exit(f"错误：{search_dir} 下没有任何 .json 检索结果")

    pool = {}  # 保序 dict：dedup_key -> 合并后的条目
    excluded = []
    group_stats = {}

    for path in files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            sys.exit(f"错误：解析 {path} 失败：{e}")
        group = data.get("query_group") or path.stem
        stats = group_stats.setdefault(group, {"included": 0, "excluded": 0})

        for paper in data.get("included", []):
            stats["included"] += 1
            key = dedup_key(paper)
            if key is None:
                key = f"__nokey__{len(pool)}"  # 无标题无 ID 的残条目，不去重
            entry = {k: v for k, v in paper.items() if k != "source_groups"}
            if key in pool:
                merge_into(pool[key], entry, group)
            else:
                entry["source_groups"] = [group]
                pool[key] = entry

        for paper in data.get("excluded", []):
            stats["excluded"] += 1
            excluded.append({**paper, "query_group": group})

    papers = list(pool.values())
    years = Counter(str(p.get("year")) for p in papers if p.get("year"))
    published = [str(p["published"]) for p in papers if p.get("published")]
    total_included = sum(s["included"] for s in group_stats.values())

    stats = {
        "per_group": group_stats,
        "included_before_dedup": total_included,
        "after_dedup": len(papers),
        "year_distribution": dict(sorted(years.items())),
        "latest_published": max(published) if published else None,
    }

    out = {
        "merged_from": [p.name for p in files],
        "stats": stats,
        "papers": papers,
        "excluded": excluded,
    }
    (survey_dir / "pool.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(f"pool.json 已写入 {survey_dir}/pool.json")
    for group, s in group_stats.items():
        print(f"  {group}: 纳入 {s['included']} / 排除 {s['excluded']}")
    print(f"  合并前 {total_included} 篇 → 去重后 {len(papers)} 篇")
    print(f"  年份分布: {stats['year_distribution']}")
    print(f"  扫新覆盖: 最新 published = {stats['latest_published'] or '未知（条目未带 published 字段）'}")


if __name__ == "__main__":
    main()
