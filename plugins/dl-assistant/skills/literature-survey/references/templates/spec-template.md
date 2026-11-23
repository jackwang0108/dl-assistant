# spec.json：调研方案、确认与进度

本文件说明怎样保存用户确认的检索和详细阅读方案、记录执行进度，以及下次怎样从未完成的步骤继续。

按 [运行步骤](../workflow.md) 将 `spec.json` 保存到本次调研目录。Step 1 确认检索方案，Step 3 确认分类和详细阅读方案。只有收到用户确认才把对应计划的 `approved` 改为 `true`。执行记录如实更新。下列例子用固定日期和假设批次演示写法。

## Step 1：检索方案

向用户说明「为什么搜这些来源、各查什么、准备何时停」。分别询问或沿用用户已说明的用途与熟悉度。按 [来源选择](../source-strategy.md) 明确整体范围、近期窗口、截至日期和各组的日期口径。查询组中的 `params` 直接使用当前 paper-search v2 的参数结构。选用其他工具时记录实际命令或入口，以及它所能核对的日期。每组给出输出路径和理由。

下面的完整例子演示用户**已确认** Step 1、尚未确认 Step 3 的状态。拟定阶段把相应的 `approved` 设为 `false`。预算是计划上限；实际执行参数、来源状态、分页和消耗写入 `search/*.json`，覆盖和待补项写入 `coverage-review.md`。

```json
{
  "schema_version": 2,
  "topic": "边缘设备上的视觉模型加速",
  "created": "2025-09-01",
  "output_dir": "docs/literature-survey/2025-09-01-edge-vision",
  "search_plan": {
    "purpose": "选技术方案",
    "familiarity": "有点了解",
    "include": ["视觉模型的边缘端推理优化", "有单图或批大小为 1 的延迟测量"],
    "exclude": ["仅比较云端大批量吞吐的工作"],
    "borderline": ["只报告 FLOPs 的工作可作技术背景，需另核对有无设备实测"],
    "time_range": {"start": "2020-01-01", "end": "2025-08-31"},
    "recent_window": {"start": "2025-06-01", "end": "2025-08-31"},
    "as_of": "2025-08-31",
    "seed_papers": [],
    "source_rationale": [
      {"source": "openalex", "selected": true, "reason": "按发表日期找已出版的代表工作"},
      {"source": "arxiv", "selected": true, "reason": "按首次提交时间找近期预印本"},
      {"source": "hf_papers", "selected": false, "reason": "第一批先查上述来源；必要时再按已批准范围用 HF 补术语"}
    ],
    "query_groups": [
      {
        "name": "已发表的代表路线",
        "tool": "search_papers",
        "rationale": "查找模型级优化和运行时优化中可追溯的代表作",
        "params": {
          "queries": [{"text": "on-device vision inference latency", "sources": ["openalex"]}],
          "filters": {"date_range": {"date_type": "published", "start": "2020-01-01", "end": "2025-08-31"}},
          "sort": "relevance",
          "budget": {"max_requests": 4, "max_items": 30, "max_seconds": 45}
        },
        "output": "search/representative-routes.json"
      },
      {
        "name": "近期预印本",
        "tool": "search_papers",
        "rationale": "让近期论文与代表作一起参与分类，观察是否有新的优化路线",
        "params": {
          "queries": [{"text": "single-image inference latency edge device", "sources": ["arxiv"]}],
          "filters": {"date_range": {"date_type": "first_submitted", "start": "2025-06-01", "end": "2025-08-31"}},
          "sort": "date_desc",
          "budget": {"max_requests": 4, "max_items": 30, "max_seconds": 45}
        },
        "output": "search/recent-preprints.json"
      }
    ],
    "budget": {
      "initial_max_requests": 8,
      "initial_max_items": 60,
      "followup_max_requests": 2
    },
    "stop_conditions": [
      "执行计划内两组查询，核对近期窗口及截至日期的实际覆盖",
      "重点路线有可回查的代表证据，定向补查没有改变关键比较",
      "达到确认预算仍有缺口时，记录待补项并按实际范围交付"
    ],
    "approved": true
  },
  "deep_dive_plan": {
    "axis": null,
    "axis_rationale": null,
    "scale_recommendation": null,
    "taxonomy": [],
    "subfields": [],
    "budget": null,
    "approved": false
  },
  "progress": {
    "status": "planned",
    "completed_batches": [],
    "remaining": [
      {"step": 2, "batch": "representative-routes", "path": "search/representative-routes.json", "next_action": "执行已发表代表路线查询"},
      {"step": 2, "batch": "recent-preprints", "path": "search/recent-preprints.json", "next_action": "执行近期预印本查询"}
    ],
    "source_failures": []
  },
  "changes": []
}
```

