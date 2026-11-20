# literature.json：论文、证据与假设关系

保留该文件供当前问题与后续取证使用，不使用“没人碰/做得差/solid”等空白矩阵把有限检索包装为领域结论。可以由文献产生新问题，不只为初始候选做验证。

```json
{
  "schema_version": 2,
  "topic": null,
  "problem_ids": [],
  "seed_sources": [],
  "request_records": [],
  "groups": [],
  "closest_assessment": [],
  "hypothesis_evidence": [],
  "new_questions": [],
  "unresolved_identity_or_evidence": [],
  "coverage_notes": [],
  "history": []
}
```

groups是可交叉的组织方式；每篇保存实际标题、稳定ID/DOI/URL、版本、来源、阅读范围与证据位置。closest_assessment比较现有工作具体命题、条件、证据及与当前问题的关系，不用成熟度或热度替代内容。

hypothesis_evidence每项为H编号、具体命题、证据出处/版本/位置、原文事实、支持或反对哪一步、条件可比性、推断和限制。明确尚无支持、已有反证与资料未取得，不把文献放进本项目实验结果。

new_questions保留新发现的问题/解释及来源。覆盖说明列实际执行、失败、部分与未查范围，最新命中时间不等于查全。字段冲突、身份待定、版本不一致均保留，标题相似仅提示核对；不静默选最大引用数或丢不利证据。

history记录命题或判断变更、旧理由、新证据和受影响候选。旧blank_matrix只作为历史判断，不默认相信其“空白真实”结论。
