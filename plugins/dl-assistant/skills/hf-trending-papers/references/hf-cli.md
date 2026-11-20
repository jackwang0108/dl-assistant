# hf papers 命令参考

本文件集中维护 CLI 用法，入口只维护分析流程。参数以当前安装版本帮助为准，不将旧版观测当作永久接口保证。

## 本地版本与命令检查

以下语法曾在本机 `huggingface_hub / hf 1.16.1` 的帮助中核对。使用其他版本时先检查：

```bash
hf version
hf papers --help
hf papers ls --help
hf papers info --help
hf papers search --help
```

`list` 的别名为 `ls`。帮助仅证明命令支持，不证明服务端数据完整、字段固定或时间语义。

```bash
hf papers ls --date YYYY-MM-DD --format json
hf papers ls --week YYYY-Www --sort trending --limit 50 --format json
hf papers ls --month YYYY-MM --sort trending --limit 50 --format json
hf papers ls --sort trending --limit 50 --format json
hf papers search '<方向>' --limit 20 --format json
hf papers info <arxiv_id> --format json
```

日期、周、月按用户请求择一，不混用。昨天先解析为明确日期，不传 `today`。无日期的热门查询不能标为某日完整日报。`--format json` 显式请求结构化结果；保存退出状态、原始 JSON 与实际字段。

上述版本的列表默认 limit 为 50，搜索为 20；帮助没有分页选项。旧文档记录过服务端 limit 上限为 100，当前使用时按真实响应核实，不承诺该上限恒定或返回全部结果。达到上限或完整性未知时标为有限样本，主题搜索也不能当作全面检索。

## 安装与认证

命令不存在时说明缺失，安装方式参考可用的 `hf-cli` skill 或官方文档。临时运行可使用明确的包名：

```bash
uvx --from huggingface_hub hf papers --help
```

安装或升级会改变环境，按用户授权执行；不为普通查询自动全局升级。不同版本的可用参数先用帮助核实。

公开只读数据先匿名查询。需要认证时使用当前版本支持的 `hf auth login`，交互输入凭据；不把 token 放入命令记录、原始文件或报告。不要假设登录必须经过浏览器，也不为普通错误要求用户登录。

## 返回字段处理

字段以每次原始响应为准；先验证 JSON 结构再解析，保留原始字段，不静默将 schema 变化当成空结果。

| 内容 | 处理 |
| --- | --- |
| `id`、`title`、`summary`、作者 | 检查实际是否存在；确认 ID 为 arXiv ID 后用于交接 |
| `published_at`、`submitted_at` 等日期 | 保留源字段含义和时区；不混同日报日期、arXiv 提交日或指标观测时间 |
| `upvotes`、`comments` | 分别记录，缺失/null 与 0 不同 |
| `organization` | 某些响应可能有，注明来源，不保证完整作者机构归属 |
| `ai_keywords`、`ai_summary` | 平台生成内容，可能为空；结合原始标题与摘要核对 |
| `github_repo`、`github_stars` | 仓库关联与关注度，不是代码有效性或使用量证明 |
| `linked_models`、`linked_datasets`、`num_total_models` | 保留资源 ID、是否为部分列表及总数字段；未列 ID 时不能精确去重累加 |

列表和详情字段可能不同，不能以一个响应缺字段判断该资源不存在。`info` 不保证包含正文；本 skill 的内容判断须标明实际使用摘要还是其他来源。深入阅读交 `paper-reading`。

## 日期与错误处理

| 情况 | 动作与停止条件 |
| --- | --- |
| 命令或子命令不存在、参数不兼容 | 检查版本与帮助，按实际支持的语法调整；能力确实缺失时报告，不循环重试 |
| 合法空列表 | 说明请求范围与获取时间；不自动换日期或推测原因 |
| 日期超过源站可用日期 | 原样记录错误与其提示的最新日期，询问是否改查该日；未经用户选择不自动回退 |
| 明确认证错误，如 401 | 检查是否需要登录或现有认证失效，请用户完成认证后再试；不显示凭据 |
| 403 | 按错误内容区分权限与服务拒绝，不能一律靠登录处理 |
| 429 或明确限流 | 按 Retry-After 等待；无指示时有限退避，最多额外重试两次；等待较长时报告并停止，不把登录当成必然修复 |
| 超时、DNS、连接失败、5xx | 先区分环境网络限制与源站错误，按环境权限要求处理；对可重试故障最多额外重试两次，仍失败则保存错误并报告 |
| 非法 JSON 或结构变化 | 保存原始错误响应、注明解析失败，不继续用不完整数据生成确定结论 |

不同故障分别记录，探测与正式请求共享重试上限，不设置无限重试流程。用户重新授权或外部条件改变后可以再次尝试。一个详情请求失败不影响其余已获取论文的介绍，但报告需写明缺失。

跨日期查询得到的投票与 star 都记录实际观测时间；除非有历史证据，不能回填成历史日期当时的值。

官方参数文档可在需要时查阅：https://huggingface.co/docs/huggingface_hub/en/guides/cli
