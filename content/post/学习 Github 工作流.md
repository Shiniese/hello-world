+++
date = "2024-07-19"
title = "学习 Github 工作流"
slug = "learn-github-workflow"
categories = [ "技术笔记", "版本控制" ]
tags = [ "Git", "GitHub", "工作流" ]
readingtime = true
+++

介绍了在使用 Git 时，向远程仓库推送更新的步骤和注意事项，包括从未拉取过仓库和已拉取过仓库两种情景下的操作。

视频 By [码农高天](https://www.bilibili.com/video/BV19e4y1q7JJ/?share_source=copy_web&vd_source=df20b14076e1e3e1de093bce845df04d)

# 笔记

## 情景 1：向远程仓库 push 更新（本地从未拉取过仓库）

1. 克隆远程仓库到本地:
```bash
git clone <repository_url>
```

2. 创建并切换到新的功能分支:
```bash
git checkout -b my_feature
```

3. 修改代码后,查看更改:
```bash
git diff
```

4. 添加修改的文件到暂存区:
```bash
git add <file_name>
```

5. 提交更改:
```bash
git commit -m "注释"
```

6. 将功能分支推送到远程仓库:
```bash
git push origin my_feature
```

## 情景 2：向远程仓库 push 更新（已拉取过仓库，但写代码时发现远端 GitHub 上代码出现改变）

1. 当主分支(main)有更新时,同步这些更新到功能分支:
```bash
git checkout main
git pull origin main
git checkout my_feature
git rebase main
```

`git rebase main` 意思是先把 main 移过来，然后根据我的 commit 来修改成新的内容。中途可能会出现 `rebase conflict`，这时需要手动选择保留哪段代码。

2. 强制推送更新后的功能分支到远程仓库:
```bash
git push -f origin my_feature
```

需要注意的是,在使用 `git push -f` (强制推送)时要格外小心,因为它会覆盖远程分支的历史。只有在确定没有其他人在同一分支上工作或者大家都是用这样同一套工作流时才应使用此命令。

3. 在GitHub上创建Pull Request

## 情景 3：远程仓库完成更新后

合并 Pull Request 后，清理分支:
```bash
git checkout main
git pull origin main
git branch -d my_feature
```
