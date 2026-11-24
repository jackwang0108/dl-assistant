# 目标 1：init-setup（一次性起手）

## 何时用

第一次建立写作记录，或现有稿件尚缺工程与来源信息时使用。改稿和续写沿用实际论文根，按需核对当前稿、构建入口、配置和已有写作记录。

## 读哪些

- `references/craft/venue-specs.md`（官网入口 + 时区规范 + 图尺寸）。
- `references/craft/latex-landing.md`（clone + 协作同步纪律）。

## 子动作

1. **访谈**（不问 Overleaf 项目——模板由 venue 决定，现在问也是空问）：
    - **材料在哪**。新稿读 `docs/research/paper-package.md` 或用户提供的等价材料，核其中的研究证据、命题和代码版本。改稿读指定稿件、修改清单及批准范围。先讲清实际缺什么，已有记录直接沿用。
    - 会议 / 语言 / **deadline**（写进 state，建议机制加权用；此处先记用户口径，③ 爬官网后核对）。
    - GPU 服务器路径（论文准备材料 / 中期 repo 在哪）。
2. **核已知信息和缺项**。先从项目记录核材料和要求，向用户汇报会影响本次任务的未知。选择投稿目标或确认实际编辑范围时，说明需要作出的决定。
3. **派子 agent 爬 venue 官网的日程与政策**（general-purpose，禁 Explore）：从 `venue-specs.md` 的官网入口找当年 CFP / Important Dates，取 **deadline 系列**（abstract / full paper / rebuttal / 录用通知 / camera-ready，按 `venue-specs.md` 时区规范做原文 + 本地换算双写）、**投稿入口**、**政策类条目**（双重投稿政策、匿名期、利益冲突登记、代码/数据开源声明要求）。**格式类不爬**——页限/模板/栏/双盲写法/强制章节/checklist 一律以 authorkit 为准（⑧）。
4. **产 目标会议要求初版（官网日程与政策）**：爬取结果整理成契约的「日程与政策」一节（每个日期记原文表述 + 原文时区 + 本地换算；重要日期；投稿入口；政策条目）。**确认点**：向用户说明契约内容（尤其 deadline 时区换算），用户可纠正。注意这只是**初版**——「格式与写作规范」一节要等核实际 author kit 后写入（见 ⑧），契约才算定稿。
5. **确定工程和 author kit**。已有本地论文时直接核现有模板和主文件。新建本地稿件时，按已确认的目标会议导入对应 author kit。选择 Overleaf 时，把 author kit（用哪个模板、从哪下、Overleaf 怎么建项目灌这个模板）人话讲给用户；让用户在 Overleaf 配好项目，给回 **project_id + 项目官方 git 链接**（Overleaf 项目菜单提供）。
6. **按实际采用的工作方式接入**。使用 Overleaf 且没有本地副本时，方向根没有 `papers/` 先建；用官方 git 链接 clone，目录名默认 = Overleaf 项目名（即 paper slug；认证如需 token，按 `overleaf-mcp` SKILL的认证与 Git 说明一次性配置）。clone 出来的目录即论文根、是 git 仓库。
7. **建 `_draft/` + 契约初版落盘**：建 `_draft/`（config / paper-state / venue-contract / blueprint / content / experiments / visuals / scripts / writing.log）；核工作记录和构建缓存的保存与共享范围，沿用已有项目规则。第 ④ 步的契约初版落 `_draft/venue-contract.md`。
8. **探 authorkit（格式规范的权威来源，别只把它当格式模板）**：authorkit 自带的填充 tex/pdf 本身就是 venue 最详细的写作规范。逐个盘点：
    - **文件清单**：主 tex 叫什么（main.tex / egpaper_final.tex / <conf><year>.tex……不假设）、有哪些 .sty/.cls/.bst、有没有自带的 checklist/声明材料（原创性声明、代码开源承诺等）。主 tex 文件名 + kit 布局记进 `config.json`（后续落地操作要用）。
    - **读自带主 tex 的填充内容**：它原始填充的文字就是 venue 自带的写作 guideline，把要点写进契约的「格式与写作规范」一节（页数要求/匿名写法/图表规范/措辞禁忌/结构要求/强制章节）。契约到此**定稿**（与 ④ 官网内容有出入时摆给用户裁决）。
    - **读 .sty/.bst**：引用风格（natbib / 数字 / 作者-年份）、排版风格要点，记进契约（write-section 写引用、latex-landing 转译要用）。
    - **产 `_draft/venue-contract.json`（机读子集）**：契约定稿时，把其中**硬合规项**（没有判断空间、脚本可机械核对的）抽成机读 JSON——`page_limit`（页限）、`anonymity`（匿名要求）、`citation_style`（numeric / author-year）、`mandatory_sections`（强制章节清单，如 limitations / ethics / checklist）、`caption_position`（图表 caption 位置规范）等；探不到确切值的字段写 `null` 并在 .md 里标注「待确认」。`_draft/scripts` 外的确定性检查脚本（`run_checks.py` 一族）读这份 JSON 而非解析 prose——**字数带、贡献条数这类形状指标不进 JSON**（页数是软约束、先完整写出各节内容，见核心纪律 6；机读的只有硬合规）。契约定稿后硬合规项有变（如 venue 发 errata）时 .md 和 .json 同步改。
    - **注册合规待办项**：强制章节（limitations 等）→ write-section 项；ethics/reproducibility 声明 → write-section 项；kit 自带 checklist/声明材料 → finalize 项；③ 爬到的政策动作（利益冲突登记、开源声明）→ finalize 项（均 source=venue-contract）。**需要完成的投稿要求从第一天就在队列里，不许最后才发现。**
