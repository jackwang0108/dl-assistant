# 目标 5：ingest-results（处理一批实验结果）

## 何时用

收到 CPE 的首次回包或后续修订时，先处理已核实且适用于稿件的部分。按批次和修订登记结果，例如先填主表，对仍缺数据的分析保留待办。

## 读哪些

- 回包入口 `paper-results.json`、所引用的获批 plan 和 run-spec 快照，以及实际证据。按[记录字段说明](../../../code-paper-experiment/references/records.md)核批次、修订、实验和读数身份。
- `_draft/paper-state.json` 的 `experiments.data_dependencies`（本批数据用于哪些论点、章节或图表）。
- `_draft/visuals/manifest.json` + 各数据可视化 doc（`_draft/visuals/<id>.md`）。
- `_draft/blueprint.md`（claim 对照）+ `_draft/experiments/plan-vN.json`（预先记录的比较与 interpretation）。
- `references/sections/experiment-writing-results.md`（结果/分析怎么写 + 全节自查）。
- `references/craft/numerical-display.md`（数据可视化工艺 + 自查）。
- `references/craft/section-self-audit.md`（写后自审子 agent 协议）。

## 子动作

1. **逐项核可用范围**。对照当前数据包格式、获批 plan 及实际实验清单。找实际运行和来源，核有效配置、权重与数据身份、对照、重复、统计口径、遗漏和偏差，区分包完整性、测量有效性与论文能用的范围。实际可核的结果可先接收，缺项与未回填的章节保留待办。
   - 数字和原主张仍对齐时，按实际证据回填。
   - 适用范围改变时，列出受影响的主张、正文和图表，交用户确认实质调整。
   - 核心贡献动摇时，保存已有证据和受影响的段落，带具体未知回 iterate。其他已有授权的工作可继续。
2. **按批次、回包修订及实验 ID 对账。** 按下方命令核实际回包与之前接收的修订。逐项对照任务、执行状态、测量有效性及实际证据。查统计实际纳入的尝试、独立重复和取舍。重试沿用原重复身份。复杂分析从指定的输入和脚本抽查。新增读数补回填，更正按 `changes` 核旧值、理由和所有受影响位置。将已导入的批次、修订、包路径及实际写入的实验和统计 ID 记在已有写作日志，重复收到同一修订时据此跳过已回填项。按[实验结果写作指引](../sections/experiment-writing-results.md)写可用结果。
3. **写实验结果/分析文字**：主结果（防过度宣称）+ 消融叙述（防戏剧化）+ 分析 + 弱/负结果处理 + 三位一体（每实验回扣 claim）。
4. **写后自审（子 agent，general-purpose 禁 Explore）**：跑 `experiment-writing-results.md` 全节自查 + 句段、字词和常见生成式写作问题三类写作要求 + **诚实性**（实际观察与计划的 interpretation 对照：否定信号老实写没、claim ≤ 实验所示）+ 跨节数值（results 数字 vs blueprint claims + 已写节 digest 的 key_numbers）。不过回 ③。
5. **数据图：根据实际实验数据详细设计 + 产图**：遍历本批涉及的 dataviz 条目（manifest status=intent）——先详细设计（示例锚定：问用户有没有参照，没有搜同 venue 论文同类图；抉择程序定图类型 + 元素，**根据实际实验数据**，补进 `<id>.md`）→ 当场写 `_draft/scripts/plot_<名>.py`（seaborn 默认 / matplotlib 兜底，**加载 paper palette 不自挑色**）出**快稿预览** → 用户看预览图后确认（并入 ⑫ 确认点）→ 正式导出 svg+pdf。读 `numerical-display.md`。**数据图绝不用生成式 AI**（避免图表出现未经实测的数据）。
6. **按已核对的实际读数填表。** 根据有效的比较组与统计量定表结构，写入 `tables/<id>.tex` 并从正文引用。对缺组的比较保留未决记录。只有已核且含义相同的统计量才在不同位置共用同一个值。
7. **图/表产出后自检**（主 agent）：跑 `numerical-display.md` 自查（数据保真 / 编码类型对 / mark 规范 / 可读）+ **引用句对齐**（图/表画的跟正文引用句说的对得上）。
8. **占位替换 / 填入核对过的实际结果**：图——方框占位替换成真图；表——注释占位替换成 `\input{tables/<id>}`（结构 + 真数字已在 ⑥ 一次完成）。
9. **回填 Intro / Abstract 数字**（如本批涉及）。
10. **同步更新数值来源。** 同一个比较和统计量在摘要、引言、结果及图表中保持一致。更新节摘要里的 key_numbers，并在 `_draft/canonical-values.json` 登记实际使用的数值、来源和适用章节。来源能定位到计划版本、实验 ID、读数或统计入口。后续回包先对照实际运行和上次导入范围，新增或更正受影响的条目。
11. **验证实际稿件**。按工程配置编译、渲染并报实际页数。验证受阻时保存草稿及待核项。提交及同步按实际授权，详见 `latex-landing.md`。
12. **确认点：用户审**——对得上实际、数字对、图对。

