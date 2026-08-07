+++
date = "2026-08-06"
title = "Hugo 实现专业术语自动链接百度百科与外链新标签页打开"
slug = "hugo-auto-baike-link-external-blank"
categories = [ "技术教程", "Hugo 建站" ]
tags = [ "Hugo", "静态站点生成", "模板开发", "百度反爬", "博客优化" ]
readingtime = true
+++

## 开篇：我想给博客加两个小功能

我的 Hugo 静态博客写了不少技术文章，里面经常出现一些专业术语——密度泛函理论、机器学习、QSAR、DFT 之类的。读者如果不熟悉这些概念，得自己另开浏览器去搜。我就想：**能不能让文章里的术语自动变成百度百科的链接？**

另外还有个体验问题：文章里的外部链接（维基百科、GitHub 等）点击后直接在当前页跳走了，读完外链回来得重新找阅读位置。我希望**外部链接在新标签页打开，站内链接保持当前页跳转**。

这两个需求看起来不复杂，但真正动手实现时，我踩了一连串 Hugo 模板函数的坑，也第一次跟百度的反爬机制正面交锋。这篇文章完整记录我的探索过程。

## 第一个功能：外部链接新标签页打开

### 思路选择

Hugo 支持 Markdown 渲染钩子（render hooks），可以自定义链接的 HTML 输出。我选择**仅外部链接加 `target="_blank"`**，内部链接（相对路径、锚点、脚注引用）保持当前页跳转。

### 实现

创建 `layouts/_default/_markup/render-link.html`：

```html
{{- $u := urls.Parse .Destination -}}
{{- $external := and $u.Host (ne $u.Host (urls.Parse site.BaseURL).Host) -}}
<a href="{{ .Destination | safeURL }}"{{ with .Title }} title="{{ . }}"{{ end }}{{ if $external }} target="_blank" rel="noopener noreferrer"{{ end }}>{{ .Text | safeHTML }}</a>
```

逻辑很简单：解析链接的 Host，如果非空且与站点 Host 不同，就判定为外部链接。这样：

- `[文章](/post/foo/)` → 相对路径，Host 为空 → 当前页跳转
- `[^1]` 脚注引用 → `#fn:1`，Host 为空 → 当前页跳转
- `[维基百科](https://zh.wikipedia.org/...)` → Host 不同 → 新标签页

构建验证后一切正常，脚注锚点没有被误加 `target="_blank"`，外部 Wikipedia 链接正确新窗口打开。

## 第二个功能：术语自动链接百度百科

### 整体方案设计

我选择了**服务端模板预处理**方案：在 Hugo 构建时，通过模板 partial 对 `.Content` 做字符串替换，把术语替换成带百度百科链接的 `<a>` 标签。

核心文件结构：

- `data/baike.yaml` — 术语列表
- `layouts/partials/baike-links.html` — 预处理逻辑
- `layouts/_default/single.html` — 覆盖主题模板，调用 partial

### 术语数据文件

`data/baike.yaml` 格式：

```yaml
terms:
  - name: "密度泛函理论"
  - name: "机器学习"
  - name: "过氧单硫酸盐"
    url: "https://baike.baidu.com/item/单过硫酸氢钾"
  - name: "酷热指数"
    url: "https://baike.baidu.com/item/热指数"
```

默认 URL 是 `https://baike.baidu.com/item/{术语名}`，但有些术语在百科里的词条名跟我的叫法不同，所以支持 `url` 字段覆盖。

### 预处理 Partial 的核心逻辑

算法分四步：

1. **保护特殊标签**：把 `<pre>`、`<a>`、`<img>`、`<h1>`-`<h6>`、`<code>`、`<script>`、`<style>` 用占位符替换，避免术语替换破坏已有结构
2. **遍历术语列表**（按长度降序），把首次出现的术语替换为占位符
3. **还原所有占位符**为原始 HTML 或生成的链接
4. 输出 `safeHTML`

为什么要保护？因为 `.Content` 是已渲染的 HTML，里面可能有代码块包含术语文字、已有超链接的锚文本包含术语、标题里有术语——这些都不该被再次链接。

