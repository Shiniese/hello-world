+++
date = "2026-10-11"
title = "手机端 Home Assistant 部署 vivohomebridge 权限拒绝问题全解析"
slug = "ha-vivohomebridge-android-permission-denied"
categories = [ "智能家居", "Home Assistant" ]
tags = [ "Home Assistant", "vivohomebridge", "Android", "权限问题", "踩坑记录" ]
readingtime = true
+++

最近我在手机上通过 SmartHouse 运行 Home Assistant，在安装 vivo 官方的 vivohomebridge 集成时遇到了一个非常棘手的加载失败问题。整个排查过程踩了好几个经典的坑，从最基础的权限命令失效，到最终定位到 Android 文件系统的底层限制，最后靠修改源码曲线救国解决了问题。把整个过程记录下来，给同样在手机上折腾 HA 的朋友避坑。

## 一、问题出现：集成加载失败，报错 Permission denied
安装完 vivohomebridge 之后，HA 直接提示配置无效，集成无法启动。点开日志看到了核心报错信息：
```
Failed to load library: Error loading shared library /config/custom_components/vivohomebridge/py_vhome/libvhome_linux_musl_aarch64_1.1.2.so: Permission denied
```
日志后半段还有一大段关于阻塞调用的警告，不过当时我判断核心问题就是这个动态链接库文件权限被拒绝，导致整个集成导入失败。

## 二、第一次踩坑：chmod 命令执行了，但权限没变
按照常规 Linux 运维思路，缺执行权限就加执行权限呗。我立刻进到终端，对着报错的 so 文件执行 `chmod +x`，甚至尝试给整个文件夹递归赋予执行权限。
```bash
chmod +x /config/custom_components/vivohomebridge/py_vhome/libvhome_linux_musl_aarch64_1.1.2.so
```
命令执行完没有任何报错，我以为搞定了，结果用 `ls -la` 查看文件详情时傻眼了：文件权限依然是 `-rw-rw----`，代表可执行的 `x` 位根本没加上。

我当时特别困惑：命令明明执行成功了，为什么权限纹丝不动？

## 三、第二次尝试：复制中转法，依然无效
后来我猜测，会不会是因为 /config 目录是外部挂载进来的，权限被宿主机的文件系统锁定了？于是我试了网上提到的“复制中转法”：把文件先复制到容器内的 /tmp 目录，改完权限再覆盖回原路径，试图绕过挂载卷的权限锁定。
```bash
cd /config/custom_components/vivohomebridge/py_vhome/
for f in *.so; do cp "$f" /tmp/; chmod +x "/tmp/$f"; cp "/tmp/$f" ./; done
```
结果依然失败，覆盖回去的文件权限还是老样子，没有任何变化。

这时候我突然反应过来：我的部署环境不一样。我不是在树莓派、NAS 或者标准服务器 Docker 上跑 HA，我是用 SmartHouse 在**手机**上运行的 Home Assistant。问题会不会就出在这个特殊的运行环境上？

## 四、找到根源：Android 文件系统的底层限制
顺着这个思路往下查，终于搞懂了问题的本质。

SmartHouse 这类手机端 HA 应用，默认会把 HA 的 /config 目录映射到手机的公共存储空间，也就是我们在手机文件管理器里能看到的目录。而 Android 对公共存储有两个强制限制，直接导致了权限问题无解：
1. **不支持 POSIX 权限位**：公共存储用的文件系统（如 sdcardfs、FUSE）根本不识别 Linux 的可执行权限（x），所以你在容器里怎么执行 chmod，底层都会直接忽略这个操作。
2. **强制 noexec 挂载**：出于安全考虑，Android 默认禁止在公共存储分区执行任何二进制文件和动态链接库（.so），就算你能加上 x 权限，系统也不会让它真正运行起来。

简单说，只要 .so 文件还在 /config 目录（也就是手机公共存储）里，就永远不可能被加载执行，再怎么改权限都是白费功夫。

## 五、最终解决：修改源码，把动态库“搬进内存”
知道原因就好办了。我不方便整体迁移配置目录，也不想折腾挂载参数，于是选择了最直接的方案：修改插件的 Python 源码，让它在加载 .so 文件之前，先把文件复制到容器内部的 `/tmp` 目录再加载。

### 为什么选 /tmp？
`/tmp` 是 Linux 原生的 tmpfs（内存文件系统），它运行在容器内部，完全不受 Android 存储权限的管控，完美支持可执行权限位。

### 具体修改方法
我没有用命令行批量替换，而是直接把备份的 `vhome.py` 文件下载下来，手动修改好之后再上传覆盖回去，对我来说更直观可控。

找到文件中原来加载动态库的代码段：
```python
try:
    vhome_lib = ctypes.CDLL(libpath)
```

在它前面插入几行代码，实现“复制到 /tmp → 赋予权限 → 更新加载路径”的逻辑：
```python
import shutil as _shutil, tempfile as _tempfile
_tmp_so_path = os.path.join(_tempfile.gettempdir(), os.path.basename(libpath))
_shutil.copy2(libpath, _tmp_so_path)
os.chmod(_tmp_so_path, 0o755)
libpath = _tmp_so_path
```

修改完成后上传替换原文件，重启 Home Assistant，vivohomebridge 集成果然成功加载了。

## 六、后续避坑提醒
### 1. 记得备份修改后的文件
如果后续通过 HACS 或者手动更新 vivohomebridge 插件，官方的 `vhome.py` 会覆盖掉我们修改过的版本，权限问题会复现。建议把修改好的文件单独备份一份，插件更新后直接覆盖回去即可。

### 2. 留意无限重启 Bug
根据社区反馈，vivohomebridge 插件在部分 HA 版本中存在一个严重 Bug，可能会导致 Home Assistant 陷入无限循环重启。如果修复后发现 HA 频繁闪退、重启，直接删除 vivohomebridge 插件文件夹就能恢复正常。

## 小结
这次踩坑让我对非常规环境下的 Home Assistant 运行机制有了更深的理解，总结几个关键知识点：
- 手机端运行 HA 时，/config 目录受 Android 文件系统限制，`chmod +x` 对其中的二进制文件无效，不是命令用错了。
- 核心原因是公共存储的 `noexec` 挂载策略和不支持 POSIX 权限，属于系统底层限制。
- 无需改动整体部署结构，通过修改源码将动态库复制到 /tmp 加载即可解决。
- 插件更新会覆盖源码修改，注意提前备份修改后的文件。