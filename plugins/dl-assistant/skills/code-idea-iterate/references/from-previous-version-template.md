# 下一轮版本交接

本文件说明为什么从上一轮进入当前版本、哪些判断因证据而改变，以及本轮获准做什么。

用户确认建立下一轮取证版本后，把下方模板存为新版本目录中的 `00-from-previous-version.md`，同目录保存[机读摘要](from-previous-version-template.json)。两份文件引用确认本轮的决定记录、同一版取证方案和实际代码起点。仅讨论下一步、继续查已有材料或准备写作时，按实际决定更新 `research-assessment.md`。

## 可复制模板

```markdown
# {当前版本} ← {研究上一轮}

- **研究决定**　{决定 ID、research-assessment.md 路径及获批范围}
- **本轮材料**　{研究说明、取证方案及修订、命题快照}

## 上一轮观察与判断变化

{上一轮想区分什么，实际观察到什么。引用观察 ID、原始证据、实际条件及适用范围。写明证据改变了哪项判断、仍有哪些解释，诊断或独立核查有实质作用时引用其记录。原因尚未知时保留未知。}

## 为什么建立本轮

{要弄清哪项未知，它为何影响当前决定。写本轮选的行动、预期带回的证据、实际批准的任务和范围、停止点及待确认事项。具体设计引用 plan，其他备选引用决定记录。}

## 命题和证据的继承

{列相关命题及快照。含义不变时写沿用的 ID、历史证据及适用限制。发生变更时写旧、新 ID、变更内容和证据出处。说明停止投入的原因，并按实际证据另行判断命题。}

## 实际代码与条件的起点

{写实际核实的起点 commit、新分支、选择此起点的理由。列出本轮要复用的模型、数据、配置或基准及条件引用，区分已核实和待核。说明不匹配的条件会限制哪项解释。}
```

## 完整填写示例 · edge-vision

以下延续[先复查已有记录的决定](research-assessment-template.md#填写示例--edge-vision)。假设复查后用户在 D5 确认建立 v2，只批准核最小分派条件。示例路径均相对项目根。

```markdown
# v2-edge-vision ← v1-edge-vision

- **研究决定**　D5，ideas/decisions/D5/research-assessment.md。批准为目标输入下的实际算子分派做最小核查并建立 v2。
- **本轮材料**　ideas/v2-edge-vision/ 下的 01-idea-spec.md、02-research-plan.md（rev-1）和 claims.json。

## 上一轮观察与判断变化

Q2 想区分组合加速来自写回量下降，还是来自运行时更换算子。v1 的 OBS-02 显示，同一设备和输入下，基线 12.6 ms，组合 10.8 ms。正式计时关闭轨迹采集，另外采集的轨迹显示两组的写回量和实际算子都发生了变化。现有四组记录没有同算子、不同写回量的配对。所测设置下的配置收益已有证据，C1 的写回量解释仍缺隔离对照。见 ideas/v1-edge-vision/conclusion.json 的 OBS-02 及 exp-002-configuration-comparison 的 analysis/latency-comparison.json。

## 为什么建立本轮

已有源码显示 runtime/dispatch.py 的 select_kernel 可以请求固定分派，目标输入是否触发回退仍未知。先确认这一点能决定写回量对照是否可行。D5 只批准 T0-dispatch，在原目标设备与输入上核实际算子标识和回退行为。取得能定位的实际分派记录或确认阻塞后汇报并停止。T1-writeback 的正式对照和预算待确认，只有固定分派保留目标条件时才审阅该设计。

## 命题和证据的继承

C1 的含义、ID 和现有 insufficient_evidence 判断沿用。C2 沿用原 ID，独立检查仍待做。本轮没有修改命题或更新证据判断。v1 的读数继续用于解释配置收益，引用原始轨迹及独立核查的边界。T0-dispatch 只核 C1 所需的前置条件。

## 实际代码与条件的起点

研究上一轮是 v1-edge-vision。实际代码从已核实的 8d34a2f 建 idea/v2-edge-vision，该提交含已审阅的计时及分派入口。本轮沿用 v1 的目标设备、输入与配置口径。代码入口已核，真实回退行为及能否保持目标运行条件待 T0-dispatch 验证。
```

同一版本的 `00-from-previous-version.json` 如下。

```json
{
  "schema_version": 2,
  "version": "v2-edge-vision",
  "from_previous": "v1-edge-vision",
  "decision_ref": "ideas/decisions/D5/research-assessment.md",
  "prior_evidence": [
    {
      "observation_id": "OBS-02",
      "ref": "ideas/v1-edge-vision/experiments/exp-002-configuration-comparison/analysis/latency-comparison.json",
      "limits": "支持所测条件下的配置收益。写回量与实际算子同时变化，缺同算子配对。"
    }
  ],
  "handoff": {
    "spec_ref": "ideas/v2-edge-vision/01-idea-spec.md",
    "plan_ref": "ideas/v2-edge-vision/02-research-plan.md",
    "plan_revision": "rev-1",
    "approved_task_ids": ["T0-dispatch"],
    "pending_task_ids": ["T1-writeback"]
  },
  "claims": {
    "snapshot_ref": "ideas/v2-edge-vision/claims.json",
    "retained_ids": ["C1", "C2"],
    "changes": []
  },
  "git": {
    "implementation_parent_commit": "8d34a2f",
    "new_branch": "idea/v2-edge-vision"
  }
}
```
