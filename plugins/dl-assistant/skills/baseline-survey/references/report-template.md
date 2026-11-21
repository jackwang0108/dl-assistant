# 选型报告模板（baseline-survey）

产出两个文件，放 `docs/baseline-survey/<日期>-<slug>/`：

- **`baseline-survey.json`**：机读交接区，`code-project-setup` 直接消费。
- **`report.md`**：人读详解（对比表 / 各候选详情 / 风险 / 推荐 / handoff），引用 json。

> SKILL 讲产出流程，本份是两个文件的模板。

---

## baseline-survey.json（机读）

> 只放客观事实 + 决策记录；推荐在 `recommendation`，最终选哪个 repo 由人定——**拍板后回填 `decision`**。`code-project-setup` 启动时读 `decision.repo`（未回填则由用户现场指认），再读对应 `candidate` 字段。

```json
{
  "direction": "<方向 / 目标论文 slug>",
  "intent": "reproduce | improve",
  "idea_form": "predecessor_improve | insight_combination（前驱改进型 / 组合 insight 分析先行型）",
  "resource_constraint": "<单卡 / 8卡 / ...>",
  "paper_metrics": [
    { "metric": "<如 mAP>", "value": "<论文值>", "dataset": "<数据集/split>", "source_page": "<出处页码>" }
  ],
  "recommendation": {
    "repo": "<agent 推荐的 repo>",
    "reason": "<一句话：结合意图 / 资源 / 四维事实 + 执行链评估；若与 idea-find 草稿初步建议不一致，这里说明>"
  },
  "decision": {
    "repo": "<用户最终选定的 repo>",
    "repo_role": "baseline | substrate（对打 baseline / 实验基座——CPS 透传、CPR 据此定复现目标）",
    "reason": "<用户一句话理由>",
    "date": "<YYYY-MM-DD>"
  },
  "candidates": [
    {
      "repo": "<repo 名>",
      "url": "<GitHub / HuggingFace URL>",
      "repo_role": "baseline | substrate",
      "official": true,
      "weights": { "available": "直链可下 | 需申请 | 无", "url": "<权重链接>", "aligns_code_version": "true | false | 未知" },
      "license": "<MIT / 未声明 / ...>",
      "dataset": { "version": "<v2 / ...>", "aligns_paper": "true | false | 未知" },
      "exec_chain": {
        "train": "<train.py:main → build_model() → forward() → compute_loss() → backward()>",
        "eval": "<eval.py:evaluate → load_checkpoint() → forward() → coco_eval()>",
        "data": "<dataset.py:__getitem__ → transforms → collate_fn>"
      },
      "method_insertion_point": "<意图=改进时：方法接在哪条链哪一环；复现则留空>",
      "env_deps": { "key_deps": "<关键依赖 + 版本>", "compile_landmines": "<编译型地雷如 mmcv/flash-attn；无则空>", "uncommon": "<不常见库一句解释；无则空>" },
      "build_cost": "低 | 中 | 高",
      "adapt_cost": "<近亲 repo 的改造成本；现成 repo 留空>",
      "key_risks": ["<风险1 一句话指针>", "<风险2>"]
    }
  ]
}
```

字段说明（json 无注释，写在这里）：

- `intent`：为 `improve` 时各 candidate 必须带 `method_insertion_point`。
- `idea_form`：idea 形态——`predecessor_improve`（前驱改进型，选对打 baseline）/ `insight_combination`（组合 insight 分析先行型，选实验基座）。`repo_role`（candidate 与 decision 上都有）：`baseline` / `substrate`——CPS 透传、CPR 据此定复现目标（论文表格行 vs 基座自报参考数字）。
- `paper_metrics`：论文报告的主指标，**复现意图必填**——code-paper-reproduction 的验收基准（指标链的起点，见「指标契约」）。
- `decision`：**用户拍板后回填**——选型决策落盘可回溯，code-project-setup 直接读。
- `exec_chain`：`文件:函数` 级，远程读文件推断的骨架（未运行验证）。
- `build_cost`：接入成本。
- `key_risks`：一句话指针，详见 report.md「关键风险与坑」。

---

## report.md（人读详解）

