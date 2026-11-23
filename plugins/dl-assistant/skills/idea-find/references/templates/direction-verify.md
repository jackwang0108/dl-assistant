# 模板：方向N-<slug>-verify.json（Step 6 充实子 agent 落盘 · 方向可行性验证 · 机读）

> 流程见 `direction.md` Step 6；公共语言规范见 `output-contract.md`。

充实子 agent 的验证留痕——**只验「方向」可行性**（与已有工作重合/有效/能启动/资源够）；gap 真实性已由 Step 3 定向调研回答，这里不重复。主会话按需回读。

```json
{
  "direction": "{方向 slug}",
  "filter": [
    { "check": "撞车吗", "verdict": "立得住 | 丢弃", "evidence": "{这个具体方向思路有没有人做了——最接近的工作、为何差异足够}" },
    { "check": "有效吗", "verdict": "立得住 | 丢弃", "evidence": "{这方向真的能解决痛点吗——逻辑是否成立}" },
    { "check": "能启动吗", "verdict": "立得住 | 丢弃", "evidence": "{有 baseline / 数据 / 开源代码可起步——附线索 URL}" },
    { "check": "资源匹配吗", "verdict": "立得住 | 丢弃", "evidence": "{所需算力/数据在用户约束内}" }
  ],
  "search_trail": ["{搜了哪些 query、命中哪些最接近的工作、为何差异足够（或为何判撞车丢弃）}"],
  "covered_but_explorable": {
    "triggered": false,
    "original_core": "{若因撞车判丢弃：原方向核心}",
    "covered_by": "{被哪篇覆盖，URL}",
    "as_new_seed": "{是否适合作新起点}"
  },
  "conclusion": "{立得住 / 丢弃 + 一句话依据}"
}
```

> 「已覆盖·可深挖」：与已有工作重合判丢弃时 `covered_but_explorable.triggered = true` 并填全三字段——被覆盖的方向可评估对应论文能否作为更合适的研究起点，留痕供讨论①决定是否换起点重跑。
