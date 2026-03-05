"""Tests for git_weekly.report."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from git_weekly.analyzer import CommitInfo, RepoStats
from git_weekly.i18n import set_lang
from git_weekly.report import build_report, render_markdown


def _make_stats(commits: Optional[list[CommitInfo]] = None) -> RepoStats:
    commits = commits or []
    return RepoStats(
        repo_path="/tmp/test",
        repo_name="test-repo",
        commits=commits,
        total_files_changed=len({f for c in commits for f in c.files}),
        total_insertions=sum(c.insertions for c in commits),
        total_deletions=sum(c.deletions for c in commits),
    )


def _make_commit(message: str, **kwargs) -> CommitInfo:
    defaults = {
        "hash": "a" * 40,
        "author": "test",
        "date": datetime(2025, 3, 5),
        "message": message,
    }
    defaults.update(kwargs)
    return CommitInfo(**defaults)


class TestBuildReport:
    def test_empty_commits(self):
        report = build_report(_make_stats(), "2025-03-03", "2025-03-07")
        assert len(report.categories) == 0
        assert report.stats.total_commits == 0

    def test_categorizes_commits(self):
        commits = [
            _make_commit("feat: add login"),
            _make_commit("fix: broken link"),
        ]
        report = build_report(_make_stats(commits), "2025-03-03", "2025-03-07")
        assert "feat" in report.categories
        assert "fix" in report.categories


class TestRenderMarkdown:
    def setup_method(self):
        set_lang("zh")

    def test_markdown_has_title(self):
        report = build_report(_make_stats(), "2025-03-03", "2025-03-07")
        md = render_markdown([report])
        assert "周报" in md

    def test_markdown_en(self):
        set_lang("en")
        commits = [_make_commit("feat: new feature", insertions=10, deletions=2)]
        report = build_report(_make_stats(commits), "2025-03-03", "2025-03-07")
        md = render_markdown([report])
        assert "Weekly Report" in md
        assert "Features" in md

    def test_markdown_includes_stats(self):
        commits = [_make_commit("feat: x", insertions=50, deletions=10, files=["a.py"])]
        report = build_report(_make_stats(commits), "2025-03-03", "2025-03-07")
        md = render_markdown([report])
        assert "+50" in md
        assert "-10" in md

    def test_markdown_includes_ai_summary(self):
        report = build_report(_make_stats([_make_commit("feat: x")]), "2025-03-03", "2025-03-07")
        report.ai_summary = "This week was productive."
        md = render_markdown([report])
        assert "This week was productive." in md
