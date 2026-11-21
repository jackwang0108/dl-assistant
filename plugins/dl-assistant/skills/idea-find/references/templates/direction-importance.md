# 模板：方向N-<slug>-importance.json（Step 5 重要性独立预审落盘 · 机读）

> 流程见 `direction.md` Step 5；公共语言规范见 `output-contract.md`。

1 个重要性独立预审（人设 = 严苛顶会审稿人 / AC）对 1-2 个方向骨架逐个过 Hamming 五问，论证"**为什么这个方向重要**"——影响面（谁会在意）、时机（浪潮头还是退潮尾）、被忽视的代价（不填这个空白会怎样）。**拿真实文献证据戳，产重要性漏洞清单，不打分不排序**（判决归讨论①的用户）。

```json
{
  "direction": "{方向 slug}",
  "verdict": "立得住 | 存疑 | 没人需要",
  "affected_community": "{哪类研究者 / 哪个子社区，具体到人群}",
  "timing": {
    "label": "浪潮头 | 上升期 | 退潮尾",
    "evidence": "{近 1-2 年该问题的论文数趋势 + arXiv ID}"
  },
  "neglected_cost": "{这空白一直被忽视的代价，一句话}",
  "hamming": [
    { "q": "谁会在意这个结果？", "answer": "{具体人群，答不出 = 没人 care 的边角}", "evidence": ["{arXiv ID}"] },
    { "q": "审稿人凭什么 care？", "answer": "{significance 一句话}", "evidence": ["{arXiv ID}"] },
    { "q": "三年后还有人做吗？", "answer": "{浪潮头 / 退潮尾 + 趋势}", "evidence": ["{arXiv ID}"] },
    { "q": "做出来了谁接着做？", "answer": "{能开一条线 / 一次性工作}", "evidence": ["{arXiv ID}"] },
    { "q": "太小（一个 trick）或太老（十年前的问题）？", "answer": "{是 / 否 + 依据}", "evidence": ["{arXiv ID}"] }
  ],
  "flaws": [
    { "flaw": "{戳出来的重要性漏洞}", "evidence": "{实证依据 + 出处}" }
  ],
  "conclusion": "{立得住 / 存疑 / 没人需要 + 一句话依据}"
}
```

> **预审铁律**：产**漏洞清单（哪点重要 / 哪点像自嗨 + 证据）**，不打分排序。pitch 品味杀验"用户想不想做"，Step 3 调研验"空白真不真"，本份验"**这空白值不值得填**"；被戳死的方向不是"没人做过"的问题，是"**没人需要**"的问题。
