# spec.json：计划、批准与进度

检索计划及分类/详细阅读计划分别经用户确认后保存；继续已有调研时保留旧计划和修改原因。未知字段用 null，示例不是已执行结果。

```json
{
  "schema_version": 2,
  "topic": "待调研问题",
  "created": "2026-07-13",
  "output_dir": "用户确认的实际目录",
  "search_plan": {
    "purpose": "学习理解",
    "familiarity": "有点了解",
    "include": [],
    "exclude": [],
    "borderline": [],
    "time_range": null,
    "date_basis": null,
    "seed_papers": [],
    "source_rationale": [],
    "query_groups": [],
    "budget": null,
    "stop_conditions": [],
    "approved": false
  },
  "deep_dive_plan": {
    "axis": null,
    "taxonomy": [],
    "subfields": [],
    "budget": null,
    "approved": false
  },
  "progress": {"status": "planned", "completed_batches": [], "remaining": []},
  "changes": []
}
```

用途和背景独立记录；时间范围、来源与预算用具体值，不用“全且新”等模糊等级。`source_rationale` 记录各来源采用/不采用的理由；query_groups 写实际查询、范围与输出路径。停止条件可检查且不声称绝对搜全。

详细阅读计划保留 `axis` 名称供旧调用识别，值为具体分类维度；taxonomy 可含交叉类别。每个 subfield 写类别、分配的 pool_id/稳定标识、需回答问题、读取范围与独立路径。`approved` 只在真实收到用户确认后改 true。

progress 用 planned/in_progress/partial/completed，completed 指本次约定范围完成，不是全领域覆盖；剩余工作和来源故障单独列出。方案调整和引用版本变化进 changes。
