"""Report generation and formatting."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

from .analyzer import CATEGORY_ORDER, CommitInfo, RepoStats, categorize_commit
from .i18n import get_category_label, t


@dataclass
class CategorizedReport:
    """Commits grouped by category with summary info."""
    categories: dict[str, list[CommitInfo]]
    stats: RepoStats
    since: str
    until: str
    ai_summary: str | None = None


def build_report(stats: RepoStats, since: str, until: str) -> CategorizedReport:
    """Categorize commits and build a structured report."""
    categories: dict[str, list[CommitInfo]] = defaultdict(list)
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


def render_terminal(reports: list[CategorizedReport]) -> None:
    """Render reports to terminal with ANSI colors."""
    BOLD = "\033[1m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    RED = "\033[31m"
    DIM = "\033[2m"
    RESET = "\033[0m"

    for report in reports:
        date_range = _format_date_range(report.since, report.until)
        title = f" {t('report.title')} ({date_range})"
        if len(reports) > 1:
            title += f" — {report.stats.repo_name}"

        width = 50
        print()
        print(f"{CYAN}{'─' * width}{RESET}")
        print(f"{BOLD}{CYAN}{title}{RESET}")
        print(f"{CYAN}{'─' * width}{RESET}")

        if not report.stats.commits:
            print(f"\n  {DIM}{t('report.no_commits')}{RESET}\n")
            continue

        print(f"\n{BOLD}{t('report.section.work')}{RESET}\n")

        for cat_key in CATEGORY_ORDER:
            if cat_key not in report.categories:
                continue
            commits = report.categories[cat_key]
            label = get_category_label(cat_key)
            print(f"  {BOLD}{label}{RESET}")
            for commit in commits:
                msg = commit.message
                if len(msg) > 72:
                    msg = msg[:72] + "..."
                print(f"    • {msg}")
            print()

        print(f"{BOLD}{t('report.section.stats')}{RESET}\n")
        print(f"  {t('stats.commits')}  {BOLD}{report.stats.total_commits}{RESET}{t('stats.commits_unit')}")
        print(f"  {t('stats.files')}  {BOLD}{report.stats.total_files_changed}{RESET}{t('stats.files_unit')}")
        print(f"  {t('stats.insertions')}  {GREEN}+{report.stats.total_insertions}{RESET}")
        print(f"  {t('stats.deletions')}  {RED}-{report.stats.total_deletions}{RESET}")
        print()

        if report.ai_summary:
            print(f"{BOLD}{t('report.section.ai')}{RESET}\n")
            for line in report.ai_summary.strip().splitlines():
                print(f"  {line}")
            print()


def render_markdown(reports: list[CategorizedReport]) -> str:
    """Render reports as Markdown string."""
    lines: list[str] = []

    for report in reports:
        date_range = _format_date_range(report.since, report.until)
        heading = f"{t('report.title')} ({date_range})"
        if len(reports) > 1:
            heading += f" — {report.stats.repo_name}"

        lines.append(f"# {heading}")
        lines.append("")

        if not report.stats.commits:
            lines.append(f"_{t('report.no_commits')}_")
            lines.append("")
            continue

        lines.append(f"## {t('report.section.work')}")
        lines.append("")

        for cat_key in CATEGORY_ORDER:
            if cat_key not in report.categories:
                continue
            commits = report.categories[cat_key]
            label = get_category_label(cat_key)
            lines.append(f"### {label}")
            lines.append("")
            for commit in commits:
                lines.append(f"- {commit.message}")
            lines.append("")

        lines.append(f"## {t('report.section.stats')}")
        lines.append("")
        lines.append(f"| {t('md.metric')} | {t('md.value')} |")
        lines.append("|------|------|")
        lines.append(f"| {t('stats.commits')} | {report.stats.total_commits}{t('stats.commits_unit')} |")
        lines.append(f"| {t('stats.files')} | {report.stats.total_files_changed}{t('stats.files_unit')} |")
        lines.append(f"| {t('stats.insertions')} | +{report.stats.total_insertions} |")
        lines.append(f"| {t('stats.deletions')} | -{report.stats.total_deletions} |")
        lines.append("")

        if report.ai_summary:
            lines.append(f"## {t('report.section.ai')}")
            lines.append("")
            lines.append(report.ai_summary.strip())
            lines.append("")

    return "\n".join(lines)
