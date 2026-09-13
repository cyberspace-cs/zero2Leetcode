#!/usr/bin/env python3
"""
代码库索引生成 + 源码打包

一条命令完成三件事：

  1. 扫描 solutions/*.py 与外部做题仓库 -> 生成 _data/code_library.yml
  2. 扫描 06_code_archive/problems/*.md -> 生成 _data/acm_problems.yml
  3. 打包上述内容                -> downloads/zero2Leetcode-my-solutions-v0.1.0.zip
     并把 zip 的大小与 SHA-256 写回 _data/downloads.yml

用法：

    python scripts/build-archive.py

外部做题仓库（Gitee: buleboy8065/leetcode）默认取本仓库的同级目录 `../leetcode`，
可用环境变量覆盖：

    LEETCODE_REPO=D:/path/to/leetcode python scripts/build-archive.py

该目录不存在时会**保留上次生成的条目**（服务器上构建时不需要这个仓库）。

每次新增题目或代码后跑一次即可，页面索引和下载包会同步更新。
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import zipfile
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOLUTIONS_DIR = ROOT / "solutions"
ACM_DIR = ROOT / "06_code_archive" / "problems"
DATA_DIR = ROOT / "_data"
DOWNLOADS_DIR = ROOT / "downloads"

# 外部的 LeetCode / ACM 做题仓库（Gitee 上的 buleboy8065/leetcode）。
# 它位于本项目之外，属于「本地历史代码库」，通过环境变量可指向任意位置。
LEETCODE_REPO = Path(os.environ.get("LEETCODE_REPO") or (ROOT.parent / "leetcode"))

CODE_LIBRARY_YML = DATA_DIR / "code_library.yml"
ACM_PROBLEMS_YML = DATA_DIR / "acm_problems.yml"
DOWNLOADS_YML = DATA_DIR / "downloads.yml"

ARCHIVE_NAME = "zero2Leetcode-my-solutions-v0.1.0.zip"
ARCHIVE_PATH = DOWNLOADS_DIR / ARCHIVE_NAME

# zip 内条目的固定时间戳，保证内容不变时打包结果稳定
ZIP_TIMESTAMP = (2026, 1, 1, 0, 0, 0)

# 打包时跳过的目录/文件（.git 是外部做题仓库里必须排除的）
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".ipynb_checkpoints", ".idea", ".vscode"}
SKIP_FILES = {".DS_Store", "Thumbs.db"}


def q(value) -> str:
    """把值序列化成合法的 YAML 标量（JSON 是 YAML 的子集）。"""
    return json.dumps("" if value is None else str(value), ensure_ascii=False)


# ---------------------------------------------------------------------------
# 解析
# ---------------------------------------------------------------------------

DOC_FIELD_RE = {
    "title": re.compile(r"^Problem:\s*(.+?)\s*$", re.M),
    "link": re.compile(r"^Link:\s*(.+?)\s*$", re.M),
    "difficulty": re.compile(r"^Difficulty:\s*(.+?)\s*$", re.M),
    "topic": re.compile(r"^Category:\s*(.+?)\s*$", re.M),
    "date": re.compile(r"^Date:\s*(.+?)\s*$", re.M),
}

FILENAME_RE = re.compile(r"^lc_(\d+)_(.+)\.py$")


def parse_solution(path: Path) -> dict:
    """从一个解题文件里提取索引信息。"""
    text = path.read_text(encoding="utf-8", errors="replace")

    info = {}
    for key, pattern in DOC_FIELD_RE.items():
        m = pattern.search(text)
        info[key] = m.group(1) if m else ""

    # 文件名兜底：lc_0001_two_sum.py
    m = FILENAME_RE.match(path.name)
    if m:
        problem_id = m.group(1)
        slug = m.group(2)
        info.setdefault("slug", slug)
    else:
        problem_id = ""
        slug = ""

    info["problem_id"] = problem_id

    # 标题兜底：用 slug 拼一个可读标题
    if not info.get("title") and slug:
        info["title"] = slug.replace("-", " ").title()

    # 占位符没被替换的情况（直接用模板手抄的文件）
    if info.get("title", "").startswith("<"):
        info["title"] = ""
    for key in ("difficulty", "topic"):
        if info.get(key, "").startswith("<"):
            info[key] = ""

    return {
        "name": path.name,
        "problem_id": problem_id or "—",
        "title": info.get("title") or "—",
        "difficulty": info.get("difficulty") or "—",
        "topic": info.get("topic") or "—",
        "date": info.get("date") or "—",
        "link": info.get("link") or "",
        "source": "solutions/",
    }


# 外部仓库命名：LC <题号>-<题名>.py，例如 "LC 1-两数之和.py"
LC_FILENAME_RE = re.compile(r"^LC\s*(\d+)\s*[-–—]\s*(.+?)\.py$", re.IGNORECASE)
# 误操作产生的副本后缀：" copy 2"
COPY_SUFFIX_RE = re.compile(r"\s+copy(\s*\d+)?$", re.IGNORECASE)


def parse_leetcode_solution(path: Path, repo_root: Path) -> dict:
    """解析外部做题仓库里的 LC 题解文件。

    这些文件没有 docstring 元数据，题号/题名全部取自文件名，
    所在子目录作为「来源」（例如 leetcode/ACM-lc/HOT100）。
    """
    m = LC_FILENAME_RE.match(path.name)
    problem_id = m.group(1) if m else "—"
    title = m.group(2).strip() if m else path.stem
    title = COPY_SUFFIX_RE.sub("", title).strip() or path.stem

    parent = path.parent.relative_to(repo_root)
    source = "leetcode" if str(parent) == "." else f"leetcode/{parent.as_posix()}"

    return {
        "name": path.name,
        "problem_id": problem_id,
        "title": title,
        "difficulty": "—",
        "topic": "—",
        "date": "—",
        "link": "",
        "source": source,
    }


def parse_front_matter(path: Path) -> dict:
    """解析 markdown 顶部的简单 front matter（只支持 key: value 标量）。"""
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        return {}

    end = text.find("\n---", 3)
    if end < 0:
        return {}

    block = text[3:end]
    data: dict[str, str] = {}
    for line in block.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        value = value.strip().strip('"').strip("'")
        if key.strip() == "permalink":
            # /06_code_archive/problems/cf-4a-watermelon/ -> problems/cf-4a-watermelon
            value = value.strip("/")
            prefix = "06_code_archive/"
            if value.startswith(prefix):
                value = value[len(prefix):]
        data[key.strip()] = value
    return data


def parse_aca_problem(path: Path) -> dict | None:
    """把一个 ACM 题解 md 转成索引记录；跳过模板文件。"""
    if path.name.startswith("_"):
        return None

    fm = parse_front_matter(path)
    slug = fm.get("permalink") or f"problems/{path.stem}"

    title = fm.get("title", "")
    if not title or "<" in title or title == "题目标题":
        return None

    eyebrow = fm.get("eyebrow", "")
    source = eyebrow.split("/")[-1].strip() if "/" in eyebrow else "—"

    # 从正文里补出题号/难度/考点/日期/状态
    body = path.read_text(encoding="utf-8", errors="replace")
    fields: dict[str, str] = {}
    for line in body.splitlines():
        m = re.match(r"^\|\s*(来源|题号|难度|考点|完成日期|状态)\s*\|\s*(.+?)\s*\|\s*$", line)
        if m:
            fields[m.group(1)] = m.group(2).strip()

    return {
        "title": title,
        "slug": slug,
        "source": fields.get("来源") or source,
        "code": fields.get("题号", "—"),
        "difficulty": fields.get("难度", "—"),
        "topic": fields.get("考点", "—"),
        "date": fields.get("完成日期", "—"),
        "status": fields.get("状态", "—"),
    }


# ---------------------------------------------------------------------------
# 生成
# ---------------------------------------------------------------------------

def write_code_library(entries: list[dict]) -> None:
    lines = [
        "# 本文件由 scripts/build-archive.py 自动生成，请勿手工编辑。",
        f"generated_at: {q(date.today().isoformat())}",
        f"count: {len(entries)}",
        "files:",
    ]
    for e in entries:
        lines.append(f"  - name: {q(e['name'])}")
        lines.append(f"    source: {q(e.get('source', '—'))}")
        lines.append(f"    problem_id: {q(e['problem_id'])}")
        lines.append(f"    title: {q(e['title'])}")
        lines.append(f"    difficulty: {q(e['difficulty'])}")
        lines.append(f"    topic: {q(e['topic'])}")
        lines.append(f"    date: {q(e['date'])}")
    lines.append("")
    CODE_LIBRARY_YML.write_text("\n".join(lines), encoding="utf-8")


def write_acm_problems(entries: list[dict]) -> None:
    if not entries:
        ACM_PROBLEMS_YML.write_text(
            "# 本文件由 scripts/build-archive.py 自动生成，请勿手工编辑。\n[]\n",
            encoding="utf-8",
        )
        return

    lines = ["# 本文件由 scripts/build-archive.py 自动生成，请勿手工编辑。"]
    for e in entries:
        lines.append(f"- title: {q(e['title'])}")
        lines.append(f"  slug: {q(e['slug'])}")
        lines.append(f"  source: {q(e['source'])}")
        lines.append(f"  code: {q(e['code'])}")
        lines.append(f"  difficulty: {q(e['difficulty'])}")
        lines.append(f"  topic: {q(e['topic'])}")
        lines.append(f"  date: {q(e['date'])}")
        lines.append(f"  status: {q(e['status'])}")
    lines.append("")
    ACM_PROBLEMS_YML.write_text("\n".join(lines), encoding="utf-8")


def human_size(num_bytes: int) -> str:
    if num_bytes >= 1024 * 1024:
        return f"{num_bytes / 1024 / 1024:.1f} MB"
    if num_bytes >= 1024:
        return f"{num_bytes / 1024:.0f} KB"
    return f"{num_bytes} B"


def build_zip() -> tuple[int, str]:
    """打包 solutions/、ACM 题解与外部做题仓库，返回 (字节数, sha256)。"""
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

    members: list[tuple[Path, str]] = []
    sources = [
        (SOLUTIONS_DIR, "solutions"),
        (ACM_DIR, "06_code_archive/problems"),
        (LEETCODE_REPO, "leetcode"),
    ]
    for src_dir, prefix in sources:
        if not src_dir.is_dir():
            continue
        for path in sorted(src_dir.rglob("*")):
            if not path.is_file():
                continue
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            if path.name in SKIP_FILES:
                continue
            members.append((path, f"{prefix}/{path.relative_to(src_dir).as_posix()}"))

    with zipfile.ZipFile(ARCHIVE_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for path, arcname in members:
            info = zipfile.ZipInfo(arcname, date_time=ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, path.read_bytes())

    digest = hashlib.sha256(ARCHIVE_PATH.read_bytes()).hexdigest()
    return ARCHIVE_PATH.stat().st_size, digest


def update_downloads(archive_size: str, archive_sha: str) -> bool:
    """把代码包的 size/sha256 写回 _data/downloads.yml。

    注意：条目以内联的 ``- title:`` 开头，``file:`` 是同一缩进层级下的后续键，
    所以不能拿 ``file:`` 当条目边界，要先按列表项切块再在块内定位。
    """
    if not DOWNLOADS_YML.exists():
        return False

    lines = DOWNLOADS_YML.read_text(encoding="utf-8").splitlines()
    out = list(lines)

    # 每个以 "- " 开头的行是一个新条目，末尾补一个哨兵便于切片
    starts = [i for i, line in enumerate(lines) if re.match(r"^\s*-\s+\S", line)]
    if not starts:
        return False
    starts.append(len(lines))

    file_re = re.compile(r'file:\s*"?%s"?' % re.escape(ARCHIVE_NAME))

    for idx in range(len(starts) - 1):
        block_start, block_end = starts[idx], starts[idx + 1]
        if not any(file_re.search(lines[j]) for j in range(block_start, block_end)):
            continue

        for j in range(block_start, block_end):
            if re.match(r"^\s*size:\s*", out[j]):
                out[j] = f'    size: "{archive_size}"'
            elif re.match(r"^\s*sha256:\s*", out[j]):
                out[j] = f'    sha256: "{archive_sha}"'

        DOWNLOADS_YML.write_text("\n".join(out) + "\n", encoding="utf-8")
        return True

    return False


# ---------------------------------------------------------------------------

def load_preserved_external_entries() -> list[dict]:
    """外部仓库不存在时，复用上次生成的外部条目。

    服务器（或 CI）上只有本仓库，没有同级目录的 leetcode 仓库，
    此时不能把外部记录清空，否则页面索引会莫名少掉一大块。
    """
    if not CODE_LIBRARY_YML.exists():
        return []

    out: list[dict] = []
    cur: dict[str, str] | None = None
    for line in CODE_LIBRARY_YML.read_text(encoding="utf-8").splitlines():
        m = re.match(r'^\s*-\s+(\w+):\s*"(.*)"\s*$', line)
        if m:
            if cur and str(cur.get("source", "")).startswith("leetcode"):
                out.append(cur)
            cur = {m.group(1): m.group(2)}
            continue
        m = re.match(r'^\s+(\w+):\s*"(.*)"\s*$', line)
        if m and cur is not None:
            cur[m.group(1)] = m.group(2)

    if cur and str(cur.get("source", "")).startswith("leetcode"):
        out.append(cur)
    return out


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("== 1. 扫描本地代码库 solutions/ ==")
    entries = [
        parse_solution(p)
        for p in sorted(SOLUTIONS_DIR.glob("*.py"))
        if p.name != "solution_template.py"
    ]
    print(f"   -> {len(entries)} 个文件")

    print("== 2. 扫描外部做题仓库 ==")
    print(f"   路径: {LEETCODE_REPO}")
    if LEETCODE_REPO.is_dir():
        lc_entries = [
            parse_leetcode_solution(p, LEETCODE_REPO)
            for p in sorted(LEETCODE_REPO.rglob("*.py"))
            if not any(part in SKIP_DIRS for part in p.relative_to(LEETCODE_REPO).parts)
        ]
        print(f"   -> {len(lc_entries)} 个文件")
        entries += lc_entries
    else:
        preserved = load_preserved_external_entries()
        print(f"   ! 目录不存在，保留上次索引中的 {len(preserved)} 条外部记录")
        entries += preserved

    write_code_library(entries)
    print(f"   -> _data/code_library.yml  ({len(entries)} 个文件)")

    print("== 3. 扫描 ACM 题解 06_code_archive/problems/ ==")
    problems = []
    if ACM_DIR.exists():
        for p in sorted(ACM_DIR.glob("*.md")):
            rec = parse_aca_problem(p)
            if rec:
                problems.append(rec)
    write_acm_problems(problems)
    print(f"   -> _data/acm_problems.yml  ({len(problems)} 道题)")

    print("== 4. 打包源码压缩包 ==")
    size_bytes, sha = build_zip()
    size_human = human_size(size_bytes)
    print(f"   -> downloads/{ARCHIVE_NAME}  ({size_human})")
    print(f"   sha256 = {sha}")

    update_downloads(size_human, sha)
    print("   -> 已回写 _data/downloads.yml")

    print("\n完成。下一步：")
    print("  git add -A && git commit -m \"chore: 更新代码库索引与源码包\" && git push")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
