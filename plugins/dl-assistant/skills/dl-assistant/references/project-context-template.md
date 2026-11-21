# 项目背景（PROJECT_CONTEXT）

> 项目级、少改、不随版本。住 `ideas/PROJECT_CONTEXT.md`。
> 每次 server 端 session 开头，execution / iterate 先读它（加 claims.json + 当前代码），
> 渲染 session 开头恢复记忆的四节小结（我们在干啥 / 我们在哪 / 代码长这样 / 准备干啥）。
> 详见 `session-recovery.md`。
>
> **本文件是导航枢纽，不重抄别处已有的内容**——环境 / 代码 / 数据 / checkpoint / ready 命令
> 都在 Project Setup Report 里（`code-project-setup` 产），baseline 可信度 + reduced 配置在
> Reproduction Report 里（`code-paper-reproduction` 产）。本文件只放这些 report 没有的：
> 研究框架 + baseline 身份一行 + docs 深背景索引。

## 研究框架

- **要解决的问题**：一句话（每版的假设看当前版本的 `01-idea-spec.md` §0）
- **目标会议 / 截稿**：

## baseline 身份

- **当前使用的可信 baseline**：哪个 repo、可信 baseline 在哪个分支/tag（`baseline-prepared` CIP 产 / 全退则 `baseline-reproduced`）、复现关键指标（如 refcoco val cIoU 77.49）
- **可信度 + reduced 配置**：见 Reproduction Report（含 baseline 可信度四档 + `reduced_setting`）——路径：`<repro-report 路径>`

## 环境 / 代码 / 数据 / checkpoint

Project Setup Report 已有：conda env、ready 命令、数据 / checkpoint 路径、编译依赖、seed / determinism 设置。要细节去读它——路径：`<setup-report 路径>`

> session 恢复记忆的"代码长这样"那节：读 Setup Report 的 ready_commands + 当前 spec 附录 A 代码锚点 + 实际 cat 当前代码。

## docs 深背景索引（按需派子 agent 读）

- literature-survey 报告：`docs/...`
- idea-find 分析：`docs/...`
- baseline-survey 报告：`docs/...`

> 遇深问题（"为啥选这 baseline""文献怎么说 X"）派子 agent 读对应那篇返回摘要，别把全文灌进主上下文。
