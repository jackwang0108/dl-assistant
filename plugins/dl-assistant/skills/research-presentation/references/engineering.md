# 安装与检查

在包含本 skill 的 `package.json` 的目录运行：

```bash
npm ci
```

`check-overflow.js` 通过 Puppeteer 打开浏览器，`check-charts.js` 通过 Cheerio 检查图表配置。如果默认 Chrome 无法启动，可安装 headless shell，或用 `PUPPETEER_EXECUTABLE_PATH` 指向本机浏览器。

```bash
npx puppeteer browsers install chrome-headless-shell
node scripts/check-overflow.js /path/to/presentation.html
node scripts/check-charts.js /path/to/presentation.html
```

生成初始 HTML 后，在浏览器中检查所有幻灯片。按 [逐页截图检查步骤](../SKILL.md#step-6-visual-review-with-screenshots) 用 Decktape 导出 PDF 和截图。v9 生成的 HTML 从 CDN 载入前端库，打开 HTML 和导出时需要能访问这些资源。
