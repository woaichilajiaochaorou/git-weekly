"""Git log parsing and diff analysis."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

COMMIT_SEPARATOR = "\x00"
COMMIT_FORMAT = "%H%x00%an%x00%aI%x00%s"

CATEGORY_PATTERNS: dict[str, dict[str, object]] = {
    "feat": {
        "keywords": ["add", "feat", "feature", "new", "implement", "support", "create"],
    },
    "fix": {
        "keywords": ["fix", "bug", "patch", "resolve", "close", "repair", "correct"],
    },
    "refactor": {
        "keywords": ["refactor", "restructure", "reorganize", "clean", "simplify", "extract",
                      "move", "rename", "optimize"],
    },
    "docs": {
        "keywords": ["doc", "readme", "comment", "changelog", "license"],
    },
    "test": {
        "keywords": ["test", "spec", "coverage", "mock", "assert"],
    },
    "chore": {
        "keywords": ["chore", "ci", "cd", "build", "deploy", "config", "deps", "bump",
                      "upgrade", "update dep", "docker", "makefile", "lint"],
    },
    "style": {
        "keywords": ["style", "format", "indent", "whitespace", "prettier", "eslint"],
    },
    "other": {
        "keywords": [],
    },
}

CATEGORY_ORDER: list[str] = ["feat", "fix", "refactor", "docs", "test", "chore", "style", "other"]


MAX_DIFF_PER_COMMIT = 2000
MAX_TOTAL_DIFF = 12000


@dataclass
class CommitInfo:
    hash: str
    author: str
    date: datetime
    message: str
    files_changed: int = 0
    insertions: int = 0
    deletions: int = 0
    files: list[str] = field(default_factory=list)
    diff: str = ""


@dataclass
class RepoStats:
    repo_path: str
    repo_name: str
    commits: list[CommitInfo] = field(default_factory=list)
    total_files_changed: int = 0
    total_insertions: int = 0
    total_deletions: int = 0

    @property
    def total_commits(self) -> int:
        return len(self.commits)


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


def get_git_email(repo_path: str) -> str:
    try:
        return _run_git(["config", "user.email"], cwd=repo_path)
    except RuntimeError:
        return ""


def _get_system_username() -> str:
    """Get the OS-level username for fuzzy author matching."""
    import getpass
    return getpass.getuser()


def find_author_aliases(repo_path: str, name: str, email: str) -> list[str]:
    """Find all author names in the repo that likely belong to the current user.

    Matches by: exact name, exact email, or system username appearing in
    the commit author name or email (handles name changes across machines).
    """
    sys_user = _get_system_username().lower()

    try:
        raw = _run_git(["log", "--format=%an|%ae", "--all"], cwd=repo_path)
    except RuntimeError:
        return [name] if name else []

    aliases: set[str] = set()
    if name:
        aliases.add(name)

    for line in raw.split("\n"):
        if "|" not in line:
            continue
        commit_name, commit_email = line.rsplit("|", 1)
        cn_lower = commit_name.lower()
        ce_lower = commit_email.lower()

        if (name and cn_lower == name.lower()) or \
           (email and ce_lower == email.lower()) or \
           (sys_user and (sys_user in cn_lower or sys_user in ce_lower)):
            aliases.add(commit_name)

    return list(aliases)


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
    author: str | None = None,
) -> RepoStats:
    """Parse git log and return structured commit data."""
    repo_path = str(Path(repo_path).resolve())
    repo_name = get_repo_name(repo_path)

    git_args = [
        "log",
        f"--since={since}",
        f"--until={until}",
        f"--format={COMMIT_FORMAT}",
        "--numstat",
    ]
    if author:
        git_args.append(f"--author={author}")

    raw = _run_git(git_args, cwd=repo_path)
    if not raw:
        return RepoStats(repo_path=repo_path, repo_name=repo_name)

    stats = RepoStats(repo_path=repo_path, repo_name=repo_name)
    commits: list[CommitInfo] = []
    current_commit: CommitInfo | None = None

    for line in raw.split("\n"):
        if not line:
            continue

        if COMMIT_SEPARATOR in line:
            parts = line.split(COMMIT_SEPARATOR, 3)
            if len(parts) == 4 and len(parts[0]) == 40:
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


def collect_diffs(stats: RepoStats) -> None:
    """Fetch diff content for each commit, truncated to stay within token budget."""
    budget = MAX_TOTAL_DIFF
    for commit in stats.commits:
        if budget <= 0:
            break
        try:
            raw = _run_git(
                ["show", commit.hash, "--format=", "--patch", "--no-color",
                 "--diff-filter=AMCR", "--no-ext-diff"],
                cwd=stats.repo_path,
            )
        except RuntimeError:
            continue
        lines: list[str] = []
        size = 0
        per_commit_budget = min(MAX_DIFF_PER_COMMIT, budget)
        for line in raw.split("\n"):
            if line.startswith("diff --git"):
                lines.append(line)
            elif line.startswith("@@"):
                lines.append(line)
            elif line.startswith(("+", "-")) and not line.startswith(("+++", "---")):
                lines.append(line)
            else:
                continue
            size += len(line) + 1
            if size >= per_commit_budget:
                lines.append("... (truncated)")
                break
        diff_text = "\n".join(lines)
        commit.diff = diff_text
        budget -= len(diff_text)


def categorize_commit(commit: CommitInfo) -> str:
    """Categorize a commit based on its message using keyword matching."""
    msg = commit.message.lower()

    prefix_match = re.match(r"^(\w+)[\(:]", msg)
    if prefix_match:
        prefix = prefix_match.group(1)
        for cat_key in CATEGORY_PATTERNS:
            if cat_key == "other":
                continue
            if prefix == cat_key or prefix in CATEGORY_PATTERNS[cat_key]["keywords"]:
                return cat_key

    extensions = {Path(f).suffix for f in commit.files}
    if extensions & {".md", ".rst", ".txt"} and not (extensions - {".md", ".rst", ".txt"}):
        return "docs"
    if commit.files and all("test" in f.lower() or "spec" in f.lower() for f in commit.files):
        return "test"

    for cat_key, cat_info in CATEGORY_PATTERNS.items():
        if cat_key == "other":
            continue
        for keyword in cat_info["keywords"]:
            if keyword in msg:
                return cat_key

    return "other"


def get_default_since() -> str:
    """Return the Monday of the current week as YYYY-MM-DD."""
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    return monday.strftime("%Y-%m-%d")


def get_default_until() -> str:
    """Return tomorrow as YYYY-MM-DD to include today's commits."""
    tomorrow = datetime.now() + timedelta(days=1)
    return tomorrow.strftime("%Y-%m-%d")
