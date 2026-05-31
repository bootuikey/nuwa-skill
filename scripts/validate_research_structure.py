#!/usr/bin/env python3
"""
Validate that a generated perspective skill has the required research package.

Usage:
    python3 validate_research_structure.py <skill-dir>

This is the Phase 1.5 hard gate. A generated skill must not move to synthesis
or delivery unless the six research files exist and Agent 2 includes long-form
conversation/video coverage.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


REQUIRED_RESEARCH_FILES = [
    "01-writings.md",
    "02-conversations.md",
    "03-expression-dna.md",
    "04-external-views.md",
    "05-decisions.md",
    "06-timeline.md",
]

VIDEO_MARKERS = [
    "youtube",
    "youtu.be",
    "bilibili",
    "b站",
    "video",
    "视频",
    "podcast",
    "播客",
    "transcript",
    "字幕",
    "演讲",
    "访谈",
    "lecture",
    "interview",
    "q&a",
    "问答",
]


def count_urls(text: str) -> int:
    return len(set(re.findall(r"https?://[^\s)>\]]+", text)))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def validate(skill_dir: Path) -> tuple[bool, list[str]]:
    messages: list[str] = []

    if not skill_dir.exists() or not skill_dir.is_dir():
        return False, [f"skill目录不存在: {skill_dir}"]

    research_dir = skill_dir / "references" / "research"
    if not research_dir.exists():
        return False, [f"缺少research目录: {research_dir}"]

    passed = True

    for filename in REQUIRED_RESEARCH_FILES:
        path = research_dir / filename
        if not path.exists():
            passed = False
            messages.append(f"FAIL 缺少 {filename}")
            continue

        text = read_text(path).strip()
        if len(text) < 500:
            passed = False
            messages.append(f"FAIL {filename} 内容过短 ({len(text)} 字符)，不像完整调研文件")
        else:
            messages.append(f"PASS {filename} 存在，{len(text)} 字符，URL {count_urls(text)} 个")

        if "来源" not in text and "source" not in text.lower():
            passed = False
            messages.append(f"FAIL {filename} 缺少来源清单/Source标记")

    conversations = research_dir / "02-conversations.md"
    if conversations.exists():
        text = read_text(conversations).lower()
        marker_hits = [marker for marker in VIDEO_MARKERS if marker.lower() in text]
        url_count = count_urls(text)

        if len(marker_hits) < 3:
            passed = False
            messages.append(
                "FAIL 02-conversations.md 缺少长访谈/视频/transcript覆盖标记"
            )
        else:
            messages.append(
                f"PASS 02-conversations.md 视频/对话标记: {', '.join(marker_hits[:8])}"
            )

        if url_count < 3:
            passed = False
            messages.append(
                f"FAIL 02-conversations.md URL数量不足 ({url_count})，应至少列出3个长对话/视频来源"
            )

        if "公开视频覆盖检查" not in read_text(conversations) and "video coverage" not in text:
            passed = False
            messages.append("FAIL 02-conversations.md 缺少「公开视频覆盖检查」小节")

    transcripts_dir = skill_dir / "references" / "sources" / "transcripts"
    transcript_files = []
    if transcripts_dir.exists():
        transcript_files = [
            p for p in transcripts_dir.iterdir() if p.is_file() and p.suffix.lower() in {".txt", ".md", ".srt", ".vtt"}
        ]
    if transcript_files:
        messages.append(f"PASS transcripts目录包含 {len(transcript_files)} 个文件")
    else:
        messages.append("WARN transcripts目录没有字幕/文字稿文件；若公开视频有字幕，应补充")

    return passed, messages


def main() -> None:
    if len(sys.argv) != 2:
        print("用法: python3 validate_research_structure.py <skill-dir>")
        sys.exit(1)

    skill_dir = Path(sys.argv[1])
    passed, messages = validate(skill_dir)

    print(f"调研结构检查: {skill_dir}")
    print("=" * 60)
    for message in messages:
        print(message)
    print("=" * 60)
    print("结果:", "PASS" if passed else "FAIL")

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
