"""Command-line interface for git-weekly."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .analyzer import get_default_since, get_default_until, get_git_user, parse_commits
from .report import build_report, render_markdown, render_terminal


def main():
    """Generate weekly report from Git commit history."""
    parser = argparse.ArgumentParser(
        description="Generate weekly report from Git commit history.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  git-weekly                                    # 当前仓库本周周报
  git-weekly --since 2025-02-24 --until 2025-02-28
  git-weekly --repo /path/to/project
  git-weekly --repo ./proj-a --repo ./proj-b    # 多仓库聚合
  git-weekly -o report.md                       # 输出 Markdown 文件
  git-weekly --all-authors                      # 包含所有人的提交
  git-weekly --ai                               # AI 智能总结
  git-weekly --ai --base-url https://api.deepseek.com/v1  # 用 DeepSeek
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

    args = parser.parse_args()

    repos = args.repo or ["."]
    since = args.since or get_default_since()
    until = args.until or get_default_until()
    author = args.author

    if not author and not args.all_authors:
        first_repo = str(Path(repos[0]).resolve())
        author = get_git_user(first_repo)
        if not author:
            print("Warning: could not detect git user, showing all authors", file=sys.stderr)
            author = None

    reports = []
    for repo_path in repos:
        resolved = str(Path(repo_path).resolve())
        if not Path(resolved, ".git").exists():
            print(f"Error: {repo_path} is not a git repository", file=sys.stderr)
            sys.exit(1)

        try:
            stats = parse_commits(resolved, since, until, author if not args.all_authors else None)
            report = build_report(stats, since, until)
            reports.append(report)
        except RuntimeError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    if not reports:
        print("No repositories to analyze.", file=sys.stderr)
        sys.exit(0)

    if args.ai:
        try:
            from .llm import generate_summary, load_config

            llm_cfg = load_config(
                api_key=args.api_key,
                base_url=args.base_url,
                model=args.model,
            )
            print("Generating AI summary...", file=sys.stderr)
            summary = generate_summary(reports, llm_cfg)
            for report in reports:
                report.ai_summary = summary
        except RuntimeError as e:
            print(f"AI summary failed: {e}", file=sys.stderr)

    if args.output:
        md = render_markdown(reports)
        Path(args.output).write_text(md, encoding="utf-8")
        print(f"Report saved to {args.output}")
    else:
        render_terminal(reports)


if __name__ == "__main__":
    main()
