# 代码与输出

启用--features code，使用本地RevealHighlight插件。只展示需要解释的真实片段或显式标注的小例子，保留来源文件/版本；省略部分注明，不以伪代码冒充项目已经实现。

```html
<pre><code class="language-python" data-trim data-line-numbers="1-2|3-4">
values = read_observations()
valid = select_by_approved_rule(values)
result = summarize(valid)
print(result)
</code></pre>
```

代码行高亮可逐步讲述，旁边或下一页放相应输入/输出。真实输出给运行来源；示例输出说明计算假设，不编执行记录。控制代码宽度/行长，需要滚动才能看关键行时拆成几页。

PDF保留必要完整代码与输出，避免只导出某个高亮步骤而遗漏解释。截图核高亮对比度和字号；默认代码深色底，本地主题与正文配色需兼容。
