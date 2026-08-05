+++
date = "2026-08-05"
title = "Hugo 静态站点踩坑实录：分页、归档、脚注引用与 TOML 配置的连环坑"
slug = "hugo-static-site-troubleshooting-pagination-archive-footnote-toml-guide"
categories = [ "技术教程", "静态站点" ]
tags = [ "Hugo", "静态博客", "模板开发", "TOML", "踩坑记录" ]
readingtime = true
+++

## 开篇：一个 Hugo 静态站点的"体验"之旅

我用 Hugo 搭了一个站点，站点跑起来之后，看着似乎一切正常，直到我仔细点了点页面底部的分页按钮——**翻页之后，文章列表纹丝不动，每一页都显示全部文章**。

这成了我一系列踩坑的起点。从分页失效，到分页样式丑陋，再到文章归档后列表凭空消失，再到 TOML 配置写错位置导致功能静默失效……前后折腾了好几轮，把 Hugo 模板渲染、页面集合、分页机制、CSS 构建、TOML 层级解析这些知识点扎扎实实地过了一遍。

这篇文章按我实际排查和修复的顺序，把整个过程和学到的东西完整记录下来。

---

## 一、分页不生效：`.Pages` 和 `.Paginator.Pages` 是两回事

### 现象

`/post/` 列表页底部有分页导航（页码 1、2，还有 Prev/Next 箭头），看起来像是正常渲染了。但点击第 2 页后，**文章列表和第 1 页完全一样**，全部 17 篇文章原封不动地展示。

### 排查过程

我先去看了主题的列表模板 `layouts/_default/list.html`：

```go-html-template
{{ define "main" }}
    {{ partial "breadcrumb.html" . }}
    <h1 class="text-2xl font-bold mb-4">{{ .Title | default (.Section | humanize) }}</h1>
    {{ .Content }}
    {{ range .Pages }}
        {{ partial "list-item.html" . }}
    {{ end }}
    {{- /* Pagination */ -}}
    {{ if .Paginator }}
    {{ partial "pagination.html" . }}
    {{ end }}
{{ end }}
```

问题一目了然：**循环遍历用的是 `.Pages`，不是 `.Paginator.Pages`**。

`.Pages` 返回的是当前 section 下的**全部页面集合**，跟分页没有任何关系。而 `.Paginator` 虽然在后面的 `{{ if .Paginator }}` 里被访问了（Hugo 会在首次访问 `.Paginator` 时自动初始化分页器，并生成 `/post/page/2/` 等分页页面），但循环体仍然在遍历完整的 `.Pages`，所以每一页渲染出来的文章列表都是全量。

我用 grep 验证了一下构建产物：

```bash
grep -c 'itemprop="name"' public/post/index.html
# 输出 17（全部文章）
grep -c 'itemprop="name"' public/post/page/2/index.html
# 输出 17（还是全部文章）
```

两页都是 17 篇，确认了问题。

### 修复

把 `{{ range .Pages }}` 改成 `{{ range .Paginator.Pages }}`：

```go-html-template
{{ range .Paginator.Pages }}
    {{ partial "list-item.html" . }}
{{ end }}
```

访问 `.Paginator` 会触发分页初始化，`.Paginator.Pages` 只返回**当前页**对应的那部分文章。同时把 `{{ if .Paginator }}` 的判断去掉，直接渲染分页导航即可。

分类页 `category.html` 和标签页 `tag.html` 也有同样的写法，一并修复。

### 顺带修复：废弃的 Scratch API

分页导航模板 `pagination.html` 里用了 `$.Scratch.Set` / `$.Scratch.Get`。这是 Hugo 早期版本提供的临时数据存储机制，后来被 `$.Store` 替代。我当前 Hugo 版本是 v0.154.5，`Scratch` 虽然还能用（构建没报错），但已经被标记为废弃。为了避免将来升级 Hugo 后模板报错，我把所有 `$.Scratch` 替换成了 `$.Store`：