9. **本地编译工具链探测**：`latexmk`/`pdflatex` 在不在 → 在，用 kit 原地**试编一次 baseline**（模板 demo 能编绿 = 工具链可用）→ `config.json` 记 `compile_mode: local`，编译产物目录 `_draft/build/`；本地没有 TeX 工具链时，已配置并获授权使用 Overleaf 的项目可核实际远端编译，并记录 `compile_mode: overleaf`。当前工具均不可用时，记录阻塞及已核范围，草稿可按授权继续。
10. **写 `config.json`**（材料 / Overleaf 链接 / 会议 / deadline / 服务器路径 / **主 tex 文件名 + kit 布局** / **compile_mode**）+ **初始化 `paper-state.json`**（照 `references/templates/paper-state-template.json`；venue 块填契约字段）。
11. **选题复盘（仅从零写）**：读论文准备材料的「复盘材料」+ idea-find `spec.json` 的「选题理由快照」→ 写选题复盘（当时判断 vs 实际走向）→ 追加到跨项目统一目录的 `idea-retrospectives.md`（首次问用户位置、记进 config.json，之后沿用）。改稿场景跳过。
12. **初始 backlog**：从零写——提示用户下一步通常进 design-story；改稿——把修改清单逐项进 backlog（source=review-response 或 user），按类型预路由。

## 产出

`config.json`（含**主 tex 文件名 + kit 布局 + compile_mode**）、`venue-contract.md`（日程与政策初版 + authorkit 格式规范定稿）+ `venue-contract.json`（硬合规项机读子集）、初始化的 `paper-state.json`（含合规待办项）、`_draft/` 结构。

## 状态更新

venue 块（含 deadline）、backlog 合规项、config 路径。writing.log 记起手。

## 确认点

- 子动作 ②：材料路径 / 会议 / deadline / 服务器无误。
- 子动作 ④：契约初版（日程与政策）说明，deadline 时区换算无误，用户可纠正。
- 选择 Overleaf 时核具体项目及实际允许的同步范围。
- 确认实际论文根与主文件后继续。
- 子动作 ⑧：契约写入格式规范后定稿——与爬取内容有出入时摆给用户裁决。

## 易错点

- **格式规范只认 authorkit**——官网 author guidelines 页面常是 kit 内容的转述，爬来反而引入第二来源；官网只爬日程与政策。
- **deadline 时区双写**——每个日期记原文表述 + 原文时区 + 本地换算；原文没写时区按 AoE 假设并显式标注「待确认」，别默默换算。
- **访谈不问 Overleaf 项目**——顺序：爬官网日程政策 → 产契约初版 → 告知 author kit → 用户配 Overleaf 给链接 → agent clone → 探 authorkit 写格式规范定稿。顺序不能反。
- **authorkit 自带的填充 tex/pdf 必读**——它就是 venue 自带的详细写作规范，不是只有格式价值的模板；clone 后不读它，契约就是半残的。
- **主文件名不假设 main.tex**——以探到的为准（egpaper_final.tex / <conf><year>.tex 都有可能），记进 config.json，后续所有落地操作用 config 里的名字。
- **clone 用项目官方 git 链接**（Overleaf 项目菜单提供），别走 session cookie 等非官方路子。
- skill **不建** Overleaf 项目——用户照 author kit 建；agent clone、在论文根里当 git 仓库管。
- `_draft/` 必须 `.gitignore`，别推 Overleaf 污染模板。
- **合规待办项当场注册**——别想着「到时候再说」，到时候就是投稿前一天。
- **写作循环不碰 Overleaf**——本地验证走本地编译（`compile_mode: local`），Overleaf 同步只在关键节点（里程碑/用户要求/协作需要）；每节都 push 会把远端编译 log、同步噪音灌进上下文，agent 容易漂移。