- `purpose` 可用「学习理解」「找研究方向」「定位自己的工作」「选技术方案」。`familiarity` 单独记录，例如「基本陌生」「有点了解」「就在其中做」。
- 起点论文有就保存已核标题和稳定标识；没有就留空数组。日期窗口与日期口径分别写。预算写入可检查的数量或时间，范围变更按确认记录更新。
- `output_dir` 是用户确认的实际调研目录，批次和产物路径相对该目录。未知标量用 `null`，没有条目时用空数组。

## Step 3：分类和详细阅读方案

向用户说明「为什么这样分类、选哪几篇、读哪部分、每篇回答什么」。按 [分类与分析分工](../organizing-axis.md) 提出分类理由、交叉项和暂未归类项。从合并后的论文池选择代表作和相关近作。给每篇分配具体核查范围、问题和输出笔记。跨组论文沿用同一身份，已读过的证据可以按原笔记位置复用。

下例只展示对 `deep_dive_plan` 的更新。论文标题与 `pool_id` 为假设值；真实执行时填已核实的稳定标识。有些论文尚未核实到稳定标识时保留其论文池条目和原始出处，待核后再补。

```json
{
  "deep_dive_plan": {
    "axis": "按优化发生的位置分类",
    "axis_rationale": "模型结构与运行时实现的改动通常需要核对不同条件，混合方案允许跨组",
    "scale_recommendation": "先读两篇代表作和一篇近期工作；其余论文保留摘要分类",
    "taxonomy": ["模型级改动", "运行时与算子优化"],
    "subfields": [
      {
        "name": "模型级改动",
        "notes_path": "notes/model-optimization.md",
        "papers": [
          {
            "pool_id": "p00001",
            "title": "示例论文 A",
            "paper_ref": null,
            "read_locations": ["方法的模型结构描述", "实验设置和表 2"],
            "question": "延迟下降是否来自模型轻量化，比较是否使用同一硬件和批大小？",
            "role": "代表作"
          },
          {
            "pool_id": "p00003",
            "title": "示例近作 C",
            "paper_ref": null,
            "read_locations": ["方法概述", "部署实验和配置附录"],
            "question": "近期工作是否补足了代表作未覆盖的设备或推理设置？",
            "role": "近期工作"
          }
        ]
      },
      {
        "name": "运行时与算子优化",
        "notes_path": "notes/runtime-optimization.md",
        "papers": [
          {
            "pool_id": "p00002",
            "title": "示例论文 B",
            "paper_ref": null,
            "read_locations": ["算子实现", "评测环境与延迟表"],
            "question": "报告的收益在多大程度上依赖算子实现和计时口径？",
            "role": "代表作"
          }
        ]
      }
    ],
    "budget": {"papers_to_read": 3},
    "approved": true
  }
}
```

## 进度、变更和续做

`progress.status` 用 `planned`、`in_progress`、`partial` 或 `completed`。完成指本次约定的范围已完成。已完成批次和待做事项都记录步骤、批次、路径；待做事项额外写具体的下一步。来源故障及未补范围说明原因并指向相应记录。

下面是同一调研在 **Step 2 查询已保存、论文池尚未合并** 时的状态。时序仅用于演示各次更新，真实文件保留实际进度。续做时核对文件和 `merged_from`，然后从合并继续。

```json
{
  "progress": {
    "status": "partial",
    "completed_batches": [
      {"step": 2, "batch": "representative-routes", "path": "search/representative-routes.json"},
      {"step": 2, "batch": "recent-preprints", "path": "search/recent-preprints.json"}
    ],
    "remaining": [
      {"step": 2, "batch": "merge-pool", "path": "pool.json", "next_action": "运行 merge_pool.py，确认两批文件已并入，并复核待定和冲突记录"}
    ],
    "source_failures": []
  }
}
```

方案发生变化时，在 `changes[]` 记录日期、原因、调整前后的范围或预算及用户确认情况。在确认前把拟议修改记为待确认，执行仍按最后获批的方案。确认后更新相应计划并保留变更记录。论文版本或判断变化也可在这里注明受影响的批次和文件。续做时保留原始查询、既有笔记和更正依据。

例如，用户同意增加一轮近作补查后，在 `changes[]` 追加下列记录，并把新查询组及预算写回方案。未确认时将 `user_confirmation` 记为待确认，保留正在执行的获批方案。

```json
{
  "date": "2025-09-01",
  "step": 1,
  "reason": "近期预印本检索发现运行时优化可能使用了另一组术语",
  "before": {"followup_max_requests": 2},
  "after": {"followup_max_requests": 4},
  "user_confirmation": "已确认增加两次查询，日期窗口不变",
  "affected_files": ["spec.json", "search/recent-runtime-followup.json"]
}
```