```go-html-template
{{/* 旧写法 */}}
{{ $.Scratch.Set "__paginator.ellipsed" false }}
{{ $.Scratch.Get "__paginator.ellipsed" }}

{{/* 新写法 */}}
{{ $.Store.Set "__paginator.ellipsed" false }}
{{ $.Store.Get "__paginator.ellipsed" }}
```

修复后重新构建，第 1 页 10 篇、第 2 页 7 篇，分页导航的 Prev/Next 也正确指向对应页面。

### 踩坑记录

- 我一开始以为 `.Paginator` 需要用 `.Paginate` 显式初始化才能工作，后来发现 Hugo 在首次访问 `.Paginator` 时就会自动创建分页器。关键区别在于：**`.Pages` 是全量集合，`.Paginator.Pages` 才是当前页的子集**。
- 模板里 `{{ range .Pages }}` 在 `{{ if .Paginator }}` 之前执行，但这不影响分页器的初始化——Hugo 的分页页面（`/page/2/` 等）是在渲染阶段自动生成的，跟模板里访问 `.Paginator` 的时机无关。

---

## 二、分页修好了，但丑得没法看

### 现象

分页功能正常了，但页面上出现了一个**竖向排列的带圆点无序列表**，页码和箭头上下堆叠，非常难看。

### 原因

我检查了整个主题的 CSS 文件，发现 `.page-links`、`.page-links-active`、`.page-links-disabled` 这几个类名**只有模板里在用，没有任何 CSS 定义**。

而主题的 `main.css`（Tailwind 源文件）里，base 层给了所有 `<ul>` 和 `<li>` 默认样式：

```css
li {
    @apply list-disc;   /* 圆点 */
}
ul, ol {
    @apply pl-10;       /* 左内边距 */
}
```

分页的 `<ul class="page-links">` 没有任何样式覆盖，直接继承了这些 base 样式，就变成了默认的竖向圆点列表。

### 为什么不重新跑 Tailwind 构建？

主题的 CSS 构建流程是 `npx tailwindcss -i ./assets/css/main.css -o ./assets/css/style.css`。但我检查了本机 npm 缓存，**没有 tailwindcss 包**，`npx` 需要联网下载。更关键的是，`npx tailwindcss` 可能拉到 v4 版本，而主题的配置（`tailwind.config.js` 里的 `darkMode: 'class'`、`@tailwind base` 指令等）是 v3 格式，**v4 和 v3 配置不兼容**，贸然升级会导致整个样式系统崩溃。

### 解决方案：直接往编译产物里追加 CSS

`style.css` 虽然是 Tailwind 的编译产物，但它就是一个普通的 CSS 文件。Hugo 构建时通过 `resources.Minify` 加载它，只做压缩，不校验内容来源。所以我直接在 `style.css` 末尾追加了一段手写 CSS：

```css
.page-links {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: .5rem;
  list-style: none;
  padding-left: 0;
  margin: 2rem 0;
}
.page-links li {
  list-style: none;
}
.page-links a {
  padding: .25rem .75rem;
  border: 1px solid #d4d4d8;
  border-radius: .375rem;
  color: #1e40af;
}
.page-links a:hover {
  background: #f4f4f5;
  border-color: #a1a1aa;
}
.page-links-active a {
  background: #1e40af;
  color: #fff;
  border-color: #1e40af;
}
.page-links-disabled a {
  color: #a1a1aa;
  pointer-events: none;
  border-color: #e4e4e7;
}
/* 暗色模式适配 */
.dark .page-links a {
  color: #93c5fd;
  border-color: #52525b;
}
.dark .page-links a:hover {
  background: #3f3f46;
}
.dark .page-links-active a {
  background: #1e40af;
  color: #fff;
}
.dark .page-links-disabled a {
  color: #71717a;
  border-color: #3f3f46;
}
```

暗色模式的适配靠 `.dark` 选择器实现——主题的 `common.js` 通过在 `<html>` 上切换 `dark` class 来控制明暗主题。

重新构建后验证，分页变成了一行居中排列的圆角按钮，当前页蓝底白字高亮，无可用页时箭头置灰且不可点击。

