"""LLM-powered weekly report summarization (OpenAI-compatible API)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .report import CategorizedReport

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError:
        tomllib = None  # type: ignore[assignment]

CONFIG_DIR = Path.home() / ".config" / "git-weekly"
CONFIG_FILE = CONFIG_DIR / "config.toml"

DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = """\
你是一位专业的技术周报撰写助手。根据提供的 Git commit 数据和代码 diff，写一段 3-5 句话的工作总结。

要求：
- 用中文输出
- 像开发者写给团队看的周报，语气专业但不生硬
- 基于 diff 内容理解实际代码变更，总结技术细节和设计决策
- 突出本周重点工作和技术亮点，不要逐条罗列 commit
- 如果有 bug fix，简要提及稳定性改进和修复的具体问题
- 如果有重构，说明技术改进的意义
- 不要编造不存在的内容，只基于提供的数据总结
"""


@dataclass
class LLMConfig:
    api_key: str
    base_url: str = DEFAULT_BASE_URL
    model: str = DEFAULT_MODEL


def _load_config_file() -> dict[str, str]:
    """Load config from ~/.config/git-weekly/config.toml if it exists."""
    if tomllib is None or not CONFIG_FILE.exists():
        return {}
    try:
        with open(CONFIG_FILE, "rb") as f:
            data = tomllib.load(f)
        return data.get("ai", {})
    except Exception:
        return {}


def load_config(
    *,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
) -> LLMConfig:
    """Build LLM config from CLI args > env vars > config file."""
    file_cfg = _load_config_file()

    resolved_key = (
        api_key
        or os.environ.get("GIT_WEEKLY_API_KEY")
        or file_cfg.get("api_key", "")
    )
    if not resolved_key:
        raise RuntimeError(
            "未找到 API Key。请通过以下任一方式配置：\n"
            "  1. --api-key 参数\n"
            "  2. 环境变量 GIT_WEEKLY_API_KEY\n"
            f"  3. 配置文件 {CONFIG_FILE}\n\n"
            "配置文件示例：\n"
            "  [ai]\n"
            '  api_key = "sk-xxx"\n'
            '  base_url = "https://api.openai.com/v1"\n'
            '  model = "gpt-4o-mini"'
        )

    resolved_url = (
        base_url
        or os.environ.get("GIT_WEEKLY_BASE_URL")
        or file_cfg.get("base_url", "")
        or DEFAULT_BASE_URL
    )
    resolved_model = (
        model
        or os.environ.get("GIT_WEEKLY_MODEL")
        or file_cfg.get("model", "")
        or DEFAULT_MODEL
    )

    return LLMConfig(api_key=resolved_key, base_url=resolved_url, model=resolved_model)


def _build_prompt(reports: list[CategorizedReport]) -> str:
    """Serialize reports into structured text for the LLM."""
    from .analyzer import CATEGORY_PATTERNS

    parts: list[str] = []
    for report in reports:
        parts.append(f"仓库: {report.stats.repo_name}")
        parts.append(f"时间范围: {report.since} ~ {report.until}")
        parts.append(f"提交次数: {report.stats.total_commits}")
        parts.append(f"文件变更: {report.stats.total_files_changed} 个文件")
        parts.append(f"新增: +{report.stats.total_insertions} 行, 删除: -{report.stats.total_deletions} 行")
        parts.append("")

        for cat_key, commits in report.categories.items():
            label = CATEGORY_PATTERNS.get(cat_key, {}).get("label", cat_key)
            parts.append(f"【{label}】")
            for c in commits:
                file_hint = ""
                if c.files:
                    top_files = c.files[:3]
                    file_hint = f" ({', '.join(top_files)})"
                parts.append(f"  - {c.message}{file_hint}")
            parts.append("")

        diffs_with_content = [
            c for c in report.stats.commits if c.diff
        ]
        if diffs_with_content:
            parts.append("--- 代码变更详情 ---")
            parts.append("")
            for c in diffs_with_content:
                parts.append(f"[{c.hash[:8]}] {c.message}")
                parts.append(c.diff)
                parts.append("")

    return "\n".join(parts)


def generate_summary(reports: list[CategorizedReport], config: LLMConfig) -> str:
    """Call OpenAI-compatible API to generate a narrative summary."""
    try:
        from openai import OpenAI
    except ImportError:
        raise RuntimeError(
            "AI 功能需要安装 openai 库。请运行:\n"
            '  pip install "git-weekly[ai]"'
        )

    client = OpenAI(api_key=config.api_key, base_url=config.base_url)

    user_content = _build_prompt(reports)

    response = client.chat.completions.create(
        model=config.model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.3,
        max_tokens=1024,
    )

    return response.choices[0].message.content or ""
