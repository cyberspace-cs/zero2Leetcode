---
layout: default
title: CF 4A Watermelon 题解
description: Codeforces 4A Watermelon 题解，判断偶数能否拆成两个正偶数之和
eyebrow: 代码库 / Codeforces
permalink: /06_code_archive/problems/cf-4a-watermelon/
---

# CF 4A Watermelon

## 题目信息

| 字段 | 内容 |
|------|------|
| 来源 | Codeforces |
| 题号 | CF 4A |
| 难度 | 入门（800） |
| 考点 | 数学 / 奇偶性 |
| 完成日期 | 2026-09-10 |
| 状态 | 独立完成 |

## 题目描述

给定一个重量 $w$（$1 \le w \le 100$），判断能否把它切成**两块**，要求两块都是**正偶数**。

## 输入格式

一行一个整数 $w$。

## 输出格式

能切成两块正偶数输出 `YES`，否则输出 `NO`。

## 样例

**输入**

```
8
```

**输出**

```
YES
```

> $8 = 4 + 4$，两块都是正偶数。

## 思路

1. 两块都是**正偶数**，所以每块至少是 $2$，两块之和至少是 $4$。
2. 偶数 + 偶数 = 偶数，所以 $w$ 必须是偶数。
3. 但 $w = 2$ 时只能拆成 $1+1$ 或 $0+2$，都不是两块正偶数，要特判掉。

结论：**$w$ 是偶数且 $w > 2$** 时输出 `YES`。

## 代码

```python
import sys

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    w = int(data[0])
    # 偶数且大于 2 才能拆成两个正偶数
    print("YES" if w % 2 == 0 and w > 2 else "NO")

if __name__ == "__main__":
    solve()
```

## 复杂度

- 时间：$O(1)$
- 空间：$O(1)$

## 易错点

- 忘记特判 $w = 2$，会错答 `YES`。
- 题目要求两块都是**正**偶数，所以 $0$ 不算。

## 同类题

- CF 231A Team
- CF 158A Next Round
