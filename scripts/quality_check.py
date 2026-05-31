#!/usr/bin/env python3
"""
自动检查生成的SKILL.md是否通过Phase 4质量标准。
对照通过标准表格逐项检查，输出通过/不通过和具体原因。

用法:
    python3 quality_check.py <SKILL.md路径>

示例:
    python3 quality_check.py .claude/skills/elon-musk-perspective/SKILL.md
"""

import sys
import re
from pathlib import Path


REQUIRED_RESEARCH_FILES = [
    "01-writings.md",
    "02-conversations.md",
    "03-expression-dna.md",
    "04-external-views.md",
    "05-decisions.md",
    "06-timeline.md",
]


def check_mental_models(content: str) -> tuple[bool, str]:
    """检查心智模型数量（3-7个）"""
    # 匹配 ### 模型N: 或 ### N. 等模式
    models = re.findall(r'^###\s+(?:模型|Model|心智模型)\s*\d', content, re.MULTILINE)
    if not models:
        # fallback: 数「### 」开头的行在心智模型section中
        in_section = False
        count = 0
        for line in content.split('\n'):
            if re.match(r'^##\s+.*心智模型|Mental Model', line, re.IGNORECASE):
                in_section = True
                continue
            if in_section and re.match(r'^##\s+', line) and '心智模型' not in line:
                break
            if in_section and re.match(r'^###\s+', line):
                count += 1
        if count > 0:
            passed = 3 <= count <= 7
            return passed, f"{count}个心智模型 {'✅' if passed else '❌ (应为3-7个)'}"

    count = len(models)
    if count == 0:
        return False, "未检测到心智模型section"
    passed = 3 <= count <= 7
    return passed, f"{count}个心智模型 {'✅' if passed else '❌ (应为3-7个)'}"


def check_limitations(content: str) -> tuple[bool, str]:
    """检查每个模型是否有局限性"""
    has_limitation = bool(re.search(r'局限|失效|不适用|盲区|limitation|blind spot', content, re.IGNORECASE))
    return has_limitation, "有局限性标注 ✅" if has_limitation else "❌ 未找到局限性描述"


def check_expression_dna(content: str) -> tuple[bool, str]:
    """检查表达DNA辨识度"""
    dna_section = bool(re.search(r'表达DNA|Expression DNA|表达风格', content, re.IGNORECASE))
    if not dna_section:
        return False, "❌ 未找到表达DNA section"

    # 检查是否有具体的风格描述（句式、词汇等）
    style_markers = len(re.findall(r'句式|词汇|语气|幽默|节奏|确定性|引用|口头禅', content))
    passed = style_markers >= 3
    return passed, f"表达DNA特征: {style_markers}项 {'✅' if passed else '❌ (应≥3项)'}"


def check_honest_boundary(content: str) -> tuple[bool, str]:
    """检查诚实边界（至少3条）"""
    # 找诚实边界section
    boundary_match = re.search(r'(?:##\s+.*诚实边界|## Honest Boundary)(.*?)(?=\n##\s|\Z)', content, re.DOTALL | re.IGNORECASE)
    if not boundary_match:
        return False, "❌ 未找到诚实边界section"

    boundary_text = boundary_match.group(1)
    # 计算列表项
    items = re.findall(r'^[-*]\s+', boundary_text, re.MULTILINE)
    count = len(items)
    passed = count >= 3
    return passed, f"诚实边界: {count}条 {'✅' if passed else '❌ (应≥3条)'}"


def check_tensions(content: str) -> tuple[bool, str]:
    """检查内在张力（至少2对）"""
    tension_markers = len(re.findall(r'张力|矛盾|tension|paradox|一方面.*另一方面|既.*又', content, re.IGNORECASE))
    passed = tension_markers >= 2
    return passed, f"内在张力: {tension_markers}处 {'✅' if passed else '❌ (应≥2处)'}"


