#!/usr/bin/env python3
"""
下载清单同步

扫描 downloads/ 目录，把每个文件的大小和 SHA-256 写进 _data/downloads.yml：

  - 已有条目  -> 更新 size / sha256（保留你写的 title / desc）
  - 没有条目  -> 自动追加一条，title 默认取文件名，desc 留占位提示

这样上传新 PDF / 压缩包时，不用手动算哈希。

用法：

    python scripts/sync-downloads.py

上传新 PDF 的完整流程：

    1. 把文件复制到 downloads/
    2. python scripts/sync-downloads.py
    3. 打开 _data/downloads.yml，补一下 title 和 desc
    4. git add -A && git commit -m "feat: 新资料" && git push
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOWNLOADS_DIR = ROOT / "downloads"
DOWNLOADS_YML = ROOT / "_data" / "downloads.yml"

# 这些扩展名会被纳入清单
WANTED_SUFFIXES = {".pdf", ".zip", ".tar", ".gz", ".tgz", ".7z", ".epub"}


def human_size(num_bytes: int) -> str:
    if num_bytes >= 1024 * 1024:
        return f"{num_bytes / 1024 / 1024:.1f} MB"
    if num_bytes >= 1024:
        return f"{num_bytes / 1024:.0f} KB"
    return f"{num_bytes} B"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def q(value) -> str:
    return json.dumps("" if value is None else str(value), ensure_ascii=False)


def scan_items(text: str) -> list[dict]:
    """按列表项切块，解析出每个条目的 file 字段和所在行范围。"""
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines) if re.match(r"^\s*-\s+\S", line)]
    if not starts:
        return []
    starts.append(len(lines))

    items = []
    for idx in range(len(starts) - 1):
        s, e = starts[idx], starts[idx + 1]
        entry = {"start": s, "end": e, "file": None}
        for j in range(s, e):
            m = re.match(r'^\s*file:\s*"?([^"]+?)"?\s*$', lines[j])
            if m:
                entry["file"] = m.group(1)
                break
        items.append(entry)
    return items


def main() -> int:
    if not DOWNLOADS_DIR.is_dir():
        print(f"错误：找不到目录 {DOWNLOADS_DIR}", file=sys.stderr)
        return 1

    files = sorted(
        p for p in DOWNLOADS_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in WANTED_SUFFIXES
    )
    if not files:
        print(f"{DOWNLOADS_DIR} 下没有可纳入清单的文件。")
        return 0

    print(f"扫描 {DOWNLOADS_DIR.name}/，共 {len(files)} 个文件")

    if DOWNLOADS_YML.exists():
        text = DOWNLOADS_YML.read_text(encoding="utf-8")
    else:
        text = "items:\n"

    lines = text.splitlines()
    entries = scan_items(text)
    known = {e["file"] for e in entries if e["file"]}

    # 1) 更新已有条目的 size / sha256
    updated = 0
    for item in entries:
        name = item["file"]
        if not name:
            continue
        path = DOWNLOADS_DIR / name
        if not path.is_file():
            continue

        size = human_size(path.stat().st_size)
        sha = sha256_of(path)

        touched = False
        for j in range(item["start"], item["end"]):
            if re.match(r"^\s*size:\s*", lines[j]):
                lines[j] = f'    size: "{size}"'
                touched = True
            elif re.match(r"^\s*sha256:\s*", lines[j]):
                lines[j] = f'    sha256: "{sha}"'
                touched = True

        if touched:
            print(f"  ~ {name}  ({size})")
            updated += 1

    # 2) 追加新文件
    added: list[str] = []
    for path in files:
        if path.name in known:
            continue
        size = human_size(path.stat().st_size)
        sha = sha256_of(path)
        lines.append("")
        lines.append(f'  - title: {q(path.stem)}')
        lines.append(f'    file: {q(path.name)}')
        lines.append('    desc: "（待补充说明）"')
        lines.append(f'    size: "{size}"')
        lines.append(f'    sha256: "{sha}"')
        print(f"  + {path.name}  ({size})  <- 已追加，请补充 title / desc")
        added.append(path.name)

    DOWNLOADS_YML.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print()
    print(f"完成：更新 {updated} 条，新增 {len(added)} 条 -> {DOWNLOADS_YML.relative_to(ROOT)}")
    if added:
        print("记得打开 _data/downloads.yml 补写 title 和 desc。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
