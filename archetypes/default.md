+++
date = "{{ .Date }}"
title = "{{ replace .File.ContentBaseName "-" " " | title }}"
slug = ""
categories = [  ]
tags = [  ]
readingtime = true

# 可选补充字段（可根据你的站点需求选择开启）：
# 文章摘要，用于列表页展示，不填则默认截取正文前N个字符
# description = ""
# 文章封面图路径
# cover = ""
# 是否在首页置顶，设为true则优先展示
# sticky = false
# 是否开启评论，默认开启，不需要的单篇文章可设为false
# comment = true
# 是否为草稿，设为true则hugo build时不会生成公开页面
# draft = true
+++
