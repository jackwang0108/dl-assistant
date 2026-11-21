# LaTeX 落地工艺：论文根（= papers/ 下 Overleaf git clone）→ 本地编译 → 关键节点同步

writing-paper 的落地工艺。**论文根 = `<方向根>/papers/<slug>/` 下的一个 Overleaf git clone**：用户先在 Overleaf 从会议 author toolkit 建项目（含模板 主 tex（名字随 kit）/sty/cls），再把**项目官方 git 链接**（Overleaf 项目菜单 Menu → Git 里拿）给 agent，agent `git clone` 到方向根的 `papers/` 下（slug 默认 = 项目名）。论文根是 git 仓库，当 git 仓库管：fetch/整合/commit/push。skill 在论文根里工作——`.md` 源在 `_draft/content/`、转译的 `.tex` 按文件组织纪律落位、图落 `figures/`、bib 落 `refs.bib`。

**落地分两层，频率差一个量级**：

- **本地验证（默认，高频）**：每次内容变更后做——本地编译（`latexmk`）→ 本地渲染（`pdftoppm`）审阅 → 本地 commit。**不 push、不调 overleaf-mcp**。写作主线全程只跟本地工具打交道，上下文不被远端编译 log/同步噪音淹没。
- **Overleaf 同步（关键节点，低频）**：只在三种时机做——① **里程碑**（full-draft、finalize 前——Overleaf 是协作真相源，定稿交接必须远端编译绿）；② **用户显式要求**（"推上去看看"）；③ **协作需要**（远端有新 commits 必须整合时，整合完顺带 push）。动作：fetch+整合 → push → `overleaf_compile` 确认**远端也绿**（协作者可能动了别的文件；Overleaf 的 TeX Live 版本和本地可能差一两年，本地绿 ≠ 远端绿）→ 远端渲染回归。

落地时机绑定各目标操作：

- **write-section 的 ④⑧**：④ 每写完一节初稿、⑧ 本节定稿后——各做一次**本地验证**（转译该节 `.tex` → 本地编译 → 渲该节 PDF 给用户审，WYSIWYG）。
- **make-visual / ingest-results 的占位替换**：示意图复刻完、实验数据回填成正式表格后，替换占位框/占位表，做**本地验证**。
- **里程碑 / finalize**：走 **Overleaf 同步**全文复核编译 + 视觉回归。

> `_draft/` 是 skill 作者工作区（.md 源/蓝图/实验计划/图脚本/config/log/`paper-state.json`/本地编译产物），**`.gitignore` 不推 Overleaf**——根目录只留 LaTeX 该有的（模板 + `sections/` + `tables/` + figures 输出 + refs.bib）。Overleaf 云能力（编译/渲染/评论/历史）只在同步节点调 `overleaf-mcp`，本文只讲**转译与编译工艺**。

## 核心纪律

- **调的是呈现，不是内容**：转译只改格式（md → latex、svg → pdf、挂引用风格），不改语义。内容问题（该有的图没有、该拆的段没拆、强调缺失）**标出来回 write-section**，不在 LaTeX 落地里改内容。
- **正文结构跟论文草稿走，格式规范跟模板走**：模板不提供"空槽位"——按 `content/` 的真实 section 组织正文，用模板的命令 / 环境 / 引用风格排版。
- **本地编译常绿**：**本地编译绿了才 commit**——编译红了**先修红再继续**，不带红 commit，更不带红 push（远端是协作方也在看的共享状态）。
- **上下文卫生**：本地编译失败只把 **log 尾部错误摘要**（`grep "^!"` + 前后几行）带进上下文，不整篇 log 倒进来——log 全文在 `_draft/build/` 里，需要再查。
- **pending 占位不跳过**：示意图等还没齐的产物留占位框 + TODO，不阻塞编译，汇报里标出。

## Step A：git clone Overleaf 项目到 `papers/` 下（op-1-init-setup 起手做）

用户**已**照 author kit 指导在 Overleaf 建好项目（含模板），并从**项目菜单拿到官方 git 链接**给 agent。

