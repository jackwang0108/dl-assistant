# DL Assistant

面向深度学习科研的 Codex 插件和本地 MCP 工具。覆盖文献调研、研究问题与实验设计、复现、结果分析、论文写作、审稿和汇报。流程入口是 [dl-assistant skill](plugins/dl-assistant/skills/dl-assistant/SKILL.md)。

## 在新机器上安装

以下命令面向 macOS 和 Linux，需要 Git、Codex、Python 3 和 uv。安装脚本默认使用 Python 3.12 运行 MCP 服务。使用 Windows 时可在 WSL 内运行命令，并从同一环境启动 Codex。

1. 把 GitHub 仓库克隆到本机，然后进入仓库根目录。在 Codex 桌面端打开这个目录，进入 Plugins，在仓库提供的 **DL Assistant** 来源中安装插件。希望在其他科研仓库中也找到它时，可从本仓库根目录运行 `codex plugin marketplace add "$(pwd)"`，再从桌面端安装。找不到来源时，重启桌面端后再检查。安装流程见 [OpenAI 插件文档](https://developers.openai.com/plugins/build/plugins)。
2. 需要论文检索、TeX、PDF 或 Overleaf 时，运行下面的命令。它安装本地 MCP，并生成基于当前克隆位置的 Codex 配置。添加到本机 `~/.codex/config.toml`，已有同名服务时替换对应段落，然后重启 Codex。

   ```bash
   python3 scripts/setup-mcp.py
   ```

   可用 `--server paper-search --server tex-mcp --server pdf-mcp` 只装所需服务。`--proxy http://127.0.0.1:7890` 会用于安装依赖，并写入生成的 MCP 配置。移动克隆目录后重新生成配置并重建本地环境。
3. 在新会话调用 `dl-assistant` skill 或请求阅读一篇论文。MCP 启动自检如下，默认配置装好后即可运行。只装部分服务时，用任一已安装 MCP 的 Python 运行脚本，传入 `--server` 指定需要检查的服务目录名。

   ```bash
   mcp-servers/paper-search-mcp/.venv/bin/python scripts/check-mcp.py
   ```

插件负责安装 skills。MCP 是各机器独立启动的服务，路径、凭证、代理及可选模型按机器配置。已有全局安装的同名旧 skill 时，让测试会话选用插件里的版本，避免混用。

## 可选能力

| 能力 | 配置 |
| --- | --- |
| 论文检索 | [Paper Search](mcp-servers/paper-search-mcp/README.md) 支持 arXiv。其他来源按需使用该目录的 `.env.example` 建本地 `.env` 并配置对应密钥。 |
| TeX 源码阅读 | [TeX MCP](mcp-servers/tex-mcp/README.md) 提供本地源码与 arXiv 阅读。复杂图的隔离渲染单独配置。 |
| PDF 与结构化全文 | [PDF MCP](mcp-servers/pdf-mcp/README.md) 默认支持原页与文字读取。需要 Docling 时，安装命令加 `--docling`，模型按 PDF MCP 文档准备。 |
| Overleaf | [Overleaf MCP](mcp-servers/overleaf-mcp/README.md) 按需在本地终端运行 `mcp-servers/overleaf-mcp/.venv/bin/python -m overleaf_mcp.auth_setup`。需要代理时给命令传 `--proxy`。使用新机器上的有效登录会话，凭证默认存在用户目录。 |
| W&B | 按 [接入说明](plugins/dl-assistant/skills/wandb/references/deployment.md) 配置自己的实例、SDK、MCP 和凭证。 |
| 汇报幻灯片 | 用 Node.js ≥ 22.12，按 [汇报工程说明](plugins/dl-assistant/skills/research-presentation/references/engineering.md) 安装依赖和准备浏览器。 |

科研项目、实验数据和结果放在自己的研究仓库里。插件仓库只保留可复用的 skills、MCP 源码、测试和示例。详见 [维护与发布](docs/maintaining.md)。
