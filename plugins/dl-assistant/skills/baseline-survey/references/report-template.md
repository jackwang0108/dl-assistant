# 选型报告模板（baseline-survey）

产出两个文件，放 `docs/baseline-survey/<日期>-<slug>/`：

- **`baseline-survey.json`**：供下游技能读取的记录，`code-project-setup` 直接读取。
- **`report.md`**：供用户阅读的详细报告（对比表 / 各候选详情 / 风险 / 推荐 / handoff），引用 json。

> SKILL 讲产出流程，本份是两个文件的模板。

---

## baseline-survey.json（机读）

> 只放客观事实 + 决策记录；推荐在 `recommendation`，最终选哪个 repo 由人定——**用户确认选择后回填 `decision`**。`code-project-setup` 启动时读 `decision.repo`（未回填则由用户现场指认），再读对应 `candidate` 字段。

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
- `idea_form`：idea 形态——`predecessor_improve`（前驱改进型，选用于比较的基线代码）/ `insight_combination`（结合多篇论文发现并先做分析的研究，选用于分析实验的代码仓库）。`repo_role`（candidate 与 decision 上都有）：`baseline` / `substrate`——由 code-project-setup 原样传递，供 code-paper-reproduction 选择复现目标，即论文表格中的对应结果或仓库维护者报告的参考结果。
- `paper_metrics`：论文报告的主指标，**复现意图必填**——code-paper-reproduction 的验收基准（后续复现核对的依据，见「指标契约」）。
- `decision`：**用户用户确认选择后回填**——选型决策落盘可回溯，code-project-setup 直接读。
- `exec_chain`：`文件:函数` 级，远程阅读文件后梳理的调用关系（未运行验证）。
- `build_cost`：接入成本。
- `key_risks`：一句话风险摘要，详见 report.md「关键风险」。

---

## report.md（供用户阅读的详细报告）

```markdown
# Baseline 选型报告：[方向 / 目标论文 slug]

> 由 baseline-survey 本地产出的纯调研尽调。**机读交接在 `baseline-survey.json`**；本份是供用户阅读的详细报告。
> 根据远程查阅的文件梳理主要调用关系，未 clone、下载或运行候选仓库。中期由 code-paper-reproduction 在服务器上验证复现结果。

## 调研所需的信息

- 方向 / 目标论文：[...]
- 意图：复现 / 改进（影响尽调侧重）
- 资源约束：[单卡 / 8卡 / ...]
- 初始搜索线索来源：idea-find 草稿 [路径] / 用户指定 [repo或论文]
- 论文报告的主指标（复现意图必填）：[metric = 值 @ 数据集/split（出处页码）——code-paper-reproduction 的验收基准]

## 候选 baseline 对比表（客观事实）

| 候选 repo      | 官方?    | 活跃度 | star | 权重     | license | 数据集版本      | 社区复现      | 接入成本 | 改造成本\*     |
| -------------- | -------- | ------ | ---- | -------- | ------- | --------------- | ------------- | -------- | -------------- |
| [repo A]       | 是       | 近1月  | 1.2k | 直链可下 | MIT     | v2,与论文一致   | 多人复现成功  | 低       | —              |
| [repo B]       | 否(三方) | 半年前 | 800  | 需申请   | 未声明  | v1,与论文有出入 | issue多报失败 | 中       | —              |
| [repo C]       | 否（论文实现所基于的仓库） | ...    | ...  | ...      | ...     | ...             | ...           | ...      | 中改:需加X模块 |

> \*目标论文缺少可直接复现的实现时，查找论文实现所基于的仓库，并为它填写改造成本。可直接复现的仓库标「—」。
> 表里只放查证到的事实，每个判断可追溯到 repo 页面 / issue / 读过的文件。查不到的标"未知"，不编。

## 各候选尽调详情

> 为每个仓库说明接手需要哪些准备和改动可能涉及哪些模块。代码质量分析要引用读过的文件，并梳理主要调用关系。

### [repo A]

**代码质量与可接入性**（重点）

- **环境依赖**：[关键依赖 + 版本；不常见库逐个解释；已知的依赖安装或版本兼容问题]
- **主要调用关系**（`文件:函数` 级，未运行验证）：
    - 训练链：`train.py:main → build_model() → Model.forward() → compute_loss() → loss.backward()`
    - 推理/eval 链：`eval.py:evaluate → load_checkpoint() → Model.forward() → coco_eval()`
    - 数据处理流程：`dataset.py:__getitem__ → transforms → collate_fn → DataLoader`
    - 方法接入点（意图=改进时）：[你的方法接在哪条链哪一环、该处代码是否易于修改、有无扩展点]
- **按需核查**：[可读性 / 可扩展性 / 工程化 / 复现设施 / 资源需求 / 依赖维护情况 / 社区维护情况 / 加载链路——挑相关的写]
- **接入成本结论**：[低/中/高 + 主要难点]

**权重 & license**：[可得性 / 链接 / license / 与代码版本是否对齐]
**数据集版本**：[版本 / 预处理协议是否对齐论文 / 已知数据问题]
**社区复现**：[复现成功/失败记录、链接]

### [repo B] …（同上结构）

## 关键风险

[把尽调发现的严重问题集中列出：权重失效、license 不可用、数据集对不上、多条社区复现失败记录、已知的依赖安装或版本兼容问题等。
这些是后续 code-project-setup / code-paper-reproduction 要重点提防的。]

## 选型建议

[基于客观事实给出推荐：我推荐 [repo X]，因为 [结合意图(复现/改进)、资源约束、四维事实 + 执行链评估]。
若与 idea-find 草稿初步建议不一致，显式说明：草稿建议 Y，尽调后我推荐 X，因为…]

> **最终决定由你做。** 以上是基于客观尽调的推荐，不是结论。你可能有报告里没体现的偏好
> （熟悉某个 codebase、和某作者有联系、想故意挑战某个实现），这些只有你知道。
> 用户确认选择后把最终选定回填 `baseline-survey.json` 的 `decision` 字段（repo + 一句话理由）。

## Clone 卡（最终交付）

> 用户确认后，`code-project-setup` 按卡片所列的仓库、版本和资源信息准备服务器环境。

- **clone**：<repo URL>（建议 commit / tag：<...>）
- **角色**：用于比较的基线代码 / 用于分析实验的代码仓库（= `decision.repo_role`）
- **权重**：<下载链接 / 方式 / 需申请>
- **数据集**：<版本 / split / 下载源>
- **已知风险**：<「关键风险」里与 setup 最相关的 2-3 条>
- **code-paper-reproduction 要复现的参考结果**：<前驱改进型：论文表格行（`paper_metrics` 指针）/ 用于分析实验的代码仓库：仓库维护者报告的参考结果（哪个模型 @ 哪个 benchmark = 多少，出处）>

## 交接与后续步骤

- **用户确认选择后先回填 `decision`**：选型决策落盘可回溯，`code-project-setup` 启动直接读 `decision.repo`，不用现场再问。
- 选定后，把本报告 + `baseline-survey.json` + idea-find 草稿作为跨机器交接物，需要时请用户把文件传到服务器（不绑传输方式）。
- 中期 `code-project-setup` 读 `baseline-survey.json` 把选定 repo 跑起来，并核查本报告列出的关键风险。
- 再用 `code-paper-reproduction` 按仓库用途验证相应的参考结果。
- `code-idea-execution` 选对比 baseline 时以本报告为客观依据，不再凭空选。
```