## 检查回包

变量换成实际 skill 目录与回包目录。首次导入用第一条。已导入前一修订时用第二条核对两次交付。

```bash
bash "$cpe_skill_dir/scripts/check-run-artifacts.sh" --pkgdir "$handoff_dir"
bash "$cpe_skill_dir/scripts/check-run-artifacts.sh" --pkgdir "$handoff_dir" --previous "$previous_dir"
```

检查结果用于定位文件、身份、对账和有限复算。若返回 3，读 `UNCHECKED` 项，记录接收端暂不可查的 W&B 离线恢复材料。已独立核实且适用于稿件的本地证据仍可使用。写入论文前核实际条件、原始出处及结论边界。

## 示例 · 回填目标设备比较，保留第二台设备待办

沿用[机读计划中的 edge-vision](../templates/paper-experiment-plan-template.json)。本例的已批准文件为 `plan-v1.json`，下面是一次虚构的部分回包。论文目前只主张组合配置在指定设备和所测输入上降低延迟。

| 回包或原始依据 | 实际核到什么 | 如何处理 |
| --- | --- | --- |
| `paper-results.json` 的回包身份 | 批次 edge-vision-latency，修订 1。计划和执行规格的快照及摘要与本批一致 | 保存回包、获批版本和实际执行来源 |
| `exp-target-latency` | 目标设备两组均完成。原版 12.5、12.6、12.7 ms，组合 10.7、10.8、10.9 ms。逐对差值均为 −1.8 ms。实际配置和 run 记录证实输入、预热及同步条件一致，计时时均关闭轨迹采集 | 主表目标设备行写 12.6 和 10.8 ms，并在结果段注明配对差值、测量条件和实际重复数。摘要或引言若用同一差值，沿用同一数值及范围。把这些值及其实际来源登记到 `canonical-values.json` |
| `exp-second-device-latency` | 第二台设备只取得组合配置的读数。原版入口受阻，偏差和缺组记在回包及运行报告 | 已有读数保留在实验记录。附录的设备内差值留待确认，数据依赖保持待办。恢复该设备的原版入口后，再核是否可以按原口径补测 |

本次将目标设备比较的数据依赖标为已回填，保存仍缺的第二台设备原版对照。向用户说明目前支撑的表述和还缺的材料。后续若收到同批修订 2，核上一回包摘要和两组实际记录。第二台设备取得三个有效配对后，用实际读数复算新增差值，再回填附录。目标设备原统计沿用同一 ID 和实际出处。若原值被更正，按 `changes` 同步受影响的正文、图表和数字来源。

如果作者原来想声称跨设备通用，先复核并审阅收窄到目标设备后的表述。若随后取得的**目标设备有效对照**稳定显示方向相反，使论文赖以成立的收益判断动摇，把实测读数、运行条件和受影响的主张交 iterate。

## 产出

experiment/appendix 更新（.md + .tex）、`figures/` 用实际数据绘制的图（svg+pdf）、`tables/<id>.tex` 填入核对过的实际结果、`_draft/scripts/plot_<名>.py`、Intro/Abstract 数字回填、`_draft/canonical-values.json`（数字白名单，供 check_numbers.py 核对）。

## 状态更新

按 `batch_id` 找到 `experiments.batches` 的记录，在 `handoffs` 按修订登记回包路径、接收日期和写作日志位置。相同修订沿用原条目，已回填的实验和统计 ID 从对应日志回查。例如：

```json
{
  "revision": 1,
  "path": "_draft/experiments/edge-vision-latency/handoffs/rev-1/paper-results.json",
  "received_at": "2026-11-24",
  "writing_log_ref": "_draft/writing.log#edge-vision-latency-rev-1"
}
```

把已实际回填的数据依赖标为 `ingested`。尚缺数据或证据的章节保留原待办，逐项更新节摘要和图表台账。适用范围变化时，登记受影响的章节和需复核的提纲。核心科学判断受到影响时，带实际证据交 iterate，等研究判断明确后更新相应主张。

## 确认点

用户确认图表中的实际结果准确（对得上实际、数字对、图对）。

## 易错点

- **数据逐项核对**。先确认已有部分能支持哪些表述，再登记缺失、失败、偏差及需要补的材料。
- **按批消化，不空等**——没到的批不阻塞已到的批；写作继续推进其他节。
- **写后自审是子 agent**——实验结果是 over-claim / 戏剧化 / 外推重灾区。
- **对照计划解释实际结果。** 用原判据及其依据复核，再看执行、测量和比较是否支撑论文主张。事后发现记录来源和边界。
- **回填后核查 canonical 值一致**——abstract/intro/results 三处同一个数。
- **保留偏差和缺项。** 按实录写方法和结果，对原主张的影响单独记录。
- **脚本用 paper palette、导出 svg+pdf**（无 png）。
