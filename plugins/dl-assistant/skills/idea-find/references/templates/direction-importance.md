# 研究价值讨论记录

文件可用 `方向N-<slug>-importance.json`。不需要固定的“严苛审稿人”轮次；agent应提出自己的推荐并解释正反理由，用户能理解后参与决定。

```json
{
  "schema_version": 2,
  "problem_id": null,
  "problem_version": null,
  "question": null,
  "if_supported": {"new_knowledge_or_capability": null, "why_it_matters": null, "evidence": []},
  "limited_value_results": [],
  "closest_work_differences": [],
  "counterarguments": [],
  "unknowns": [],
  "agent_recommendation": null,
  "recommendation_reason": null,
  "user_response": null,
  "decision": null,
  "scope_change": {"previous_question": null, "retained_value": null, "lost_value": null, "reassessed": false}
}
```

研究价值可以是认识、方法、理论、评测或实际能力，不要求全部满足。差异、文献覆盖、证据支持与价值分别论证；引用数、star、热度、方法年代和关键词缺失不证明重要或无用。

用当前问题评价，不把“该大领域重要”直接套到收窄后命题。decision可为继续推理/进一步取证/修改问题/暂缓/停止；认同继续讨论不自动批准实验预算。不要预测录用概率或三年后关注度。
