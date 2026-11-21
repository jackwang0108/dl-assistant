# Venue Specs（会议规格）

`writing-paper`（起手爬取入口 + 时区规范）/ `numerical-display`（图尺寸）共用。

> **信息分源纪律**：格式与写作规范（页限/模板/栏/匿名写法/图表规范/强制章节/checklist）的权威源是**当年 authorkit**——kit 自带的填充 tex/pdf 就是 venue 亲手写的 guideline，由 op-1 探 kit 时读入契约，不从官网爬。官网入口只用于爬**日程与政策**（deadline / 重要日期 / 投稿入口 / 双重投稿与匿名政策）——这两类信息 authorkit 里没有。两边内容都落 `_draft/venue-contract.md`，那才是本次运行的权威约束。

## 官网入口（爬日程与政策的起点）

| 会议        | 官网（找当年的 Call for Papers / Important Dates）                        |
| ----------- | ------------------------------------------------------------------------- |
| CVPR / ICCV | https://cvpr.thecvf.com/ · https://iccv.thecvf.com/                       |
| ECCV        | https://eccv.eu/                                                          |
| NeurIPS     | https://neurips.cc/                                                       |
| ICLR        | https://iclr.cc/                                                          |
| AAAI        | https://aaai.org/                                                         |
| ACL / EMNLP | https://www.aclweb.org/portal/acl · https://www.aclweb.org/portal/emnlp   |
| TPAMI       | https://www.computer.org/csdl/journals/tp/                                |

子 agent 从入口找**当年** CFP / Important Dates，取：

- **deadline 系列**：abstract 截止、full paper 截止、rebuttal、录用通知、camera-ready 等重要日期（按下节时区规范处理）。
- **投稿入口**：投稿系统链接（OpenReview / CMT / Softconf……）。
- **政策类条目**：双重投稿政策、匿名期规定、利益冲突登记要求、代码/数据开源声明要求。

**格式类（页限/模板/栏/双盲写法/强制章节/checklist）不从官网爬**——官网 author guidelines 页面常是 authorkit 内容的转述，爬来反而引入第二来源、还要和 kit 对账；一律以 authorkit 为准（op-1 子动作 ⑧）。

## 时区规范

deadline 原文的时区表述各异，必须**原文 + 换算双写**进契约，换算结果给用户确认：

- **AoE（Anywhere on Earth）= UTC-12**：CVPR/ICCV/NeurIPS/ICLR/AAAI 等主流会议常用。注意 AoE 3 月 13 日 = 北京时间 3 月 14 日 19:00，别误当成 3 月 13 日 23:59。
- **PST = UTC-8**（部分美国会议/投稿系统）、**CET = UTC+1**（ECCV 等欧洲会议偶用）。
- 原文**没写时区**：按 AoE 假设，契约里显式标注「假设 AoE，待用户确认」——别默默换算。
- 契约中每个日期记三样：**官网原文表述、原文时区、换算后的用户本地时间**。

## 图尺寸（双栏 vs 单栏）

- **双栏会议（CVPR/AAAI/TPAMI）**：单栏图宽 ~3.3 in，双栏图（跨栏）宽 ~7.0 in。文字嵌入后 ≥8pt 可读。
- **单栏会议（NeurIPS/ICLR/ACL）**：图宽 ~5.0-5.5 in，文字 ≥9pt。

当场写绘图脚本时按目标会议设 figsize + 字号（双栏嵌入后仍 ≥8pt 可读）。栏别以契约为准。

## 期刊 vs 会议

- **期刊（TPAMI/IJCV）**：无严格页数，求完整；审稿周期长，可补实验。
- **会议**：严格页数，appendix 补充。
