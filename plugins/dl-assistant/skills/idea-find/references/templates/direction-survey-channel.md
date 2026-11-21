# 模板：survey-channels/<channel>.json（Step 3 调研通道子 agent 落盘 · 机读）

> 流程见 `direction.md` Step 3；公共语言规范见 `output-contract.md`。

一个通道一份（`fresh.json` / `closest.json` / `negative.json`），是子 agent 的**原始产出**——主会话只拿紧凑摘要，合并去重成 `literature.json`；原始件留着，合并时丢了什么、改判了什么才可审计。**写 json 不写散文**。字段值用中文，专有名词保留英文。

```json
{
  "channel": "fresh | closest | negative",
  "anchor": "{幸存 pitch 的核心机制一句话}",
  "queries": ["{实际跑过的 query，留痕}"],
  "scan_window": "{扫新窗口，如 2025-07 至 2026-07}",
  "hf_checked": true,
  "found": [
    {
      "title": "{标题}",
      "arxiv": "{arXiv ID}",
      "doi": null,
      "url": null,
      "year": 2026,
      "published": "2026-03",
      "one_liner": "{这篇干了啥，一句}",
      "relation_to_anchor": "{跟哪个查询锚点（哪个 pitch）相关、什么关系}",
      "anchor_status": "没人碰 | 粗糙 | 做得差 | solid解决 | 死路信号 | 跨域现成解法",
      "maturity_note": "{仅 closest 通道：做得好不好——方法成熟度 / 效果 / 作者承认的 limitation}"
    }
  ],
  "excluded": [
    { "title": "...", "arxiv": "...", "reason": "离题 / 重复 / 质量存疑…" }
  ],
  "key_insights": ["{3 条最关键洞察，供主会话合并时抓重点}"]
}
```

**字段纪律**：

- 去重靠主会话合并时按 arXiv ID 归一化，所以 **`arxiv` / `doi` / `title` 三个至少填准一个**。
- `anchor_status` 是本通道对"这个 pitch 现在还能不能做"的结论，每条 `found` 都要落到具体 pitch 上——游离于锚点之外的好文章也登记（`relation_to_anchor` 记「背景文献」），主会话合并时分组用。
- `maturity_note` 只有 closest 通道必填（铁规 3：最接近的 3-5 篇读深浅）；其他通道留空。
- negative 通道的 `found` 里，死路信号要写清**证据原文**（"we tried X but..."出自哪篇哪节），跨域解法写清哪个域、怎么解的。
- 排除项也要留痕——它是覆盖度自检和"为什么没收这篇"的依据，比直接丢弃诚实。
- `hf_checked` 记录有没有查 `hf papers` 日报/trending（铁规 1 的留痕）；false 要有理由。
