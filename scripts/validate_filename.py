#!/usr/bin/env python3
"""
日记文件名合规性校验工具
根据 emotion-companion-diary skill v1.7.1 的四规则命名规范校验文件名。
用法: python validate_filename.py <用户原文> <生成的标题> [--verbose]
"""

import sys
import re

KNOWN_ERRORS = {
    "缺课": "用户未说'缺课'", "失眠": "用户未说'失眠'",
    "抑郁": "用户未说'抑郁'", "危机": "用户未说'危机'",
    "PUA": "用户未说'PUA'", "崩溃": "用户未说'崩溃'",
}

SEP_RE = re.compile(r'[的与和了着在地得之而对以就也但或还又被把从让给向到为因所其只可由，,、\-\s]+')


def title_core(title: str) -> str:
    c = re.sub(r'^\d{4}-\d{2}-\d{2}-\d{6}-', '', title)
    return re.sub(r'\.md$', '', c)


def user_cn(text: str) -> str:
    return re.sub(r'[^\u4e00-\u9fff]', '', text)


def validate(user_text: str, generated_title: str) -> dict:
    core = title_core(generated_title)
    ucn = user_cn(user_text)
    violations = []
    suggestions = []

    # 按分隔符切片，检查每片是否在用户原文中
    parts = [p for p in SEP_RE.split(core) if len(p) >= 2]
    bad_grams = []

    for part in parts:
        if part in ucn:
            continue
        # 片不匹配，滑动 2-gram 找出具体问题词
        for i in range(len(part) - 1):
            g = part[i:i+2]
            if g not in ucn and g not in bad_grams:
                bad_grams.append(g)

    # 去噪：过滤跨边界伪词
    clean_grams = []
    for g in bad_grams:
        if g in KNOWN_ERRORS:
            clean_grams.append(g)
        else:
            all_chars_found = all(c in ucn for c in g)
            if not all_chars_found:
                clean_grams.append(g)

    for g in clean_grams:
        if g in KNOWN_ERRORS:
            violations.append(f"规则一违反: '{g}' — {KNOWN_ERRORS[g]}")
        else:
            violations.append(f"规则一违反: '{g}' 在用户原文中找不到对应")
        suggestions.append(f"将'{g}'替换为用户原文中的实际用词")

    suggestions = list(dict.fromkeys(suggestions))
    cn_len = len(user_cn(core))

    if cn_len > 15:
        violations.append(f"规则三提醒: 简述纯中文 {cn_len} 字，超上限 15")
    elif cn_len < 4:
        violations.append(f"规则三提醒: 简述纯中文 {cn_len} 字，可能过简")

    if '-' not in core and cn_len > 6:
        suggestions.append("规则二提醒: 考虑用'情境-情绪'格式")

    return {
        "pass": len(violations) == 0,
        "violations": violations,
        "suggestions": suggestions,
        "title_core": core,
    }


def main():
    if len(sys.argv) < 3:
        print("用法: python validate_filename.py <用户原文> <生成的标题> [--verbose]")
        sys.exit(1)

    r = validate(sys.argv[1], sys.argv[2])
    status = "PASS" if r["pass"] else "FAIL"
    print(f"[{status}] {r['title_core']}")

    if r["violations"]:
        for v in r["violations"]:
            print(f"  X {v}")
    if r["suggestions"]:
        for s in r["suggestions"]:
            print(f"  > {s}")

    if "--verbose" in sys.argv:
        print(f"\n[verbose] 用户: {sys.argv[1]}")
        print(f"[verbose] 标题: {sys.argv[2]}")

    sys.exit(0 if r["pass"] else 1)


if __name__ == "__main__":
    main()
