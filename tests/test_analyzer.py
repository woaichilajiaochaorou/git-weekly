"""Tests for git_weekly.analyzer."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from git_weekly.analyzer import (
    CATEGORY_PATTERNS,
    CommitInfo,
    categorize_commit,
    get_default_since,
    get_default_until,
)


def _make_commit(message: str, files: Optional[list[str]] = None) -> CommitInfo:
    return CommitInfo(
        hash="a" * 40,
        author="test",
        date=datetime.now(),
        message=message,
        files=files or [],
    )


class TestCategorizeCommit:
    def test_conventional_prefix_feat(self):
        assert categorize_commit(_make_commit("feat: add login")) == "feat"

    def test_conventional_prefix_fix(self):
        assert categorize_commit(_make_commit("fix: null pointer")) == "fix"

    def test_conventional_prefix_with_scope(self):
        assert categorize_commit(_make_commit("feat(auth): add JWT")) == "feat"

    def test_keyword_matching(self):
        assert categorize_commit(_make_commit("add user registration")) == "feat"
        assert categorize_commit(_make_commit("fix broken pagination")) == "fix"
        assert categorize_commit(_make_commit("refactor database layer")) == "refactor"

    def test_docs_by_file_extension(self):
        c = _make_commit("update project info", files=["README.md"])
        assert categorize_commit(c) == "docs"

    def test_test_by_file_path(self):
        c = _make_commit("add more checks", files=["tests/test_foo.py", "tests/test_bar.py"])
        assert categorize_commit(c) == "test"

    def test_fallback_to_other(self):
        assert categorize_commit(_make_commit("initial commit")) == "other"


class TestDateDefaults:
    def test_default_since_is_monday(self):
        since = get_default_since()
        dt = datetime.strptime(since, "%Y-%m-%d")
        assert dt.weekday() == 0  # Monday

    def test_default_until_is_tomorrow(self):
        until = get_default_until()
        dt = datetime.strptime(until, "%Y-%m-%d")
        today = datetime.now().date()
        assert dt.date() > today


class TestCategoryPatterns:
    def test_all_categories_have_keywords(self):
        for key, info in CATEGORY_PATTERNS.items():
            assert "keywords" in info, f"Category '{key}' missing keywords"

    def test_category_keys_are_known(self):
        expected = {"feat", "fix", "refactor", "docs", "test", "chore", "style", "other"}
        assert set(CATEGORY_PATTERNS.keys()) == expected
