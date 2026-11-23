# 目标 8：finalize（定稿交接）

## 何时用

内容定稿（audit 通过）后，做投稿前的最后整理与交接。分两半，中间一个确认点等用户交付。

## 读哪些

- `references/craft/visual-aesthetic-review.md`（全局版式回归的检查清单）。
- `_draft/visuals/manifest.json`（图表终稿清单 + priority）+ `_draft/venue-contract.md`（页限 + 排版层手段是否允许）+ `paper-state.json`（`compress_candidates`）。

## 子动作

### 上半：确认正文，再请用户准备终稿材料

1. 跑 audit（见 op-7）确认内容锁死。**先锁内容再让用户画 PPT 终稿**——内容还在动会让用户白干。
2. **blueprint 同步 + 确定性门禁**：刷新 `blueprint.md` 与成稿一致（标「竣工版」）——下游（response / 改稿 / 续写）拿到真实脊柱。随后 `python <writing-paper-skill目录>/scripts/run_checks.py <论文根> all` 必须 exit 0 才许往下——audit 跑过之后 blueprint 同步/交互改可能又动了 .tex，交接前以这次全绿为准。

### 确认点：等用户交付（异步，可续跑）

3. 请用户准备以下两项材料，收到后继续：
   - **示意图 PPT 终稿**（照 HTML 草稿在 PPT 重绘成投稿质量，导出 PDF 替换 `figures/<id>.pdf`；草稿里的终稿交接备注在 `<id>.md`）。
   - **bib 正式 venue 格式**（proceedings/booktitle/页码统一手修）。

### 下半：定稿（交付物到位后）

4. **替换 + 关键节点 Overleaf 同步**：PPT 终稿替换 `figures/<id>.pdf` + 正式 bib 落 `refs.bib` → 确认本地编译通过 → fetch+整合 → push → `overleaf_compile` 确认远程编译也通过 → 远端渲染回归（这是同步节点，finalize 前必做）。
5. **定稿时压缩篇幅（在最终版面上做，一次到位）**——终稿图已插入、版面是最终的，此刻压缩才不会白压：

    1. **算缺口**：当前页数 vs venue 页限（venue-contract）——每次本地验证都在报页数，这里不该有惊喜。没超 → 跳到 6。
    2. **产压缩方案**：以 state 的 `compress_candidates` 为底 + 全文过一遍，逐项列「动作 + 预估回收页数」，按对正文影响从小到大排序：
        - ① **内容移入附录**（对正文影响最小）。
        - ② **删减次要内容**（compress_candidates 清单优先）。
        - ③ **精简文字**（合并重复表述、删铺垫冗余、RW 收紧、setup 细节挪 appendix）。
        - ④ **表处理**（大表拆：正文留核心列、全表进附录）。
        - ⑤ **排版层**（图表-caption 间距 / 浮动体间距——**先查 目标会议要求是否允许**，禁 `\vspace` 类间距 hack 的会议靠 ①②③④）。
    3. **图的挪/不挪（硬规则）**：
        - **不可挪**：teaser（首页图，故事线核心）、pipeline/架构图（Method 的载体）——正文硬性，不单独挪附录。
        - **可挪**：次要分析图、补充定性图、数字已进表的消融图。
        - **判据**：按 visual spec 的 `priority`——must 不挪，should/appendix 可挪；挂正文核心 contribution 的图不挪。
    4. **禁区**：teaser/pipeline 等核心图**不压尺寸**（它们就该大）；图内字号**不压到 venue 下限以下**。
    5. **确认点：由用户逐项确认**——内容取舍的判断权在人，agent 不替人砍。每执行一批重新本地编译看页数，迭代到达标。
    6. **定案回写 state**：compress_candidates 各项置 accepted/rejected；受影响节 status 置 needs-revision（或修完回 drafted）。
6. **全局版式回归**（收窄——逐节美学不再重复，每张图都是用户看预览图后确认过的）：只查全文拼起来才出现的问题——浮动体全局位置（图跑到引用位置太远）、跨页断表、空白页、overfull 超宽警告堆积、全文图表尺寸一致性、首页 teaser 位置、无 `??`（清单见 `visual-aesthetic-review.md`；压缩重排过版面，这步必须在压缩后）。
7. **manifest + writing.log + 汇报**：产物（C-ID 关联）+ 论文状态 + 待人修项。
8. **里程碑**：用户认可 → git tag + state 记里程碑。
9. **交接包清点 + 交接**：简要说明交接状态（编译通过 / 页数合规 / 强制章节齐 / authorkit 待填材料已注册 backlog / 补充材料齐没齐）→ PDF + 论文草稿 → `writing-paper-review`（盲审）/ `writing-paper-submission`（终审 + authorkit 材料填写）；`venue-contract.md` 已就位，submission 直接消费。

## 产出

最终 `content/*.md` + `sections/*.tex`（Overleaf 编译出 PDF）、`figures/`（PPT 终稿 + 用实际数据绘制的图）、正式 `refs.bib`、竣工版 blueprint、压缩定案（state）、里程碑 tag、汇报。

## 状态更新

节 status → locked；blueprint 竣工标记；compress_candidates 定案；milestones 加一条；backlog 清帐。

## 确认点

- 上半：audit 中可能改变原意的修改（meaning-risk）。
- 中间：等用户交付 PPT 终稿 + 正式 bib。
- 定稿时压缩篇幅：逐项由用户确认。

## 易错点

- **先锁内容再让用户画 PPT 终稿**——避免用户白干费时人工。
- **先插终稿图再压缩**——终稿图和草稿/占位的物理尺寸不完全一致，先压缩再换图版面变了可能白压一轮；在最终版面上压缩，一次到位。
- **示意图终稿是用户 PPT 画**，agent 不画终稿（agent 的 HTML 永远只是草稿）。
- **bib 正式化是用户的事**，agent 不花力气搞正式检索。
- **finalize 不是第一次查合规的地方**——合规全程在查（目标会议要求 + 每次本地验证报页数 + audit），这里只是确认。
- **定稿时压缩篇幅才做内容取舍**——写作期先完整写出各节内容（可砍项在 state 的 `compress_candidates` 里攒着）；图的挪/不挪按 priority + 核心 contribution 判（teaser/pipeline 不可挪）；核心图尺寸与字号是禁区，不碰。
- **全局版式回归在压缩后**——压缩重排了所有浮动体，压缩前查等于白查；逐节美学不重复（每图用户都拍过板）。
- 合规终审（字体嵌入/断引用/重 label/PDF metadata/bib 格式）+ authorkit 材料填写 → `writing-paper-submission`；reviewer 通读 → `writing-paper-review`。