def check_primary_sources(content: str) -> tuple[bool, str]:
    """检查一手来源占比"""
    # 找调研来源section
    source_section = re.search(r'(?:##\s+.*来源|## Source|## Reference)(.*?)(?=\n##\s|\Z)', content, re.DOTALL | re.IGNORECASE)
    if not source_section:
        return True, "未找到来源section（跳过检查）"

    source_text = source_section.group(1)
    primary = len(re.findall(r'一手|primary|本人著作|原始', source_text, re.IGNORECASE))
    secondary = len(re.findall(r'二手|secondary|转述|评论', source_text, re.IGNORECASE))
    total = primary + secondary
    if total == 0:
        return True, "未标记来源类型（跳过检查）"

    ratio = primary / total
    passed = ratio > 0.5
    return passed, f"一手来源占比: {primary}/{total} ({ratio:.0%}) {'✅' if passed else '❌ (应>50%)'}"


def check_research_package(skill_path: Path) -> tuple[bool, str]:
    """检查skill包是否包含Phase 1要求的六个research文件。"""
    skill_dir = skill_path.parent
    research_dir = skill_dir / "references" / "research"
    if not research_dir.exists():
        return False, f"❌ 缺少research目录: {research_dir}"

    missing = [name for name in REQUIRED_RESEARCH_FILES if not (research_dir / name).exists()]
    if missing:
        return False, f"❌ 缺少research文件: {', '.join(missing)}"

    too_short = []
    for name in REQUIRED_RESEARCH_FILES:
        text = (research_dir / name).read_text(encoding="utf-8", errors="replace").strip()
        if len(text) < 500:
            too_short.append(f"{name}({len(text)}字)")

    if too_short:
        return False, f"❌ research文件过短: {', '.join(too_short)}"

    return True, "6个research文件齐全 ✅"


def check_conversation_video_coverage(skill_path: Path) -> tuple[bool, str]:
    """检查Agent 2是否包含长对话/视频/transcript覆盖。"""
    conversations = skill_path.parent / "references" / "research" / "02-conversations.md"
    if not conversations.exists():
        return False, "❌ 缺少02-conversations.md"

    text = conversations.read_text(encoding="utf-8", errors="replace")
    lowered = text.lower()
    markers = [
        "youtube",
        "youtu.be",
        "bilibili",
        "b站",
        "podcast",
        "播客",
        "transcript",
        "字幕",
        "视频",
        "演讲",
        "访谈",
        "lecture",
        "interview",
        "q&a",
        "问答",
    ]
    hits = [marker for marker in markers if marker.lower() in lowered]
    url_count = len(set(re.findall(r"https?://[^\s\)>\]]+", text)))
    has_coverage_section = "公开视频覆盖检查" in text or "video coverage" in lowered

    passed = len(hits) >= 3 and url_count >= 3 and has_coverage_section
    detail = f"标记{len(hits)}项、URL {url_count}个、覆盖检查{'有' if has_coverage_section else '无'}"
    return passed, f"{detail} {'✅' if passed else '❌ (应补充长对话/视频/transcript)'}"


def main():
    if len(sys.argv) < 2:
        print("用法: python3 quality_check.py <SKILL.md路径>")
        sys.exit(1)

    skill_path = Path(sys.argv[1])
    if not skill_path.exists():
        print(f"❌ 文件不存在: {skill_path}")
        sys.exit(1)

    content = skill_path.read_text(encoding='utf-8')

    checks = [
        ("心智模型数量", lambda _: check_mental_models(content)),
        ("模型局限性", lambda _: check_limitations(content)),
        ("表达DNA辨识度", lambda _: check_expression_dna(content)),
        ("诚实边界", lambda _: check_honest_boundary(content)),
        ("内在张力", lambda _: check_tensions(content)),
        ("一手来源占比", lambda _: check_primary_sources(content)),
        ("调研包完整性", lambda _: check_research_package(skill_path)),
        ("对话视频覆盖", lambda _: check_conversation_video_coverage(skill_path)),
    ]

    print(f"质量检查: {skill_path.name}")
    print("=" * 50)

    passed_count = 0
    total = len(checks)

    for name, check_fn in checks:
        passed, detail = check_fn(content)
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {name:<12} {status}  {detail}")
        if passed:
            passed_count += 1

    print("=" * 50)
    print(f"结果: {passed_count}/{total} 通过")

    if passed_count == total:
        print("🎉 全部通过，可以交付")
    elif passed_count >= total - 1:
        print("⚠️ 基本通过，建议修复不通过项后交付")
    else:
        print("❌ 多项不通过，建议回到Phase 2迭代")

    sys.exit(0 if passed_count == total else 1)


if __name__ == '__main__':
    main()
