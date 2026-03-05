"""Command-line interface for git-weekly."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .analyzer import (
    collect_diffs,
    find_author_aliases,
    get_default_since,
    get_default_until,
    get_git_email,
    get_git_user,
    parse_commits,
)
from .i18n import set_lang, t
from .report import TemplateConfig, build_report, render_markdown, render_terminal

PROVIDERS = [
    {"name": "OpenAI", "base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini"},
    {"name": "DeepSeek", "base_url": "https://api.deepseek.com/v1", "model": "deepseek-chat"},
    {"name": "通义千问 (Qwen)", "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "model": "qwen-plus"},
    {"name": "Ollama (local)", "base_url": "http://localhost:11434/v1", "model": "llama3"},
    {"name": "Custom", "base_url": "", "model": ""},
]


def _init_config() -> None:
    """Interactive configuration wizard for git-weekly."""
    from .llm import CONFIG_DIR, CONFIG_FILE

    BOLD = "\033[1m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    DIM = "\033[2m"
    RESET = "\033[0m"

    print(f"\n{BOLD}{CYAN}git-weekly init{RESET}")
    print(f"{DIM}交互式生成配置文件 {CONFIG_FILE}{RESET}\n")

    # --- Provider selection ---
    print(f"{BOLD}选择 LLM 服务商:{RESET}\n")
    for i, p in enumerate(PROVIDERS, 1):
        hint = f"  {DIM}{p['base_url']}{RESET}" if p["base_url"] else ""
        print(f"  {BOLD}{i}{RESET}) {p['name']}{hint}")
    print()

    while True:
        choice = input(f"请输入编号 [1-{len(PROVIDERS)}] (默认 1): ").strip()
        if not choice:
            choice = "1"
        if choice.isdigit() and 1 <= int(choice) <= len(PROVIDERS):
            provider = PROVIDERS[int(choice) - 1]
            break
        print(f"  无效选项，请输入 1-{len(PROVIDERS)}")

    # --- Base URL ---
    if provider["base_url"]:
        custom_url = input(f"Base URL [{provider['base_url']}]: ").strip()
        base_url = custom_url or provider["base_url"]
    else:
        base_url = input("Base URL: ").strip()
        while not base_url:
            print("  Base URL 不能为空")
            base_url = input("Base URL: ").strip()

    # --- API Key ---
    is_local = "localhost" in base_url or "127.0.0.1" in base_url
    if is_local:
        api_key = input(f"API Key {DIM}(本地服务可留空){RESET}: ").strip() or "ollama"
    else:
        api_key = input("API Key: ").strip()
        while not api_key:
            print("  API Key 不能为空")
            api_key = input("API Key: ").strip()

    # --- Model ---
    default_model = provider["model"] or "gpt-4o-mini"
    model = input(f"Model [{default_model}]: ").strip() or default_model

    # --- Language ---
    lang = ""
    while lang not in ("zh", "en"):
        lang = input("默认语言 zh/en [zh]: ").strip() or "zh"

    # --- Report style ---
    style = ""
    while style not in ("dev", "manager"):
        style = input("AI 报告风格 dev(技术)/manager(商业) [dev]: ").strip() or "dev"

    # --- Template options ---
    print(f"\n{BOLD}报告模板配置 (可选, 直接回车跳过):{RESET}\n")

    custom_title = input(f"自定义标题 {DIM}(默认: 周报){RESET}: ").strip()

    show_hash_input = input(f"显示 commit hash? y/N [{DIM}N{RESET}]: ").strip().lower()
    show_hash = show_hash_input in ("y", "yes")

    show_date_input = input(f"显示提交日期? y/N [{DIM}N{RESET}]: ").strip().lower()
    show_date = show_date_input in ("y", "yes")

    show_author_input = input(f"显示作者名? y/N [{DIM}N{RESET}]: ").strip().lower()
    show_author = show_author_input in ("y", "yes")

    # --- Write config ---
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    lines = [
        "[ai]",
        f'api_key = "{api_key}"',
        f'base_url = "{base_url}"',
        f'model = "{model}"',
        f'style = "{style}"',
        "",
        "[general]",
        f'lang = "{lang}"',
        "",
        "[template]",
    ]
    if custom_title:
        lines.append(f'title = "{custom_title}"')
    lines.append(f"show_hash = {'true' if show_hash else 'false'}")
    lines.append(f"show_date = {'true' if show_date else 'false'}")
    lines.append(f"show_author = {'true' if show_author else 'false'}")
    lines.append('sections = ["work", "stats", "ai"]')
    lines.append("")
    config_text = "\n".join(lines)

    if CONFIG_FILE.exists():
        print(f"\n{BOLD}配置文件已存在:{RESET} {CONFIG_FILE}")
        overwrite = input("是否覆盖? [y/N]: ").strip().lower()
        if overwrite not in ("y", "yes"):
            print("已取消。")
            return

    CONFIG_FILE.write_text(config_text, encoding="utf-8")
    print(f"\n{GREEN}✔ 配置已保存至 {CONFIG_FILE}{RESET}")
    print(f"\n{DIM}现在可以直接运行:{RESET}")
    print(f"  {BOLD}git-weekly --ai{RESET}")
    print()


def _load_template_config() -> TemplateConfig:
    """Load [template] section from config and build TemplateConfig."""
    from .llm import load_template_config
    raw = load_template_config()
    if not raw:
        return TemplateConfig()
    default_sections = ["work", "stats", "ai"]
    sections_raw = raw.get("sections")
    if isinstance(sections_raw, (list, tuple)):
        sections = list(sections_raw)
    else:
        sections = default_sections
    return TemplateConfig(
        title=raw.get("title", ""),
        show_hash=raw.get("show_hash", False),
        show_date=raw.get("show_date", False),
        show_author=raw.get("show_author", False),
        sections=sections,
    )


def main():
    """Generate weekly report from Git commit history."""
    if len(sys.argv) >= 2 and sys.argv[1] == "init":
        _init_config()
        return

    parser = argparse.ArgumentParser(
        description="Generate weekly report from Git commit history.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  git-weekly init                               # 交互式配置 AI 参数
  git-weekly                                    # 当前仓库本周周报
  git-weekly --since 2025-02-24 --until 2025-02-28
  git-weekly --repo /path/to/project
  git-weekly --repo ./proj-a --repo ./proj-b    # 多仓库聚合
  git-weekly -o report.md                       # 输出 Markdown 文件
  git-weekly --all-authors                      # 包含所有人的提交
  git-weekly --ai                               # AI 智能总结
  git-weekly --ai --base-url https://api.deepseek.com/v1  # 用 DeepSeek
  git-weekly --ai --style manager               # 面向管理层的商业化周报
  git-weekly --lang en                          # English output
""",
    )
    parser.add_argument(
        "--repo", "-r", action="append", default=None,
        help="Git repository path (can specify multiple times, default: current directory)",
    )
    parser.add_argument(
        "--since", "-s", default=None,
        help="Start date YYYY-MM-DD (default: Monday of current week)",
    )
    parser.add_argument(
        "--until", "-u", default=None,
        help="End date YYYY-MM-DD (default: today)",
    )
    parser.add_argument(
        "--author", "-a", default=None,
        help="Filter by author name (default: git config user.name)",
    )
    parser.add_argument(
        "--output", "-o", default=None,
        help="Output to Markdown file instead of terminal",
    )
    parser.add_argument(
        "--all-authors", action="store_true", default=False,
        help="Include commits from all authors",
    )
    parser.add_argument(
        "--ai", action="store_true", default=False,
        help="Enable AI-powered summary (requires: pip install git-weekly[ai])",
    )
    parser.add_argument(
        "--api-key", default=None,
        help="LLM API key (or set GIT_WEEKLY_API_KEY env var)",
    )
    parser.add_argument(
        "--base-url", default=None,
        help="LLM API base URL (default: OpenAI; set for DeepSeek/Ollama/etc.)",
    )
    parser.add_argument(
        "--model", default=None,
        help="LLM model name (default: gpt-4o-mini)",
    )
    parser.add_argument(
        "--no-diff", action="store_true", default=False,
        help="Skip collecting diff content (faster, but AI summary less detailed)",
    )
    parser.add_argument(
        "--lang", default="zh", choices=["zh", "en"],
        help="Output language: zh (Chinese, default) or en (English)",
    )
    parser.add_argument(
        "--style", default="dev", choices=["dev", "manager"],
        help="AI summary style: dev (technical, default) or manager (business-oriented)",
    )

    args = parser.parse_args()

    lang = args.lang
    if lang == "zh" and "--lang" not in sys.argv:
        from .llm import load_general_config
        lang = load_general_config().get("lang", "zh")
    set_lang(lang)

    repos = args.repo or ["."]
    since = args.since or get_default_since()
    until = args.until or get_default_until()

    author_aliases: list[str] = []
    if args.author:
        author_aliases = [args.author]
    elif not args.all_authors:
        first_repo = str(Path(repos[0]).resolve())
        name = get_git_user(first_repo)
        email = get_git_email(first_repo)
        if name or email:
            author_aliases = find_author_aliases(first_repo, name, email)
        if not author_aliases:
            print(t("warn.no_git_user"), file=sys.stderr)

    reports = []
    for repo_path in repos:
        resolved = str(Path(repo_path).resolve())
        if not Path(resolved, ".git").exists():
            print(t("warn.not_git_repo", path=repo_path), file=sys.stderr)
            sys.exit(1)

        try:
            if author_aliases:
                all_commits = []
                seen_hashes: set[str] = set()
                for alias in author_aliases:
                    stats = parse_commits(resolved, since, until, alias)
                    for c in stats.commits:
                        if c.hash not in seen_hashes:
                            seen_hashes.add(c.hash)
                            all_commits.append(c)
                stats.commits = sorted(all_commits, key=lambda c: c.date, reverse=True)
                stats.total_files_changed = len({f for c in all_commits for f in c.files})
                stats.total_insertions = sum(c.insertions for c in all_commits)
                stats.total_deletions = sum(c.deletions for c in all_commits)
            else:
                stats = parse_commits(resolved, since, until, None)
            report = build_report(stats, since, until)
            reports.append(report)
        except RuntimeError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    if not reports:
        print(t("warn.no_repos"), file=sys.stderr)
        sys.exit(0)

    if args.ai:
        if not args.no_diff:
            for report in reports:
                collect_diffs(report.stats)
        try:
            from .llm import _load_config_file, generate_summary, load_config

            llm_cfg = load_config(
                api_key=args.api_key,
                base_url=args.base_url,
                model=args.model,
            )
            style = args.style
            if style == "dev" and "--style" not in sys.argv:
                style = _load_config_file().get("style", "dev")
            print(t("msg.ai_generating"), file=sys.stderr)
            summary = generate_summary(reports, llm_cfg, style=style)
            for report in reports:
                report.ai_summary = summary
        except RuntimeError as e:
            print(t("msg.ai_failed", error=str(e)), file=sys.stderr)

    tpl = _load_template_config()

    if args.output:
        md = render_markdown(reports, tpl=tpl)
        Path(args.output).write_text(md, encoding="utf-8")
        print(t("msg.saved", path=args.output))
    else:
        render_terminal(reports, tpl=tpl)


if __name__ == "__main__":
    main()
