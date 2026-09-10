# 每日刷题记录

这个目录用来保存你的刷题进度，方便回溯、统计和向别人展示刷了多少题。

## 文件说明

| 文件 | 用途 |
|------|------|
| `daily_progress.csv` | 刷题总台账，每刷一题追加一行 |
| `DAILY_TEMPLATE.md` | 每日复盘模板，按天复制一份 |
| `YYYY-MM-DD.md` | 当天的复盘记录（由模板复制而来） |

## daily_progress.csv 字段

| 字段 | 说明 | 示例 |
|------|------|------|
| `date` | 刷题日期 | `2026-09-10` |
| `problem_id` | 力扣题号（补零到 4 位） | `0001` |
| `problem_title` | 题目标题 | `Two Sum` |
| `difficulty` | 难度 | `Easy` / `Medium` / `Hard` |
| `category` | 考点分类 | `Hash Table` |
| `language` | 语言 | `Python` |
| `status` | 状态 | `not_started` / `in_progress` / `solved` / `review` |
| `notes` | 备注（易错点、关键思路） | `边界：空数组` |
| `link` | 题目链接 | `https://leetcode.com/problems/two-sum/` |

## 每天怎么刷（推荐流程）

### 1. 挑题

按 `04_real_interviews/` 里的公司真题，或 `03_leetcode_practice/` 的题单挑一道。

### 2. 一条命令登记

```bash
python scripts/new_problem.py \
    --id 1 --title "Two Sum" --difficulty Easy \
    --category "Hash Table" --slug two-sum
```

这条命令会同时：

- 生成 `solutions/lc_0001_two_sum.py`（已按模板预填题号、链接、日期）
- 在 `records/daily_progress.csv` 追加一行记录

> 只有题号也能用：`python scripts/new_problem.py --id 1`

### 3. 写题解

打开生成的文件，把思路、复杂度、易错点写进 docstring，然后实现 `solve()`。

### 4. 更新状态

把 `records/daily_progress.csv` 中该行 `status` 改成 `solved`。

### 5. 写当天复盘

复制模板：

```bash
cp records/DAILY_TEMPLATE.md records/2026-09-10.md
```

填完后提交推送：

```bash
git add -A
git commit -m "feat: 0001 Two Sum"
git push
```

## 统计进度

```bash
# 一共记了多少题
awk -F, 'NR>1' records/daily_progress.csv | wc -l

# 按状态统计
awk -F, 'NR>1 {print $7}' records/daily_progress.csv | sort | uniq -c

# 按难度统计
awk -F, 'NR>1 {print $4}' records/daily_progress.csv | sort | uniq -c
```

## 命名规范

- 解题文件：`solutions/lc_<4位题号>_<slug>.py`，例如 `lc_0001_two_sum.py`
- 每日复盘：`records/<YYYY-MM-DD>.md`
