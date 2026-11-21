# 模板：literature.json（文献台账 + 空白矩阵 · 主会话合并落盘 · 机读）

> 流程见 `direction.md` Step 3；公共语言规范见 `output-contract.md`。

**IF 找方向阶段的中心产物**：主会话把 `survey-channels/*.json` 合并去重（arXiv ID 归一化）后的全量台账。**回退重生成时主会话读的就是这份全量最新的台账**（审计链：方向 ← pitch（痛点 × 筹码）← 文献验证——**空白矩阵是验证器，回答"pitch 是不是已被做了、做到什么程度"，不是生成器**）；挑错/验证新发现随时追加进来。

```json
{
  "topic": "{topic-slug}",
  "anchor": "{清晰锚点一句话}",
  "pitches": ["{幸存 pitch-N-<slug>}"],
  "seed_sources": {
    "paper_cards": ["{docs/paper-reading/... 路径}"],
    "ls_report": "{docs/literature-survey/... 路径或 null}",
    "dt_library": "{docs/direction-tracking/... 路径或 null}"
  },
  "freshness": {
    "scan_window": "2025-07 至 2026-07",
    "channels_run": ["fresh", "closest", "negative"],
    "hf_checked": true,
    "note": "{扫新覆盖说明：查了哪些源、HF 有无命中}"
  },
  "groups": [
    {
      "name": "{组名——默认沿 LS taxonomy 分组；视角不合才重分并记理由}",
      "papers": [
        {
          "title": "{标题}",
          "arxiv": "{arXiv ID}",
          "year": 2025,
          "published": "2025-11",
          "approach": "{一句话路子}",
          "relation_to_anchor": "{跟哪个 pitch / 锚点相关 / 背景文献}",
          "source_channel": "fresh | closest | negative | 后续追加"
        }
      ]
    }
  ],
  "blank_matrix": [
    {
      "group": "{组名}",
      "status": "没人碰 | 粗糙 | 做得差 | solid",
      "evidence": ["{arXiv ID}"],
      "gaps_here": "{落在本格的空白/机会，一句}",
      "history": [
        { "date": "2026-07-30", "old": "没人碰", "new": "做得差", "reason": "{改判依据，arXiv ID}" }
      ]
    }
  ],
  "closest_assessment": [
    {
      "arxiv": "{arXiv ID}",
      "title": "{标题}",
      "what_they_did": "{做到了什么，一句}",
      "maturity": "{做得好不好：方法成熟度 / 效果 / 作者承认的 limitation}",
      "verdict": "solid解决 | 做得差 | 粗糙"
    }
  ],
  "negative_signals": [
    { "signal": "{死路信号}", "evidence": "{出自哪篇哪节，arXiv ID}", "implication": "{对 pitch 意味着什么}" }
  ],
  "cross_domain": [
    { "mechanism": "{核心机制}", "where_proven": "{哪个域已验证，arXiv ID}", "transfer_note": "{迁移机会一句}" }
  ]
}
```

**字段纪律**：

- **空白矩阵的每个格子必须带 arXiv 依据**——status 是调研**结论**，不是印象。调研即验证：这格标什么，Step 4 方向成型就直接信什么，没有二次核验环节。
- `history` 记改判：后续挑错/充实发现新文献填了判空白的格子就**改判**，但留原判 + 新证据（时间序留痕），不覆盖。
- `closest_assessment` 是铁规 3 的落点——最接近的 3-5 篇的深浅评估，"没人做 vs 没人做好"就看这里。
- 新发现随时追加进 `groups` 对应组（`source_channel` 记「后续追加」），并在相关空白格 `history` 留改判痕。
