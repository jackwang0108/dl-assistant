# 证据状态与启动条件

文件可用 `方向N-<slug>-verify.json`，记录已知与未知，不在没有新实验时验证新方法有效。

```json
{
  "schema_version": 2,
  "problem_id": null,
  "hypotheses": [],
  "closest_work_comparison": [],
  "scientific_unknowns": [],
  "resource_leads": [],
  "engineering_unknowns": [],
  "constraints": [],
  "next_evidence_needed": [],
  "recommendation": null,
  "reason": null
}
```

hypotheses 每项含ID、命题、推理与条件、支持与反对证据及来源位置、适用性、尚无/未取得证据的区别。资源线索含真实URL、确认了什么、未核实什么；不将存在项目页等同可运行。

比较现有工作检查具体命题与条件，不按关键词相同或只看摘要判已覆盖。候选受到反证时区分当前机制、当前设计和研究问题，不能从一个方法失败否定所有方法。有限搜索未发现不是证明空白。

可行性为已核实/待核实/阻塞，不能默认填“通过”。最终仓库尽调归 baseline-survey；资源估计注明来源和误差，尚可申请资源不计作确定可用。
