# 用 HF Papers 补查相关论文和近期工作

本文件说明文献调研什么时候用 HF Papers 补查、怎样调用和筛选结果，以及怎样记录实际查到的范围。

定向调用 → 日期后筛 → 记录纳排 → 合并论文身份 → 汇报覆盖限制

HF Papers 用于补充候选、发现替代术语、了解社区关注的工作。按 [来源选择](source-strategy.md) 和已确认的方案决定在哪些主题上使用。第一批查到且符合范围的论文可以参与分类；查漏时按具体路线或别名定向补查。HF 的搜索、日报和热门列表都只覆盖平台收录的部分论文。正式调研还需用适合本领域的来源查近期进展。

## 一、先核对命令，再按目标调用

`hf papers` 是独立 CLI。不要把 HF 填进 paper-search MCP 的 `sources`。先用 `hf --version` 和相应子命令的 `--help` 核对本机版本与参数。安装、认证和历史观察到的返回限制见 [统一的 HF CLI 说明](../../hf-trending-papers/references/hf-cli.md)。

| 目标 | 命令示例 | 怎样使用结果 |
| --- | --- | --- |
| 按主题补候选 | `hf papers search "on-device vision inference" --limit 3 --format json` | 先看标题和摘要是否符合调研问题，再按实际日期字段后筛。可换一个任务别名，例如 `mobile vision latency`，检查是否有实质新增。 |
| 查看平台日报或列表 | `hf papers ls --limit 2 --format json` | 要看特定日期时按本机帮助加 `--date YYYY-MM-DD`。列表没有主题过滤，有限样本不能当作该主题的全量结果。 |
| 核对已知论文的 HF 条目 | `hf papers info 2112.10752 --format json` | 核对返回的 `id`、标题和可用字段。`ai_keywords` 可提供补搜词，`ai_summary` 可帮助定位要回查的内容。字段以实际返回为准。 |

搜索结果的顺序不能当发表时间顺序，达到 `--limit` 时记录可能受限。日报尚未发布时，记录原请求及失败原因；需要改查提示中的可用日报日期时，写清实际查的是哪一天。限流或网络故障先看错误并按计划处理；缺少 CLI 时说明可用入口，只有实际需要认证时才按统一说明处理。剩余覆盖由其他已批准来源继续。

## 二、日期后筛与纳排记录

`search` 没有服务端日期过滤参数。保留原始返回的 `published_at`，按本次确认的时区和起止日期后筛。将它标为 **HF 返回的日期**；若调研按 arXiv 首次提交或正式发表统计，另从对应来源核对日期。把 HF 日报日期、记录中的 `published_at` 和本次获取时间分开写。缺日期时单独标记待核查；有日期且在窗口内的候选仍要按主题和纳排规则判断。

每个查询批次按 [运行步骤](workflow.md) 保存到 `search/<批次>.json`。在 `requests[]` 记录命令、查询词、`--limit`、获取时间、实际返回数、后筛窗口和筛选后数量。按实际情况保存 `included`、`excluded` 和 `pending`。写明每条纳排理由，保留论文 ID、标题和原始返回。HF 的 `id` 核实为 arXiv ID 后，填入归一化记录的 `arxiv` 字段；合并时用同一稳定标识关联其他来源。保留 HF 的原始观测和自己的来源记录。

平台生成的关键词和摘要用作候选线索。介绍论文的方法、结果和证据时，回到作者摘要或正文核对。投票、评论和仓库 stars 随观测时间记录；历史日报中今天查到的指标，按今天的观测处理。

## 三、完整填写示例

以下用「边缘设备上的视觉模型加速」说明执行和记录。示例命令通过本机 Clash 代理 `127.0.0.1:7890` 实测。代理只用于本次环境测试，运行时按所在机器的网络条件配置。

```bash
hf papers search "on-device vision inference" --limit 3 --format json
```

1. **定向调用。** 实测返回 3 条，依次是 `2601.20262`、`2412.11475` 和 `2606.07431`。日期顺序并不单调。
2. **日期后筛。** 假设本轮窗口是 2026-01-01 至 2026-06-30，按返回的 `published_at` 的 UTC 日期后筛。前者和最后一条落在窗口内，中间一条落在窗口外。记录日期后筛结果为 2 条。
3. **记录纳排。** 如本轮只收窄到视觉模型在设备上的单图推理，`2412.11475` 的排除理由可写「HF 日期在窗口外」。两条窗内结果先放入 `pending`，分别核查任务和测量设置是否符合本轮要求。满足日期条件并不自动纳入。
4. **合并论文身份。** 将下列示例记录写入 `search/hf-edge-vision.json`，再按运行步骤执行合并脚本。如果另一批也记录了相同 arXiv ID，检查 `pool.json` 是否保留两批观测；遇到纳排分歧时按 Step 2 核查。

以下 JSON 摘出本次返回的必要字段。正式记录保留原始条目和真实获取时间。

```json
{
  "query_group": "HF 边缘视觉补查",
  "requests": [{
    "source": "hf_papers",
    "command": "hf papers search \"on-device vision inference\" --limit 3 --format json",
    "status": "ok",
    "limit": 3,
    "returned_count": 3,
    "date_filter": {"field": "published_at", "timezone": "UTC", "start": "2026-01-01", "end": "2026-06-30", "applied_after_fetch": true},
    "in_window_count": 2,
    "limitations": ["返回数等于查询上限", "日期只在返回结果上后筛"]
  }],
  "included": [],
  "excluded": [{
    "source": "hf_papers",
    "arxiv": "2412.11475",
    "title": "OmniVLM: A Token-Compressed, Sub-Billion-Parameter Vision-Language Model for Efficient On-Device Inference",
    "reason": "HF published_at 为 2024-12-16，落在窗口外"
  }],
  "pending": [
    {"source": "hf_papers", "arxiv": "2601.20262", "title": "Shallow-π: Knowledge Distillation for Flow-based VLAs", "reason": "日期在窗口内，待核任务与推理测量设置"},
    {"source": "hf_papers", "arxiv": "2606.07431", "title": "OpenGlass: Ultra-Low-Power On-Device AI Eyewear with Event-based Vision", "reason": "日期在窗口内，待核是否报告单图延迟"}
  ]
}
```

5. **汇报覆盖限制。** 在 `coverage-review.md` 写明，这次 HF 搜索返回 3 条，达到查询上限，后筛留下 2 条待核查。这个结果只说明已查看的样本。另行区分未选用或未执行、执行失败、有效查询但零命中、有返回但窗口内零纳入，以及可能截断的情况。发现限制时，注明是否要扩大别名查询、核对另一来源或留作待补。
