# search/<批次>.json：原始查询与筛选记录

本文件说明怎样保存一次实际检索、记录每篇候选的纳排理由，以及让主会话能复查来源、覆盖范围和合并结果。

按 [运行步骤](../workflow.md) 在调研目录的 `search/` 下为每个批次保存独立的 JSON 文件。续做、补查和重试使用新的批次文件，便于对照前后的查询。格式版本为 2。各批次汇报简要结果和文件路径，完整查询、论文观测与纳排判断以保存的批次文件为准。

## 一、保存实际执行的查询

每次调用在 `requests[]` 记一条记录。纸面计划放在 `spec.json`，这里写实际送给工具的参数和实际取得的结果。

- **MCP v2**。记录工具名和实参 `params`，包括查询、来源、日期口径和范围、排序与预算。保留返回的 `query_id`、`snapshot_id`、`source_reports`、`coverage`、`usage` 和游标，另记获取时间与实际读到的页。续页和上游补查同样记录调用及其对应快照。逐来源保留实际查询、状态和限制。接口和分页见 [paper-search](../../../paper-search/SKILL.md)。
- **HF CLI**。保存实际命令、查询上限、返回数、获取时间、日期后筛字段和范围。日期后筛的数量单独记。详见 [HF 补充检索](../hf-papers.md)。
- **数量口径**。`returned_count` 是该次调用返回的条目数，例如首批 `items.length`，不等于各来源原始命中数之和或后筛纳入数。纳入、排除与待核数按三个数组统计。

| 本地 `status` | 含义 | `returned_count` |
| --- | --- | --- |
| `not_run` | 查询没有执行 | `null` |
| `failed` | 调用失败，未取得可用结果 | `null` |
| `partial` | 有部分结果，但来源失败、结果截断或仍有待取范围 | 已返回的数量，未知填 `null` |
| `success` | 查询实际执行，按本次请求取得可用结果 | 实际数量，确实零命中才填 `0` |

这些是本地记录状态。MCP 返回中的来源状态和覆盖字段原样保留。即使本地游标用完，上游也可能还有结果。读取异常、过滤未落实或日期精度不足，分别写明实际情况。

## 二、将返回条目写入批次

| 从哪里取 | 如何填 |
| --- | --- |
| MCP `identifiers[]` | 将 `arxiv:` 和 `doi:` 标识的值分别填入 `arxiv` 和 `doi`。已核对的具体论文页面可填 `url`，来源专用 ID 保留在原始条目。 |
| MCP 原始 `items[]` | 将对应条目保存为 `mcp_item`，保留论文身份、版本、各字段出处、冲突和 `citation_counts`。例如多来源给出不同引用数时保留全部观测。一条独立、带来源的引用观测也可用 `citations`、`source`、`observed_at` 记录。 |
| HF 原始结果 | 核实 `id` 后填入 `arxiv`，原条目及日期字段随记录保存。 |
| 作者、标题和日期 | 用实际值，保留精度及含义。首次提交、更新和正式发表分别记录；HF 日期注明为 HF 观测。没有核实的日期不填猜测值。 |
| 人工初筛 | 给每条写 `reason`。按实际已读材料填写 `approach`、`abstract_notes` 和 `reading_level`（`metadata`、`abstract`、`partial_text`、`detailed`）。核对正文时可附版本与章节、页码或图表位置。 |

每条至少有可用的 `arxiv`、`doi`、`url` 或 `title`，未知字段可为空。无可用标识也无标题的原始结果记在请求记录中，说明为何无法形成候选条目。

- **纳排在这一步。** 符合本轮调研范围的候选放 `included`，明确不符合的放 `excluded`，身份或范围待核实的放 `pending`。同一条命中在同一批只进入一个数组。符合范围仍需按计划核查证据。
- **技术分类在后续步骤。** 检索批次可以写方法线索；Step 3 再依据合并结果确定分类和详细阅读方案。
- **身份合并交给脚本。** 跨批重复保留各自观测，不因重复而排除。脚本按共享标识关联，同标题仅提示可能重复。对 `identity_conflicts`、`possible_duplicates` 和合并后 `pending` 中的纳排冲突，回查原批次的身份与理由。核实后留下依据、修正记录并重新合并。

## 三、可直接合并的完整批次示例

以下使用当前 MCP v2 实测返回的查询参数、来源状态和全部 6 条候选。为便于阅读，示例的 `mcp_item` 只摘出用于演示的字段；实际保存时使用完整原条目。纳排理由按本示例的静态图像调研范围填写。将下面的 JSON 保存为 `search/latent-diffusion.json`。

