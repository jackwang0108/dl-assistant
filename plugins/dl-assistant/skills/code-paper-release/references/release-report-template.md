# `RELEASE_REPORT.md` template（内部验证记录报告）

release 的验证报告，放 release repo 根，记录全过程（节点认定 / 基准 / 回归 / 对外验收 / 防泄露 / 开源），给用户留底。

> **含内部信息**（中期 repo 节点/分支名、排除过哪些 idea、防泄露自查、内部路径）——**不能进开源 repo**。开源前（Step 7）必做：删它 + 删 `.git` + `git init` + push。开发期它在 repo 里方便读写。
>
> 写法：人读、留底导向——半年后回来看这份文件要能复述「发了哪个节点、验了什么、数字是多少」。每节按下方指引写，示例供对标深度。

## 生成时照这个结构写

```markdown
# Release Report

## 最终方法节点

<写清：中期 repo 哪个分支/tag/commit 被认定为最终方法；由谁确认；存活 claim 有哪些（从 claims.json 来）。>

示例：
- 中期 repo 节点：分支 `idea/v3-uncal` / tag `v3-final` / commit `a1b2c3d`
- 由用户确认：2026-07-28（agent 推荐 v3-final 与 v2-base，用户定 v3-final）
- 存活 claim（claims.json）：C1（主方法增益）、C3（效率不劣化）；C2 已否（不随发行版发布）

## 基准记录

<用一行给出出处 + 口径说明：基准来自哪个 CPE 数据包、哪些 exp_id 进了主表、由谁确认容差。>

- 基准：`docs/perf-baseline.json`（status=fullscale_final，来自 CPE `paper-data-pkg-v1`）
- 主表口径：exp-main（3 seed mean±std）；容差：top-1 ±0.3（由用户确认 2026-07-28）

## 三关回归结果（标准 = 复现论文主表性能）

| 关 | 结果 | 复现值 vs 基准 vs 容差 |
|---|---|---|
| conda 复现主表 | pass | 76.2 vs 76.3±0.2 vs ±0.3 |
| Docker B 复现主表 | pass | 76.1 vs 76.3±0.2 vs ±0.3 |
| Docker A smoke | pass | loss 2.1→0.4 / 出 checkpoint |

<每关写实测值，不写「通过了」。fail 的关写排查结论：哪里漏了、怎么修的、回归后数字。>

## 对外验收（vs 论文 PDF）

<release repo 复现值 vs PDF 主表逐项对照——这是 按公开材料核验复现结果。>

| 指标 | 复现值 | PDF 主表 | 容差 | 判定 |
|---|---|---|---|---|
| <数据集> top-1 | 76.2 | 76.3 | ±0.3 | pass |

## 发行版结构 + 复现路径

<三条路径各一行真命令（README/AGENTS.md 同款）：conda、Docker B、回归脚本。>

- conda：`conda env create -f environment.yml` → `bash scripts/eval.sh --checkpoint ...`
- Docker B：`docker run --gpus all -v ... <repo>-infer ...` → 推出主表 metrics
- 回归：`bash scripts/perf-regression.sh`

## 权重发布

- 权重：<HF Hub / 云盘链接>（sha256: <校验值>）
- 来源：CPE `experiments/exp-main/runs/seed-1/`（pkg-meta.json 中记录的路径核对一致）

## 防泄露自查

<逐项打勾 + 自动扫描结果；任何一项存疑写明处理方式。>

- [x] git history：全新仓库，开发期 commit 无内部信息（开源前仍重新初始化 Git 仓库）
- [x] 无其他分支 / 被否 idea / 未发表方向的代码与注释
- [x] 无 `docs/research/` 的内部轮次、执行结论、决定和实验台账
- [x] 无 runs/ 残留、无死代码、无定义未用参数
- [x] secret 扫描：gitleaks / grep（token|api_key|password）→ 0 命中
- [x] 内部路径扫描：grep（/home/|/data/集群路径|内网 IP）→ 0 命中
- [x] 双盲风险（若会议要求）：README/代码/commit 无作者身份机构信息

## 开源

- GitHub：<链接>（公开/私有）
- LICENSE：<哪种，由谁确认>
- 开源前清理：已删 `RELEASE_REPORT.md` + 删 `.git` + `git init` + push（开源 repo 无本文件、从首次公开提交开始建立 Git 历史）
- 项目页（如做）：<GitHub Pages URL>，用户已审

## 注意事项

- 大数据/大权重准备：见 `docs/data_preparation.md`
- baseline 可信度：<若 Step 1 标过不可信，写明用户怎么定的>
- 遗留问题：<没有就写无>
```
