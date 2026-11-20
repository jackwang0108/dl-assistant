# 项目背景（PROJECT_CONTEXT）

> 项目级、少改、不随版本。保存在 `ideas/PROJECT_CONTEXT.md`。
> 每次 server 端 session 开头，execution / iterate 先读它（加 claims.json + 当前代码），
> 生成 session 开头恢复工作上下文的四节小结（我们在干啥 / 我们在哪 / 代码长这样 / 准备干啥）。
> 详见 `session-recovery.md`。
>
> **本文件是背景与文件索引，不重抄别处已有的内容**——环境 / 代码 / 数据 / checkpoint / ready 命令
> 都在 Project Setup Report 里（`code-project-setup` 产），逐目标复现结果、使用范围与可选低成本配置在
> Reproduction Report 里（`code-paper-reproduction` 产）。本文件只放这些 report 没有的：
> 研究框架 + baseline 身份一行 + docs 详细背景索引。

## 研究框架

- **要解决的问题**：一句话（每版的假设看当前版本的 `01-idea-spec.md` §0）
- **目标会议 / 截稿**：

## baseline 身份

- **当前参考实现与结果**：实际组件/代码commit及未提交diff、模型/数据/config、复现目标/协议与已取得结果的范围；分支/tag仅帮助定位，不替代证据。未复现/受阻事项见对应报告。
- **已验证条件与使用范围**：见Reproduction Report的targets、协议/实际条件、逐次结果和use_scope；可选low_cost_configs不代表跨规模外推已验证——路径：`<repro-report 路径>`

## 环境 / 代码 / 数据 / checkpoint

Project Setup Report 已有：实际环境/组件、指定操作与检查范围、数据/权重身份及路径、依赖和实际随机性设置。要细节去读它——路径：`<setup-report 路径>`

> 恢复时读setup.json的components/environments、operations/checks及supported_operations，再核实际代码/config/资产；ready_commands只是已检查入口的兼容索引，不单凭命令字符串推断就绪。当前spec的实际代码位置也需核对，不假定固定附录或旧笔记仍对应当前版本。

## docs 详细背景索引（按需派子 agent 读）

- literature-survey 报告：`docs/...`
- idea-find 分析：`docs/...`
- baseline-survey 报告：`docs/...`

> 遇深问题（"为啥选这 baseline""文献怎么说 X"）派子 agent 读对应那篇返回摘要，按当前问题读取相关内容。