### 覆盖 single.html

把主题的 `single.html` 复制到项目 `layouts/_default/single.html`，只改一行：

```html
<!-- 原来是 {{ .Content }} -->
{{ partial "baike-links.html" . }}
```

## Python 检查脚本：第一次撞上百度反爬

术语链接生成后，我得验证这些百科 URL 是不是真的能访问。于是写了个 Python 脚本 `check_baike_links.py`，逐个请求术语 URL，检查返回状态和页面内容。

### 第一版：全部 403

```python
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ...",
}

resp = requests.get(url, headers=HEADERS, timeout=15)
```

跑起来一看——18 个术语全部返回 HTTP 403。

我以为是 User-Agent 的问题，换了 Chrome、Safari、iPhone 各种 UA，甚至用 `curl` 命令行直接请求——**统统 403**。百度百科首页 `https://baike.baidu.com/` 返回 200，但 `/item/xxx` 路径一律 403。

这明显不是 UA 层面的拦截，而是 **TLS 指纹检测**（JA3）。`requests` 和 `curl` 的 TLS 握手特征跟真实浏览器不同，百度 WAF 直接拒绝了。

### 解决：curl_cffi 模拟浏览器指纹

```python
from curl_cffi import requests as http

resp = http.get(url, headers=HEADERS, impersonate="chrome", timeout=timeout)
```

`curl_cffi` 能模拟 Chrome 的完整 TLS 指纹，装上之后立刻有 4 个术语通过了。

### 反爬验证码的概率性拦截

即便用了 `curl_cffi`，百度还是有概率弹验证码（重定向到 `/anticrawl/captchaview`）。这是基于请求频率和 IP 信誉的风控，不是术语本身的问题。我在脚本里加了：

- **重试机制**（默认 2 次，指数退避）
- **区分状态**：`ok`（词条存在）、`blocked`（被反爬拦截，非术语问题）、`fail`（词条真不存在，404）
- `--strict` 选项：把 blocked 也视为失败

### 404 词条的修正

跑通后发现了 4 个真 404：

| 我的术语 | 百科实际词条 |
|---------|------------|
| 过氧单硫酸盐 | 单过硫酸氢钾 |
| 硫酸自由基 | 硫酸根自由基 |
| 磺胺类抗生素 | 磺胺类药物 |
| 酷热指数 | 热指数 |

在 `data/baike.yaml` 里给这些术语配了 `url` 字段指向正确词条。

脚本对 custom URL 的验证逻辑也做了调整：不能要求页面标题包含我的术语名（因为词条名不同），改为检查标题是否含 `_百度百科`（有效词条页的标志）。

## 需求变更：只链接首次出现

最初版本用 `replace` 替换术语的**所有**出现位置。但一篇文章里"密度泛函理论"可能出现十几次，全加链接太密了。我改成**只链接第一次出现**。

### 踩坑：Hugo 的 `slice` 不是切片操作

我的第一反应是用 `split` 拆分后取 `parts[1:]`：

```go-html-template
{{- $rest := delimit (slice $parts 1) .name -}}
```

构建后文章输出被截断了——只剩第一个链接和一个孤零零的 `1`。

我写了个最小测试：

```go-html-template
delimit: {{ delimit (slice (split "X,Y,Z" ",") 1) "," }}
```

输出：`delimit: 1`

**真相**：Hugo 的 `slice` 函数不是 Python 的 `list[1:]` 切片！它是**从给定项构造新切片**。`slice $parts 1` 创建的是 `[$parts, 1]`——一个包含原切片和整数 1 的两元素切片。

**修复**：用 `seq` 循环手动构建尾部切片：

```go-html-template
{{- $tail := slice -}}
{{- range $j := seq 1 (sub (len $parts) 1) -}}
    {{- $tail = $tail | append (index $parts $j) -}}
{{- end -}}
{{- $content = printf "%s%s%s" (index $parts 0) $token (delimit $tail .name) -}}
```

修完后每个术语只链接一次，验证通过。

## 需求变更：大小写不敏感匹配

