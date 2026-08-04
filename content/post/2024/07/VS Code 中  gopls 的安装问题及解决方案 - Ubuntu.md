+++
date = "2024-07-27"
title = "VS Code 中 gopls 的安装问题及解决方案 - Ubuntu"
slug = "vs-code-gopls-install-problems-and-solutions-ubuntu"
categories = [ "技术笔记", "开发工具" ]
tags = [ "VS Code", "gopls", "Go", "Ubuntu" ]
readingtime = true
+++

最近在使用 VS Code 编写 Go 代码时遇到安装 gopls 失败的问题，尝试多种方法未果，最终通过安装系统自带的 gopls 解决。

## 问题重现

最近在 vs code 中使用 go 语言写代码时右下角总是出现下面的弹窗，每次无论点击 `install` 还是 `install all` 都是安装失败。

![how-to-solve-vs-code-gopls-command-is-not-available-1](https://files.catbox.moe/v0qv5j.png)

安装报错：

```shell
# 安装指令
go install -v golang.org/x/tools/gopls@latest 
# 报错
../../../go/pkg/mod/golang.org/x/tools/gopls@v0.16.1/internal/golang/comment.go:12:2: package go/doc/comment is not in GOROOT (/usr/lib/go-1.18/src/go/doc/comment) 
```

报错后其实没有影响我的正常使用，因此没管它。直到有一次在我的另一台电脑上问题重现，并且一点击 `install` 就成功安装后才发现这是个好东西。它能够**实现诸如自动完成, 代码提示等功能**。因此今日决定 `fix` 这个遗留问题。

## 尝试过的方法

1. 根据报错 `package go/doc/comment is not in GOROOT`，怀疑是 GOROOT 没有正确配置

```shell
export GOROOT=/usr/lib/go
```

清理模块缓存并重新下载：

```shell
go clean -modcache
go install -v golang.org/x/tools/gopls@latest
```

仍然无法解决问题。

2. 手动安装 `go/doc/comment` 包

```shell
go get -u golang.org/x/tools/godoc
go install -v golang.org/x/tools/gopls@latest
```

仍然无法解决。

查询网上资料，可能是网络问题，但本地早已正确配置相关代理，排除。

## 最终解决方案

在 stackoverflow[^stackoverflow] 上看到有人用 `brew install gopls` 解决了。我用的是 Ubuntu，尝试搜索该包并安装。

[^stackoverflow]: [How to solve vs code - gopls command is not available](https://stackoverflow.com/questions/66668506/how-to-solve-vs-code-gopls-command-is-not-available)

```shell
# 还真有 gopls 包
sudo apt search gopls 
sudo apt install gopls
```

搞定！比网上改配置、改环境、手动下载的方法简单多了，一行代码搞定。能用系统自带包解决还要啥自行车？

## 课外知识[^语言服务器协议] - Language Server Protocol

[^语言服务器协议]: [在 VS Code 中使用 gopls](https://segmentfault.com/a/1190000020276833?u_atoken=f76fa9ca662a7c6bd0ea6eded5bccb2c&u_asig=2760774117204873388185535e622a)


> Go 扩展默认是使用大量的 Go 工具来提供各种功能的, 每个工具提供某个方面的能力, 比如代码提示是依靠 gocode 的.
> 
> 不过微软在开发 VS Code 过程中, 定义一种协议, 语言服务器协议, Language Server Protocol.
> 
> 这可是个好东西, 如果你需要开发编辑器或 IDE, 就不需要再为每种语言实现诸如自动完成, 代码提示等功能了,
> 直接利用 语言服务器协议 就行了.
> 
> 而 gopls 就是官方的语言服务器. 