### 踩坑记录

- 我最初想通过修改 `main.css` 然后跑 `npm run build-tw` 来"正规地"解决，但被 Tailwind 版本兼容性问题劝退了。**直接往编译产物追加纯 CSS 是最稳妥的零依赖方案**。
- 验证 CSS 是否生效时，我用 `grep -oE '\.page-links[^}]*}' public/css/style.min.css` 检查 minify 后的输出。一开始看到 `.dark .page-links a` 的规则好像变成了 `.page-links a`，吓了一跳，后来发现是 grep 的正则匹配到了 `.dark .page-links a` 中的后半段。用 `\.dark\s*\.page-links` 重新匹配后确认暗色模式规则完好。

---

## 三、按年月归档文章：文件结构重组

### 需求

文章越来越多后，`content/post/` 目录下堆了十几个 `.md` 文件，本地管理很不方便。我想把它们按 front matter 里的 `date` 字段归档到 `content/post/年/月/` 的子目录结构里。

### 实施

写了一个 bash 脚本，遍历 `content/post/*.md`，用正则提取 front matter 里的日期，然后 `git mv` 到对应目录：

```bash
cd content/post
for f in *.md; do
  [ "$f" = "_index.md" ] && continue
  d=$(grep -m1 -oP '^date\s*=\s*"\K[0-9]{4}-[0-9]{2}' "$f")
  [ -z "$d" ] && { echo "SKIP(no date): $f"; continue; }
  y=${d:0:4}; m=${d:5:2}
  mkdir -p "$y/$m"
  git mv "$f" "$y/$m/$f" && echo "moved: $f -> $y/$m/"
done
```

17 篇文章全部按日期归档完毕，`_index.md` 留在原位。用 `git mv` 而不是普通 `mv`，可以保留文件历史。

### 关键前提：URL 不受影响

我的 Hugo 配置里 permalink 是 slug 模式：

```toml
[permalinks]
post = "/:slug/"
```

文章的 URL 由 slug 决定，跟文件在 `content/` 下的物理路径无关。所以移动文件不会改变任何文章的公开 URL。

### 第一个错误决策：给年月目录加 `_index.md`

我当时担心 Hugo 会为每个年月子目录自动生成 section 页面（比如 `/post/2024/`），于是给每个年月目录都创建了 `_index.md`，内容是：

```toml
+++
_build = { render = "never", list = "never" }
+++
```

意图是：不渲染这些 section 页面（`render = "never"`），也不让它们出现在页面集合里（`list = "never"`）。

**这个决策后来被证明是引发下一个大坑的根源。**

---

## 四、归档后文章全部消失：嵌套 section 的连锁反应

### 现象

归档完成后，`/post/` 列表页**一篇文章都不显示了**。页面只剩标题和 `_index.md` 的内容，文章列表区域完全空白。

### 漫长的排查过程

这是整个过程中最折磨人的一段。我先后尝试了多种方案，每一次都以为找到了根因，结果构建后还是空白。

**尝试 1：用 `.RegularPagesRecursive` 替代 `.Pages`**

Hugo 文档说 `.RegularPagesRecursive` 可以递归获取当前 section 及所有子 section 下的普通页面。我在站点根目录创建了 `layouts/_default/list.html` 覆盖主题模板：

```go-html-template
{{ range (.Paginate .RegularPagesRecursive).Pages }}
    {{ partial "list-item.html" . }}
{{ end }}
```

构建后列表还是空的。

**尝试 2：怀疑是 `list = "never"` 阻断了递归**

我猜测年月目录的 `_index.md` 上设置的 `list = "never"` 可能把整个子树从页面集合里排除了，导致 `.RegularPagesRecursive` 无法穿透。于是把所有年月 `_index.md` 改成只保留 `render = "never"`：

```toml
+++
build = { render = "never" }
+++
```

（顺便把 `_build` 改成了 `build`，因为 Hugo 0.145+ 已经废弃了 `_build` 键名。）

构建后列表**依然是空的**。

**尝试 3：用 `where .Site.RegularPages` 过滤**