```json
{
  "schema_version": 2,
  "query_group": "扩散模型种子论文与后续工作",
  "requests": [
    {
      "tool": "search_papers",
      "params": {
        "queries": [
          {
            "text": "id:2112.10752",
            "syntax": "source_native",
            "sources": [
              "arxiv"
            ]
          },
          {
            "text": "High-Resolution Image Synthesis with Latent Diffusion Models",
            "sources": [
              "semantic_scholar",
              "openalex"
            ]
          }
        ],
        "budget": {
          "max_requests": 6,
          "max_items": 12,
          "max_seconds": 25
        },
        "cache": "prefer"
      },
      "query_id": "0f5716c9729142a39ce2f4aac5d5f2eb",
      "snapshot_id": "5346708d0d9a4a3bbfa4393666d0bfe4",
      "fetched_at": "2026-11-23T14:52:32.699022+00:00",
      "status": "partial",
      "returned_count": 6,
      "next_cursor": null,
      "source_reports": [
        {
          "source": "arxiv",
          "status": "ok",
          "actual_query": {
            "search_query": "id:2112.10752",
            "start": 0,
            "max_results": 4,
            "sortBy": "relevance",
            "sortOrder": "descending"
          },
          "fetched_count": 1,
          "upstream_has_more": false,
          "limitations": [],
          "fetched_at": "2026-11-23T14:52:28.859040+00:00",
          "cache_state": "miss"
        },
        {
          "source": "semantic_scholar",
          "status": "ok",
          "actual_query": {
            "query": "High-Resolution Image Synthesis with Latent Diffusion Models",
            "limit": 4,
            "offset": 0,
            "fields": "paperId,externalIds,title,authors,year,publicationDate,abstract,venue,citationCount,referenceCount,openAccessPdf,publicationTypes,url"
          },
          "fetched_count": 4,
          "upstream_has_more": true,
          "limitations": [],
          "fetched_at": "2026-11-23T14:52:30.228536+00:00",
          "cache_state": "miss"
        },
        {
          "source": "openalex",
          "status": "ok",
          "actual_query": {
            "search": "High-Resolution Image Synthesis with Latent Diffusion Models",
            "per_page": 4,
            "cursor": "*"
          },
          "fetched_count": 4,
          "upstream_has_more": true,
          "limitations": [],
          "fetched_at": "2026-11-23T14:52:32.698938+00:00",
          "cache_state": "miss"
        }
      ],
      "coverage": {
        "local_has_more": false,
        "upstream_has_more": true,
        "truncated": true,
        "limitations": [
          "Local completion does not establish exhaustive literature coverage."
        ]
      },
      "usage": {
        "requests": 3,
        "items": 9,
        "seconds": 4.699,
        "download_bytes": 0
      }
    }
  ],
  "included": [
    {
      "title": "High-Resolution Image Synthesis with Latent Diffusion Models",
      "arxiv": "2112.10752",
      "doi": "10.1109/cvpr52688.2022.01042",
      "year": 2022,
      "published": "2022-06-01",
      "reason": "用户指定的种子论文，纳入候选；本次只初审摘要。",
      "reading_level": "abstract",
      "mcp_item": {
        "paper_ref": "arxiv:2112.10752",
        "identifiers": [
          "arxiv:2112.10752",
          "doi:10.1109/cvpr52688.2022.01042",
          "openalex:W4312933868",
          "s2:f58acfeb022ba15282ec5fc047c98010311fa9da"
        ],
        "version": "v2",
        "dates": {
          "published": "2022-06-01",
          "precision": "day"
        },
        "citation_counts": [
          {
            "source": "semantic_scholar",
            "value": 29331,
            "fetched_at": "2026-11-23T14:52:30.211506+00:00"
          },
          {
            "source": "openalex",
            "value": 37803,
            "fetched_at": "2026-11-23T14:52:32.681961+00:00"
          }
        ],
        "field_provenance": {
          "title": {
            "source": "openalex",
            "fetched_at": "2026-11-23T14:52:32.681961+00:00"
          },
          "dates": {
            "source": "openalex",
            "fetched_at": "2026-11-23T14:52:32.681961+00:00"
          },
          "version": {
            "source": "arxiv",
            "fetched_at": "2026-11-23T14:52:28.854542+00:00"
          }
        },
        "conflicts": {
          "year": [
            {
              "source": "arxiv",
              "value": 2021
            },
            {
              "source": "semantic_scholar",
              "value": 2021
            },
            {
              "source": "openalex",
              "value": 2022
            }
          ]
        }
      },
      "approach": "在潜空间运行扩散过程",
      "abstract_notes": "作者报告在预训练自动编码器的潜空间生成图像，以降低计算开销。"
    }
  ],
  "excluded": [
    {
      "title": "Align Your Latents: High-Resolution Video Synthesis with Latent Diffusion Models",
      "arxiv": "2304.08818",
      "doi": "10.1109/cvpr52729.2023.02161",
      "year": 2023,
      "published": "2023-04-18",
      "reason": "本组限静态图像生成，标题与摘要指向视频生成。",
      "reading_level": "abstract",
      "mcp_item": {
        "paper_ref": "arxiv:2304.08818",
        "identifiers": [
          "arxiv:2304.08818",
          "doi:10.1109/cvpr52729.2023.02161",
          "s2:f5a0c57f90c6abe31482e9f320ccac5ee789b135"
        ],
        "version": null,
        "dates": {
          "published": "2023-04-18",
          "precision": "day"
        },
        "citation_counts": [
          {
            "source": "semantic_scholar",
            "value": 1897,
            "fetched_at": "2026-11-23T14:52:30.211639+00:00"
          }
        ]
      }
    }
  ],
  "pending": [
    {
      "title": "SDXL: Improving Latent Diffusion Models for High-Resolution Image Synthesis",
      "arxiv": "2307.01952",
      "doi": null,
      "year": 2023,
      "published": "2023-07-04",
      "reason": "可能是后续工作，待核另一条同标题记录的身份和版本。",
      "reading_level": "metadata",
      "mcp_item": {
        "paper_ref": "arxiv:2307.01952",
        "identifiers": [
          "arxiv:2307.01952",
          "s2:d7890d1906d95c4ae4c430b350455156d6d8aed9"
        ],
        "version": null,
        "dates": {
          "published": "2023-07-04",
          "precision": "day"
        },
        "citation_counts": [
          {
            "source": "semantic_scholar",
            "value": 5845,
            "fetched_at": "2026-11-23T14:52:30.211559+00:00"
          }
        ]
      }
    },
    {
      "title": "Diffusion-4K: Ultra-High-Resolution Image Synthesis with Latent Diffusion Models",
      "arxiv": "2503.18352",
      "doi": "10.1109/cvpr52734.2025.02185",
      "year": 2025,
      "published": "2025-06-10",
      "reason": "可能与高分辨率图像生成相关，待核方法与纳入范围。",
      "reading_level": "metadata",
      "mcp_item": {
        "paper_ref": "arxiv:2503.18352",
        "identifiers": [
          "arxiv:2503.18352",
          "doi:10.1109/cvpr52734.2025.02185",
          "openalex:W4413145214",
          "s2:bf232b405cad758317ddf0114f4822c5cec23efb"
        ],
        "version": null,
        "dates": {
          "published": "2025-06-10",
          "precision": "day"
        },
        "citation_counts": [
          {
            "source": "semantic_scholar",
            "value": 87,
            "fetched_at": "2026-11-23T14:52:30.211600+00:00"
          },
          {
            "source": "openalex",
            "value": 105,
            "fetched_at": "2026-11-23T14:52:32.682213+00:00"
          }
        ]
      }
    },
    {
      "title": "SDXL: Improving Latent Diffusion Models for High-Resolution Image Synthesis",
      "arxiv": null,
      "doi": "10.48550/arxiv.2307.01952",
      "year": 2024,
      "published": "2024-05-31",
      "reason": "与另一条标题相同，标识不同，先保留并核实是否为同一工作。",
      "reading_level": "metadata",
      "mcp_item": {
        "paper_ref": "doi:10.48550/arxiv.2307.01952",
        "identifiers": [
          "doi:10.48550/arxiv.2307.01952",
          "openalex:W4383472654"
        ],
        "version": null,
        "dates": {
          "published": "2024-05-31",
          "precision": "day"
        },
        "citation_counts": [
          {
            "source": "openalex",
            "value": 4382,
            "fetched_at": "2026-11-23T14:52:32.682420+00:00"
          }
        ]
      }
    },
    {
      "title": "Latent Patched Efficient Diffusion Model for High Resolution Image Synthesis",
      "arxiv": null,
      "doi": "10.1109/cvprw67362.2025.00633",
      "year": 2025,
      "published": "2025-06-11",
      "reason": "仅根据书目信息暂不能确定是否适合作为本轮代表作。",
      "reading_level": "metadata",
      "mcp_item": {
        "paper_ref": "doi:10.1109/cvprw67362.2025.00633",
        "identifiers": [
          "doi:10.1109/cvprw67362.2025.00633",
          "openalex:W4414198496"
        ],
        "version": null,
        "dates": {
          "published": "2025-06-11",
          "precision": "day"
        },
        "citation_counts": [
          {
            "source": "openalex",
            "value": 5,
            "fetched_at": "2026-11-23T14:52:32.682581+00:00"
          }
        ]
      }
    }
  ]
}
```

再从 [运行步骤](../workflow.md) 执行合并：

```bash
python3 <skill目录>/scripts/merge_pool.py <调研目录>
```

在 `pool.json` 的 `requests` 里核对来源和覆盖，再到 `papers`、`excluded` 和 `pending` 看归档结果。用 `observations[].file`、`observations[].index` 和 `observations[].record` 找回原批次和具体观测。示例里的两条 SDXL 同名记录分别保留，`possible_duplicates` 提示人工核实。即使本例的 `next_cursor` 为空，`coverage.upstream_has_more` 仍为真，不能据此认定上游搜全。

## 四、HF 后筛如何计数

例如，[HF 补充检索](../hf-papers.md) 的实测主题查询返回 3 条，按 HF 的 `published_at` 后筛有 2 条在窗口内。请求记录写 `returned_count: 3`、`in_window_count: 2`。示例中的两条窗内论文均待核查，放 `pending`；窗外一条写明理由放 `excluded`。本批纳入数为 0，查询本身有返回。未选用 HF 时示例记录写法为：

```json
{"source": "hf_papers", "status": "not_run", "returned_count": null, "reason": "本轮方案未选用 HF"}
```
