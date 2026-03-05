"""Internationalization support for git-weekly."""

from __future__ import annotations

_DEFAULT_LANG = "zh"
_current_lang = _DEFAULT_LANG

STRINGS: dict[str, dict[str, str]] = {
    # Category labels
    "cat.feat": {"zh": "\U0001f680 新功能", "en": "\U0001f680 Features"},
    "cat.fix": {"zh": "\U0001f41b Bug 修复", "en": "\U0001f41b Bug Fixes"},
    "cat.refactor": {"zh": "\u267b\ufe0f 重构", "en": "\u267b\ufe0f Refactoring"},
    "cat.docs": {"zh": "\U0001f4dd 文档", "en": "\U0001f4dd Documentation"},
    "cat.test": {"zh": "\U0001f9ea 测试", "en": "\U0001f9ea Tests"},
    "cat.chore": {"zh": "\U0001f527 工程化", "en": "\U0001f527 Chores"},
    "cat.style": {"zh": "\U0001f3a8 代码风格", "en": "\U0001f3a8 Code Style"},
    "cat.other": {"zh": "\U0001f4e6 其他", "en": "\U0001f4e6 Other"},

    # Report structure
    "report.title": {"zh": "\U0001f4cb 周报", "en": "\U0001f4cb Weekly Report"},
    "report.section.work": {"zh": "本周工作", "en": "Work Summary"},
    "report.section.stats": {"zh": "代码统计", "en": "Statistics"},
    "report.section.ai": {"zh": "\U0001f916 AI 总结", "en": "\U0001f916 AI Summary"},
    "report.no_commits": {"zh": "这段时间没有提交记录", "en": "No commits found in this period"},

    # Stats labels
    "stats.commits": {"zh": "提交次数", "en": "Commits"},
    "stats.files": {"zh": "文件变更", "en": "Files Changed"},
    "stats.insertions": {"zh": "新增行数", "en": "Insertions"},
    "stats.deletions": {"zh": "删除行数", "en": "Deletions"},
    "stats.commits_unit": {"zh": " 次", "en": ""},
    "stats.files_unit": {"zh": " 个文件", "en": " files"},

    # Markdown table header
    "md.metric": {"zh": "指标", "en": "Metric"},
    "md.value": {"zh": "数据", "en": "Value"},

    # CLI / warnings
    "warn.no_git_user": {
        "zh": "Warning: could not detect git user, showing all authors",
        "en": "Warning: could not detect git user, showing all authors",
    },
    "warn.not_git_repo": {
        "zh": "Error: {path} is not a git repository",
        "en": "Error: {path} is not a git repository",
    },
    "warn.no_repos": {
        "zh": "No repositories to analyze.",
        "en": "No repositories to analyze.",
    },
    "msg.ai_generating": {
        "zh": "正在生成 AI 总结...",
        "en": "Generating AI summary...",
    },
    "msg.ai_failed": {
        "zh": "AI 总结失败: {error}",
        "en": "AI summary failed: {error}",
    },
    "msg.saved": {
        "zh": "报告已保存至 {path}",
        "en": "Report saved to {path}",
    },

    # LLM prompts - dev style (technical, for developers)
    "llm.system_prompt.dev": {
        "zh": (
            "你是一位专业的技术周报撰写助手。根据提供的 Git commit 数据和代码 diff，"
            "写一段 3-5 句话的工作总结。\n\n"
            "要求：\n"
            "- 用中文输出\n"
            "- 像开发者写给团队看的周报，语气专业但不生硬\n"
            "- 基于 diff 内容理解实际代码变更，总结技术细节和设计决策\n"
            "- 突出本周重点工作和技术亮点，不要逐条罗列 commit\n"
            "- 如果有 bug fix，简要提及稳定性改进和修复的具体问题\n"
            "- 如果有重构，说明技术改进的意义\n"
            "- 不要编造不存在的内容，只基于提供的数据总结"
        ),
        "en": (
            "You are a professional technical weekly report writing assistant. "
            "Based on the provided Git commit data and code diffs, "
            "write a 3-5 sentence work summary.\n\n"
            "Requirements:\n"
            "- Write in English\n"
            "- Write like a developer reporting to their team — professional but not stiff\n"
            "- Analyze the diff content to understand actual code changes, "
            "summarize technical details and design decisions\n"
            "- Highlight key work and technical highlights, don't just list commits\n"
            "- If there are bug fixes, briefly mention stability improvements\n"
            "- If there is refactoring, explain the significance of the technical improvements\n"
            "- Do not fabricate content — only summarize based on the provided data"
        ),
    },

    # LLM prompts - manager style (business-oriented, for non-technical readers)
    "llm.system_prompt.manager": {
        "zh": (
            "你正在为管理层生成一份简洁易读的周工作报告。\n\n"
            "## 输出格式：\n"
            "- 输出纯文本，可以直接粘贴到邮件中\n"
            "- 不要使用 Markdown 或 HTML 格式\n"
            "- 用大写标题、短横线列表、空行分隔段落\n"
            "- 总字数控制在 300-500 字\n\n"
            "## 报告结构：\n\n"
            "**1. 概要（50-75 字）**\n"
            "   - 总结本周交付了什么业务能力或完成了什么改进\n"
            "   - 量化进展（例如"完成了计划中 4 项任务中的 3 项"）\n\n"
            "**2. 主要成果**\n"
            "   - 每项工作以业务成果开头，而不是技术实现\n"
            "   - 重点描述"用户/系统现在可以做什么"，而不是"改了什么文件"\n"
            "   - 按业务主题分组（如：接口集成、质量改进、基础设施）\n"
            "   - 技术细节最多用一句话补充说明\n\n"
            "**3. 下周计划**\n"
            "   - 列出 2-4 项具体的交付目标和预期业务成果\n\n"
            "## 术语翻译（技术 → 业务）：\n"
            "- "单元测试" → "自动化质量检查"\n"
            "- "重构" → "提升代码可维护性"\n"
            "- "接口" → "系统对接"\n"
            "- "依赖升级" → "基础组件更新"\n"
            "- "CI/CD" → "自动化构建部署"\n\n"
            "## 禁止出现：\n"
            "- 文件名或路径\n"
            "- 代码行数（增删）\n"
            "- Git commit hash\n"
            "- 类名/函数名\n"
            "- 未经解释的技术术语\n\n"
            "用中文输出。不要编造不存在的内容，只基于提供的数据总结。"
        ),
        "en": (
            "You are generating a manager-friendly weekly work report.\n\n"
            "## Output Format:\n"
            "- Output as plain text — directly pastable into an email\n"
            "- No Markdown or HTML formatting\n"
            "- Use CAPS for headers, dashes for bullets, blank lines for separation\n"
            "- Keep total length to 300-500 words\n\n"
            "## Report Structure:\n\n"
            "**1. EXECUTIVE SUMMARY (50-75 words)**\n"
            "   - What business capability was delivered or improved?\n"
            "   - Quantify progress (e.g., 'completed 3 of 4 planned tasks')\n\n"
            "**2. KEY ACCOMPLISHMENTS**\n"
            "   - Lead with business outcome, not technical implementation\n"
            "   - Focus on 'what users/systems can now do', NOT 'what files changed'\n"
            "   - Group by business themes (e.g., API Integration, Quality Improvements)\n"
            "   - Technical details limited to ONE supporting sentence maximum\n\n"
            "**3. NEXT WEEK FOCUS**\n"
            "   - List 2-4 concrete deliverables with expected business outcomes\n\n"
            "## Translation Guide (Technical -> Business):\n"
            "- 'unit tests' -> 'automated quality checks'\n"
            "- 'refactoring' -> 'improving code maintainability'\n"
            "- 'endpoint' -> 'API'\n"
            "- 'dependency upgrade' -> 'infrastructure update'\n"
            "- 'CI/CD' -> 'automated build and deployment'\n\n"
            "## What NOT to include:\n"
            "- File names or paths\n"
            "- Line counts (insertions/deletions)\n"
            "- Git commit hashes\n"
            "- Class/function names\n"
            "- Technical jargon without explanation\n\n"
            "Write in English. Do not fabricate content — only summarize based on the provided data."
        ),
    },
}

CATEGORY_LABEL_KEYS: dict[str, str] = {
    "feat": "cat.feat",
    "fix": "cat.fix",
    "refactor": "cat.refactor",
    "docs": "cat.docs",
    "test": "cat.test",
    "chore": "cat.chore",
    "style": "cat.style",
    "other": "cat.other",
}


def set_lang(lang: str) -> None:
    """Set the current language (zh or en)."""
    global _current_lang
    if lang not in ("zh", "en"):
        lang = _DEFAULT_LANG
    _current_lang = lang


def get_lang() -> str:
    return _current_lang


def t(key: str, **kwargs: str) -> str:
    """Translate a key to the current language."""
    entry = STRINGS.get(key)
    if entry is None:
        return key
    text = entry.get(_current_lang, entry.get("zh", key))
    if kwargs:
        text = text.format(**kwargs)
    return text


def get_category_label(cat_key: str) -> str:
    """Get the localized label for a commit category."""
    i18n_key = CATEGORY_LABEL_KEYS.get(cat_key, "cat.other")
    return t(i18n_key)
