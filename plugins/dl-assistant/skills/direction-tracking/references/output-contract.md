# 文件格式与保存顺序

每个方向使用一个 `track-<方向slug>/` 目录，每次运行都更新该目录。

## 目录树

固定保存目录为 `<项目>/docs/direction-tracking/`。

```
docs/direction-tracking/track-<方向slug>/
├── config.yaml       方向配置，用户可直接编辑
├── seen.jsonl        记录所有获取过的论文及其来源，包括未通过筛选的，供下次去重
├── library.md        累计论文库，只收录通过两轮筛选的论文，采用简报条目格式
├── runs/<日期>-<HHmm>.md   每次运行的简报，文件名附时间，同日多次运行互不覆盖
└── meta.json         上次更新时间 last_run 和进度索引
```

## config.yaml（用户可手改）

```yaml
direction: "一句话说清这方向在研究什么"
keywords:                # 供 A 类关键词查询使用
  - referring expression segmentation
synonyms:                # 可选的同义词组，覆盖不同术语，每组内用 OR
  - [referring image segmentation, RES]
seeds:                   # 供 B 类使用，初始为 2-5 篇种子论文的 arXiv ID。可提名新种子，经用户确认后加入
  - 2304.07899
  - 2305.01511
created: 2026-07-13
```

`<方向slug>` 根据 `direction` 生成，用户可修改。用户也可增删关键词和种子论文。

## seen.jsonl（去重记录，含来源）

每行是一条 JSON 记录。所有获取过的论文都要记录，包括未通过筛选的。

```json
{"id":"2406.12345","source":"A:referring expression segmentation","date":"2026-07-13"}
{"id":"2407.00123","source":"B:2304.07899","date":"2026-07-13"}
{"id":"2405.00077","source":"C:CVPR2026","date":"2026-07-13"}
```

- `source`:`A:<关键词>` / `B:<种子ID>` / `C:<会议年份>`。
- 根据 `library.md` 判断是否通过筛选。已收录表示通过，未收录表示未通过，无需单独保存 accepted 或 rejected。
- **去重依据**。`id` 优先使用 arXiv ID。没有 arXiv 版本的会议论文可用标题哈希或 DOI，标题哈希格式为 `id: "titlehash:..."`。

## library.md（累计论文库）

收录所有通过两轮筛选的论文，按运行时间倒序追加。每篇采用下方的简报条目格式。`idea-find` 可从中查找适合作为选题起点的论文。

## runs/`<日期>-<HHmm>`.md（本次简报）

简报只收录本次首次加入 library 的论文，采用下方的条目格式。文件名包含时间，同一天多次运行时分别保存。

开头说明篇数、子主题和整体情况，随后逐篇列出论文。末尾添加 **「推荐继续阅读或用于选题的论文」**，列出 3–5 篇的 arXiv ID 及具体推荐理由，供 `paper-reading` 或 `idea-find` 使用。

## 论文库和简报共用的条目格式

```markdown
### <标题>
- arXiv: <id> — https://arxiv.org/abs/<id>
- 来源: <A 关键词 / B 种子ID / C 会议年份>
- 为啥相关: <一句话,R1 给的>
- 量化: <baseline 年份·数量 / SOTA / 规模 / 可复现,R2 给的;C 类仅依据摘要和元数据>
- 值得深读   # 可选标记，用于推荐给 paper-reading 精读
```

## meta.json（进度索引，供下次继续运行）

```json
{
  "slug": "referring-segmentation",
  "created": "2026-07-13",
  "last_run": "2026-07-13T14:30:00Z",
  "total_seen": 0,
  "total_library": 0
}
```

## 每次运行的保存顺序

1. 按本次任务获取 A、B 或 C 类论文，合并并去重。**将新 ID 立即追加到 `seen.jsonl`**，这样即使后续未通过筛选，下次也能识别为已获取。
2. 依次进行 R1 和 R2，将通过的论文写入 `library.md` 和 `runs/<日期>.md`。
3. 最后更新 `meta.json` 中的 `last_run=now` 和篇数。

R1 或 R2 未通过的论文已在第一步进入 seen，不加入 library。
