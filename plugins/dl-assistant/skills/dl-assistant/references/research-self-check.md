# 关键行动前的研究自查

三个skill在主流程的指定位置执行，不能只在最后补写“通过”。自查不是独立核查，也不是科学质量认证；不要求用户逐项再确认，不默认派子agent。

## 检查项与时机

| skill / stage | 必须检查的ID | 要回答什么 |
| --- | --- | --- |
| idea-find / candidate | problem、hypothesis、reasoning、value、alternatives | 是否已从主题/目标走到明确问题；假设或探索未知是什么；推理支持到哪里；成立后的新增；反对证据/替代解释及区分办法。 |
| idea-find / handoff | problem、hypothesis、reasoning、value、alternatives、design、interpretation、budget | 除上述内容，还要检查设计能否回答、各种结果如何改变判断、实际批准投入及未知。 |
| code-idea-execution / pre_run | implementation、comparison、provenance、authorization | 实际diff/测试与批准设计对应；数据/划分/对照/统计可比；设计/代码/配置/模型/数据可追溯；用户代码审阅与具体运行范围授权。 |
| code-idea-execution / handoff | execution_state、data_validity、inference、deviations、traceability | 完成状态/缺失；数据有效范围；假设支持不超证据；全部尝试/偏差；复现与原review来源。 |
| code-idea-iterate / next_step | belief_update、competing_explanations、current_value、next_evidence、evidence_history | 认识更新；最强反证和竞争解释；当前范围价值；下一步减少的重要未知与成本；命题/证据历史。 |
| code-idea-iterate / transition | knowledge、evidence、novelty_value、remaining_work、recommendation | 五项研究与写作判断，详见research-transition.md；停止与写作分别判断，不把停止认作具备写作条件。 |

## 涉及研究条件时必须具体核查

按 [研究条件规则](research-conditions.md)，idea-find 在 reasoning/design/interpretation/budget 中核关键条件分类、推理与目标验证安排；execution 在 implementation/comparison/provenance 中核实际落实，在 inference/deviations 中核结果范围与实际变更；iterate 在 competing_explanations/current_value/next_evidence 和 evidence/remaining_work 中核条件差异、缩小后价值及目标证据缺口。将条件记录和实际配置/证据列为相关输入，改变后重新自查。

关键条件被破坏时不能把原假设检验标为可继续；影响未知可批准有边界的检查或探索，不能用其结果确认/淘汰目标假设。不是每个未知都阻塞实验，需明确被允许的具体行动。现有结构检查器不判断这些科学内容是否正确，退出 0 不等于条件审查通过。

## 使用 W&B 时的具体核查

启用时按 [共同记录](../../wandb/references/experiment-records.md) 纳入现有自查，不新增阶段：execution 的 provenance/authorization 核内网实例、实际设计/代码/config/run身份和上传范围；traceability/deviations 核全部尝试、同步/失败、本地输出和读回快照。iterate 的 evidence_history/competing_explanations/evidence 核应纳入运行集合、配置/协议差异、选择规则、查询采样/缺失和精确产物来源。不能因 finished、最高分、SDK退出或文件检查通过认证科学结论。需要新的正式分析仍交execution。

## 结果必须影响行动

逐项写：当前判断 → 实际依据/来源 → 未知 → 对当前行动的影响。不是关键词匹配或重复主张。主动问：哪条观察最不支持我？相同观察还有什么解释？成功后究竟多知道什么？是否因已投入很多而继续？

- clear：当前行动所需依据充分，不表示假设已真。
- limited：未知/限制真实存在，但不妨碍这个明确行动；说明为什么。例如无先例但推理可检查、问题有意义，可以继续探索，不能写成已经确认机制。
- needs_revision：缺陷影响当前行动，先修正/讨论。比如交实验时问题不明确、比较无法解释、未批准设计变化，不能边记缺陷边开跑。

总体decision=continue / continue_with_limits / revise。任一needs_revision则revise；有limited不能无条件continue。revise后仍可保存、报告问题或交接待解决事项，但不能把被阻止的目标行动标成已就绪。研究不确定不是自动缺陷；允许停止、暂停或探索时仍有未决，判断应针对next_action而非要求全知。

## 保存与核验

在各自研究/版本/决定目录下保存 `self-checks/<阶段>-<唯一标识>.json`。简短人读说明可直接在现有报告里引用，不新增一整套报告。当前文件先保存，再记输入快照；不要将自查文件自身或含其hash的循环文件列为输入。原输入变化后在执行目标行动前重新检查并保存新记录，不改旧记录假装当时已通过。历史记录过期只表示不能复用为当前授权，不否定当时事实。

SHA256是文件内容的校验值，用来发现输入是否改变，不证明文件内容正确。

结构如下，实际值必须来自当前工作；不直接复制示例作为通过记录：

```json
{
  "schema_version": 1,
  "skill": "idea-find",
  "stage": "candidate",
  "subject": "Q1/H1：当前问题和候选的具体版本",
  "checked_at": "实际检查时间及其时区",
  "inputs": [{"path": "notes.md", "sha256": "实际文件的SHA256"}],
  "checks": [{
    "id": "problem",
    "status": "needs_revision",
    "finding": "说明具体缺陷，不能只写通过/符合",
    "basis_refs": ["notes.md#具体位置"],
    "unknowns": ["当前未定义的对象或条件"],
    "effect": "先澄清问题，不能交研究实验"
  }],
  "decision": "revise",
  "next_action": "修订Q1的定义，保留原候选"
}
```

示例只展示一项，实际须含所选stage全部必需项。basis_refs引用实际笔记/证据的文件位置（路径相对--root，可用#位置）或真实来源URL；未取得的信息写unknowns并引用说明缺失的笔记，不伪造来源。inputs至少列当前问题/批准设计/结果分析中与本次行动有关的文件；执行还列关键代码/config或其实际diff。相关输入或代码变化后不能复用旧自查，不能只选择不变的无关文件让脚本通过。不存在文件不通过；跨机器来源无法访问时明确缺失及其影响，不凭指针声称已核查。

```bash
python3 <skills目录>/dl-assistant/scripts/check_research_self_check.py --record <自查.json> --root <项目根> --skill idea-find --stage candidate
```

脚本要求Python 3.9+、仅用标准库、只读本地文件、不联网。退出0表示必需记录、文件快照和声明的行动一致；1表示记录错误、过期或声明需修正；2表示用法错误。不判断论文价值、推理或授权真实性，不验证URL内容，不证明所选输入完整。不要为了退出0改状态或补假依据；修正实际问题后重新检查。Python不可用/来源缺失时说明未完成检查及影响，不能宣称通过或绕过受阻行动。

自查在相应步骤完成后，execution的独立证据核查仍按原契约进行。能力更弱的agent也可能填出形式完整的错误判断，因此用户审阅、原始证据和实际行为评估仍必要，不能把结构检查说成解决了创造性或研究判断质量。

维护时用 [具体案例](research-self-check-cases.md) 检查行动是否随缺陷改变；这不是独立行为验证。
