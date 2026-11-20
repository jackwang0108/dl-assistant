# 独立检索或分析记录

`survey-channels/<独立批次>.json` 保存每次来源记录，按实际任务命名，不固定三种通道、不覆盖旧文件。独立分析可提出新解释，不限于对既有候选做否定。

```json
{
  "schema_version": 2,
  "task": null,
  "problem_ids": [],
  "requests": [],
  "found": [],
  "excluded": [],
  "pending": [],
  "observations": [],
  "new_questions_or_explanations": [],
  "limitations": []
}
```

requests记录来源、实际query、时间范围及日期口径、排序、limit、分页、是否截断、获取时间、原始结果路径、成功/部分/失败/未运行。合法空结果不同于没有执行。不存在固定平台必查或12个月保证，按问题选择来源；历史报告能否复用取决于内容与实际覆盖。

found逐篇包含title、稳定arxiv/doi/url、作者、版本、来源、读取范围与位置、作者声明、已核查观察和对哪些假设的支持/反对/未知。无arXiv也可记录；仅标题未核实身份的保留待核查，不自动合并。

observations写事实与条件，new_questions_or_explanations写新构想及推理，两者分开。排除与pending有理由，空搜索不推导“没人做”或“方向已死”。主agent核对原始记录与冲突后才更新累计索引。
