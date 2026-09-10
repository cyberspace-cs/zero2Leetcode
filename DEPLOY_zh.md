# 部署与日常刷题流程

本文档说明这个仓库的**发布方式**和**每天怎么刷题**。

---

## 一、站点是怎么构建的

`zero2leetcode.taoxie.vip` 上的页面**不是手写的**，而是由 **Jekyll** 从 Markdown 源码渲染出来的。

这和上游 `onefly.top/zero2Leetcode` 用的是同一套渲染链路，所以两边页面结构完全一致：

```
index.md  ──┐
            ├─►  Jekyll  ─►  _site/  ─►  nginx  ─►  https://zero2leetcode.taoxie.vip/
_layouts/   │
assets/    ─┘
```

关键文件：

| 路径 | 作用 |
|------|------|
| `_config.yml` | Jekyll 配置（title、插件、include） |
| `_layouts/default.html` | 全站布局（导航栏、GitHub Star 按钮、页脚） |
| `_data/nav.yml` | 导航菜单数据 |
| `assets/css/docs.css` | 文档页样式（真题/面试页用这套） |
| `assets/css/style.css` | 首页样式（`index.html` 用这套） |
| `04_real_interviews/index.md` | 笔试真题页的**内容源文件** |
| `05_interview/index.md` | 面试备战页的内容源文件 |

> ⚠️ **重要**：`04_real_interviews/` 和 `05_interview/` 下**不要手写 `index.html`**。
> 它们的页面内容来自同目录的 `index.md`，手写 `index.html` 会和 Jekyll 生成的结果冲突。
> （这也是之前页面结构不对的原因。）

### baseurl 的差异

| 部署位置 | baseurl |
|----------|---------|
| `onefly.top/zero2Leetcode/`（子目录） | `/zero2Leetcode` |
| `zero2leetcode.taoxie.vip`（根路径） | 空 |

所以在本服务器构建时必须传 `--baseurl ""`，部署脚本已经处理好了。

---

## 二、发布到服务器

### 前置条件（服务器已配置完成）

```bash
sudo apt-get install -y ruby-full jekyll build-essential
sudo gem install jekyll-sitemap --no-document   # _config.yml 声明了该插件
```

### 一键发布

服务器上仓库位于 `/home/ubuntu/shuati-coach/zero2Leetcode`：

```bash
cd /home/ubuntu/shuati-coach/zero2Leetcode
bash scripts/deploy-server.sh
```

脚本会依次执行：

1. `git fetch origin && git reset --hard origin/main` 同步源码
2. 删除会冲突的手写 `index.html`（第 4、5 模块）
3. `jekyll build --baseurl ""` 构建到 `_site/`
4. 校验 `index.html`、`04_real_interviews/index.html`、`05_interview/index.html`、`assets/css/docs.css` 是否生成
5. 把 nginx 的 `root` 指向 `_site/` 并 `reload`

跳过 GitHub 同步（网络不通时）：

```bash
SKIP_PULL=1 bash scripts/deploy-server.sh
```

### 发布后自检

```bash
bash scripts/verify-deploy.sh
```

会检查构建产物、页面布局、公司分组、GitHub 链接、以及抽检一篇真题文章能否访问。

### 网络不通时的备用方案

如果服务器访问 GitHub 超时，可以**从本地直接推源码**：

```bash
# 本地：打包源码（排除 .git 和构建产物）
tar -czf z2l-src.tar.gz --exclude=.git --exclude=_site .

# 上传
scp z2l-src.tar.gz ubuntu@43.143.231.106:/tmp/

# 服务器：解包后重新构建
ssh ubuntu@43.143.231.106
cd /home/ubuntu/shuati-coach/zero2Leetcode
rm -f 04_real_interviews/index.html 05_interview/index.html
tar -xzf /tmp/z2l-src.tar.gz
SKIP_PULL=1 bash scripts/deploy-server.sh
```

### nginx 配置

`/etc/nginx/sites-available/zero2Leetcode-domain`：

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name zero2leetcode.taoxie.vip;

    root /home/ubuntu/shuati-coach/zero2Leetcode/_site;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
        autoindex off;
    }
}
```

> `root` 必须指向 **`_site`**（构建产物），而不是仓库根目录。
> 指向仓库根目录会看到目录列表，因为根目录里没有渲染好的 `04_real_interviews/index.html`。

---

## 三、每天怎么刷题

完整说明见 [`records/README.md`](records/README.md)，这里是速查版。

### 1. 登记一道题

```bash
python scripts/new_problem.py \
    --id 1 --title "Two Sum" --difficulty Easy \
    --category "Hash Table" --slug two-sum
