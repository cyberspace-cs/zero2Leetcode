---
layout: default
title: 代码库 & ACM 题解 - 我的历史代码与竞赛题目档案
description: 个人历史代码库与 ACM/竞赛题目题解归档，含可下载的 PDF 电子书与源码压缩包
eyebrow: Module 07
---

# 代码库 & ACM 题解

> 🎯 目标：把历年手写代码和刷过的 ACM/竞赛题目沉淀成**可检索、可下载、可追溯**的个人档案库。

## 概述

这个模块解决一个很现实的问题：**代码写完了就散落在硬盘各处，面试时想拿出来展示却找不到。**

本模块把两样东西集中管理：

- **本地代码库**：两个来源汇总
  - `solutions/`：按统一命名规范整理的解题文件，带题号、标题、难度、考点
  - `leetcode/`：**同步自外部做题仓库**（[Gitee buleboy8065/leetcode](https://gitee.com/buleboy8065/leetcode)）的历史代码，
    以 ACM 模式书写（`input()` 读入、`main()` 入口），题面以注释附在文件末尾
- **ACM 题解**：`06_code_archive/problems/` 下的竞赛题目，含题意、思路、代码、复杂度与易错点

所有内容都会被打包成**源码压缩包**，和 PDF 电子书一起放在下面的下载中心。

---

## 📦 下载中心

| 资料 | 说明 | 大小 | 下载 |
|------|------|------|------|
{% for item in site.data.downloads.items -%}
| **{{ item.title }}** | {{ item.desc }} | {{ item.size }} | [下载]({{ site.baseurl }}/downloads/{{ item.file }}) |
{% endfor %}

### 校验值（SHA-256）

| 文件 | SHA-256 |
|------|---------|
{% for item in site.data.downloads.items -%}
| `{{ item.file }}` | <code style="word-break:break-all;font-size:0.78em">{{ item.sha256 }}</code> |
{% endfor %}

> 下载后可用 `sha256sum <文件名>` 核对完整性。

```bash
# Linux / macOS
sha256sum zero2Leetcode-bluebook-v0.1.0-full.pdf

# Windows PowerShell
Get-FileHash .\zero2Leetcode-bluebook-v0.1.0-full.pdf -Algorithm SHA256
```

---

## 🧩 ACM 题解索引 {#acm}

{% if site.data.acm_problems.size > 0 -%}
共收录 {{ site.data.acm_problems.size }} 道题。

| 题目 | 来源 | 题号 | 难度 | 考点 | 完成日期 | 状态 |
|------|------|------|------|------|----------|------|
{% for p in site.data.acm_problems -%}
| [{{ p.title }}]({{ site.baseurl }}/06_code_archive/{{ p.slug }}/) | {{ p.source }} | {{ p.code }} | {{ p.difficulty }} | {{ p.topic }} | {{ p.date }} | {{ p.status }} |
{% endfor %}
{%- else -%}
还没有题目记录。按 [`README.md`](README.md) 的说明添加第一道题。
{%- endif %}

---

## 📁 本地代码库 {#library}

{% if site.data.code_library.files.size > 0 -%}
共 {{ site.data.code_library.count }} 个文件，最近更新：{{ site.data.code_library.generated_at }}。

| 文件 | 来源 | 题号 | 标题 | 难度 | 考点 |
|------|------|------|------|------|------|
{% for f in site.data.code_library.files -%}
| `{{ f.name }}` | `{{ f.source }}` | {{ f.problem_id }} | {{ f.title }} | {{ f.difficulty }} | {{ f.topic }} |
{% endfor %}

> 代码文件本身不单独在网页上发布，统一通过上面的**源码压缩包**下载。
> `solutions/` 是本站在用的规范格式；`leetcode/` 是同步自外部做题仓库的历史代码。
{%- else -%}
`solutions/` 目录还没有代码。用下面这条命令添加第一道题：

```bash
python scripts/new_problem.py --id 1 --title "Two Sum" --difficulty Easy --slug two-sum
```
{%- endif %}

---

## ⬆️ 怎么上传新的 PDF / 代码

本站是**纯静态站点**，没有后端，所以「上传」走 **Git 工作流**：文件放进仓库 → 推送 → 服务器重建。

### 方式一：上传 PDF

1. 把 PDF 放到 `downloads/` 目录
2. 在 `_data/downloads.yml` 里加一条记录：

   ```yaml
   - title: "我的新电子书"
     file: "my-book-v1.0.pdf"
     desc: "一句话说明"
     size: "2.5 MB"
     sha256: "<用 sha256sum 算出来的值>"
   ```

3. 提交推送，服务器重建后页面自动出现下载按钮

```bash
# 算 SHA-256
sha256sum downloads/my-book-v1.0.pdf
```

### 方式二：上传代码

代码直接交给脚本，它会自动扫描、生成索引并打包：

```bash
# 1. 添加题目（自动生成解题文件 + 登记记录）
python scripts/new_problem.py --id 121 --title "Best Time to Buy and Sell Stock" \
    --difficulty Easy --category "Greedy" --slug best-time-to-buy-and-sell-stock

# 2. 重建索引 + 重新打包源码压缩包
python scripts/build-archive.py
```

### 方式三：上传 ACM 题解

复制模板 → 填写 → 重建索引：

```bash
cp 06_code_archive/_template.md 06_code_archive/problems/cf-1234a-my-problem.md
# 编辑文件，填好 front matter 和题解内容
python scripts/build-archive.py
```

### 最后一步：发布

```bash
git add -A
git commit -m "feat: 上传新资料"
git push
```

推送后在服务器上执行重建（详见 [`DEPLOY_zh.md`](../DEPLOY_zh.md)）：

```bash
cd /home/ubuntu/shuati-coach/zero2Leetcode
bash scripts/deploy-server.sh
```

---

## 📕 怎么生成这一页的 PDF

本站的 PDF 由 **Pandoc + XeLaTeX** 链路产出，和蓝皮书是同一套：

```bash
# 完整编译（章节 1-4）
./publish-pdf/build.sh

# 只编译指定章节做预览
./publish-pdf/build.sh --chapters 1 --output bluebook-chapter-1-preview
```

产物写入 `output/pdf/`。依赖与目录说明见 [`publish-pdf/README.md`](../publish-pdf/README.md)。

编译完成后，把 PDF 复制到 `downloads/` 并按上面的「方式一」登记即可。

---

## 相关入口

- [每日刷题记录与流程](../records/README.md)
- [解题代码模板](../solutions/README.md)
- [部署与发布文档](../DEPLOY_zh.md)
- [大厂笔试真题题库](../04_real_interviews/index.html)
