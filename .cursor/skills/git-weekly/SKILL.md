---
name: git-weekly
description: Generate weekly reports from Git commit history with optional AI summary. Use when the user asks to generate a weekly report, work summary, changelog, or asks what they did this week. Also use when the user mentions git-weekly, 周报, or weekly report.
---

# git-weekly

CLI tool that generates weekly reports from Git commits, with optional AI-powered summary.

## Prerequisites

```bash
pip install git-weekly        # basic
pip install "git-weekly[ai]"  # with AI summary
```

Verify: `git-weekly --help`

## Quick Usage

Run in a Git repository directory:

```bash
# Current repo, current week
git-weekly

# With AI summary
git-weekly --ai

# English output
git-weekly --lang en

# Custom date range
git-weekly --since 2025-02-24 --until 2025-02-28

# Multiple repos
git-weekly --repo ./project-a --repo ./project-b

# Output to file
git-weekly -o weekly-report.md

# All authors (default: current git user only)
git-weekly --all-authors
```

## Common Workflows

### Generate weekly report for current project

```bash
cd /path/to/project
git-weekly
```

### Generate AI-enhanced report

Requires API key configured via `git-weekly init` or env var `GIT_WEEKLY_API_KEY`.

```bash
git-weekly --ai
```

For faster AI summary (skip diff collection):

```bash
git-weekly --ai --no-diff
```

### Multi-repo aggregated report

```bash
git-weekly --repo ~/projects/backend --repo ~/projects/frontend -o report.md
```

### First-time AI setup

```bash
git-weekly init
```

Interactive wizard that configures LLM provider (OpenAI/DeepSeek/Qwen/Ollama), API key, model, and default language. Saves to `~/.config/git-weekly/config.toml`.

## Key Options

| Flag | Description |
|------|-------------|
| `--repo PATH` | Target repository (repeatable) |
| `--since DATE` | Start date (YYYY-MM-DD, default: Monday) |
| `--until DATE` | End date (YYYY-MM-DD, default: today) |
| `--author NAME` | Filter by author |
| `--all-authors` | Include all authors |
| `-o FILE` | Output to Markdown file |
| `--ai` | Enable AI summary |
| `--no-diff` | Skip diff in AI context |
| `--lang zh/en` | Output language |
| `--api-key KEY` | LLM API key |
| `--base-url URL` | LLM API endpoint |
| `--model NAME` | LLM model name |

## Execution Notes

- Must run in (or point `--repo` to) a valid Git repository
- The tool reads `git config user.name` to filter commits by default
- AI features require `openai` package: `pip install "git-weekly[ai]"`
- Config file location: `~/.config/git-weekly/config.toml`
