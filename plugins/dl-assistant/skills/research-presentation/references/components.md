# 可复用的页面元素

组件服务信息关系，不为页面凑数量。base-styles.css包含以下可选类：

| 类 | 合理用途 |
| --- | --- |
| callout | 强调限制、待答问题或关键定义 |
| stat-card / stat-number / stat-label | 呈现少量有单位和来源的数字；不替代分布/比较 |
| feature-card | 并列说明少量项目能力/约束 |
| timeline / timeline-item | 有实际先后关系的过程或进展 |
| badge / tag | 类别/状态标注，不能仅靠颜色区分 |
| compare | 保持对象对应的两侧比较 |
| code-block | 必要的代码片段与输出说明 |
| text-muted | 次要说明；仍需足够对比度 |

同一模式多次使用时可定义CSS类。按页独有布局可行内设置，不强制“只能inline”或禁止复用grid。来源、解释和图像仍需实际落实，卡片/图标不自动计为视觉证据。
