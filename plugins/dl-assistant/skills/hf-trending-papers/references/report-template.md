# HF 论文报告与快照模板

本文件说明怎样公布本次样本范围、区分平台关注度和阅读建议，以及保留可核对的历史依据。

## radar.md

```markdown
# Hugging Face 论文 · <查询窗口或主题>

## 范围与覆盖
- <日报、周、月、近期热门或搜索。实际窗口、排序、上限和抓取时间。>
- <返回条目、去重篇数、已查详情和未核项。注明字段或覆盖限制。>
- <原始数据和请求记录位置。>

## 本次样本中的研究话题
| 问题或方法 | 篇数及样本内占比 | 代表论文 | 实际观察与限制 |
| --- | --- | --- | --- |

## 优先阅读
### <标题与 arXiv ID>
- 平台观察：<投票、评论、仓库和关联资源的实际观测、时间及缺失字段。>
- 研究内容与推荐理由：<研究什么，作者报告了什么，为什么和用户有关。>
- 阅读时核什么：<一条具体问题。已定位到章节时附实际位置。>
- 依据：<列表摘要、详情摘要或另行核实的来源。>

## 跨窗观察（可比时）
<可比窗口、排序、样本覆盖、同一论文重复出现与新出现的论文。>

## 完整分类与待核
<逐篇分类或所附记录路径、未查详情和可选后续阅读。>
```

多个话题的占比之和可能超过 100%，分母使用本次去重论文数。report 里如写仓库关注度，用可比观测并注明来源。多个话题使用相同仓库时分别说明关联，全局只按规范仓库地址计一个。机构记录只反映本次数据的可见信息。

## radar-snapshot.json

从 [快照模板](radar-snapshot-template.json) 填实际返回。使用 `sample_request_id` 指本次列表或搜索，详情只补字段。对应[请求记录](request-log-template.json)按请求 ID 保存命令、状态和时点。请求状态可用 `ok`、`empty`、`command_failed`、`invalid_response` 或 `not_run`。成功的空列表才记返回 0；失败、结构不符和未执行用 null。已返回的样本覆盖可记 `capped`、`unknown` 或有充分依据时 `confirmed`，解释依据和范围。

`papers` 每项包括 `id`、已核的 `version_id`、`topics`、原始来源和观测。投票及评论等可能有多份观测，用 `request_id` 和指标名定位。状态采用 `value`、`null` 或 `missing`，只有值确实存在才填入。下例演示结构，数字仅用于说明：

```json
{
  "id": "2501.12948",
  "version_id": null,
  "topics": ["sequence-modeling"],
  "sources": ["001", "002"],
  "activity_observations": [
    {"request_id": "001", "metric": "upvotes", "status": "missing", "value": null},
    {"request_id": "002", "metric": "upvotes", "status": "value", "value": 0}
  ],
  "resource_observations": [],
  "organization_observations": []
}
```

`resource_observations` 逐次记录 `request_id`、资源类型、规范 ID 或仓库地址、观测到的值和覆盖状态。报告只见部分模型或数据集时，保留已见 ID 及平台报告的总数，分别解释。机构记录保留 `request_id`、字段实际状态和值。`topics` 的每项保存稳定话题键、定义、关键词、去重论文 ID 和代表论文，计数可从这些记录回查。

跨窗对齐话题时看定义和研究问题。旧快照缺窗口、排序、覆盖或观测时间时，只作定性线索。同一窗口的新观测可用于比较同一项累计指标，窗口统计仍只取一份数据。
