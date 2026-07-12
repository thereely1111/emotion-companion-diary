#!/usr/bin/env python3
"""
日记文件名合规性校验工具
根据 emotion-companion-diary skill v1.7.1 的四规则命名规范校验文件名。

策略：不追求严格字符串匹配（标题本质是摘要而非引用），而是用"字符重叠度"
判断标题词与用户原文是否有语义关联。已知错误词库中的词直接报 FAIL。

用法: python validate_filename.py <用户原文> <生成的标题> [--verbose]
"""

import sys
import re

# 已知错误词库 —— 这些词出现在标题中一定是 AI 脑补/曲解
KNOWN_ERRORS = {
    "缺课": "用户说'天天要上课'，从未说'缺课'（意思完全相反）",
    "失眠": "用户说'睡不够'，未说'失眠'（临床标签化）",
    "抑郁": "用户说'提不起劲'，未说'抑郁'（临床标签化）",
    "危机": "用户说'吵架'，未说'危机'（严重度升级）",
    "PUA": "用户说'被要求重做'，未说'PUA'（主观定性标签）",
    "崩溃": "用户未说'崩溃'（严重度升级）",
    "霸凌": "用户未说'霸凌'（主观定性标签）",
    "绝境": "用户未说'绝境'（严重度升级）",
    "完蛋": "用户未说'完蛋'（严重度升级）",
}

SEP_RE = re.compile(r'[的与和了着在地得之而对以就也但或还又被把从让给向到为因所其只可由，,、\-\s]+')


def title_core(title: str) -> str:
    c = re.sub(r'^\d{4}-\d{2}-\d{2}-\d{6}-', '', title)
    return re.sub(r'\.md$', '', c)


def user_chars(text: str) -> set:
    """用户原文中的所有中文字符"""
    return set(re.findall(r'[\u4e00-\u9fff]', text))


def validate(user_text: str, generated_title: str) -> dict:
    core = title_core(generated_title)
    uchars = user_chars(user_text)
    violations = []
    suggestions = []

    # 按分隔符切片
    parts = [p for p in SEP_RE.split(core) if len(p) >= 2]

    for part in parts:
        part_chars = set(part)
        if part_chars.issubset(uchars):
            continue  # 片段的全部字符都在用户原文中 → 通过

        # 检查是否命中已知错误词库
        for i in range(len(part) - 1):
            g = part[i:i+2]
            if g in KNOWN_ERRORS:
                violations.append(f"规则一违反: '{g}' — {KNOWN_ERRORS[g]}")
                suggestions.append(f"将'{g}'替换为用户原文中的实际用词")
                break
        else:
            # 没命中错误词库，计算字符重叠率
            overlap = len(part_chars & uchars)
            ratio = overlap / len(part_chars)
            if ratio < 0.5:
                # 重叠率低于 50%，可能是 AI 自己造的词
                violations.append(f"规则一警告: '{part}' 与用户原文字符重叠率仅 {int(ratio*100)}%，可能是 AI 推断词")
                suggestions.append(f"检查'{part}'是否准确反映用户原意，考虑替换为用户原话中的词")

    suggestions = list(dict.fromkeys(suggestions))
    cn_len = len(re.sub(r'[^\u4e00-\u9fff]', '', core))

    if cn_len > 15:
        violations.append(f"规则三提醒: 简述纯中文 {cn_len} 字，超上限 15")
    elif cn_len < 4:
        violations.append(f"规则三提醒: 简述纯中文 {cn_len} 字，可能过简")

    if '-' not in core and cn_len > 6:
        suggestions.append("规则二提醒: 考虑用'情境-情绪'格式")

    # 只要有命中已知错误词库的违规 → FAIL
    hard_fail = any("规则一违反" in v for v in violations)

    return {
        "pass": not hard_fail,
        "violations": violations,
        "suggestions": suggestions,
        "title_core": core,
    }


def main():
    if len(sys.argv) < 3:
        print("用法: python validate_filename.py <用户原文> <生成的标题> [--verbose]")
        sys.exit(1)

    r = validate(sys.argv[1], sys.argv[2])
    status = "FAIL" if not r["pass"] else "PASS" if not r["violations"] else "WARN"
    print(f"[{status}] {r['title_core']}")

    if r["violations"]:
        for v in r["violations"]:
            print(f"  X {v}")
    if r["suggestions"]:
        for s in r["suggestions"]:
            print(f"  > {s}")

    if "--verbose" in sys.argv:
        print(f"\n[verbose] 用户原文: {sys.argv[1]}")
        print(f"[verbose] 生成标题: {sys.argv[2]}")

    sys.exit(0 if r["pass"] else 1)


if __name__ == "__main__":
    main()
