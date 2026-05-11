"""Enhanced heuristic draft generator for ``governspec draft``.

Turns a free-text prompt (Chinese or English) into a best-effort
GovernSpec YAML payload — without calling any LLM.
"""

from __future__ import annotations

import re
from typing import Any

from governspec_core.common.utils import dedupe_preserve_order

# ---------------------------------------------------------------------------
# CJK detection
# ---------------------------------------------------------------------------

_CJK_RE = re.compile(r"[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]")

# ---------------------------------------------------------------------------
# Profile templates (fallback when nothing better is inferred)
# ---------------------------------------------------------------------------

_PROFILES: dict[str, dict[str, Any]] = {
    "brief": {
        "title": "Generate customer brief",
        "goal": "Generate a customer meeting brief.",
        "sections": ["Summary", "Customer Background", "Risks", "Recommended Questions"],
    },
    "review": {
        "title": "Review code changes",
        "goal": "Review the codebase and report issues without editing code.",
        "sections": ["Overall Assessment", "Must Fix", "Suggestions", "Test Advice"],
    },
    "analysis": {
        "title": "Generate market analysis",
        "goal": "Produce a market analysis report.",
        "sections": ["Summary", "Market Size", "Competition", "Risks", "Recommendations"],
    },
    "deploy": {
        "title": "Deploy application",
        "goal": "Deploy the application to the target environment.",
        "sections": ["Summary", "Steps", "Verification", "Rollback Plan"],
    },
    "test": {
        "title": "Generate test plan",
        "goal": "Produce a test plan covering major scenarios.",
        "sections": ["Summary", "Test Cases", "Edge Cases", "Coverage"],
    },
    "translate": {
        "title": "Translate content",
        "goal": "Translate the provided content accurately.",
        "sections": ["Translation", "Notes"],
    },
    "summarize": {
        "title": "Summarize content",
        "goal": "Produce a concise summary of the source material.",
        "sections": ["Summary", "Key Points", "Conclusions"],
    },
}

_PROFILE_KEYWORDS: list[tuple[list[str], str]] = [
    (["review", "审查", "审核", "代码", "code review", "code audit"], "review"),
    (["brief", "简报", "会议"], "brief"),
    (["deploy", "部署", "发布", "上线"], "deploy"),
    (["test plan", "测试", "test cases", "qa"], "test"),
    (["translat", "翻译", "locali"], "translate"),
    (["summari", "总结", "摘要", "概括", "归纳"], "summarize"),
    (["analysis", "分析", "report", "报告"], "analysis"),
]

# ---------------------------------------------------------------------------
# Permission patterns
# ---------------------------------------------------------------------------

_PERMISSION_DENY_PATTERNS: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r"不要?联网|离线|offline|no\s+internet|no\s+web|without\s+web", re.I),
     "web", ""),
    (re.compile(r"不要?联网|离线|no\s+network|without\s+network|offline", re.I),
     "network", ""),
    (re.compile(
        r"不要?修改|不要?写入|不要?编辑|read[- ]?only|do\s+not\s+(?:modify|edit|write)", re.I,
    ), "filesystem", "write"),
    (re.compile(r"不要?删除|do\s+not\s+delete|never\s+delete", re.I),
     "tools", "delete_file"),
    (re.compile(r"不要?发邮件|不要?发送邮件|do\s+not\s+send\s+email", re.I),
     "tools", "send_email"),
    (re.compile(r"不要?购买|不要?付款|do\s+not\s+(?:purchase|buy)", re.I),
     "tools", "purchase"),
]

_PERMISSION_ALLOW_PATTERNS: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r"联网|需要?网络|web|internet|online|fetch\s+url|browse", re.I),
     "web", ""),
    (re.compile(r"联网|需要?网络|network|online", re.I),
     "network", ""),
    (re.compile(r"写文件|写入|创建文件|生成文件|write\s+files?|create\s+files?", re.I),
     "filesystem", "write"),
    (re.compile(r"创建文件|生成文件|create\s+files?", re.I),
     "tools", "create_file"),
    (re.compile(r"发邮件|发送邮件|send\s+(?:an?\s+)?emails?", re.I),
     "tools", "send_email"),
    (re.compile(r"日历|calendar", re.I),
     "tools", "read_calendar"),
    (re.compile(r"读邮件|read\s+(?:emails?|gmail)", re.I),
     "tools", "read_gmail"),
    (re.compile(r"购买|付款|purchase|buy|checkout", re.I),
     "tools", "purchase"),
    (re.compile(r"删除|delete|remove\s+files?", re.I),
     "tools", "delete_file"),
]

# ---------------------------------------------------------------------------
# Human gate patterns
# ---------------------------------------------------------------------------