```

一条命令做两件事：

- 生成 `solutions/lc_0001_two_sum.py`（模板已预填题号、链接、日期）
- 在 `records/daily_progress.csv` 追加一行

只有题号也能用：

```bash
python scripts/new_problem.py --id 206
```

### 2. 写题解

打开生成的 `solutions/lc_XXXX_*.py`，在 docstring 里写思路、复杂度、易错点，然后实现。

### 3. 更新状态 + 写复盘

- 把 `records/daily_progress.csv` 里对应行的 `status` 改成 `solved`
- 复制当天复盘模板：`cp records/DAILY_TEMPLATE.md records/2026-09-10.md`

### 4. 提交推送

```bash
git add -A
git commit -m "feat: 0001 Two Sum"
git push
```

推送后如果想同步到线上，再执行一次服务器发布命令。

---

## 三、代码库与 ACM 题解模块

`06_code_archive/` 是个人代码库与竞赛题目档案页，页面上的三张表全部由脚本生成，不要手写。

### 三条数据流

```
solutions/*.py 的 docstring ──┐
                              ├──► scripts/build-archive.py ──┬──► _data/code_library.yml
06_code_archive/problems/*.md ┤                               ├──► _data/acm_problems.yml
                              │                               └──► downloads/zero2Leetcode-代码库.zip
_data/downloads.yml（手工维护）──┴──► 下载中心表（sha256 自动回写）
```

### 新增代码

```bash
python scripts/new_problem.py --id 121 --title "Best Time to Buy and Sell Stock" \
    --difficulty Easy --category "Greedy" --slug best-time-to-buy-and-sell-stock
python scripts/build-archive.py     # 重建索引 + 重新打包
```

### 新增 ACM 题解

```bash
cp 06_code_archive/_template.md 06_code_archive/problems/cf-1234a-example.md
# 编辑：front matter 的 title/eyebrow/permalink + 正文的「题目信息」表
python scripts/build-archive.py
```

### 新增下载资料（PDF / 压缩包）

1. 文件放进 `downloads/`
2. 在 `_data/downloads.yml` 加一条记录（`file` / `title` / `desc` / `size` / `sha256`）
3. `git push` 后服务器重建

> `file` 为 `zero2Leetcode-代码库.zip` 的那条由脚本自动维护，手改会被覆盖。

### 生成这一页的 PDF

PDF 由 Pandoc + XeLaTeX 链路产出，和蓝皮书同一套。`06_code_archive` 已经接成**第 5 章**：

```bash
./publish-pdf/build.sh --chapters 5 --output zero2Leetcode-代码库   # 只编代码库这章
./publish-pdf/build.sh                                             # 完整编译（1-4 章）
./publish-pdf/build.sh --chapters 1 --output preview                # 只编译第 1 章做预览
```

产物写入 `output/pdf/`，把它复制到 `downloads/` 再同步清单即可：

```bash
cp output/pdf/zero2Leetcode-代码库.pdf downloads/
python scripts/sync-downloads.py
# 然后打开 _data/downloads.yml 补一下 title / desc
```

依赖：`pandoc`、`xelatex`、`pdfinfo`、`python3`。

#### Windows 上的 pandoc 坑（重要）

从 GitHub 下载的 `pandoc.exe` 约 233 MB，带 **Mark-of-the-Web**，直接运行会**静默卡住**（无输出、无报错），很容易误判成死循环。两个症状：

- `pandoc --version` 长时间没有任何输出
- 即使加了 `-halt-on-error` 也不结束

解决办法是解除文件标记并给杀软时间：

```powershell
# 一次性解除整目录的下载标记
Get-ChildItem D:\soft\pandoc -Recurse -File | Unblock-File

# 之后再跑，第一次约 24 秒（杀软冷扫描），单次转换甚至要 3 分钟
D:\soft\pandoc\pandoc-3.11\pandoc.exe --version
```

> 结论：**pandoc 不是卡死，是被杀软拖慢**。耐心等，不要中途 kill。
> 若想彻底解决，可把 pandoc 目录加入 Windows Defender 的排除项（需要管理员权限）。

#### 等宽字体回退（已修复）

`templates/bluebook.tex` 原先的等宽字体回退链是 `JetBrains Mono` → `Menlo`，
而 **Menlo 是 macOS 专有字体**，在 Windows/Linux 上会直接报错：

```
! Package fontspec Error: The font "Menlo" cannot be found.
```

现已改为四级回退，覆盖三大平台：

```
JetBrains Mono -> Consolas (Windows) -> DejaVu Sans Mono (Linux) -> Courier New
```

字体全部缺失时才会退到最后的 `Courier New`，一般不会触发。

#### 分步调试技巧

pandoc 启动很慢（杀软扫描），反复重跑很浪费时间。建议把两步拆开：

```bash
# 第 1 步：只生成 LaTeX 源码（慢，几分钟），出错时看这个文件
pandoc 00-preface.md 05-code-archive.md --to=latex --standalone \
    --template=publish-pdf/templates/bluebook.tex \
    --metadata-file=publish-pdf/templates/metadata.yaml \
    --top-level-division=chapter --syntax-highlighting=none \
    -o build/code-archive.tex

# 第 2 步：单独编译（快，约 10 秒），改字体/排版只需重跑这一步
xelatex -interaction=nonstopmode -halt-on-error build/code-archive.tex
```

> 注意：`--no-highlight` 在 pandoc 3.x 已废弃，会打警告；改用 `--syntax-highlighting=none`。

`publish-pdf/build.sh` 里的 `python3` 在 Windows 上可直接用（实测 Python 3.11.9），
`xelatex` / `pdfinfo` 来自 TeX Live，加到 PATH 即可。

---

## 四、目录速查

| 目录 | 内容 |
|------|------|
| `00_python_basics/` | Python 基础 |
| `01_data_structures/` | 数据结构 |
| `02_algorithms/` | 核心算法 |
| `03_leetcode_practice/` | LeetCode 题单 |
| `04_real_interviews/` | **大厂笔试真题题库**（22 家公司） |
| `05_interview/` | 面试备战（手撕 + 八股） |
| `06_code_archive/` | **代码库 & ACM 题解**（含下载中心） |
| `downloads/` | 对外发布的可下载资料（PDF / 压缩包） |
| `solutions/` | 你自己的解题代码 |
| `records/` | 刷题记录与每日复盘 |
| `scripts/` | 构建、部署、拓题、打包脚本 |
