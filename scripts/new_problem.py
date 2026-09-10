#!/usr/bin/env python3
"""
新建一道 LeetCode 题目记录

一条命令同时完成三件事：
  1. 在 solutions/ 下按命名规范生成解题文件（从 solutions/solution_template.py 派生）
  2. 在 records/daily_progress.csv 末尾追加一行刷题记录
  3. 打印接下来的 git 提交命令

用法示例：

  # 只给编号，标题/难度/标签自动留空待填
  python scripts/new_problem.py --id 1

  # 完整信息
  python scripts/new_problem.py \
      --id 1 --title "Two Sum" --difficulty Easy \
      --category "Hash Table" --slug two-sum

  # 从今天开始记，一次加多题
  python scripts/new_problem.py --id 1 --title "Two Sum" --difficulty Easy --slug two-sum
  python scripts/new_problem.py --id 206 --title "Reverse Linked List" --difficulty Easy --slug reverse-linked-list

生成的解题文件名形如 solutions/lc_001_two_sum.py。
若文件已存在，默认跳过（加 --force 覆盖）。
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOLUTIONS_DIR = ROOT / "solutions"
TEMPLATE_FILE = SOLUTIONS_DIR / "solution_template.py"
CSV_FILE = ROOT / "records" / "daily_progress.csv"

CSV_HEADER = [
    "date",
    "problem_id",
    "problem_title",
    "difficulty",
    "category",
    "language",
    "status",
    "notes",
    "link",
]

DIFFICULTIES = ("Easy", "Medium", "Hard")
STATUSES = ("not_started", "in_progress", "solved", "review")


def slugify(text: str) -> str:
    """把标题转成文件名用的 slug，例如 'Two Sum' -> 'two-sum'。"""
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def solution_filename(problem_id: str, title: str, slug: str | None) -> str:
    """规范：lc_<补零到4位的编号>_<slug>.py"""
    tail = slugify(slug) if slug else slugify(title)
    if not tail:
        tail = "problem"
    return f"lc_{int(problem_id):04d}_{tail}.py"


def render_solution(problem_id: str, title: str, difficulty: str,
                    category: str, url: str) -> str:
    """基于模板生成解题文件内容。"""
    if TEMPLATE_FILE.exists():
        base = TEMPLATE_FILE.read_text(encoding="utf-8")
    else:
        base = 'class Solution:\n    def solve(self, params):\n        raise NotImplementedError\n'

    # 填充模板里的占位符
    replacements = {
        "<Problem Title>": title or f"LeetCode {problem_id}",
        "<LeetCode URL>": url,
        "<Easy/Medium/Hard>": difficulty,
        "<Array/String/DP/Graph/...>": category,
        "<YYYY-MM-DD>": dt.date.today().isoformat(),
    }
    for old, new in replacements.items():
        base = base.replace(old, new)

    header = (
        f"# 题目编号: {int(problem_id):04d}\n"
        f"# 记录日期: {dt.date.today().isoformat()}\n"
        f"# 提示: 写完后把 records/daily_progress.csv 里对应行的 status 改成 solved\n"
    )
    return header + base


def append_progress_row(row: dict[str, str]) -> bool:
    """向 daily_progress.csv 追加一行；返回是否真的写入。"""
    CSV_FILE.parent.mkdir(parents=True, exist_ok=True)
    is_new = not CSV_FILE.exists()

    # 读出现有行，避免同一题重复记录
    existing: set[tuple[str, str]] = set()
    if not is_new:
        with CSV_FILE.open("r", encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                existing.add((r.get("date", ""), r.get("problem_id", "")))

    if (row["date"], row["problem_id"]) in existing:
        print(f"  · records/daily_progress.csv 中已有 {row['date']} #{row['problem_id']}，跳过")
        return False

    with CSV_FILE.open("a", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_HEADER)
        if is_new:
            writer.writeheader()
        writer.writerow(row)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="为一道 LeetCode 题生成解题文件并登记刷题记录",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--id", required=True, help="LeetCode 题号，例如 1")
    parser.add_argument("--title", default="", help="题目标题，例如 'Two Sum'")
    parser.add_argument("--difficulty", default="", choices=["", *DIFFICULTIES],
                        help="难度")
    parser.add_argument("--category", default="", help="考点分类，例如 'Hash Table'")
    parser.add_argument("--slug", default="", help="题目 URL slug，用于文件名，例如 two-sum")
    parser.add_argument("--language", default="Python", help="语言（默认 Python）")
    parser.add_argument("--status", default="not_started", choices=STATUSES,
                        help="初始状态（默认 not_started）")
    parser.add_argument("--notes", default="", help="备注")
    parser.add_argument("--date", default=dt.date.today().isoformat(),
                        help="记录日期 YYYY-MM-DD（默认今天）")
    parser.add_argument("--force", action="store_true", help="覆盖已存在的解题文件")
    args = parser.parse_args()

    if not re.fullmatch(r"\d+", str(args.id)):
        print(f"错误：--id 必须是数字，收到 {args.id!r}", file=sys.stderr)
        return 2

    pid = f"{int(args.id):04d}"
    slug = args.slug or slugify(args.title)
    url = f"https://leetcode.com/problems/{slug}/" if slug else ""

    # 1) 生成解题文件
    SOLUTIONS_DIR.mkdir(parents=True, exist_ok=True)
    target = SOLUTIONS_DIR / solution_filename(pid, args.title, args.slug)
    if target.exists() and not args.force:
        print(f"  · 解题文件已存在，跳过：solutions/{target.name}（--force 可覆盖）")
    else:
        target.write_text(
            render_solution(pid, args.title, args.difficulty, args.category, url),
            encoding="utf-8",
        )
        print(f"  ✓ 已生成 solutions/{target.name}")

    # 2) 写入刷题记录
    row = {
        "date": args.date,
        "problem_id": pid,
        "problem_title": args.title or f"LeetCode {pid}",
        "difficulty": args.difficulty,
        "category": args.category,
        "language": args.language,
        "status": args.status,
        "notes": args.notes,
        "link": url,
    }
    if append_progress_row(row):
        print("  ✓ 已登记 records/daily_progress.csv")

    # 3) 给出下一步
    print("\n下一步：")
    print(f"  1. 打开 solutions/{target.name} 写题解")
    print("  2. 填好后把 records/daily_progress.csv 里该行 status 改成 solved")
    print("  3. 提交推送：")
    print(f"     git add -A && git commit -m \"feat: {pid} {row['problem_title']}\" && git push")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
