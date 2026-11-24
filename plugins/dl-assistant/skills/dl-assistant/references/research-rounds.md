# 研究轮次登记与 Git 交接

本文件说明何时登记一轮研究、同轮多批执行怎样归档，以及怎样用 Git 找到实际代码。轮次索引保存在 `docs/research/research-rounds.json`，结构见[索引模板](research-rounds-template.json)。路径相对研究项目根，外部材料记录可取得的位置和版本。

## 1. 什么时候登记

| 情况 | 谁写、写到哪里 |
| --- | --- |
| 首次准备研究仓库 | `code-idea-prepare` 初始化缺少的索引为空数组 `{"rounds": []}`，并建立 `docs/research/PROJECT_CONTEXT.md`。已有记录沿用。跳过 prepare 时由首次接手的 execution 补建 |
| 首轮方案获批并开立 | `code-idea-execution` 保存获批的研究说明、取证方案和初始命题快照，在索引追加 v1。批准引用指向 idea-find 的 `spec.json` 中对应决定 |
| 复查已有证据，或在原问题下增补任务 | 复查和决定保存在提供证据的轮次。经确认需要新读数时，iterate 保存本轮获批的 plan 修订，execution 登记新批次。继续使用本轮索引条目 |
| 用户同意建立下一轮 | `code-idea-iterate` 在新轮目录保存获批方案和命题快照，按登记顺序在 `rounds` 末尾追加条目。在提供证据的上一轮保存决定，新轮的 `approval_ref` 引用该决定 |
| 整轮收尾交接 | `code-idea-execution` 补实际交接 commit 和 tag（有时）。只交回一批结果时，更新本轮结论、实验台账和批次记录 |

`previous_round` 记录研究上的上一轮。通常是上一个已登记的轮次，由本次研究决定确认。版本号随登记推进，历史条目保留。重试登记前先按轮次 ID 核是否已经存在，再核目录、代码起点和批准引用是否一致。运行状态、测量质量和命题证据分别从实际实验记录、结论及 `claims.json` 查。

## 2. 同一轮怎样串起执行和决定

本轮的 `research-spec.md`、`research-plan.md` 和 `claims.json` 随正式轮次交接。一轮可以有多批 `execution → iterate`。各层产物按下面入口查。

| 要查什么 | 打开哪里 |
| --- | --- |
| 本轮获批做什么，补证依据哪次确认 | `research-plan.md` 的修订、任务 slug 和批准引用。修改 plan 时，保留原批准稿的 Git commit 或固定副本，每次实际运行绑定使用的批准修订 |
| 一批执行包含哪些实验和运行 | `experiments/index.json` 的批次登记和对应实验、尝试元记录。单实验报告、配置和运行证据在 `experiments/<experiment-id>/` |
| 哪一批结果做过独立核查 | `executions/<批次-slug>/execution-result-review.md`。每份覆盖的实验和 run 以报告列出的范围为准 |
| 看完本轮证据后决定做什么 | `decisions/<决定-slug>/next-step-decision.md`。复查材料或待审草案与该决定一同保存。确认开新轮时，从决定链接到新轮的获批方案 |
| 各批证据合起来支持到哪里 | 本轮 `execution-conclusion.md` 和 `execution-conclusion.json`，再沿出处回查单实验报告、原始读数及独立核查 |

例如，v1 完成配置比较后，用户批准在 v1 补采缺失轨迹。这次追加相应的 plan 修订和执行批次，索引仍只有 v1。若随后确认开 v2 核固定分派，把决定留在 v1 的决定目录，再登记 v2。

## 3. 沿 main 推进，用 tag 标记交接代码

- **实际代码起点。** 默认在研究仓库的 `main` 上持续提交。同一条提交历史可以容纳多个研究轮次。开轮前核当前 checkout 和用户已有改动，确认所需实现已在 `main` 的当前代码中，再登记实际 `start_commit`。续做时以轮次目录、获批 plan 和实际运行记录定位。
- **实际执行代码。** 一轮可有多次提交，不同实验和 run 可以用不同 commit。每次运行记录实际 commit、生效配置和数据。涉及未提交改动时保留实际 diff。
- **需要另试路线时。** 需要并行试验，或确实要从旧实现另起一条路线时，再按实际决定使用临时分支。记录决定和实际起点，保留 `main` 的既有提交。
- **收尾代码。** 需要交接代码时，按授权在实际收尾 commit 打 annotated tag，例如 `research-round/v2-edge-vision`，并把 commit 和 tag 写进索引。有效反证或未区分的结果也可形成交接。纯分析且无新代码交接时，记录实际使用的 commit，tag 留空。补交时保留已经发布的标签和它对应的历史记录。单次实验的实际代码仍以运行记录为准。

先核工作区和 `main` 当前指向。需要切回 `main` 时，先确认已有改动已妥善保留，再执行 `git switch main`。若预定起点或准备结果尚未纳入 `main`，先核差异和实际采用的基线，按项目约定处理后再登记。

```bash
git status --short --branch
git rev-parse --verify 'main^{commit}'
git log -1 --oneline main
```

打 tag 时把变量设为已确认的轮次和收尾代码，核目标 commit 及已有标签。

```bash
git rev-parse --verify "${handoff_commit}^{commit}"
git tag --list "$round_tag"
git tag -a "$round_tag" "$handoff_commit" -m "Hand off $round_id"
git rev-parse --verify "${round_tag}^{commit}"
```

原始数据、checkpoint 或大型输出留在实际存储位置时，仓库中的报告和运行记录给出可查的路径、配置及版本。跨机器交接沿用项目当前的传输方式。