我换了个思路，从全站页面集合里过滤：

```go-html-template
{{ $pages := where .Site.RegularPages "Section" "==" .Section }}
{{ range (.Paginate $pages).Pages }}
    {{ partial "list-item.html" . }}
{{ end }}
```

加了调试输出后确认：`where` 过滤确实返回了 17 篇文章，但 `.Paginate $pages` 的结果是 **0 页**。

**尝试 4：发现 `.Paginate` 的调用时机问题**

Hugo 要求 `.Paginate` 必须在渲染任何内容之前调用。我的模板里，`{{ partial "breadcrumb.html" . }}` 和 `{{ .Content }}` 在 `.Paginate` 之前执行了。我把 `.Paginate` 挪到模板最顶部，结果还是 0 页。

**真正的根因：`head.html` 里的 `.Paginator` 抢先初始化了**

最终我在主题的 `head.html` 里发现了这段代码：

```go-html-template
{{- if and .IsNode .Paginator -}}
{{- if .Paginator.HasPrev -}}
<link rel="prev" href="{{ .Paginator.Prev.URL | absURL }}">
{{- end -}}
{{- if .Paginator.HasNext -}}
<link rel="next" href="{{ .Paginator.Next.URL | absURL }}">
{{- end -}}
{{- end -}}
```

`head.html` 在 `baseof.html` 的 `<head>` 里渲染，**先于 `main` 模板块执行**。它访问了 `.Paginator`，用默认的页面集合（对 `/post/` 来说就是直接子页面——归档后为空）初始化了分页器。Hugo 的规则是：**`.Paginate` 只能调用一次，第一次调用生效，后续调用被忽略**。所以我在 `list.html` 里用自定义集合调用 `.Paginate` 完全无效。

### 最终解决方案：删掉年月目录的 `_index.md`

既然问题的根源是年月目录被 `_index.md` 标记为独立 section，那最简单的方案就是：**删掉所有年月目录的 `_index.md`**。

Hugo 的规则是：**没有 `_index.md` 的子目录不算独立 section，只是组织结构**。`content/post/2024/07/foo.md` 里的文章仍然属于 `post` section，主题的原始模板（用 `.Paginator.Pages`）可以直接递归包含它们。

```bash
rm -f content/post/202*/_index.md content/post/202*/*/_index.md
rm -f layouts/_default/list.html  # 删掉自定义覆盖模板，用回主题原版
```

构建验证：

```
/post/ 列表：10 篇 ✓
/post/page/2/：7 篇 ✓
无 /post/2024/ 等归档页面 ✓
无构建警告 ✓
```

完美。不需要修改任何主题文件，本地归档结构保留，站点行为和归档前完全一致。

### RSS 的修复

删掉 `_index.md` 后，列表和分页都正常了，但 RSS feed（`/post/index.xml`）是空的。Hugo 内置的 RSS 模板对 section 页面用的是 `.Pages`，而我的 Hugo 版本（0.154）对子目录里普通页面的处理可能有差异。我创建了一个 `layouts/_default/rss.xml` 覆盖模板，核心改动是把页面来源换成 `.RegularPages`：

```go-html-template
{{- $pages := .RegularPages -}}
{{- if .IsHome }}{{ $pages = .Site.RegularPages }}{{ end -}}
{{- $limit := .Site.Config.Services.RSS.Limit -}}
{{- if ge $limit 1 -}}
{{- $pages = $pages | first $limit -}}
{{- end -}}
```

构建后 RSS 正常输出 10 条（受 `rssLimit = 10` 配置限制）。

### 踩坑记录

- **`_index.md` 的存在与否决定了目录是否是独立 section**。这个知识点我最初理解得不够深，导致走了很多弯路。
- `.Paginate` 只能调用一次，而且会被 `head.html` 里的 `.Paginator` 访问抢先初始化。这是 Hugo 分页机制里最隐蔽的坑。
- `list = "never"` 的 `_build` / `build` 选项只影响 section 页面本身是否出现在集合里，但 `.RegularPagesRecursive` 的递归遍历可能受其影响（具体行为在不同 Hugo 版本中有差异）。最稳妥的方案就是不让年月目录成为 section。