1. **clone 用官方 git 链接**：Overleaf 项目菜单（Menu → Sync → Git，或项目设置页）里有形如 `https://git.overleaf.com/<project_id>` 的官方 git 链接，用户复制给 agent；方向根没有 `papers/` 先建，agent `git clone <链接> papers/<slug>`（slug 默认 = Overleaf 项目名）。**认证按 `overleaf-mcp` SKILL的认证与 Git 说明做一次性的 git 凭证配置**（credential helper 配一次，之后 clone/push 都走缓存凭证），不再以 session cookie 排 git 的障。clone 出来的目录即论文根（模板 主 tex（名字随 kit）/sty/cls 就在根下）。
2. **本地编译工具链探测**（op-1 做）：`latexmk`/`pdflatex` 在不在 → 在，用 kit 原地**试编一次 baseline**（模板 demo 能编绿 = 工具链可用）→ `config.json` 记 `compile_mode: local`。本地没有 TeX 工具链 → 记 `compile_mode: overleaf`，**诚实降级**：本地验证层改走 `overleaf-mcp` 编译（老路，调用频率降不下来，告诉用户装 MacTeX/BasicTeX 即可解锁本地模式）。
3. 论文根建 `_draft/`（作者工作区）+ 写 `.gitignore` 排除 `_draft/`（不推 Overleaf）。

> skill **不建** Overleaf 项目——用户从 author toolkit 建（保证模板正宗）。skill 只 `git clone` + 在论文根里工作（当 git 仓库管）。

## 多人协作同步纪律（重点）

Overleaf 项目是**共享远端**：协作方在网页端写作时，Overleaf 会**频繁自动 commit**——远端几乎一直有新 commit。论文根这个本地 clone 不同步就会落后，下次 push 必然被拒。纪律：

- **每次会话开始先同步**：`git fetch` + 整合（rebase 或 merge，跟远端对齐后再动手）。不 fetch 就写等于在过期基线上改。会话开始同步只 pull 不 push——保持本地新鲜，控制的是**分歧窗口**。
- **每次 Overleaf 同步前再同步**：同步节点的固定动作是 fetch → 整合 → push，不是攒完直接 push。
- **push 被拒就循环**：`push` 因远端新 commit 被拒 → `fetch` → 整合（rebase/merge）→ 再 push，**循环重试直到成功**。这是协作常态，不是错误。
- **提交切小**：本地一次验证一个提交粒度（一节初稿、一次占位替换），写完即本地 commit——本地历史细粒度，回滚/查账都方便；push 集中在同步节点（一批本地 commit 一起上）。
- **同一处冲突即停交用户**：只自动合并**不重叠**的改动（不同节、不同段落）；同一处（同段落/同行）冲突**立即停下，把冲突双方摆给用户裁决**，agent 不猜谁的版本对。
- **协作方高频写时错峰**：发现远端 commit 很密（协作方正在线写），提醒用户跟协作方错峰，或由用户协调分工（各写各的节），别硬顶着冲突窗口写。

## 文件组织纪律

- **section 一节一文件**：每节正文落 `sections/<名>.tex`（如 `sections/intro.tex`、`sections/method.tex`），主 tex（名字随 kit，见 config.json）只做 `\input{sections/intro}` 等串接 + 导言区，正文不堆主 tex。一节一文件让并行协作、git 冲突面、逐节验证都干净。
- **数据表单独文件**：实验数据表落 `tables/<id>.tex`（如 `tables/main-results.tex`），正文 `\input{tables/main-results}`——**脚本重生成表格时只碰这个小文件**，不动正文，diff 干净、可重跑。
- **纯文字小表可内联**：无脚本再生成的纯文字小表（如符号表、设置小结）可直接内联在 section 文件里。
- **尊重 author kit 期望位置**：探模板时如果 author kit 对文件布局有明确要求（如规定图放某目录、规定主文件名），按 kit 的来，纪律给模板让路。

## label/\ref 纪律

- **节/图/表全带 `\label`**：`\section{...}\label{sec:intro}`、figure 环境内 `\label{fig:arch}`、table 环境内 `\label{tab:main}`。命名带类型前缀（`sec:` / `fig:` / `tab:`）。
- **正文引用一律 `\ref` / `\ref` 系命令**：写 `Section~\ref{sec:method}`、`Figure~\ref{fig:arch}`、`Table~\ref{tab:main}`，**禁止手写 "Figure 3" 式裸编号**——浮动体重排后裸编号全错，`\ref` 自动跟。
- **每次本地验证顺手 grep 检查本节新增内容**：`grep` 本节改的 `.tex`，查有没有裸写的 Figure/Table/Section + 数字、有没有 `\ref` 指向不存在的 label（本地编译 log 里的 `??` 警告也要看）。本节新增不带 label/裸编号，修完再 commit。

## Step B：探模板格式规范 + 给用户导读（动手前关卡）

> op-1-init-setup 已探过 authorkit（文件清单、自带填充 tex 的写作规范已进 `venue-contract.md`，主 tex 文件名在 config.json）。本步不重复盘点，聚焦**转译要的格式规范**。

