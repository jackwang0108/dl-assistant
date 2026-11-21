# session 开头恢复记忆

> 每次 server 端开新 session（每个版本一个）必做。SKILL.md 的「Step 1 恢复记忆」只放主流程，细节在这。
> 治"服务器每版开新 session 失忆 + 不读代码就瞎跑/瞎改，用户得拦着"。

## 四节小结

session 开头先从盘上把上下文灌回来，吐这四节给用户：

1. **我们在干啥**：项目要解决什么、baseline 是啥（读 `PROJECT_CONTEXT.md`）。
2. **我们在哪**：当前版本 + claim 树地图。读 `claims.json` 渲染**两层**：
   - 总论点 claim 的 verdict（paper 总主张目前稳不稳）
   - 子论点 status 分布（active / refuted / pending 各几个）+ 已成立子论点数（= 创新点数）+ 关键裁决
3. **代码现在长这样**：读 spec 附录（代码锚点概览）+ plan 的代码指引，**实际 cat 当前代码**，小结关键模块 + plan 的接入点在哪。
4. **准备干啥**：当前 plan（idea-find/iterate 给的）的下一步 / `00-from-previous`（v2+）给的方向。execution 不提方案，只确认 plan 可执行 + 接着跑。

## 硬规矩

**读完代码 + plan 才准实现。** execution 是纯执行引擎——方法在 plan 里（IF/iterate 设计），不读代码 + plan 就动手，大概率对不上当前实现、误解接入点，用户得拦着纠正。这条规矩治这个。

## PROJECT_CONTEXT.md（项目级稳定背景）

- 住 `ideas/PROJECT_CONTEXT.md`。
- **首次没有时**：协助用户填一份（按 `project-context-template.md`：研究框架 + baseline 身份 + 指针 + docs 索引）。
- **何时更新**（少改，但不是冻结）：
  - **docs 索引**：session 开头 cheap 对一眼（`ls docs/` vs 索引），docs/ 真多了文档才补——大多时候不用动。
  - **baseline 身份 / 环境代码数据指针**：`code-project-setup` / `code-paper-reproduction` / `code-idea-prepare` 重做（重配环境 / 重选 baseline / 重复现 / 重清理）时。
  - **研究框架**（问题 / 目标会议）：iterate + 用户决定换方向 / 换会议时——这条归 `code-idea-iterate`。

## 三层记忆（别把所有背景塞 PROJECT_CONTEXT）

| 层 | 是啥 | 啥时候读 |
|---|---|---|
| `claims.json`（每版） | 进展地图（**两层 claim**：总论点 verdict + 子论点 status/裁决） | 每次 session 开头，渲染"我们在哪" |
| `PROJECT_CONTEXT.md`（项目根） | 稳定导航：研究框架 + baseline 身份 + 指针（setup/repro/cleanup report）+ docs 索引 | 每次 session 开头读（凝练） |
| `docs/`（深背景全文） | literature-survey、idea-find、baseline-survey 等 | 按需——遇深问题才派子 agent 读对应那篇返回摘要 |

**不每次 session 都扫 `docs/`**（贵且大多当次用不上）——PROJECT_CONTEXT 的 docs 索引让 agent 知道"深背景在哪、要时翻哪篇"，需要时再派子 agent 精读返回摘要。