---

## 五、给文章添加脚注引用：GB/T 7714 格式

### 需求

我的博客文章需要引用标注，使用 Markdown 脚注语法，脚注格式按论文标准（GB/T 7714—2015）改写。

### Hugo 的脚注支持

Hugo 的 Goldmark 渲染器原生支持 `[^1]` 脚注语法。在正文中用 `[^1]` 标注引用，在文末定义脚注内容：

```markdown
正文中的引用标注[^1]。

[^1]: 作者. 题名[J]. 刊名, 年, 卷(期): 页码.
```

同一个脚注 ID 可以在正文中多次引用（`[^1]` 出现多次），Hugo 会自动处理上标编号和返回链接。

### 脚注格式的三轮迭代

**第一版：完整 GB/T 7714 格式 + 裸 URL**

最初我按标准格式写了脚注，URL 用尖括号包裹（`<https://...>`）：

```markdown
[^1]: 文章标题[EB/OL]. 网站名称, (2023-09)[2026-07-31]. <https://example.com/article>.
```

**第二版：改为超链接，隐藏长 URL**

我看了一下效果，觉得脚注引用链接不用展示出来，太长了，用超链接。于是把 URL 改成 Markdown 链接，让文章标题本身成为可点击的超链接：

```markdown
[^1]: [文章标题](https://example.com/article). 网站名称, 2023-09.
```

**第三版：确保每个脚注都有 URL**

有些脚注（论文、专利）最初没有附带链接。要求每个脚注必须有 URL 以保证来源可追溯：

```markdown
{{/* 论文脚注 */}}
[^1]: ZENG J, et al. [论文标题](https://doi.org/...)[J]. 期刊名, 2026, 5: 26-42.

{{/* 专利脚注 */}}
[^2]: 发明人. [专利名: 专利号](https://patents.google.com/patent/...)[P]. 2022-07-29.

{{/* 网络资料脚注 */}}
[^3]: [文章标题](https://example.com). 网站名称, 2023-09.
```

### 构建验证

用 Python 脚本检查所有脚注定义是否都包含超链接，以及是否有长 URL 作为可见文本泄露：

```python
import re, glob
for f in sorted(glob.glob('public/*/index.html')):
    html = open(f).read()
    m = re.search(r'<div class=footnotes.*?</ol></div>', html, re.S)
    if not m: continue
    for li in re.findall(r'<li id=(fn:\d+)>(.*?)</li>', m.group(0), re.S):
        fn, body = li
        # 检查是否有 http 链接
        if not re.search(r'href=[\'"]?https?:', body):
            print(f"{f} {fn}: NO URL LINK")
        # 检查可见文本中是否有裸 URL
        text = re.sub(r'<[^>]+>', '', body)
        if re.search(r'https?://', text):
            print(f"{f} {fn}: visible URL in text")
```

全部通过。

### 踩坑记录

- YAML front matter 里如果值包含冒号（如 `journal: Environmental Functional Materials, 5: 26-42`），**必须加引号**，否则 Hugo 解析会报错：`mapping value is not allowed in this context`。
- Markdown 链接里的 URL 如果包含括号（如文件名 `(1).docx`），Goldmark 可以处理平衡括号，但为了安全最好用 URL 编码（`%28`、`%29`）。

---

## 六、TOML 配置的层级陷阱：`blogrss` 不生效

### 现象

主题页脚有一个 RSS 订阅链接，由 `blogrss` 参数控制显示：

```go-html-template
{{ if isset .Site.Params "blogrss" }}
<li>
  <a href="{{ .Site.BaseURL }}{{ "index.xml" }}" type="application/rss+xml">
    {{ i18n "footerRSS" }}
  </a>
</li>
{{ end }}
```

配置文件里我明明写了 `blogrss = true`，但页脚就是不显示 RSS 链接。

### 排查

