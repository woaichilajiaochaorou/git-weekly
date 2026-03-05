"""Report generation and formatting."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

from .analyzer import CATEGORY_PATTERNS, CommitInfo, RepoStats, categorize_commit


@dataclass
class CategorizedReport:
    """Commits grouped by category with summary info."""
    categories: dict
    stats: RepoStats
    since: str
    until: str


def build_report(stats: RepoStats, since: str, until: str) -> CategorizedReport:
    """Categorize commits and build a structured report."""
    categories = defaultdict(list)
    for commit in stats.commits:
        cat = categorize_commit(commit)
        categories[cat].append(commit)
    return CategorizedReport(
        categories=dict(categories),
        stats=stats,
        since=since,
        until=until,
    )


def _format_date_range(since: str, until: str) -> str:
    try:
        s = datetime.strptime(since, "%Y-%m-%d")
        u = datetime.strptime(until, "%Y-%m-%d")
        return f"{s.month:02d}/{s.day:02d} - {u.month:02d}/{u.day:02d}"
    except ValueError:
        return f"{since} ~ {until}"


def render_terminal(reports: list):
    """Render reports to terminal with ANSI colors."""
    BOLD = "\033[1m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    RED = "\033[31m"
    DIM = "\033[2m"
    YELLOW = "\033[33m"
    RESET = "\033[0m"

    for report in reports:
        date_range = _format_date_range(report.since, report.until)
        title = f" 📋 周报 ({date_range})"
        if len(reports) > 1:
            title += f" — {report.stats.repo_name}"

        width = 50
        print()
        print(f"{CYAN}{'─' * width}{RESET}")
        print(f"{BOLD}{CYAN}{title}{RESET}")
        print(f"{CYAN}{'─' * width}{RESET}")

        if not report.stats.commits:
            print(f"\n  {DIM}这段时间没有提交记录{RESET}\n")
            continue

        print(f"\n{BOLD}本周工作{RESET}\n")

        category_order = ["feat", "fix", "refactor", "docs", "test", "chore", "style"]
        for cat_key in category_order:
            if cat_key not in report.categories:
                continue
            commits = report.categories[cat_key]
            label = CATEGORY_PATTERNS.get(cat_key, {}).get("label", cat_key)
            print(f"  {BOLD}{label}{RESET}")
            for commit in commits:
                msg = commit.message
                if len(msg) > 72:
                    msg = msg[:72] + "..."
                print(f"    • {msg}")
            print()

        print(f"{BOLD}代码统计{RESET}\n")
        print(f"  提交次数  {BOLD}{report.stats.total_commits}{RESET} 次")
        print(f"  文件变更  {BOLD}{report.stats.total_files_changed}{RESET} 个文件")
        print(f"  新增行数  {GREEN}+{report.stats.total_insertions}{RESET}")
        print(f"  删除行数  {RED}-{report.stats.total_deletions}{RESET}")
        print()


def render_markdown(reports: list) -> str:
    """Render reports as Markdown string."""
    lines = []

    for report in reports:
        date_range = _format_date_range(report.since, report.until)
        heading = f"周报 ({date_range})"
        if len(reports) > 1:
            heading += f" — {report.stats.repo_name}"

        lines.append(f"# {heading}")
        lines.append("")

        if not report.stats.commits:
            lines.append("_这段时间没有提交记录_")
            lines.append("")
            continue

        lines.append("## 本周工作")
        lines.append("")

        category_order = ["feat", "fix", "refactor", "docs", "test", "chore", "style"]
        for cat_key in category_order:
            if cat_key not in report.categories:
                continue
            commits = report.categories[cat_key]
            label = CATEGORY_PATTERNS.get(cat_key, {}).get("label", cat_key)
            lines.append(f"### {label}")
            lines.append("")
            for commit in commits:
                lines.append(f"- {commit.message}")
            lines.append("")

        lines.append("## 代码统计")
        lines.append("")
        lines.append("| 指标 | 数据 |")
        lines.append("|------|------|")
        lines.append(f"| 提交次数 | {report.stats.total_commits} 次 |")
        lines.append(f"| 文件变更 | {report.stats.total_files_changed} 个文件 |")
        lines.append(f"| 新增行数 | +{report.stats.total_insertions} |")
        lines.append(f"| 删除行数 | -{report.stats.total_deletions} |")
        lines.append("")

    return "\n".join(lines)
