# 工具与编译流程

## 25 个工具

| 工具 | 用途 |
|---|---|
| overleaf_capabilities | 实例、运行方式和限制 |
| overleaf_auth_status | 配置状态及可选会话验证 |
| overleaf_import_auth | 从私有文件验证/导入会话 |
| overleaf_projects | 项目列表快照与续读 |
| overleaf_create_project | 明确创建项目 |
| overleaf_delete_project | 核对当前 ID/名称后删除指定远端项目，保留本地证据 |
| overleaf_project_files | 项目文件树 |
| overleaf_project_settings | 明确修改编译器、根文档 ID 或检查语言 |
| overleaf_bind_workspace | 绑定并核对现有本地 Git 仓库 |
| overleaf_workspace / overleaf_workspaces | 仓库状态与本地绑定 |
| overleaf_compile | 记录请求后发起一次编译 |
| overleaf_compile_status | 请求状态与已知限制，不虚构远端运行状态 |
| overleaf_compiles | 按请求记录顺序列历史编译 |
| overleaf_compile_report | 源码依据、构建 ID、诊断和产物校验信息 |
| overleaf_read_log | 精确读取已验证日志行，支持续读 |
| overleaf_download_output | 明确下载某次构建的产物并校验 |
| overleaf_render | 渲染明确编译的已验证 PDF |
| overleaf_compare_compiles | 源文件变更、诊断与指定 PDF 页面对比 |
| overleaf_pin_compile | 保留指定编译记录 |
| overleaf_prune_compiles | 预览或明确清理未保留的已结束记录 |
| overleaf_threads | 带历史上下文的评论快照 |
| overleaf_history | 去重、识别停滞的有界历史读取 |
| overleaf_labels | 版本标签 |
| overleaf_version_snapshot | 校验并保存历史 ZIP，不解包 |

## 调用示例

```python
overleaf_capabilities()
overleaf_auth_status(verify=True)
overleaf_projects()
overleaf_bind_workspace(project_id=project, repo_dir="/path/to/paper", remote="overleaf", remote_branch="main")
overleaf_workspace(project_id=project)
# 源码编辑和必要的 Git 同步由调用方完成。
overleaf_compile(project_id=project, expected_commit=full_local_commit)
# 保留真实返回的 compile_id：
overleaf_compile_report(project_id=project, compile_id=run)
overleaf_read_log(project_id=project, compile_id=run, start_line=1)
overleaf_download_output(project_id=project, compile_id=run, filename="output.pdf")
overleaf_render(project_id=project, compile_id=run, pages="1-3", dpi=150)
overleaf_render(project_id=project, compile_id=run, pages="2", bbox=[50,80,400,500], dpi=200)
overleaf_threads(project_id=project)
overleaf_history(project_id=project, max_pages=1)
overleaf_labels(project_id=project)
overleaf_version_snapshot(project_id=project, version=version)
overleaf_pin_compile(project_id=project, compile_id=run)
overleaf_compare_compiles(project_id=project, left_compile_id=old_run, right_compile_id=run, pages="2")
overleaf_prune_compiles(project_id=project, keep=10, dry_run=True)
```

参数以实际 MCP schema 为准。root_resource_path 省略时不向服务器发送 null；它是项目相对路径。root_doc_id 是服务器文档 ID，与路径不同。需要改持久根文档时使用 settings，不能把一次编译选择误当持久设置。

expected_commit 检查本地仓库、未提交内容和校验范围，不执行 Git 同步，也不认证远端编译源码；源文件清单不完整、含不支持的链接或脏工作区时不能通过该检查。没有绑定时仍可编译网页端项目，报告未确认的本地关联。

## 状态与恢复

state 表示请求过程：requested、completed、failed 或 outcome_unknown；classification 为 failed、warnings、clean 或 unknown。completed 不等于编译 clean；clean 不等于 PDF 已下载；PDF 可读不等于论文已完成。

请求先写本地记录，超时/网络中断可能留下 outcome_unknown。进程中断留下的 requested 记录，在保存的请求期限过后会转为未知状态；有已保存服务器响应时可恢复完成记录。不自动再次请求；确认情况并明确决定重试时才用 retry_unknown=true。

当前适配器没有可靠的远端运行中查询接口，因此 compile_status 给本地已知状态，不据旧 PDF 的存在推断后台是否空闲。不可宣称 HTTP 超时就代表服务器编译已停止。

## 日志、产物及比较

诊断保留原始日志流、行号、报告的源文件/行号与严重性。报告的源路径不是本地路径执行指令；需与当前源码及编译版本对应。缺失日志、stderr 或下载错误单列，不能静默忽略后认证成功。

图像名称绑定 PDF 校验值、页码、DPI 和区域，不同渲染不互相覆盖。单次最多十页，DPI 36–400，每页最多 3000 万像素。页码或 bbox 非法明确报错。图像比较只指出像素/页面变化，不解释科学结论，也不把排版位移当成内容错误。

产物先完整下载、格式检查并原子保存，记录字节数与校验值。已保存文件被修改或丢失时报告 ARTIFACT_CHANGED，不静默用另一份文件替换。普通产物的字节下载与 PDF 可读性分别记录；历史 ZIP 做完整性、文件数、展开尺寸和路径检查，不自动提取。

清理先按 dry_run 候选核对。pin 和实际删除以数据库事务保护；下载旧记录不更改最新请求。清理只作用于该实例的托管编译产物，不删除用户仓库、凭证或保留的记录。

## 续读

带 next_cursor 时保持 project、compile_id、流/行号/选页、预算等参数不变。结果快照固定，续读不重新请求远端。records 过大时以 JSON 字符串分片，按 record_index/offset 合并到 final=true 后再解码。

历史还区分上游 next_before_timestamp 与本地 next_cursor：前者获取另一批远端历史，后者读完当前已保存结果。upstream_has_more=null 表示未知，不表示已经读完。