```markdown
# Baseline 选型报告：[方向 / 目标论文 slug]

> 由 baseline-survey 本地产出的纯调研尽调。**机读交接在 `baseline-survey.json`**；本份是人读详解。
> 只核查看得见的事实、远程读文件，未 clone / 未下载 / 未跑——执行链是推断的骨架，"真能复现吗"由中期 code-paper-reproduction 在服务器上验。

## 调研锚点

- 方向 / 目标论文：[...]
- 意图：复现 / 改进（影响尽调侧重）
- 资源约束：[单卡 / 8卡 / ...]
- 种子线索来源：idea-find 草稿 [路径] / 用户指定 [repo或论文]
- 论文报告的主指标（复现意图必填）：[metric = 值 @ 数据集/split（出处页码）——code-paper-reproduction 的验收基准]

## 候选 baseline 对比表（客观事实）

| 候选 repo      | 官方?    | 活跃度 | star | 权重     | license | 数据集版本      | 社区复现      | 接入成本 | 改造成本\*     |
| -------------- | -------- | ------ | ---- | -------- | ------- | --------------- | ------------- | -------- | -------------- |
| [repo A]       | 是       | 近1月  | 1.2k | 直链可下 | MIT     | v2,与论文一致   | 多人复现成功  | 低       | —              |
| [repo B]       | 否(三方) | 半年前 | 800  | 需申请   | 未声明  | v1,与论文有出入 | issue多报失败 | 中       | —              |
| [repo C(近亲)] | 否(祖先) | ...    | ...  | ...      | ...     | ...             | ...           | ...      | 中改:需加X模块 |

> \*改造成本列仅用于血缘溯源的「近亲 repo」（论文无可直接复现实现时）；现成 repo 标"—"。
> 表里只放查证到的事实，每个判断可追溯到 repo 页面 / issue / 读过的文件。查不到的标"未知"，不编。

## 各候选尽调详情

> 详尽、技术化——用户懂技术，要能据此判断"接手顺不顺、改起来疼不疼"。代码质量部分尤其落到读过的真实文件，并给出执行链骨架。

### [repo A]

**代码质量与可接入性**（重点）

- **环境依赖**：[关键依赖 + 版本；不常见库逐个解释；依赖地雷]
- **执行链骨架**（`文件:函数` 级，未运行验证）：
    - 训练链：`train.py:main → build_model() → Model.forward() → compute_loss() → loss.backward()`
    - 推理/eval 链：`eval.py:evaluate → load_checkpoint() → Model.forward() → coco_eval()`
    - 数据链：`dataset.py:__getitem__ → transforms → collate_fn → DataLoader`
    - 方法接入点（意图=改进时）：[你的方法接在哪条链哪一环、那一环干不干净、有无扩展点]
- **按需深挖**：[可读性 / 可扩展性 / 工程化 / 复现设施 / 资源足迹 / 依赖健康 / 社区健康 / 加载链路——挑相关的写]
- **接入成本结论**：[低/中/高 + 卡点]

**权重 & license**：[可得性 / 链接 / license / 与代码版本是否对齐]
**数据集版本**：[版本 / 预处理协议是否对齐论文 / 已知数据问题]
**社区复现**：[复现成功/失败记录、链接]

### [repo B] …（同上结构）

## 关键风险与坑

[把尽调发现的硬伤集中列出：权重失效、license 不可用、数据集对不上、复现失败潮、依赖地雷等。
这些是后续 code-project-setup / code-paper-reproduction 要重点提防的。]

## Agent 推荐

[基于客观事实给推荐：我推荐 [repo X]，因为 [结合意图(复现/改进)、资源约束、四维事实 + 执行链评估]。
若与 idea-find 草稿初步建议不一致，显式说明：草稿建议 Y，尽调后我推荐 X，因为…]

> **最终决定由你做。** 以上是基于客观尽调的推荐，不是结论。你可能有报告里没体现的偏好
> （熟悉某个 codebase、和某作者有联系、想故意挑战某个实现），这些只有你知道。
> 拍板后把最终选定回填 `baseline-survey.json` 的 `decision` 字段（repo + 一句话理由）。

## Clone 卡（最终交付）

> 本报告的落点：拍板后拿着它直接去服务器开 `code-project-setup`，不用再翻正文。

- **clone**：<repo URL>（建议 commit / tag：<...>）
- **角色**：对打 baseline / 实验基座（= `decision.repo_role`）
- **权重**：<下载链接 / 方式 / 需申请>
- **数据集**：<版本 / split / 下载源>
- **已知坑**：<「关键风险与坑」里与 setup 最相关的 2-3 条>
- **CPR 对齐目标**：<前驱改进型：论文表格行（`paper_metrics` 指针）/ 基座型：基座自报参考数字（哪个模型 @ 哪个 benchmark = 多少，出处）>

## Handoff（下一步）

- **拍板后先回填 `decision`**：选型决策落盘可回溯，`code-project-setup` 启动直接读 `decision.repo`，不用现场再问。
- 选定后，把本报告 + `baseline-survey.json` + idea-find 草稿作为跨机器交接物，需要时找用户弄到服务器（不绑传输方式）。
- 中期 `code-project-setup` 读 `baseline-survey.json` 把选定 repo 跑起来（本报告「关键风险与坑」是它要提防的）。
- 再用 `code-paper-reproduction` 验证它真能复现论文性能。
- `code-idea-execution` 选对比 baseline 时以本报告为客观依据，不再凭空选。
```
