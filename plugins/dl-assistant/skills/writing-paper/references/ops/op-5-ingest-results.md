# 目标 5：ingest-results（消费一批 CPE 数据）

## 何时用

一批 CPE 实验数据包到达。**按批 ingest，没有「等全部跑完」这个状态**——state 的 `experiments.batches` 里哪批 received 了，就消化哪批。同一批可以只消化一部分（比如先填主表，分析后补），剩下的留在 backlog。

## 读哪些

- CPE **`experiments-actual.json`**（实际跑了哪些，含加/改）+ **`results.json`**（结果）+ **`pkg-meta.json`**（验收清单）——schema 见 `code-paper-experiment/references/templates/data-pkg-schema.json`，验收照它机械核对。
- `paper-state.json` 的 `data_dependencies`（这批数据喂谁）。
- `_draft/visuals/manifest.json` + 各数据可视化 doc（`_draft/visuals/<id>.md`）。
- `_draft/blueprint.md`（claim 对照）+ `_draft/experiments/plan-vN.json`（expected_signal，诚实性对照）。
- `references/sections/experiment-writing-results.md`（结果/分析怎么写 + 全节自查）。
- `references/craft/numerical-display.md`（数据可视化工艺 + 自查）。
- `references/craft/section-self-audit.md`（写后自审子 agent 协议）。

## 子动作

1. **数据到达验收**（主 agent）：照 data-pkg-schema.json 机械核对——本批 must 全 done（`pkg-meta.json` 验收清单）？`results.json` 每条目 `n_seeds` / `signal_verdict` / `output_to_paper` 字段齐？数字在合理范围？残缺/异常 → 找用户回 CPE 补，别拿坏数据就写。
2. **按 CPE 实际说明对齐**：实际跑了哪些、CPE 加/改的补进实验节/appendix、删掉没跑的、结果分析按报告不按原 plan。读 `experiment-writing-results.md`。
3. **写实验结果/分析文字**：主结果（防过度宣称）+ 消融叙述（防戏剧化）+ 分析 + 弱/负结果处理 + 三位一体（每实验回扣 claim）。
4. **写后自审（子 agent，general-purpose 禁 Explore）**：跑 `experiment-writing-results.md` 全节自查 + 三层 craft + **诚实性**（results vs expected_signal：否定信号老实写没、claim ≤ 实验所示）+ 跨节数值（results 数字 vs blueprint claims + 已写节 digest 的 key_numbers）。不过回 ③。
5. **数据图：对着真数据详细设计 + 产图**：遍历本批涉及的 dataviz 条目（manifest status=intent）——先详细设计（示例锚定：问用户有没有参照，没有搜同 venue 论文同类图；抉择程序定图类型 + 元素，**对着真数据**，补进 `<id>.md`）→ 当场写 `_draft/scripts/plot_<名>.py`（seaborn 默认 / matplotlib 兜底，**加载 paper palette 不自挑色**）出**快稿预览** → 用户看图拍板（并入 ⑫ 确认点）→ 正式导出 svg+pdf。读 `numerical-display.md`。**数据图绝不用生成式 AI**（造假红线）。
6. **表：对着真数据定结构 + 填真**：此时才定表结构（几行几列 / 表头每列含义 / 每行含义 / best-2nd 标记）——不对着想象中的数据锁结构 → 落 `tables/<id>.tex`（正文 `\input`）并填真数字（一个 claim 一个 canonical 值）。例外：数据本就在手、write-section 时已落骨架的，核对结构是否随真实数据调整（CPE 加/改实验时同步改）。
7. **图/表产出后自检**（主 agent）：跑 `numerical-display.md` 自查（数据保真 / 编码类型对 / mark 规范 / 可读）+ **引用句对齐**（图/表画的跟正文引用句说的对得上）。
8. **占位替换 / 填真**：图——方框占位替换成真图；表——注释占位替换成 `\input{tables/<id>}`（结构 + 真数字已在 ⑥ 一次完成）。
9. **回填 Intro / Abstract 数字**（如本批涉及）。
10. **回填数字一致性核查**（主 agent）：abstract / intro / results 三处是同一个 canonical 值；不一致回 ⑨ 对齐。更新已写节 digest 的 key_numbers。**同步更新 `_draft/canonical-values.json`（数字白名单）**：从本批数据包 `results.json` 提取全部 canonical 数字（含表内值、均值±方差、百分比），每条记 `{value, source（哪个实验/表）, 允许出现的节}`——后续批次增量合并。它是 `check_numbers.py` 的白名单来源：正文 prose 里的小数/百分比不在白名单 = 可疑数字（`suspicious_number`），audit 与 finalize 机器核。
11. **本地验证**：本地编译（红修红）→ 渲 PDF → 报页数 → 本地 commit。不 push；Overleaf 同步走关键节点（见 `latex-landing.md`）。
12. **确认点：用户审**——对得上实际、数字对、图对。

## 产出

experiment/appendix 更新（.md + .tex）、`figures/` 真数据图（svg+pdf）、`tables/<id>.tex` 填真、`_draft/scripts/plot_<名>.py`、Intro/Abstract 数字回填、`_draft/canonical-values.json`（数字白名单，供 check_numbers.py 核对）。

## 状态更新

`data_dependencies` 对应项标 ingested；节 status（needs-data→drafted）；digest key_numbers 更新；manifest 条目 status 更新；backlog 关单。**否定信号触发时**：标「蓝图脱节」，建议回 design-story 重审 contribution。**优势换位触发时**：本批数据揭示比原优势锚更强的卖点（或原优势锚被证伪）→ 同样标「蓝图脱节」，建议回 design-story 换优势锚/重排故事（正向触发，见 blueprint-design 蓝图更新规则）——不围着旧故事防守。

## 确认点

填真满意（对得上实际、数字对、图对）。

## 易错点

- **数据到达先验收**——must 齐全 / 数字合理 / seed 报了才写；残缺异常找用户回 CPE 补。
- **按批消化，不空等**——没到的批不阻塞已到的批；写作继续推进其他节。
- **写后自审是子 agent**——实验结果是 over-claim / 戏剧化 / 外推重灾区。
- **结果照 expected_signal 判**——否定信号回 design-story 重审，不硬写。
- **回填后核查 canonical 值一致**——abstract/intro/results 三处同一个数。
- **按 CPE 实际说明对齐，不按原 plan**——CPE 加/改的实验要补进 section/appendix。
- **脚本用 paper palette、导出 svg+pdf**（无 png）。