我的术语表里有 `dft`、`go`、`hugo`、`qsar` 这些英文缩写，但文章里写的是 `DFT`、`Go`、`Hugo`、`QSAR`。我需要大小写不敏感匹配。

### 实现思路

用 `lower` 归一化后定位位置，再从原文取回匹配文本（保留原始大小写作为链接文字）：

```go-html-template
{{- $parts := split (lower $content) (lower .name) -}}
{{- if gt (len $parts) 1 -}}
    {{- $pos := strings.RuneCount (index $parts 0) -}}
    {{- $rlen := strings.RuneCount .name -}}
    {{- $matched := substr $content $pos $rlen -}}
    ...
{{- end -}}
```

### 踩坑：`substr` 的参数语义

第一版我写了 `substr $content $pos (len .name)`，结果输出完全错乱。

测试发现 Hugo 的 `substr` 语义是：
- **START**：rune 下标（不是字节）
- **第二参数**：**长度**（不是结束下标）

而且 `len` 返回的是**字节数**，中文一个字符占 3 字节。用字节数当 rune 下标，位置全偏了。

**修复**：统一用 `strings.RuneCount` 计算字符数：

```go-html-template
{{- $pos := strings.RuneCount (index $parts 0) -}}
{{- $rlen := strings.RuneCount .name -}}
{{- $matched := substr $content $pos $rlen -}}
{{- $content = printf "%s%s%s" (substr $content 0 $pos) $token (substr $content (add $pos $rlen)) -}}
```

修完后 `dft` 正确匹配文中的 `DFT`，链接文字显示原文的 `DFT`。

## 踩坑：`go` 匹配进了 `Hugo`

大小写匹配跑通后，我发现 Hugo 那篇文章里出现了诡异的链接：`Hu` + 链接的 `go` + ` 模板渲染`。

原因：术语 `hugo` 只链接了第一次出现的 `Hugo`（首次匹配原则），第二次出现的 `Hugo` 还是纯文本。接着处理术语 `go` 时，在第二个 `Hugo` 里找到了子串 `go`，就链接了。

同理，`go` 还可能匹配进 `Google`、`gopls`、`golang` 等词。

### 解决：词边界检查

对**含拉丁字母的术语**，匹配位置的前后字符如果是字母或数字，就跳过该匹配，继续找下一个出现位置：

```go-html-template
{{- $isAscii := findRE "[A-Za-z0-9]" .name -}}
...
{{- $prev := "" -}}
{{- if gt $cp 0 -}}{{- $prev = substr $content (sub $cp 1) 1 -}}{{- end -}}
{{- $next := "" -}}
{{- if lt $np $totalRunes -}}{{- $next = substr $content $np 1 -}}{{- end -}}
{{- $boundaryOk := or (not $isAscii) (and (not (findRE "[A-Za-z0-9]" $prev)) (not (findRE "[A-Za-z0-9]" $next))) -}}
```

- 术语 `go` 在 `Hugo` 中：前一个字符是 `u` → 拒绝
- 术语 `go` 在 `Go 语言` 中：前一个字符是空格 → 通过
- 中文术语不做边界检查（`机器学习` 匹配 `机器学习方法` 是合理的）

### 占位符的连锁问题

加了边界检查后又发现一个新问题：保护阶段的占位符 `ZZBK0ZZ` 全是字母。如果一个术语紧挨着被保护的代码块或脚注（如 `机器学习[^1]`），替换后变成 `机器学习ZZBK0ZZ`——边界检查看到下一个字符是 `Z`，判定为字母，拒绝匹配。

**修复**：把占位符改为 Unicode 私用区字符 `\ue000` 包裹：

```go-html-template
{{- $token := printf "\ue000BK%d\ue000" $i -}}
```

`\ue000` 不是 ASCII 字母数字，不会触发边界拒绝。

## 踩坑：术语链接跑进了标题的 id 属性

加了词边界检查后我以为万事大吉，直到我在渲染结果里看到一个匪夷所思的东西——本文里 "## 踩坑：`go` 匹配进了 `Hugo`" 这个标题，渲染出来变成了：