> **注意：模板 ≠ 内容骨架。** 会议模板的主 tex 往往是一篇 demo / 示例论文（`egpaper_final.tex`、`frog.tex` 之类）或 `.sty` 命令说明——它提供的是**格式规范**（怎么排版、有哪些命令 / 环境 / 引用风格），**不是"有空 `\section` 等你填"的骨架**。要做的是：保留模板格式规范（导言区 / 文档类 / 宏包 / 自定义命令），清掉 demo 正文，按论文草稿的真实 section 结构重组正文（落成 `sections/*.tex`）。

1. **探格式规范**（读论文根里的模板 `.cls` / `.sty` / 主 tex 导言区）：
   - 文档类、双栏 / 单栏、字体、页面尺寸
   - 自定义命令（`\cvprfinalcopy` / `\teaser` 等）、`\title` / `\author` 怎么写
   - 表格用什么宏包（`booktabs` / 模板自带）、图怎么引、有无 `\appendix`
   - **引用风格**：natbib? 数字 `[1]`? 作者-年份? `.bib` 怎么挂（`\bibliography` / `biblatex`）——决定正文怎么转 `\cite`
   - **author kit 的文件布局期望**（规定目录/主文件名的话，文件组织纪律按 kit 调整）
2. **给用户模板导读**（建映射表前的必经一步）：用户不一定精通 LaTeX，先用人话讲清"这是什么模板 / 几栏 / 图表怎么走 / 引用显示成什么样 / 有哪些特有规矩 / 哪些 demo 会被清掉"，别直接甩术语映射表。

## Step C：建转译映射表（给用户过目）

读论文草稿各产物，建"产物 → LaTeX"映射给用户过目（口头，git commit message 兜底）：

```
论文草稿产物                    →  转成什么                       →  LaTeX 处理
content/intro.md              →  sections/intro.tex          →  md 正文转 LaTeX，主 tex \input
content/method.md             →  sections/method.tex         →  md 正文转 LaTeX
content/experiment.md         →  sections/experiment.tex     →  \input tables/，引图 \ref
数据表（ingest-results 产出）  →  tables/main-results.tex     →  脚本生成，正文 \input
figures/loss.pdf（数据图）    →  figure 环境                 →  \includegraphics（矢量 pdf 直接用）+ \label{fig:}
figures/fig-2.pdf（示意图）   →  figure 环境                 →  HTML 草稿/PPT 终稿都是同名 pdf，\includegraphics + \label{fig:}
图还没产出（status=intent）   →  占位框 + TODO               →  不阻塞编译，汇报标出
refs.bib                      →  挂模板引用风格              →  \bibliography{refs}
```

> `blueprint.md` 给节清单 + 每节叙事任务；`content/` 给各 section 正文；`figures/` 给图；`refs.bib` 给引用。映射表按这些**实际文件**建，不强依赖某个 manifest 字段——产物齐不齐看文件本身（section md 写完即落；示意图 `*.png` 草图未复刻成 `*.svg`/`*.pdf` 就占位）。

## Step D：逐产物转译填充

按论文草稿文件实际状态转，**允许"内容没齐也先把正文搭起来编译起来"**：

| 产物 | 转译 |
|---|---|
| `content/*.md`（写完的 section）| 按论文草稿结构建 `sections/<名>.tex`：`\section` / `\subsection` + `\label{sec:}`，md 正文转 LaTeX 段落，数学 `$...$` 直接落 |
| 数据表 | 生成 `tables/<id>.tex`（含 `\label{tab:}`），正文 `\input`；脚本重生成只覆盖这个小文件 |
| `figures/*.pdf`（数据图 / 示意图 HTML 草稿 / PPT 终稿）| 拷进 repo 图目录，figure 环境 `\includegraphics` + `\label{fig:}`（矢量 pdf 直接用，同名替换即更新）|
| 图还没产出（manifest status=intent）| **留占位框 + TODO 注释**（`% TODO: fig-2 pending production`），汇报标出，不阻塞编译 |
| `content/appendix/*` | 转进模板 `\appendix` 区 |

**正文引用 → `\cite{}`**：论文草稿正文里引用是 markdown link `[@cite_key](规范URL)`。转译时读 link 文本里 `@` 后的 `cite_key`，替换成 `\cite{cite_key}`（url 只给人点击核对，转译不依赖它）。`refs.bib` 的 key 是同一套 cite_key，天然对齐。