_GATE_PATTERNS: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r"隐私|privacy|private\s+data|personal\s+data|PII|敏感", re.I),
     "Task involves privacy-sensitive information",
     "ask_confirmation"),
    (re.compile(r"问我|先确认|先问|confirm|ask\s+me|approval|审批|审核", re.I),
     "High-risk action is required",
     "ask_confirmation"),
    (re.compile(r"联网|web|internet|network|external\s+api", re.I),
     "Task requires external network access",
     "ask_confirmation"),
    (re.compile(r"删除|delet(?:e|ing)|remov(?:e|ing)\s+files?|drop|truncate", re.I),
     "Destructive operation is requested",
     "ask_confirmation"),
    (re.compile(r"购买|付款|purchas|buy|payment|billing", re.I),
     "Financial transaction is involved",
     "ask_confirmation"),
    (re.compile(r"发邮件|send\s+(?:an?\s+)?emails?|邮件发送", re.I),
     "Outbound communication is involved",
     "ask_confirmation"),
]

_NEGATION_PREFIX_RE = re.compile(
    r"(?:不要?|别|禁止|do\s+not|don['\u2019]t|never|must\s+not|should\s+not)\s*",
    re.I,
)

# ---------------------------------------------------------------------------
# Constraint patterns
# ---------------------------------------------------------------------------

_CONSTRAINT_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"隐私|privacy|private\s+data|personal\s+data|PII|敏感", re.I),
     "Do not expose private or personal data."),
    (re.compile(r"不要?修改|不要?编辑|read[- ]?only|do\s+not\s+(?:modify|edit|change)", re.I),
     "Do not modify existing files or code."),
    (re.compile(r"不要?删除|do\s+not\s+delete|never\s+delete", re.I),
     "Do not delete any files."),
    (re.compile(r"机密|confidential|classified|保密|secret", re.I),
     "Do not disclose confidential information."),
]

# ---------------------------------------------------------------------------
# Priority patterns
# ---------------------------------------------------------------------------

_PRIORITY_HIGH_RE = re.compile(
    r"紧急|urgent|critical|高优|asap|尽快|立即|immediately|highest\s+priority", re.I
)
_PRIORITY_LOW_RE = re.compile(
    r"低优|low\s+priority|when\s+(?:you\s+have|possible)|不着?急|有空", re.I
)

# ---------------------------------------------------------------------------
# Output format detection
# ---------------------------------------------------------------------------

_JSON_FORMAT_RE = re.compile(
    r"json|结构化输出|structured\s+output|json\s+format|json\s+格式|json\s+schema", re.I
)

# ---------------------------------------------------------------------------
# Section extraction from prompt
# ---------------------------------------------------------------------------

_SECTION_SPLIT_RE = re.compile(r"[，,、和及与：:]|\band\b|\bwith\b")

_SECTION_TRIGGER_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r"(?:需要?包[含括]|包[含括]|包括有?|including|include|contain|with)\s*[:：]?\s*(.+)", re.I,
    ),
    re.compile(r"(?:sections?|章节|部分)\s*[:：]\s*(.+)", re.I),
    re.compile(r"(?:涵盖|覆盖|cover(?:ing)?)\s*[:：]?\s*(.+)", re.I),
]

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def heuristic_draft_payload(prompt: str) -> dict[str, Any]:
    """Generate a draft GovernSpec payload from a free-text prompt."""
    profile = _detect_profile(prompt)
    language = _detect_language(prompt)
    priority = _detect_priority(prompt)
    output_format = _detect_format(prompt)
    permissions = _infer_permissions(prompt)
    constraints = _infer_constraints(prompt)
    human_gates = _infer_human_gates(prompt, permissions)
    sections = _extract_sections(prompt) or profile["sections"]
    goal = _extract_goal(prompt) or profile["goal"]
    title = _extract_title(prompt) or profile["title"]

    if output_format == "json":
        output_spec: dict[str, Any] = {
            "format": "json",
            "schema": {
                "type": "object",
                "properties": {},
            },
        }
        tests: list[dict[str, Any]] = [
            {"name": "Must match JSON schema", "assert": [{"type": "json_schema"}]},
        ]
    else:
        output_spec = {
            "format": "markdown",
            "language": language,
            "max_words": 800,
            "sections": sections,
        }
        tests = [
            {"name": "Must include all sections", "assert": [{"type": "required_sections"}]},
        ]

    return {
        "version": "0.1",
        "kind": "GovernSpec",
        "metadata": {
            "name": "draft_intent",
            "title": title,
            "description": prompt.strip(),
            "owner": "draft",
        },
        "task": {
            "goal": goal,
            "audience": ["Primary stakeholder"],
            "priority": priority,
        },
        "context": {
            "domain": "General",
            "facts": [],
            "assumptions": [],
            "glossary": {},
        },
        "inputs": [],
        "permissions": permissions,
        "constraints": dedupe_preserve_order(constraints),
        "evidence": {
            "require_sources": False,
            "mark_uncertainty": True,
            "distinguish": ["fact", "inference"],
        },
        "output": output_spec,
        "quality": {
            "tone": ["clear"],
            "must_include": [],
            "must_avoid": [],
        },
        "human_gates": dedupe_preserve_order(human_gates),
        "tests": tests,
    }


