# 目标 7：audit（写作质量检查，可反复跑）

## 何时用

任何想要一次全面体检的时刻：初稿齐、一批将实验结果写入论文完、改稿一轮后、投 review 前、finalize 前。**不是终点一次性动作**——milestone 级节点都该跑。

## 读哪些

- `references/craft/self-check.md`（一致性 lens 清单——纯内容一致性，给子 agent）。
- `references/craft/section-self-audit.md`（润色 lens 协议 + 「为什么要子 agent」）。
- `_draft/blueprint.md` + `paper-state.json`（蓝图↔成稿一致性）+ `_draft/experiments/plan-vN.json`（interpretation 与实际回包，核表述依据）+ `_draft/venue-contract.md`（合规）+ `_draft/visuals/manifest.json`（图表台账）。

## 检查项的 owner 划分（每样恰好一个 owner）

- **需要判断的内容检查**由未参与起草的子 agent 分别负责（见步骤 1）。
- **确定性检查**（grep/对照就能定的）→ 主 agent 自己干（子动作 2），overhead > 收益不派子 agent。
- **渲染/美观检查** → `visual-aesthetic-review.md`（随本地验证/同步节点跑，不在 audit 重复）。
- **合规终审**（匿名/format/字体嵌入/authorkit 材料）→ `writing-paper-submission`；**reviewer 通读** → `writing-paper-review`。

## 子动作

1. **并行派 3 个未参与起草的子 agent。** 每个都用 general-purpose，禁用 Explore。分别负责一致性与完整性、证据与表述、语言润色。各自读全文，任务中直接提供对应清单、检查规则片段、提纲和实验计划。每项检查结果写入 `_draft/audit/`。

    | lens | 查什么 | 给什么 |
    |---|---|---|
    | **一致性/完整性** | 跑 `self-check.md` 清单：claim 回扣（uncited_assertions / claim_drifts）/ 三位一体 / 数值 canonical / 引用完整 / 图表内容完整（caption 三段式·正文引用句·风格 palette 统一）/ 附录完整 / 符号一致 | 全文 `content/*.md` + self-check 清单 + blueprint + 已写节 digest + notation.md |
    | **诚实性** | over-claim（claim ≤ 实验所示）/ **under-claim（claim ≥ 已证的——优势有没有被满强度主张：预防性示弱措辞、局部弱结果上升为整体否定、结论以局限收尾、摘要引言里优势没有明说）**/ 弱·负结果诚实报（对照计划 `interpretation` 和实际回包，否定信号有没有老实写）/ limitations 实在不敷衍 | 全文 `content/*.md` + blueprint + `plan-vN.json`（interpretation）及 paper-results.json |
    | **润色** | 句段、字词和常见生成式写作问题三类写作要求（句段/字词/AI）+ 英文打磨；标出可能改变原意的修改（meaning-risk） | 协议见 `section-self-audit.md` 二 |

    诚实性 lens 报法：`## over-claim 命中` / `## under-claim 命中` / `## 弱负结果隐瞒` / `## limitations 不实` / `## 结论`——每条位置 + 问题 + 改法。同等重视夸大结论和低估已有证据的问题。
2. **主 agent 自己查的（确定性检查，不派子 agent）**——**先跑脚本，手工只补脚本未覆盖项**：
   - **脚本层**：`python <writing-paper-skill目录>/scripts/run_checks.py <论文根> all`（在论文工程所在仓库根执行；脚本与 cwd 无关，吃论文根路径）——一次跑完全部确定性检查并出汇总报告（label/\ref + 裸编号、引用 cite↔bib + references.json 字段与 section 一致性、AI 硬正则、prose 数字白名单核对、venue 硬合规项），有硬失败 exit 非零。**绿脚本 = 该项接受标准**；报告原样贴进 audit findings。
   - **蓝图↔成稿一致性**：总论点/contribution/每节叙事任务跟实际写的对得上吗？脱节 → 标「蓝图脱节」，建议回 design-story。
   - **venue 合规**：对照 `venue-contract.md`——页数（当前 vs 页限）、匿名纪律（无身份泄露写法）、强制章节齐没齐（对照 backlog 里 venue-contract 项；机读部分脚本已查，这里判 prose 级要求）、图表规范。
   - **页数报告**：当前页数 vs 页限（逐节 + 全文）——超多少摆出来（信息不是警告；删减或移入附录是 finalize 定稿时压缩篇幅的事）。
3. **十分钟读者测试**（子 agent 或主 agent 模拟 skim）：只读 title / abstract / intro / Figure 1 / 全部图表 caption——能不能五到十分钟内把故事讲全（问题→方法→结果）？**读完记住的是不是最有证据支持的核心贡献（而不是局限或过程）**？讲不全或记错重点 → 定位断在哪（intro 没收束？首图信息量不够？caption 不自足？优势没明说？），生成修订项进 backlog。审稿人就是这么 skim 的。
4. **主 agent 合并 findings**（去重、排优先：诚实性 > 一致性 > 合规 > 润色）+ 修内容问题 + 复现信息 checklist（配置/超参/数据指针/code release 齐？缺的补或标）。**请用户确认**可能改变原意的修改（meaning-risk）。
5. 修不完/要回写的项进 backlog（type=write-section 等），别当场全堆着改。

## 产出

audit findings（合并后的清单，落 `_draft/audit-<日期>.md`）+ 修复 + backlog 新项。

## 状态更新

backlog 新项；受影响节 status 置 needs-revision；页数消耗刷新。

## 确认点

可能改变原意的修改（meaning-risk）请用户确认。

## 易错点

- **独立检查只分派需要判断的内容**——机械检查（label/页数/合规）主 agent 干（确定性，overhead > 收益）；其中 label/\ref、裸编号、引用、AI 硬正则、数字白名单已脚本化（`run_checks.py`），别再手工 grep 重复造轮子，手工只补脚本未覆盖的 prose 级判断；渲染检查归 visual-aesthetic-review，别在 audit 重复跑。
- **诚实性 > 一致性 > 合规 > 润色**——别先修措辞后修 over-claim。
- **润色不补内容**——要补内容回 write-section（hard rule）。
- **读者测试只 skim**——别读着读着变成全文精读，测的就是第一印象。
- **audit 出的问题进队列**——audit 是体检不是手术台，大改动走对应目标。