**bib 落地**：根目录 `refs.bib`（write-section 的 ② 当场 paper-search 构造的非正式条目）按 Step B 探到的引用风格挂上（`\bibliography{refs}` / `biblatex`）。正式 venue 格式收尾用户手修。`refs.bib` 缺失或正文 `\cite` 找不到对应 cite_key → **停下回 write-section 的 ② 补**，不自己查文献。

## Step E：本地验证（默认路径，每次内容变更后跑）

本地验证的固定动作序列（顺序不能乱）：

```
转译该节 .tex（Step D）
  → 本地编译（见下；红了先修红——本地常绿）
  → grep 本节新增内容的 label/\ref（纪律见上）
  → 本地渲染审阅（pdftoppm 出 PNG，逐页看）
  → 报当前页数
  → git add（排除 _draft/）→ 本地 commit（切小，一次验证一个粒度）
```

**本地编译**（`compile_mode: local`）：

```bash
latexmk -pdf -interaction=nonstopmode -outdir=_draft/build <主tex>.tex   # 自动处理 bibtex/多遍
```

- 编译产物（pdf/log/aux）全落 `_draft/build/`——被 `.gitignore` 排除，不污染 repo。
- **红了**：只取错误摘要进上下文（`grep -n "^!" _draft/build/<主tex>.log` + 上下文几行），修红再编；整篇 log 在 `_draft/build/` 里可查。
- **渲染审阅**：`pdftoppm -png -r 150 _draft/build/<主tex>.pdf _draft/build/page` → ReadMediaFile 逐页看（用户审 PDF 也看这个）。页数用 `pdfinfo _draft/build/<主tex>.pdf`。
- 没有 latexmk 用 `pdflatex`（bibtex 要手动按 pdflatex→bibtex→pdflatex×2 跑）。

**降级路径**（`compile_mode: overleaf`，本地无 TeX 工具链）：本地验证层改用 `overleaf_compile` + `overleaf_render` 完成同样动作（见其 SKILL「编译与核查」），其余不变。

## Step E2：Overleaf 同步（只在关键节点跑）

同步节点的固定动作序列（顺序不能乱）：

```
git fetch → 整合（rebase/merge，冲突同一处即停交用户）
  → 本地编译确认绿（本地常绿：红了先修红）
  → push（被拒 → fetch/整合/push 循环重试）
  → overleaf_compile → 读 log（远端必须也绿——本地绿 ≠ 远端绿）
  → overleaf_download_output 下载指定 compile_id 的 output.pdf → overleaf_render 渲染同一轮
```

调 `overleaf-mcp` 标准编译循环（见其 SKILL「编译与核查」）：用 `overleaf_compile_report` 核对同一个 `compile_id` 的状态和 `classification`（failed / warnings / clean / unknown），失败先修，结果未知先核状态。

## Step F：视觉 + 美观回归

编译通过 ≠ 合格。渲染 PDF 后查两层——**正确性**（图表显示 / 引用编号 / 公式 / 有无 `??` 未解析——`??` 多半就是 label/\ref 纪律破了）+ **美观性**（图表拥挤 / 占比 / 文本节奏 / 浮动体溢出）。本地验证时用 Step E 的本地渲染做；Overleaf 同步节点用远端渲染复核。

详细检查清单、诊断方法、呈现类怎么调，见 **`visual-aesthetic-review.md`**（本目录）。

**处理边界**：
- **呈现类问题**（浮动体位置 / 图表大小 / 间距 / 宏包参数）直接调——这是呈现，落地工艺的职责。
- **根因在内容的问题**（内容没安排图 / 该拆没拆 / 强调缺失）→ 标出来回 write-section，不在 LaTeX 里改内容。

## Step G：人类最终视觉审阅 → 交接

内容在 write-section 已定稿，这步人类是**最终视觉 / 外观审阅人**——审"PDF 长得对不对、美不美"，不是审内容对错。agent 不自行宣布完成：

```
汇报（转了哪些 / 占位哪些 / 编译状态 / 视觉美观检查）
  → 用户审阅 PDF 呈现与美观（本地渲染的 PNG）
  → 有呈现问题 → 回 Step E / F 改进
  → 循环到用户对外观满意（放行）
  → 交接
```

交接去向：

- 准备投稿 → `writing-paper-submission`（机器自检 / 视觉检查 / 匿名终审 + authorkit 材料填写）
- 审阅中发现内容问题（不只是呈现）→ 回 write-section
- 示意图 PPT 终稿用户画完 → 替换 `figures/<id>.pdf` → 本地验证（见 finalize）
