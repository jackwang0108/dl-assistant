# search/<query组-slug>.json 模板（Step 2 检索子 agent 落盘 · 机读）

检索阶段的零损耗留痕——主会话只拿紧凑清单，跑 `scripts/merge_pool.py` 合并去重成 `pool.json`；要看摘要 / 核查取舍就读这里。**写 json 不写散文**：合并去重由脚本做，json 才喂得进脚本。字段全用中文值，专有名词保留英文。

```json
{
  "query_group": "核心概念组",
  "sources": ["semantic_scholar", "arxiv", "hf-papers"],
  "included": [
    {
      "title": "High-Resolution Image Synthesis with Latent Diffusion Models",
      "arxiv": "2112.10752",
      "doi": null,
      "url": null,
      "year": 2022,
      "venue": "CVPR",
      "citations": 12000,
      "published": "2021-12",
      "role": "里程碑",
      "approach": "在 latent 空间做扩散，降算力",
      "reason": "为何纳入（一句）",
      "abstract_notes": "摘要要点（中文转述或摘录，供主会话定轴探针 / 核查用）"
    }
  ],
  "excluded": [
    { "title": "...", "arxiv": "...", "reason": "离题 / 重复 / 质量存疑…" }
  ]
}
```

**字段纪律**：

- 去重靠脚本三级键（arXiv ID → DOI → 归一化标题），所以 **`arxiv` / `doi` / `title` 三个至少填准一个**；都没有的条目脚本不去重、原样保留。
- `published` 填 `YYYY-MM`（有就填，hf 源天然带）——脚本的扫新覆盖统计靠它，没有它扫新覆盖行只能报「未知」。
- `role` 用固定枚举：奠基 / 里程碑 / 近期前沿（拿不准留 null）。
- `approach` 是「走什么路子」的技术路线短标签（如「基于 {某机制}」「{某范式} 的变体」），粒度到方法家族、不泛泛说「很相关」——这是 Step3 定轴的关键便宜信号。
- 排除项也要留痕——它是覆盖度自检和「为什么没收这篇」的依据，比直接丢弃诚实。
- 同一工作多版本（arXiv 预印本 vs 正式版）：合并为一条，venue 优先记正式版，arXiv ID 保留（下游 bibtex-on-the-fly 和读 PDF 都要用）。