# ---------------------------------------------------------------------------
# Detection helpers
# ---------------------------------------------------------------------------


def _detect_profile(prompt: str) -> dict[str, Any]:
    lowered = prompt.lower()
    for keywords, profile_key in _PROFILE_KEYWORDS:
        for kw in keywords:
            if kw in lowered or kw in prompt:
                return _PROFILES[profile_key]
    return _PROFILES["analysis"]


def _detect_language(prompt: str) -> str:
    cjk_count = len(_CJK_RE.findall(prompt))
    total_chars = len(prompt.strip())
    if total_chars == 0:
        return "en"
    if cjk_count / total_chars > 0.15:
        return "zh-CN"
    return "en"


def _detect_priority(prompt: str) -> str:
    if _PRIORITY_HIGH_RE.search(prompt):
        return "high"
    if _PRIORITY_LOW_RE.search(prompt):
        return "low"
    return "medium"


def _detect_format(prompt: str) -> str:
    if _JSON_FORMAT_RE.search(prompt):
        return "json"
    return "markdown"


def _infer_permissions(prompt: str) -> dict[str, Any]:
    permissions: dict[str, Any] = {
        "web": False,
        "filesystem": {"read": True, "write": False},
        "network": False,
        "tools": {
            "send_email": False,
            "read_calendar": False,
            "read_gmail": False,
            "create_file": False,
            "delete_file": False,
            "purchase": False,
        },
    }

    for pattern, group, subkey in _PERMISSION_ALLOW_PATTERNS:
        if pattern.search(prompt):
            if subkey:
                permissions[group][subkey] = True
            else:
                permissions[group] = True

    for pattern, group, subkey in _PERMISSION_DENY_PATTERNS:
        if pattern.search(prompt):
            if subkey:
                permissions[group][subkey] = False
            else:
                permissions[group] = False

    return permissions


def _infer_constraints(prompt: str) -> list[str]:
    constraints = ["Do not fabricate facts."]
    for pattern, constraint_text in _CONSTRAINT_PATTERNS:
        if pattern.search(prompt):
            constraints.append(constraint_text)
    return constraints


def _is_negated_match(prompt: str, match: re.Match[str]) -> bool:
    """Return True if the match is preceded by a negation prefix."""
    start = match.start()
    preceding = prompt[max(0, start - 20):start]
    return bool(_NEGATION_PREFIX_RE.search(preceding)) or bool(
        _NEGATION_PREFIX_RE.match(prompt[max(0, start - 5):])
    )


def _infer_human_gates(
    prompt: str, permissions: dict[str, Any]
) -> list[dict[str, str]]:
    gates: list[dict[str, str]] = []
    seen_whens: set[str] = set()

    for pattern, when_text, action in _GATE_PATTERNS:
        match = pattern.search(prompt)
        if match and not _is_negated_match(prompt, match) and when_text not in seen_whens:
            seen_whens.add(when_text)
            gates.append({"when": when_text, "action": action})

    tool_perms = permissions.get("tools", {})
    high_risk_tools = ["send_email", "delete_file", "purchase"]
    for tool in high_risk_tools:
        if tool_perms.get(tool):
            when = f"Tool '{tool}' is enabled and about to be used"
            if when not in seen_whens:
                seen_whens.add(when)
                gates.append({"when": when, "action": "ask_confirmation"})

    return gates


_SECTION_BOUNDARY_RE = re.compile(r"[。.!！?？\n，]")

_INSTRUCTION_PREFIX_RE = re.compile(
    r"^(?:不要?|别|必要|需要|请|do\s+not|don't|never|must|should|please)\b", re.I
)


def _extract_sections(prompt: str) -> list[str]:
    for pattern in _SECTION_TRIGGER_PATTERNS:
        match = pattern.search(prompt)
        if match:
            raw = match.group(1).strip()
            boundary = _SECTION_BOUNDARY_RE.search(raw)
            if boundary:
                raw = raw[:boundary.start()]
            raw = raw.strip().rstrip("。.!！?？，,")
            parts = _SECTION_SPLIT_RE.split(raw)
            sections: list[str] = []
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                if _INSTRUCTION_PREFIX_RE.match(part):
                    break
                sections.append(part)
            if len(sections) >= 2:
                return sections
    return []


def _extract_goal(prompt: str) -> str:
    stripped = prompt.strip()
    if not stripped:
        return ""

    first_sentence_re = re.compile(r"^(.+?)[。.!！?\n]")
    match = first_sentence_re.match(stripped)
    candidate = match.group(1).strip() if match else stripped

    if len(candidate) > 120:
        candidate = candidate[:120].rsplit(" ", 1)[0]

    return candidate


def _extract_title(prompt: str) -> str:
    goal = _extract_goal(prompt)
    if len(goal) > 60:
        return goal[:60].rsplit(" ", 1)[0]
    return goal
