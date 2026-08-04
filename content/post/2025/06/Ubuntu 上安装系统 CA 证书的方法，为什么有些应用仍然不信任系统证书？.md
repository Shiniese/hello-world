+++
date = "2025-06-02"
title = "Ubuntu 上安装系统 CA 证书的方法，为什么有些应用仍然不信任系统证书？"
slug = "ubuntu-install-system-ca-certificates"
categories = [ "技术笔记", "Linux" ]
tags = [ "Ubuntu", "CA 证书", "HTTPS" ]
readingtime = true
+++

下面我将从以下几个方面详细说明在 Ubuntu 上安装系统 CA 证书的方法、为什么有些应用安装后仍不信任系统证书、`~/.pki/nssdb` 的定义与作用，以及常用的互动命令示例。

[TOC]

---

## 1. 在 Ubuntu 上安装系统级 CA 证书

Ubuntu 使用 `/etc/ssl/certs` 目录和 `update-ca-certificates` 工具来管理系统信任的根证书：

1. **准备 PEM 格式的证书文件**
   通常扩展名为 `.crt` 或 `.pem`，如 `MyCA.crt`。

2. **复制到信任目录**

   ```bash
   sudo cp MyCA.crt /usr/local/share/ca-certificates/
   ```

   > 也可以放到 `/usr/share/ca-certificates/extra/`，但推荐前者。

3. **更新信任列表**

   ```bash
   sudo update-ca-certificates
   ```

   执行后，系统会将 `/usr/local/share/ca-certificates/` 中的新证书自动转换并链接到 `/etc/ssl/certs/ca-certificates.crt`。
   输出示例：

   ```
   Updating certificates in /etc/ssl/certs...
   1 added, 0 removed; done.
   ```

---

## 2. 为什么有些应用仍然不信任系统证书？

虽然系统已经信任了新证书，但部分应用并不会使用系统默认的 `/etc/ssl/certs/ca-certificates.crt`，而是有自己的证书存储：

* **Firefox**：使用基于 NSS（Network Security Services）的独立数据库，位于用户家目录：`~/.pki/nssdb`
* **Chrome/Chromium**：在 Linux 上默认会调用系统证书，但在某些发行版或 Snap 包中可能有嵌入版本
* **Java 应用（Keytool）**：使用 `cacerts` 文件，位置通常在 `/etc/ssl/certs/java/cacerts` 或 Java 安装目录下
* **其他语言运行时**（如 Python `requests`、Go）：可能使用各自绑定的证书文件

因此，仅更新系统存储并不能覆盖它们的私有存储。

---

## 3. `~/.pki/nssdb` 是什么？为什么需要它？

* **NSS（Network Security Services）数据库**
  NSS 是 Mozilla 提供的安全库，用于管理证书、私钥、CRL 等。
* **`~/.pki/nssdb`**

  * 每个用户如果使用基于 NSS 的应用（如 Firefox、命令行工具 `certutil`、某些 Electron 应用），就会在用户家目录创建这个数据库。
  * 存储用户信任的 CA、客户端证书、私钥等。与系统级 `/etc/ssl/certs` 相互独立。

**为什么需要它？**

1. **应用隔离**：Firefox 等浏览器不直接读取系统证书库，使用自己的机制来保证跨平台行为一致。
2. **用户级信任**：允许用户在不需要管理员权限的情况下，新增或撤销信任的证书。
3. **灵活管理**：支持多种格式（`dbm`、`sql`）；可以为不同应用或场景维护独立信任链。

---

## 4. `~/.pki/nssdb` 与系统证书的区别

| 特性   | 系统证书库 (`/etc/ssl/certs`) | NSS 数据库 (`~/.pki/nssdb`)       |
| ---- | ------------------------ | ------------------------------ |
| 作用范围 | 全系统                      | 单个用户或应用                        |
| 格式   | 单一合并的 PEM 文件             | 多个文件（cert8.db/cert9.db 等）      |
| 管理命令 | `update-ca-certificates` | `certutil` 工具                  |
| 权限   | 需要 root                  | 用户级，无需 sudo                    |
| 应用调用 | OpenSSL、curl、apt 等       | Firefox、Chrome (部分)、`certutil` |

---

## 5. 常见的 NSS 数据库 (`~/.pki/nssdb`) 操作方法

> **前提**：确保已安装 `libnss3-tools`，其中包含 `certutil`。

```bash
sudo apt update
sudo apt install libnss3-tools
```

### 5.1 查看当前数据库位置

默认位置为 `sql:$HOME/.pki/nssdb`（SQL 格式）或 `dbm:$HOME/.pki/nssdb`（传统 DBM 格式）：

```bash
certutil -L -d sql:$HOME/.pki/nssdb
```

### 5.2 列出已信任的 CA

```bash
certutil -L -d sql:$HOME/.pki/nssdb
# 输出示例：
# Cert Nickname                                         Trust Attributes
#                                                          
# Builtin Object Token:Entrust.net Certification Authority   CT,, 
# Builtin Object Token:VeriSign Class 3 Public Primary G5     CT,, 
# ...
```

### 5.3 将 PEM 证书导入到 NSS 数据库

```bash
certutil -A \
  -n "MyCA" \
  -t "TCu,Cu,Tu" \
  -d sql:$HOME/.pki/nssdb \
  -i /path/to/MyCA.pem
```

* `-n "MyCA"`：给证书设置一个别名
* `-t "TCu,Cu,Tu"`：信任标志，T：信任该证书用于SSL/TLS连接（服务器认证），C：信任该证书用于客户端认证，u：信任该证书用于SSL/TLS连接的用户身份（用户认证）。
* `-i`：指定输入文件

### 5.4 删除某个证书

```bash
certutil -D -n "MyCA" -d sql:$HOME/.pki/nssdb
```

### 5.5 导出证书

```bash
certutil -L -n "MyCA" -d sql:$HOME/.pki/nssdb -a > MyCA-export.pem
```

得到 PEM 格式的导出文件。

---

## 6. 典型场景与建议

1. **Web 服务客户端（curl、wget）不信任**

   * 先确保系统级 CA 已更新：`sudo update-ca-certificates`
   * 如果使用 Snap 包形式的 curl，可能需要重新安装或配置其自身证书。

2. **Firefox 抛出“证书不受信任”**

   * 打开 `证书管理器` → “您的证书”/“服务器证书” → “导入”
   * 或在命令行用 `certutil` 按上节流程导入到 `~/.pki/nssdb`。

3. **Java 程序（Tomcat、Spring Boot）**

   * 使用 `keytool -importcert -file MyCA.crt -keystore /path/to/cacerts -alias myca`
   * 默认密码通常是 `changeit`。

---

## 总结

* **系统级证书** 管理在 `/etc/ssl/certs`，通过 `update-ca-certificates` 更新；
* **NSS 数据库** (`~/.pki/nssdb`) 则是用户或应用级的证书存储，需要用 `certutil` 单独维护；
* 不同应用依赖不同信任链，所以需要针对性地将 CA 导入相应的存储位置。

这样，你就能保证无论是系统命令行工具、浏览器还是 Java 等环境，都能正确识别并信任安装的自签 CA 了。