```html
<h2 id="踩坑<a href="https://baike.baidu.com/item/go" target="_blank" rel="noopener noreferrer" class="baike-link">go</a>-匹配进了-hugo">
```

`<a>` 标签被整个塞进了 HTML 属性值里！这个标题的锚点彻底废了，浏览器根本没法解析这个 id。

### 排查：占位符神秘消失

我先用 `strings.Count` 埋点，检查 protect 阶段生成的 h2 占位符是否还在内容里：

```go-html-template
AFTER-PROTECT-H2TOKEN: {{ strings.Count $content "\ue000BK98\ue000" }}
```

输出 `AFTER-PROTECT-H2TOKEN: 0`——protect 阶段刚结束，h2 的占位符就已经不在内容里了。

再给每个 match 打印"它的原始串此刻还在不在内容里"：

```go-html-template
MATCH idx={{ $i }} len={{ len $m }} found={{ strings.Contains $content $m }}
```

输出：

```
MATCH idx=96 len=16 found=false head=<code>DFT</code>
MATCH idx=97 len=16 found=false head=<code>DFT</code>
MATCH idx=98 len=96 found=false head=<h2 id="踩坑go-匹配进了-hugo">踩坑：<code>go</code> 匹配
```

真相浮出水面：**h2 被 `findRE` 匹配到了（idx 98），但轮到它替换时，`$content` 里已经没有这个完整字符串了。** 直接 dump protect 后的内容看 h2 区域：

```html
<h2 id="踩坑go-匹配进了-hugo">踩坑：\ue000BK79\ue000 匹配进了 \ue000BK84\ue000</h2>
```

h2 的开标签和 id 是**裸的**，只有它内部的 `<code>` 被替换成了占位符（BK79、BK84）。

### 根因：`replace` 是全量替换

我把 `replace $content $m $token` 当成了"只替换 findRE 返回的那一处"。实际上 **Hugo 的 `replace` 函数会替换内容里所有匹配的子串**。于是事情变成了这样：

1. `findRE` 一次性匹配出所有受保护元素：正文里先出现的 `<code>go</code>` 是 idx 79，而 h2 内部的 `<code>go</code>` 是 h2 整体（idx 98）的一部分
2. 处理 idx 79 时，`replace $content "<code>go</code>" $token` **把全文所有 `<code>go</code>` 都替换了**，包括 h2 内部的
3. 同理 `<code>Hugo</code>`（idx 84）也把 h2 内部的换掉了
4. 轮到 h2（idx 98）时，它的 `$m`（含原始 `<code>` 标签的完整字符串）已经不存在 → `replace` 静默空操作，h2 从头到尾没被保护
5. 术语阶段做边界检查：id 里的 `go` 前面是 `坑`、后面是 `-`，都不是字母数字 → 检查通过 → 链接成功进入 id 属性

### 修复：标题单独一轮先保护

解决思路：让标题**整体**（含 id）在一个独立的 `findRE` 中先被替换，这样它内部的标签永远不会被第二轮匹配到：

```go-html-template
{{- /* 第一轮：整体保护标题（含 id），内部内联标签不再被单独匹配 */ -}}
{{- range $i, $m := findRE `<h[1-6][^>]*>[\s\S]*?</h[1-6]>` $content -}}
    {{- $token := printf "\ue000BKH%d\ue000" $i -}}
    {{- $protected = $protected | append (dict "token" $token "html" $m) -}}
    {{- $content = replace $content $m $token -}}
{{- end -}}

{{- /* 第二轮：保护其余元素 */ -}}
{{- $protectPattern := `<pre[\s\S]*?</pre>|<a\s[^>]*>[\s\S]*?</a>|<img[^>]*?>|<code[^>]*>[\s\S]*?</code>|<script[\s\S]*?</script>|<style[\s\S]*?</style>` -}}
{{- range $i, $m := findRE $protectPattern $content -}}
    {{- $token := printf "\ue000BKO%d\ue000" $i -}}
    {{- $protected = $protected | append (dict "token" $token "html" $m) -}}
    {{- $content = replace $content $m $token -}}
{{- end -}}
```

