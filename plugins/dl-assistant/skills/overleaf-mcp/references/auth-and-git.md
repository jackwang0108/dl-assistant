# 认证、实例与 Git

## 网页会话

编译、项目元数据、评论和历史使用网页登录会话；Git 使用单独的认证 token，不互相替代。

优先复用已经配置且验证有效的本地会话。需要更新时，在本机终端运行仓库的 `python -m overleaf_mcp.auth_setup --proxy http://127.0.0.1:7890`。脚本在终端不回显地读取 Cookie，取得 CSRF 并验证后才保存，不接收命令行 Cookie 参数，也不把凭证作为工具返回值。

用户需要手动取得 Cookie 时：登录 Overleaf，在浏览器 Network 刷新并选中发往 Overleaf 的请求，从 Request Headers 复制 Cookie 值，粘贴到本地脚本提示处。不要让用户复制整段 cURL 到聊天。不要假定当前浏览器工具能够读取 httpOnly Cookie；有明确支持的认证方式时才使用。

私有 JSON 格式是 origin、cookie、csrf_token；默认路径 `~/.local/share/overleaf-mcp/auth-v2.json`，权限 0600。`overleaf_import_auth(path=...)` 可以验证并导入已有的同实例私有文件；无效候选不替换有效会话。可用 OVERLEAF_CREDENTIALS_PATH 指定文件，但不把凭证本身写进环境变量、仓库或报告。

区分 AUTH_EXPIRED、FORBIDDEN、RATE_LIMITED、网络故障和 API_SCHEMA。403 不自动等于重新登录；编译 CDN 拒绝访问也不等于会话过期。接口结构变了不能当成空项目/空历史。

## 实例与下载

OVERLEAF_BASE_URL 指定实例，记录和凭证绑定实例。OVERLEAF_MCP_HOME 管理本地记录；现有 Git 仓库通过显式绑定保持在用户指定目录。

OVERLEAF_PROXY_URL 可设为 `http://127.0.0.1:7890`。OVERLEAF_CDN_ORIGINS 为允许的下载 origin 列表；默认支持已验证的 Overleaf 编译域。Cookie/CSRF 仅发给配置的 Overleaf 实例，不发送给 CDN；重定向逐次检查。无法确认的域名不自动放行。错误不显示完整请求 URL、Cookie 或 CSRF。

## Git 认证与分支

使用项目提供的官方 Git 链接，凭证使用 [Overleaf Git authentication token](https://docs.overleaf.com/integrations-and-add-ons/git-integration-and-github-synchronization/git-integration/git-integration-authentication-tokens)。官方仍支持在 Account Settings 生成 token；用户名为 git，token 作为密码。优先系统凭证管理器，不在 remote URL 中嵌入 token，不默认使用明文 store。

Overleaf 远端只维护受支持的单一分支；本地可以使用不同分支，通过明确 refspec 对应远端目标。[官方高级操作](https://docs.overleaf.com/integrations-and-add-ons/git-integration-and-github-synchronization/git-integration/advanced-git-operations)说明本地分支映射；旧仓库可能使用不同历史分支名，应核实际目标，不能只凭本地名称判失败。

[官方 Git 限制](https://docs.overleaf.com/integrations-and-add-ons/git-integration-and-github-synchronization/git-integration)说明重命名、移动及普通 push 都可能影响评论/修订，且云端 Git 功能受项目权限/订阅限制。保留当前反馈上下文；有改名必要时依据授权和实际风险处理，不把所有 rename 一律视为禁止。symlink/LFS、文件大小/数量和速率限制需要单独核。

同步被拒时先识别原因；授权允许的整合最多进行有限重试。远端持续变化或语义冲突时保存当前状态、说明差异，不循环直到成功，也不自动 force push。
