# 代码库 & ACM 题解

个人历史代码库与竞赛题目档案。页面由 Jekyll 从本目录的 `index.md` 渲染，索引数据由脚本自动生成。

## 目录结构

```
06_code_archive/
├── index.md          # 模块主页（下载中心 + 两个索引表）
├── _template.md      # ACM 题目模板，复制它来新建题目
├── README.md         # 本文件
└── problems/         # 每道 ACM 题一个 md
    └── cf-4a-watermelon.md
```

> `_template.md` 以 `_` 开头，**不会被 Jekyll 发布，也不会进索引**，可以放心留在这里当模板。

## 数据从哪来

页面上的两张表不是手写的，由 `scripts/build-archive.py` 扫描生成：

| 页面区块 | 数据来源 | 生成的中间文件 |
|----------|----------|----------------|
| 下载中心 | `_data/downloads.yml` | 手工维护 |
| 本地代码库 | `solutions/*.py` 的 docstring | `_data/code_library.yml` |
| ACM 题解索引 | `06_code_archive/problems/*.md` 的 front matter | `_data/acm_problems.yml` |

## 新增一道 ACM 题

```bash
# 1. 复制模板（文件名用英文 slug，不带空格）
cp 06_code_archive/_template.md 06_code_archive/problems/cf-1234a-example.md

# 2. 编辑文件：
#    - 顶部 front matter 的 title / eyebrow（eyebrow 末段会作为「来源」列）
#    - permalink 保持 /06_code_archive/problems/<slug>/ 格式
#    - 正文里填好「题目信息」表格，脚本会读取其中的题号/难度/考点等

# 3. 重建索引 + 重新打包
python scripts/build-archive.py
```

### front matter 要求

```yaml
---
layout: default
title: CF 1234A Example        # 必填，标题里含 "<" 会被脚本忽略
description: 一句话描述
eyebrow: 代码库 / Codeforces    # 末段作为「来源」列
permalink: /06_code_archive/problems/cf-1234a-example/
---
```

### 正文里的题目信息表

脚本按固定表头抓取，**表头文字要一致**：

| 字段 | 内容 |
|------|------|
| 来源 | Codeforces |
| 题号 | CF 1234A |
| 难度 | 普及- |
| 考点 | 贪心 |
| 完成日期 | 2026-09-10 |
| 状态 | 独立完成 |

## 新增解题代码

不要手工建文件，用脚本：

```bash
python scripts/new_problem.py --id 121 --title "Best Time to Buy and Sell Stock" \
    --difficulty Easy --category "Greedy" --slug best-time-to-buy-and-sell-stock
```

生成 `solutions/lc_0121_best-time-to-buy-and-sell-stock.py`，并登记到 `records/daily_progress.csv`。

脚本会读取解题文件 docstring 里的 `Problem:` / `Difficulty:` / `Category:` 字段来做索引，
所以**不要删掉这些字段**。

## 打包与发布

`build-archive.py` 会同时把 `solutions/` 和 `06_code_archive/problems/` 打包成
`downloads/zero2Leetcode-my-solutions-v0.1.0.zip`，并把大小和 SHA-256 回写到 `_data/downloads.yml`。

```bash
python scripts/build-archive.py     # 重建索引 + 打包
git add -A && git commit -m "chore: 更新代码库"
git push
```

推送后在服务器重建（见 [`DEPLOY_zh.md`](../DEPLOY_zh.md)）：

```bash
cd /home/ubuntu/shuati-coach/zero2Leetcode
bash scripts/deploy-server.sh
```

## 常见问题

**页面上的表是空的？**
忘了跑 `python scripts/build-archive.py`，或者新题目的 front matter 里 `title` 还是模板占位符（含 `<`）。

**zip 里的内容是旧的？**
同上，需要重新跑一次打包脚本。

**下载链接 404？**
确认文件确实在 `downloads/` 目录且文件名与 `_data/downloads.yml` 里的 `file` 完全一致（区分大小写）。
