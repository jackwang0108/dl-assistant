# paper-search-mcp v2

面向 agent 的论文检索 MCP：稳定标识解析、多来源检索、引用与相关论文、作者机构消歧、资源校验下载和记录导出。旧接口与数据库不兼容；保留的是原有功能，不是旧名称/参数。

## 安装与运行

```bash
cd mcp-servers/paper-search-mcp
uv sync --extra dev
uv run python -m paper_search_mcp
```

MCP 客户端配置中的 directory 应指向本目录，入口为 `python -m paper_search_mcp`。更新后重启 MCP 进程并确认 `get_capabilities().api_version == 2`、工具列表包含以下 15 项。不要只更新说明文档却继续调用旧进程。

环境变量及本目录 `.env` 可提供 `SEMANTIC_SCHOLAR_API_KEY`、`SERPAPI_KEY`、`OPENALEX_API_KEY`。Scholar 需要 SerpAPI 密钥；其他来源的认证状态和实际错误由工具报告，不保证匿名访问可用。配置模板见 `.env.example`，不要提交真实密钥。

`PAPER_SEARCH_CACHE_DIR` 默认 `~/.cache/paper-search-mcp`，v2 使用 `records-v2.sqlite3` 和 `assets/`。旧缓存不迁移也不读取；旧 `PAPER_SEARCH_DB_PATH` 已取消。重建缓存会使查询 ID/游标失效，长期交接使用论文稳定标识及导出记录。

## 工具

| 工具 | 用途 |
|---|---|
| get_capabilities | 启用来源、实际支持条件及配置缺失 |
| resolve_papers | 外部标识/URL 解析，或书目信息候选匹配 |
| get_papers | 批量元数据，normalized/sources/versions 视图 |
| search_papers | 多表达式、按来源查询及明确过滤 |
| get_paper_citations | 后续引用者 |
| get_paper_references | 参考文献 |
| find_related_papers | 共同引用关系或来源推荐 |
| search_authors | 作者候选及消歧信息 |
| search_institutions | 机构候选及消歧信息 |
| get_entity_papers | 已确定作者/机构的论文 |
| get_query_results | 读取已有不可变快照，不调用上游 |
| extend_query | 继续获取、补失败、增加检索表达式、刷新 |
| list_paper_assets | 来源发现的页面/PDF/源码及版本 |
| download_paper_asset | 限额下载、格式验证、校验值及缓存 |
| export_records | JSON/BibTeX/Markdown 导出及缺失项 |

使用指南与示例见 [paper-search skill](../../plugins/dl-assistant/skills/paper-search/SKILL.md)。签名与嵌套输入约束由 MCP schema 提供，避免维护第二份参数定义。`examples.py` 默认只展示能力；`--search` 才执行一项受限检索。

## 返回与内部实现

- `paper_ref` 是带命名空间的外部标识，不是本地整数主键。只依据来源提供的标识关联记录，不按同名标题合并作者或论文。
- `store.py` 独立保存各来源原始观测，合并视图保留字段出处和冲突；不将合并信息写回成各来源数据。
- `providers.py` 使用明确 REST 请求及真实上游分页，不依赖旧 arxiv/pyalex 包的隐含重试与分页。
- `transport.py` 控制请求/耗时预算、限流和有限重试；错误返回不含认证请求 URL 或密钥。来源按任务顺序执行，组合结果不是全局相关性排名。
- `service.py` 保存不可变检索快照，`extend_query` 创建新快照；旧游标仍读取旧内容。查询状态、来源失败、预算停止及覆盖限制分别报告。
- `assets.py` 仅下载该论文已发现资源，流式限制大小、处理有限重定向、验证可解析文件，完成后原子替换。PDF 格式验证不等于论文身份独立认证；源码只验证 tar、不解压。
- `server.py` 仅注册上述 15 项工具，业务逻辑可脱离 MCP 协议测试。

字段少不等于数据可信：搜索片段与摘要分开，各来源引用数分开，版本视图只列已观察内容。精确日期缺失、来源不支持过滤和有限推荐集合均需向调用方说明。没有命中不能证明没有先例。

## 测试

```bash
uv run pytest -q
uv run ruff check src tests examples.py
uv run ruff format --check src tests examples.py
# 显式启用，使用临时缓存；会访问真实来源并可能使用付费额度：
RUN_LIVE_TESTS=1 uv run pytest tests/test_live.py -q
```

单元测试覆盖标识、字段与版本保存、输入验证、HTTP 错误、限流和预算；集成测试通过受控 HTTP 响应执行真实来源适配、SQLite、快照、引用和文件流程。e2e 通过 FastMCP Client 检查完整工具列表、多步调用、错误参数，并启动真实 stdio 子进程检查连接与调用。默认不会请求真实上游；live 测试显式启用且逐来源报告失败，不将网络故障算作成功。

重构过程中已对四来源真实检索、SS 日期/引用分页/参考文献/作者/推荐、OpenAlex 引用/机构及论文、付费 Scholar 搜索与引用、15 页真实 PDF 下载作小规模验证。已保留不含密钥的[真实验证记录](tests/live-validation-report.json)。真实接口仍可能变更或限流，这些测试不证明完整召回或长期可用性。
