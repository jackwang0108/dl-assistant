# Overleaf MCP v2

绑定现有本地 Git 仓库，记录远程编译请求、源码依据、日志/PDF、评论与历史。源码编辑与 clone/fetch/push 仍由调用方通过 Git CLI 完成。接口和存储不兼容旧版。

## 安装与认证

```bash
cd mcp-servers/overleaf-mcp
uv sync --extra dev
# 仅首次配置或会话失效时，在本地终端输入，不把 Cookie 放进命令参数或聊天：
uv run python -m overleaf_mcp.auth_setup --proxy http://127.0.0.1:7890
# 启动：
OVERLEAF_PROXY_URL=http://127.0.0.1:7890 uv run python -m overleaf_mcp
```

网页会话用于编译/项目/评论/历史；Git token 单独管理。认证脚本验证后原子写入私有文件，失败不替换原会话。Cookie 和 CSRF 不作为 MCP 参数或返回值。新进程需确认 overleaf_capabilities.api_version=2。

环境变量：OVERLEAF_BASE_URL（默认 www.overleaf.com）、OVERLEAF_MCP_HOME、OVERLEAF_CREDENTIALS_PATH、OVERLEAF_PROXY_URL、OVERLEAF_CDN_ORIGINS、OVERLEAF_COMPILE_TIMEOUT（1–600 秒）。默认认证文件为 `~/.local/share/overleaf-mcp/auth-v2.json`，0600 权限。实例记录放在 home/v2/{instance_hash}/records.sqlite3 和托管 artifacts 中；本地仓库保持原位置。

Cookie/CSRF 只发送给指定实例，下载域名须显式允许；跨域重定向不继承凭证，也不使用 HTTP 客户端的 Cookie jar。默认允许已实测的 Overleaf 编译域，实例/CDN 授权错误、会话过期、限流和网络错误分别返回。不自动重试写请求。

## 25 个工具

| 工具 | 用途 |
|---|---|
| overleaf_capabilities | 实例、格式、限制与凭证配置状态 |
| overleaf_auth_status | 配置/有效/未知状态，可选验证 |
| overleaf_import_auth | 从同实例私有文件验证/导入认证 |
| overleaf_projects | 项目列表快照与续读 |
| overleaf_create_project | 明确创建项目 |
| overleaf_delete_project | 当前项目 ID/名称核对后删除指定远端项目 |
| overleaf_project_files | 项目文件树 |
| overleaf_project_settings | 编译器、根文档和语言设置 |
| overleaf_bind_workspace | 绑定并核对已有 Git 仓库 |
| overleaf_workspace | 本地提交、修改与源文件校验依据 |
| overleaf_workspaces | 本地绑定列表 |
| overleaf_compile | 先记录请求，再发起一次远程编译 |
| overleaf_compile_status | 本地请求状态和无法确认的远端状态 |
| overleaf_compiles | 稳定的编译请求顺序 |
| overleaf_compile_report | 源码/服务器构建依据、诊断和产物信息 |
| overleaf_read_log | 按流/行号读取已验证日志 |
| overleaf_download_output | 按构建引用下载、原子保存、校验产物 |
| overleaf_render | 1-based PDF 页面或区域渲染 |
| overleaf_compare_compiles | 源文件、诊断和页面图像对比 |
| overleaf_pin_compile | 保留指定记录 |
| overleaf_prune_compiles | 默认 dry-run，明确清理未保留的结束记录 |
| overleaf_threads | 评论原文、定位与版本观察快照 |
| overleaf_history | 有界历史读取、去重与停滞检查 |
| overleaf_labels | 版本标签 |
| overleaf_version_snapshot | 校验历史 ZIP 并保存，不解包 |

具体调用与规则见 [skill](../../plugins/dl-assistant/skills/overleaf-mcp/SKILL.md)。

## 证据与状态

state 记录 requested/completed/failed/outcome_unknown；classification 记录 failed/warnings/clean/unknown。服务器失败不会被日志的未命中覆盖。PDF 是否可读另列，不能把三个状态互相替代。

每次返回本地 compile_id，并保留可取得的远端 build ID。源码记录包括用户绑定的本地 Git 提交/工作区状态、内容校验值及前后历史观察。expected_commit 只检查干净的本地提交；网页接口没有可认证的“原子编译指定 Git SHA”能力，因此 source_binding 保留未确认状态，观察到变化时单列。

请求在发送前写入数据库。超时、进程中断或部分响应可能留下未知结果；不会自动重新编译。compile_status 返回本地证据，不根据旧 PDF 推断远端已空闲。只有调用方明确决定时才使用 retry_unknown。

下载旧记录只更新它自己的产物，不修改最新指向。并发元数据写入和保留/清理通过事务处理。没有自动删除旧十次编译的行为；pin 与显式 dry-run/prune 管理保留。工具不会删除用户仓库或凭证。

所有大结果使用 items/truncated/next_cursor；max_chars 包含完整 JSON。大记录使用 record_fragment，按 record_index/offset 拼接 text 后 JSON 解码。续读使用相同范围和预算；编译相关读取建议显式传 compile_id，避免默认 latest 在两次调用之间发生变化。

图像按 PDF 校验值、页码、DPI 和 bbox 命名。页码从 1 开始，bbox 为 `[x0,y0,x1,y1]` PDF 点、左上原点。单次最多十页、DPI 36–400、每页最多 3000 万像素。像素差异只说明排版图像变化，不替代科学或编辑判断。

Overleaf 网页接口并非稳定公开 API；响应结构不符会明确报错，不伪装成空列表。实际支持范围、请求格式和限制以实测记录为准。

## 测试

```bash
uv run pytest -q
uv run ruff check src tests
uv run ruff format --check src tests
# 显式联网；会创建且清理独立、唯一命名的测试项目，不修改已有论文：
OVERLEAF_RUN_LIVE=1 OVERLEAF_PROXY_URL=http://127.0.0.1:7890 \
uv run pytest tests/test_v2_live.py -q
```

单元测试包含判据冲突、凭证/域名边界、完整 JSON 预算、输入与路径检查。集成测试使用真实 SQLite、Git 仓库、PDF/渲染以及受控 HTTP，覆盖失败/恢复、旧产物、缓存修改、并发、保留/清理和 ZIP 验证。e2e 检查全部工具、MCP annotations，并启动真实 stdio 子进程连接真实本地 HTTP 服务。

真实 Overleaf 验证记录在 [validation-report.json](tests/validation-report.json)。测试项目使用独立名称并清理；真实 Git push 不在该测试范围内，不需要 Git token。
