"""MCP Server for git-weekly — expose weekly report generation as MCP tools."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .analyzer import (
    collect_diffs,
    find_author_aliases,
    get_default_since,
    get_default_until,
    get_git_email,
    get_git_user,
    parse_commits,
)
from .i18n import set_lang
from .report import TemplateConfig, build_report, render_markdown

mcp = FastMCP(
    "git-weekly",
    description="Generate weekly reports from Git commit history with optional AI summary",
)


@mcp.tool()
def generate_weekly_report(
    repo_path: str = ".",
    since: str = "",
    until: str = "",
    author: str = "",
    all_authors: bool = False,
    lang: str = "zh",
    include_ai: bool = False,
    no_diff: bool = False,
) -> str:
    """Generate a weekly report from Git commit history.

    Args:
        repo_path: Path to the Git repository (default: current directory)
        since: Start date in YYYY-MM-DD format (default: Monday of current week)
        until: End date in YYYY-MM-DD format (default: today)
        author: Filter by author name (default: auto-detect from git config)
        all_authors: Include commits from all authors
        lang: Output language: "zh" (Chinese) or "en" (English)
        include_ai: Enable AI-powered summary (requires API key configured)
        no_diff: Skip collecting diff content for AI (faster but less detailed)

    Returns:
        Weekly report in Markdown format
    """
    set_lang(lang)

    resolved = str(Path(repo_path).expanduser().resolve())
    if not Path(resolved, ".git").exists():
        return f"Error: {repo_path} is not a git repository"

    since = since or get_default_since()
    until = until or get_default_until()

    author_aliases: list[str] = []
    if author:
        author_aliases = [author]
    elif not all_authors:
        name = get_git_user(resolved)
        email = get_git_email(resolved)
        if name or email:
            author_aliases = find_author_aliases(resolved, name, email)

    try:
        if author_aliases:
            all_commits = []
            seen: set[str] = set()
            for alias in author_aliases:
                stats = parse_commits(resolved, since, until, alias)
                for c in stats.commits:
                    if c.hash not in seen:
                        seen.add(c.hash)
                        all_commits.append(c)
            stats.commits = sorted(all_commits, key=lambda c: c.date, reverse=True)
            stats.total_files_changed = len({f for c in all_commits for f in c.files})
            stats.total_insertions = sum(c.insertions for c in all_commits)
            stats.total_deletions = sum(c.deletions for c in all_commits)
        else:
            stats = parse_commits(resolved, since, until, None)
    except RuntimeError as e:
        return f"Error: {e}"

    report = build_report(stats, since, until)

    if include_ai:
        if not no_diff:
            collect_diffs(report.stats)
        try:
            from .llm import generate_summary, load_config

            llm_cfg = load_config()
            summary = generate_summary(report_list := [report], llm_cfg)
            report.ai_summary = summary
        except RuntimeError as e:
            report.ai_summary = f"(AI summary failed: {e})"

    return render_markdown([report])


@mcp.tool()
def get_commit_stats(
    repo_path: str = ".",
    since: str = "",
    until: str = "",
    author: str = "",
    all_authors: bool = False,
) -> str:
    """Get structured commit statistics from a Git repository as JSON.

    Args:
        repo_path: Path to the Git repository (default: current directory)
        since: Start date in YYYY-MM-DD format (default: Monday of current week)
        until: End date in YYYY-MM-DD format (default: today)
        author: Filter by author name (default: auto-detect from git config)
        all_authors: Include commits from all authors

    Returns:
        JSON string with commit statistics including counts, files, insertions, deletions, and commit list
    """
    resolved = str(Path(repo_path).expanduser().resolve())
    if not Path(resolved, ".git").exists():
        return json.dumps({"error": f"{repo_path} is not a git repository"})

    since = since or get_default_since()
    until = until or get_default_until()

    author_aliases: list[str] = []
    if author:
        author_aliases = [author]
    elif not all_authors:
        name = get_git_user(resolved)
        email = get_git_email(resolved)
        if name or email:
            author_aliases = find_author_aliases(resolved, name, email)

    try:
        if author_aliases:
            all_commits = []
            seen: set[str] = set()
            for alias in author_aliases:
                stats = parse_commits(resolved, since, until, alias)
                for c in stats.commits:
                    if c.hash not in seen:
                        seen.add(c.hash)
                        all_commits.append(c)
            stats.commits = sorted(all_commits, key=lambda c: c.date, reverse=True)
            stats.total_files_changed = len({f for c in all_commits for f in c.files})
            stats.total_insertions = sum(c.insertions for c in all_commits)
            stats.total_deletions = sum(c.deletions for c in all_commits)
        else:
            stats = parse_commits(resolved, since, until, None)
    except RuntimeError as e:
        return json.dumps({"error": str(e)})

    result = {
        "repo": stats.repo_name,
        "period": {"since": since, "until": until},
        "total_commits": stats.total_commits,
        "total_files_changed": stats.total_files_changed,
        "total_insertions": stats.total_insertions,
        "total_deletions": stats.total_deletions,
        "commits": [
            {
                "hash": c.hash[:8],
                "author": c.author,
                "date": c.date.isoformat(),
                "message": c.message,
                "files_changed": c.files_changed,
                "insertions": c.insertions,
                "deletions": c.deletions,
            }
            for c in stats.commits
        ],
    }
    return json.dumps(result, ensure_ascii=False, indent=2)


def main():
    """Run the MCP server via stdio transport."""
    mcp.run()


if __name__ == "__main__":
    main()
