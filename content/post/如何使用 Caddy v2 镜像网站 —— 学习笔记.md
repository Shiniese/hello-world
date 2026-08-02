+++
date = "2025-07-15"
title = "如何使用 Caddy v2 镜像网站 —— 学习笔记"
slug = "how-to-mirror-website-with-caddy-v2"
categories = [ "技术笔记", "Web" ]
tags = [ "Caddy", "反向代理", "学习笔记" ]
readingtime = true
+++

[TOC]

## 一、前言：为什么想用 Caddy 做镜像？

最近在学习反向代理和 Web 服务器配置，正好了解到 **Caddy** 这个非常强大的轻量级 Web 服务器。它不仅支持自动 HTTPS，还提供了模块化设计，非常适合做一些定制化的开发或部署。

我这次的目标是尝试用 **Caddy v2** 实现一个网站的镜像功能，比如把 `example.com` 的内容通过 Caddy 反代到我的域名 `my_site.com` 上，并且将网页中出现的 `example.com` 替换为 `my_site.com`，这样用户看到的就完全像是“属于”我这个域名的内容。

虽然这听起来很酷，但在实际操作过程中也遇到了不少问题，特别是插件缺失、响应替换失败等。所以这篇笔记也算是我一步步探索的过程记录吧！

---

## 二、目标清单 

1. 使用 Caddy 搭建反向代理，将请求转发到 `example.com`
2. 将返回页面中的 `example.com` 替换为 `my_site.com`
3. 启用日志记录
4. 支持 HTTP（也可以开启 HTTPS）
5. 确保 HTML 中的链接能正常替换，不影响基本展示

---

## 三、遇到的问题 & 解决思路

### 问题一：Caddy 默认不支持响应内容替换

一开始我以为 Caddy 自带了类似 Nginx 的 `sub_filter` 功能，但后来发现并不是。Caddy 官方提供了一个插件叫 `replace-response`，可以实现响应体中的字符串替换。

但是！这个插件不是默认内置的，需要我们自己构建一个带有它的 Caddy 版本。

### 解决方案：使用 xcaddy 构建自定义版本

```bash
go install github.com/caddyserver/xcaddy/cmd/xcaddy@latest
```

然后执行：

```bash
xcaddy build --with github.com/caddyserver/replace-response
```

这条命令会生成一个带有 `replace` 插件的新版 Caddy，这样才能使用响应替换功能。

---

### 问题二：Caddyfile 中 replace 指令位置错误

在写 Caddyfile 的时候，我把 `replace` 直接放在站点块下，结果报错：

> directive 'replace' is not an ordered HTTP handler, so it cannot be used here...

查了文档才知道，`replace` 是一个 HTTP 处理器，必须放在 `route` 块里才行。

### 解决方案：正确使用 route 块包裹 replace 和 reverse_proxy

最终的 Caddyfile 写法如下：

```caddyfile
my_site.com:80 {
    log {
        output file /var/log/caddy/my_site.com.log
    }

    route {
        # 替换响应体中的 example.com 为 my_site.com
        replace {
            example.com my_site.com
            https://example.com https://my_site.com
            //example.com //my_site.com
        }

        # 反向代理设置
        reverse_proxy example.com {
            header_up Host example.com
            header_up Accept-Encoding identity # 禁止压缩，确保替换生效
        }
    }
}
```

---

### 问题三：压缩内容无法替换

即使加了 `replace`，有时候页面里的 `example.com` 还是没被替换。排查后发现是因为上游返回的是 gzip 压缩过的响应，而 `replace` 插件目前不支持解压处理。

### 解决方案：禁用压缩传输

在 `reverse_proxy` 中添加：

```caddyfile
header_up Accept-Encoding identity
```

这样告诉上游服务器不要压缩响应，就能顺利进行文本替换啦！

---

## 四、验证是否成功的方法 

可以用 `curl` 来测试：

```bash
curl -H "Host: my_site.com" http://my_site.com | grep my_site.com
```

如果能看到页面中原本的 `example.com` 被替换成 `my_site.com`，说明一切正常！

---

## 五、注意事项 ⚠️

| 注意点 | 说明 |
|--------|------|
| 不适合用于登录或交互功能 | 目标网站可能有 CSP、JS 校验机制，很多功能无法正常使用 |
| 替换范围有限制 | `replace` 插件对响应大小有 2KB 的限制，太长的内容可能不会被替换 |
| 必须使用自定义 Caddy | 没有安装 `replace-response` 插件的 Caddy 无法使用该功能 |

---

## 六、总结一下 💡

通过这次实践，我对 Caddy 的插件机制、HTTP 请求流程有了更深入的理解。虽然不能完美地镜像所有网站（尤其是像 GitHub 这种复杂的网站），但对于一些静态页面或者技术演示来说，用 Caddy + `replace-response` 是完全可以做到的。

这也让我意识到，做这类镜像项目时，不仅要懂配置，还得了解底层原理，比如压缩机制、中间件顺序、插件加载方式等等。这些知识对我来说都是宝贵的积累。

---

## 七、扩展学习 📚

- [xcaddy 官方文档](https://github.com/caddyserver/xcaddy)
- [replace-response 插件介绍](https://github.com/caddyserver/replace-response)
- 学习 Caddyfile 的结构与语法
- 了解 Go 模块管理和 xcaddy 的构建流程
- 探索更多 Caddy 插件，比如 `http.cache`, `http.forwardproxy` 等
