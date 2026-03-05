"""Git log parsing and diff analysis."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional


@dataclass
class CommitInfo:
    hash: str
    author: str
    date: datetime
    message: str
    files_changed: int = 0
    insertions: int = 0
    deletions: int = 0
    files: List[str] = field(default_factory=list)


@dataclass
class RepoStats:
    repo_path: str
    repo_name: str
    commits: List[CommitInfo] = field(default_factory=list)
    total_files_changed: int = 0
    total_insertions: int = 0
    total_deletions: int = 0

    @property
    def total_commits(self) -> int:
        return len(self.commits)


CATEGORY_PATTERNS = {
    "feat": {
        "keywords": ["add", "feat", "feature", "new", "implement", "support", "create"],
        "label": "🚀 新功能",
    },
    "fix": {
        "keywords": ["fix", "bug", "patch", "resolve", "close", "repair", "correct"],
        "label": "🐛 Bug 修复",
    },
    "refactor": {
        "keywords": ["refactor", "restructure", "reorganize", "clean", "simplify", "extract",
                      "move", "rename", "optimize"],
        "label": "♻️ 重构",
    },
    "docs": {
        "keywords": ["doc", "readme", "comment", "changelog", "license"],
        "label": "📝 文档",
    },
    "test": {
        "keywords": ["test", "spec", "coverage", "mock", "assert"],
        "label": "🧪 测试",
    },
    "chore": {
        "keywords": ["chore", "ci", "cd", "build", "deploy", "config", "deps", "bump",
                      "upgrade", "update dep", "docker", "makefile", "lint"],
        "label": "🔧 工程化",
    },
    "style": {
        "keywords": ["style", "format", "indent", "whitespace", "prettier", "eslint"],
        "label": "🎨 代码风格",
    },
}


def _run_git(args: list[str], cwd: str) -> str:
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git command failed: git {' '.join(args)}\n{result.stderr.strip()}")
    return result.stdout.strip()


def get_git_user(repo_path: str) -> str:
    try:
        return _run_git(["config", "user.name"], cwd=repo_path)
    except RuntimeError:
        return ""


def get_repo_name(repo_path: str) -> str:
    path = Path(repo_path).resolve()
    try:
        remote = _run_git(["remote", "get-url", "origin"], cwd=repo_path)
        name = remote.rstrip("/").split("/")[-1]
        return name.removesuffix(".git")
    except RuntimeError:
        return path.name


def parse_commits(
    repo_path: str,
    since: str,
    until: str,
    author: Optional[str] = None,
) -> RepoStats:
    """Parse git log and return structured commit data."""
    repo_path = str(Path(repo_path).resolve())
    repo_name = get_repo_name(repo_path)

    git_args = [
        "log",
        f"--since={since}",
        f"--until={until}",
        "--format=%H|%an|%aI|%s",
        "--numstat",
    ]
    if author:
        git_args.append(f"--author={author}")

    raw = _run_git(git_args, cwd=repo_path)
    if not raw:
        return RepoStats(repo_path=repo_path, repo_name=repo_name)

    stats = RepoStats(repo_path=repo_path, repo_name=repo_name)
    commits = []
    current_commit = None

    for line in raw.split("\n"):
        if not line:
            continue

        if "|" in line and len(line.split("|")) >= 4:
            parts = line.split("|", 3)
            if len(parts[0]) == 40:  # SHA hash
                if current_commit:
                    commits.append(current_commit)
                current_commit = CommitInfo(
                    hash=parts[0],
                    author=parts[1],
                    date=datetime.fromisoformat(parts[2]),
                    message=parts[3],
                )
                continue

        if current_commit and "\t" in line:
            parts = line.split("\t")
            if len(parts) == 3:
                added, deleted, filepath = parts
                try:
                    ins = int(added) if added != "-" else 0
                    dels = int(deleted) if deleted != "-" else 0
                    current_commit.insertions += ins
                    current_commit.deletions += dels
                    current_commit.files_changed += 1
                    current_commit.files.append(filepath)
                except ValueError:
                    pass

    if current_commit:
        commits.append(current_commit)

    stats.commits = commits
    stats.total_files_changed = len({f for c in commits for f in c.files})
    stats.total_insertions = sum(c.insertions for c in commits)
    stats.total_deletions = sum(c.deletions for c in commits)

    return stats


def categorize_commit(commit: CommitInfo) -> str:
    """Categorize a commit based on its message using keyword matching."""
    msg = commit.message.lower()

    # conventional commits prefix (e.g., "feat:", "fix(scope):")
    prefix_match = re.match(r"^(\w+)[\(:]", msg)
    if prefix_match:
        prefix = prefix_match.group(1)
        for cat_key in CATEGORY_PATTERNS:
            if prefix == cat_key or prefix in CATEGORY_PATTERNS[cat_key]["keywords"]:
                return cat_key

    # file extension heuristics
    extensions = {Path(f).suffix for f in commit.files}
    if extensions & {".md", ".rst", ".txt"} and not (extensions - {".md", ".rst", ".txt"}):
        return "docs"
    if all("test" in f.lower() or "spec" in f.lower() for f in commit.files) and commit.files:
        return "test"

    # keyword matching in commit message
    for cat_key, cat_info in CATEGORY_PATTERNS.items():
        for keyword in cat_info["keywords"]:
            if keyword in msg:
                return cat_key

    return "feat"  # default to feature


def get_default_since() -> str:
    """Return the Monday of the current week as YYYY-MM-DD."""
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    return monday.strftime("%Y-%m-%d")


def get_default_until() -> str:
    """Return tomorrow as YYYY-MM-DD to include today's commits."""
    tomorrow = datetime.now() + timedelta(days=1)
    return tomorrow.strftime("%Y-%m-%d")
