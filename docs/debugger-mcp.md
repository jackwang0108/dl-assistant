# Python 调试接入

[mcp-debugger](https://github.com/debugmcp/mcp-debugger) 提供基于 debugpy 的断点、调用栈、变量查看和单步执行。MCP 和 `mcp-debugger` skill 由上游维护，按机器单独安装。本说明以 [v0.26.0](https://github.com/debugmcp/mcp-debugger/releases/tag/v0.26.0) 为接入版本。

## 安装

1. 准备 Node.js 22 或更高版本和 npm。将发行包装到用户目录，并把其启动命令注册到 Codex。

   ```bash
   debugger_prefix="$HOME/.local/share/dl-assistant/mcp-debugger/python-0.26.0"
   npm install --prefix "$debugger_prefix" --omit=optional --ignore-scripts --no-audit --no-fund @debugmcp/mcp-debugger@0.26.0
   codex mcp add mcp-debugger -- "$(command -v node)" "$debugger_prefix/node_modules/.bin/mcp-debugger"
   ```

2. 用 Codex 的 `skill-installer` 安装 `debugmcp/mcp-debugger` 在 `v0.26.0` 下的 `skills/debugging`，安装名为 `mcp-debugger`。重启 Codex，然后打开新会话。 [上游 skill](https://github.com/debugmcp/mcp-debugger/tree/v0.26.0/skills/debugging)
3. 用研究项目实际使用的 Python 执行 `python -m debugpy --version`。缺少 debugpy 时，按该项目的依赖管理方式安装到对应环境。GPU 节点独立运行 Codex 时，在那个节点配置 MCP。

## 验证

`codex mcp get mcp-debugger` 可以核对本机登记的启动命令。随后在新会话中调用 `mcp-debugger` skill，指定项目解释器，启动一个小脚本并在源码中命中断点。读取调用栈和一个局部变量，继续到程序退出，再关闭调试会话。记录所用包版本和解释器。 [上游工具参考](https://github.com/debugmcp/mcp-debugger/blob/v0.26.0/docs/tool-reference.md)

如果 MCP 能初始化，但 `start_debugging` 返回 `listen EPERM`，检查运行 MCP 的环境是否允许调试适配器绑定临时 TCP 端口。

升级时一起更新 npm 包和上游 skill，再重复上述验证。
