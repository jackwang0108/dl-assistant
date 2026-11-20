# idea-seed.json：起点、目标与未知

建立当前共同背景，不要求用户先有 idea、独特资源或明确会议。示例是待填写结构，不代表已完成确认。

```json
{
  "schema_version": 2,
  "date": null,
  "topic": null,
  "starting_point": {"kind": "field", "content": null, "sources": []},
  "problem": null,
  "user_intuition": null,
  "user_goal": null,
  "familiarity": null,
  "interests": [],
  "resources": {"available": [], "potential": [], "unknown": []},
  "time_budget": null,
  "target_venue": null,
  "seeds": [],
  "open_questions": []
}
```

starting_point.kind 可为 field/paper/observation/hypothesis/prior_results。用户只给领域时 problem、user_intuition 可为空，agent仍需主动提出问题。潜在资源不能算已获资源，一般DL经验或看过调研不自动等于独占优势。

seeds 每项写 source、ref（稳定论文标识/实际路径）、point、已核查范围和未知；来源可为用户、已有笔记、调研、方向跟踪或本次检索。用户信息与agent推测分开，不为凑字段替用户指定偏好或会议。

已有 card 的研究线索只作为待检验素材；旧 worth_reading=false 不代表研究不可做。旧 wedge/entry_track 可保留为历史信息，不能据其缺失拒绝探索。
