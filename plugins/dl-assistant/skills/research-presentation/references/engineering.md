# 构建、检查与离线交付

## 环境与固定版本

本skill基于 [ryanbbrown/revealjs-skill](https://github.com/ryanbbrown/revealjs-skill) 的工程思路扩展；核对的上游commit为 `d0ccd344c4aaf9f045e5a15be6a2ab67b595796f`。原MIT许可保存在skill根 LICENSE。内容规划、视觉取材、运行/检查与交付流程在本项目维护，不冒称上游认证。

使用Node.js 22.12+。本skill的package.json/package-lock.json固定构建和测试依赖，不依赖另一个plugin根目录。

```bash
cd <skill目录>
npm ci --ignore-scripts
```

安装阶段可按实际网络设置代理，用户指定Clash时使用 `--proxy=http://127.0.0.1:7890 --https-proxy=http://127.0.0.1:7890`。不要将代理写入所有项目的全局配置。禁安装脚本时不自动下载浏览器；渲染使用已有Chrome/Chromium，或通过 `PUPPETEER_EXECUTABLE_PATH` 指定实际可执行文件。没有浏览器时明确未渲染，不标视觉通过。

默认创建HTML/CSS、本地vendor资源和manifest。按features只加载需要的库，依赖目录可能含未加载的插件文件。所有运行文件随deck目录交付；不能只发送HTML后仍声称离线可用。本地字体采用系统中文回退，跨机器字体差异仍需目标环境查看。特殊字体经许可本地打包并检查实际字形，避免在线字体依赖。

## 新建与修改

```bash
node <skill目录>/scripts/create-presentation.js --plan talk.plan.json --features charts,math,code,mermaid --output output/talk.html
node <skill目录>/scripts/generate-theme.js --primary "#24577a" --mode light --output output/styles.css --force
node <skill目录>/scripts/serve-deck.js output/talk.html
```

--plan、--slides、--structure三选一；structure的正整数表示该横向位置的纵向页数，d表示分隔页。缺参数/非整数/未知feature不静默接受。样式文件需为输出目录内单个CSS文件名。

生成器保留待填内容和视觉位置，任何data-placeholder未落实都不是成品。--force只用于已明确需要替换的生成文件，会建立唯一备份；不要用它反复重建含用户改动的整套HTML。已有vendor文件不同会拒绝覆盖，换目录或核明差异再处理。

同目录server仅监听127.0.0.1。iframe和fetch本地JSON应通过HTTP预览，直接双击file://可能受浏览器限制。摄影/音视频/数据等放assets并用相对路径；不要用绝对机器路径。serve-deck不自动开放网络或分享项目。

## 检查和导出

```bash
node <skill目录>/scripts/check-content.js --plan output/talk.plan.json --html output/talk.html --report output/content-check.json
node <skill目录>/scripts/check-charts.js output/talk.html
node <skill目录>/scripts/check-overflow.js output/talk.html --report output/layout-check.json
node <skill目录>/scripts/render-deck.js --html output/talk.html --out output/render-round-1
```

- 内容检查：计划/实际页ID、时长声明、来源、视觉任务、素材文件/放置、媒体和交互的静态替代。0表示所查声明一致；1是错误；3是素材/占位尚未完成。
- 图表检查：实际内嵌JSON/CSV或本地数据文件、图表类型、有限数值和标签长度；不认证统计或数据真实。0无发现，1错误。
- 溢出检查：使用真实浏览器逐页和逐fragment状态测量，外网资源、加载/JS/公式/图解错误会进入问题记录。0为已检查状态无发现，1为发现问题，3为环境/渲染不足。测量不保证所有对象无遮挡。
- 导出：输出每页静态截图、live状态截图、讲者备注、PDF和render-report.json；输出目录需为空，避免覆写历史。1表示记录了渲染/布局问题，3表示导出无法完成。报错时可能已有部分产物，保留并标草稿。

浏览器检查/导出阻止外网请求。它核当前deck路径，不证明未访问的未来交互也完全离线。需实际操作关键交互；交付前核manifest/素材存在、PDF页数及关键内容，不把PDF文件非空当成功。

PDF采用export状态及Reveal的print-pdf布局；普通逐步显示合并到静态页。互斥显示、滑块、音视频、网页演示需显式export-only替代，不依赖自动冻结最后一帧。pdfMaxPagesPerSlide=1只限制分页，可能裁内容，仍须看截图和PDF。官方 [PDF导出](https://revealjs.com/pdf-export/) 和 [Fragments](https://revealjs.com/fragments/) 可用于核对当前API。

## 文字编辑

`node <skill目录>/scripts/edit-html.js talk.html` 启动本机编辑器。只更新选中的文字源片段，保留JS、SVG、图表配置及未修改源码；不把浏览器执行后的DOM整页写回。原文包含公式或代码时直接改源码。保存含行内强调的文字会将该片段变成纯文字，需要时在源码恢复格式。

保存需匹配原source hash，冲突返回409并要求重新核对；每次真实改动创建备份。局部HTTP服务限制到deck目录，不能借静态资源路径读取目录外文件。这个编辑器是便利工具，不替代Git与交付检查；修改后旧截图/PDF核查不再作为当前版通过记录。

## 验证与维护

```bash
cd <skill目录>
npm test
```

测试包含参数/覆写、图表/规划记录、编辑冲突与边界，以及真实浏览器的隐藏页溢出、渲染、导出和交互；需要本机浏览器。环境缺少时标跳过/不足，不将其写成全通过。具体本轮范围见 [验证记录](../validation/report.json)。