两轮占位符用不同前缀（`BKH`/`BKO`），避免编号冲突。

这个 bug 还顺带暴露了一个无害的小问题：**重复字符串的 match**（比如两个一模一样的 `<code>DFT</code>`）也会让第二个 match `found=false`——第一个 `replace` 全量替换时把两个都换掉了。内容不受影响，只是占位符列表里多一条永远用不上的记录。

修复后全站验证：标题 id 内嵌 `<a>` 标签 0 处，残留占位符 0，每页每术语依然只链接一次。

## 最终验证

构建后逐项检查：

```bash
# 每篇文章的百科链接数
for f in public/post/*/index.html; do
  n=$(grep -o 'class="baike-link"' "$f" | wc -l)
  [ "$n" -gt 0 ] && echo "$n links: $f"
done

# 检查重复链接
for f in public/post/*/index.html; do
  dups=$(grep -o 'class="baike-link">[^<]*' "$f" | sort | uniq -d)
  [ -n "$dups" ] && echo "DUP: $f: $dups"
done

# 检查残留占位符
rg -l '\ue000' public/post/*/index.html || echo "no leftover tokens"

# 检查标题 id 内是否嵌入了链接（id 值里出现 <a 即为异常）
rg -o '<h[1-6][^>]*id="[^"]*<a ' public/post/*/index.html || echo "no links inside heading ids"
```

全部通过：无重复链接、无残留占位符、内容无截断、代码块完整、标题 id 干净（0 处属性内嵌 `<a>`）。

## 小结与避坑清单

### 学到的关键点

1. **Hugo `slice` 函数**：构造新切片，不是 Python 式切片。要取子切片得用 `seq` + `index` 循环
2. **Hugo `substr` 语义**：第一参数是 rune 下标，第二参数是**长度**（不是结束位置），且是 rune 级别不是字节级别
3. **Hugo `len` vs `strings.RuneCount`**：`len` 返回字节数，中文字符占 3 字节；做字符定位必须用 `RuneCount`
4. **百度反爬**：TLS 指纹检测，`requests`/`curl` 直接 403；需要 `curl_cffi` 的 `impersonate="chrome"` 模拟浏览器指纹
5. **词边界**：短英文术语（如 `go`）做子串匹配时必须检查前后字符，否则会匹配进更长的单词
6. **Hugo `replace` 是全量替换**：`replace $content $m $token` 替换所有匹配子串；配合 `findRE` 循环做"逐个保护"时，重复或嵌套的子串会让后面的 replace 静默失效，且很难直接看出来

### 避坑清单

| 坑 | 表现 | 解法 |
|---|------|------|
| `slice $parts 1` 当切片用 | 内容截断，输出只剩 `1` | 用 `seq` 循环 + `append` 构建子切片 |
| `substr` 第二参数当结束下标 | 取出内容过长/错位 | 第二参数是**长度**，用 `RuneCount` 计算 |
| `len` 当字符数 | 中文定位偏移 | 用 `strings.RuneCount` |
| 占位符用纯字母 | 边界检查误判 | 用 `\ue000` 私用区字符包裹 |
| 单轮 findRE 保护所有标签 | 标题内部标签先被替换，标题整体 `$m` 失效，id 裸奔被术语链接 | 标题单独一轮先整体保护（`BKH` 前缀） |
| 术语不排序 | 短术语抢走长术语的匹配 | 按长度降序处理 |
| 用 `requests` 请求百科 | 全部 403 | 用 `curl_cffi` + `impersonate="chrome"` |

### 文件清单

```
layouts/_default/_markup/render-link.html   # 外链新标签页
data/baike.yaml                             # 术语列表
layouts/partials/baike-links.html           # 预处理核心逻辑
layouts/_default/single.html                # 覆盖主题调用 partial
check_baike_links.py                        # 百科链接可用性检查脚本
```

运行检查：`python3.14 check_baike_links.py --delay 2`（需要 `pyyaml` + `curl_cffi`）。