我先怀疑是多语言上下文的问题（主题支持多语言，`.Site.Params` 在多语言循环里可能指向语言级参数而非全局参数）。尝试了 `$.Site.Params`（全局根上下文）和 `[Languages.zh-cn.params]` 语言级参数，都没解决。

### 真正的原因

最后仔细检查配置文件，发现 `blogrss = true` 这行**写在了 `[params.imgname]` 块的下面**：

```toml
[params]
description = "..."
authorName = "..."

[params.imgname]
name = "img/main.jpg"
alt = "头像"
blogrss = true   # ← 错误！这行归属于 params.imgname，不是 params
```

TOML 的表（`[xxx]`）有层级继承特性。`[params.imgname]` 之后的键值对都归属于 `params.imgname` 子表，直到遇到下一个 `[xxx]` 标记。所以 `blogrss = true` 实际变成了 `.Site.Params.imgname.blogrss`，而不是 `.Site.Params.blogrss`。模板里 `isset .Site.Params "blogrss"` 自然返回 `false`。

### 修复

把 `blogrss = true` 挪到 `[params]` 块里、`[params.imgname]` 之前：

```toml
[params]
description = "..."
authorName = "..."
blogrss = true     # ← 正确位置

[params.imgname]
name = "img/main.jpg"
alt = "头像"
```

### 踩坑记录

- TOML 的层级继承是**隐式的**，不像 YAML 有缩进那么直观。在 Hugo 配置文件里，`[params]` 下面跟了 `[params.imgname]` 之后，后续所有键值对都归属于 `params.imgname`，直到下一个 `[xxx]` 出现。
- 这类 bug 不会报任何错误，功能只是"静默失效"，非常难排查。

---

## 七、去掉 Hugo 自动插入的 generator 标签

### 现象

构建后的 HTML 头部有一行：

```html
<meta name="generator" content="Hugo 0.154.5">
```

这是 Hugo 自动插入的，用于标识站点生成器。我不想要它。

### 解决

在配置文件根级别添加一行：

```toml
disableHugoGeneratorInject = true
```

重新构建后，generator 标签消失。这是 Hugo 官方提供的标准开关，没有任何副作用。

---

## 小结：避坑清单

| 坑 | 原因 | 正确做法 |
|---|---|---|
| 分页不生效 | 模板用 `.Pages` 而非 `.Paginator.Pages` | 列表模板中用 `{{ range .Paginator.Pages }}` |
| 分页样式缺失 | 主题没有为 `.page-links` 提供 CSS | 在 `style.css` 末尾追加手写 CSS |
| Tailwind 重建风险 | `npx tailwindcss` 可能拉到 v4，与 v3 配置不兼容 | 避免重建，直接追加纯 CSS |
| 归档后文章消失 | 年月目录有 `_index.md` 变成独立 section | 删掉年月目录的 `_index.md`，让它们只是普通文件夹 |
| `.Paginate` 返回空 | `head.html` 里的 `.Paginator` 抢先初始化了默认分页器 | 不要在自定义模板里用 `.Paginate`，改用主题原生分页 |
| YAML 冒号解析错误 | front matter 值含 `:` 未加引号 | 含特殊字符的值用双引号包裹 |
| `blogrss` 不生效 | TOML 层级继承，键值对归属到了错误的子表 | 检查配置项是否在正确的 `[xxx]` 块内 |
| generator 标签 | Hugo 默认自动插入 | `disableHugoGeneratorInject = true` |
| `_build` 废弃 | Hugo 0.145+ 废弃 `_build`，改用 `build` | 使用 `build = { render = "never" }` |
| `$.Scratch` 废弃 | 新版 Hugo 用 `$.Store` 替代 | 全部替换为 `$.Store.Set` / `$.Store.Get` |

**最核心的一条经验**：Hugo 的 `.Pages`、`.RegularPages`、`.RegularPagesRecursive`、`.Paginator.Pages` 各有各的语义，搞混了就是各种"文章不显示"或"显示了全部文章"的问题。遇到列表页异常，第一件事就是确认模板里遍历的到底是哪个集合。