# 第 2 轮：量化细评（arxiv-daily-paper · Step 3）

幸存的 ~30-45 篇，**全部交给子 agent 做**（不在主会话做）：**每 ~15 篇派一个子 agent 并行**（即 2-3 个；一律 `general-purpose`，禁 Explore——要下 PDF、写量化卡），下 PDF 读 **Experiment（+ Related Work）**，做**纯量化判断、不碰 novelty**。

## PDF 统一落盘

子 agent 下载 PDF 时，**存到当天目录的 `pdfs/<arxiv_id>.pdf`**——机制：raw.json 里每篇都带 `pdf_url`，直接 `curl -sL "<pdf_url>" -o pdfs/<arxiv_id>.pdf` 落盘即可（零依赖、确定性）。下载失败的篇目照常出量化卡，但注明「PDF 未取到，基于摘要+元数据判断，置信降一档」；个别 curl 死活下不来的，可用 pdf-mcp 直读 URL 兜底。另外，读论文内容**先用 `tex_open` 打开固定版本**（tex-mcp）——拿到源码可直接读正文/图表，源码不可用时才走 pdf-mcp（见下节）。统一落 `pdfs/` 是为了多个子 agent、以及第 3 轮，都能复用同一份，不重复下载。

## 子 agent 怎么读论文内容（tex-mcp 首选，pdf-mcp 兜底）

1. `tex_open(source=<arxiv_id>)` 打开固定版本。拿不到源码时就直接走第 4 步的 pdf-mcp 兜底，不硬试后续工具。
2. `tex_outline` → 以 `document_id` 查看章节树并定位 Experiment / Related Work；`tex_search`（query 如 "compared with" / "baseline" / "GPU"）→ 快速跳到主表和对比描述所在节，不通读全文。
3. `tex_read(document_id, section=...)` → **按节读正文**（首选）——baseline 方法名、年份、对比数字大多在正文/表格文本里，**直接读文字最准**；主表用 `tex_read` 返回对象里的表格源码，或 `tex_get_object` 单独取。
4. **源码不可用时才走 pdf-mcp**：`pdf_open` 打开 PDF 并用 `pdf_info` 核页数 → `pdf_search` 跳主表 → `pdf_read` 读文字；**仅当主表排版复杂**（多列合并、文字层抽出来错乱）时，`pdf_render` 渲染整页用"看"的兜底。

> 主表**文字优先、图兜底**：别只渲染成图让 agent 认字（易错），baseline 列表/数字优先从文字层拿。

## 量化判据（全是数得出来的事实，不涉及 novelty）

| 判据 | 看什么 | 信号方向 |
| --- | --- | --- |
| baseline 最新年份 | 对比方法里最新的是哪年 | 比近 1-2 年方法 = 强；只比 ResNet/YOLO 等多年前烂大街方法 = 弱 |
| baseline 数量 | 主表横向比了几个 | 多 = 认真；只比 1-2 个老的 = 可疑 |
| 是否含当前 SOTA | baseline 里有没有领域内公认最新强方法 | 敢比 = 强；回避 = 可疑 |
| 实验规模 | 几个 benchmark/数据集、有没有消融 | 多 = 扎实 |
| 算力投入 | 提到的 GPU 数 / 训练量 / 模型规模 | 可量化的投入信号 |
| related work 新鲜度 | 引文里有没有近期工作 | 只引老文 = 可能脱节 |
| 可复现性风险 | 完全不提开源 + 只比老 baseline + 消融避重就轻 | 三者叠加 = 标「关键风险」（"承诺开源"不计，见下） |

> **可复现性风险**是按**行为信号**给的客观预警（不针对任何作者/机构/国别）——历史上"回避开源 + 回避强 baseline + 消融避重就轻"的工作，复现踩坑率高。命中就在量化卡里标「关键风险」。
>
> **开源状态分三态**（day-1 没开源是常态，别误伤）：**已开源**（repo 有内容）/ **承诺开源**（"code will be released"、"coming soon"）/ **完全不提**。只有**完全不提**才算风险因子——day-1 论文代码常 camera-ready 后才放，"承诺开源"和"已开源"都不计风险。

## 产出

每个子 agent **把每篇的量化卡写入 `round2/<arxiv_id>.md`**（**一句话"在做什么"**：用大白话说清这篇解决什么问题、用什么方法——digest 各部分复用它，是单一数据源 + 主表 baseline 列表 + 上述各项 + 风险标注 + 一句客观小结），返回主会话精简结论（arXiv ID + 一句话"在做什么" + 各信号强弱 + 是否建议进第 3 轮）。

> **novelty 破格标记**：子 agent 读 Experiment / Related Work 时，若发现这篇 **claim 了新任务 / 新 benchmark / 新范式 / 新问题定义**，即使量化信号弱，也标"novelty 破格候选"建议进第 3 轮。这是对"质量前置筛"的 novelty 补偿——day-1 最该看 novelty，而 novel 工作往往前期（没中会、实验还在做），纯量化关会把它们刷掉。进第 3 轮的通道 C 见 `round3-deep-read.md`。

> **老话题不专门删**：这个判据自动 handle——老话题里敢比最新 SOTA 且赢的会留下、出现在 digest 的对应话题簇里；只敢比 ResNet 的自然被筛掉。不设单独的"成熟方向降级区"。
