# git-weekly

> Generate weekly reports from Git commits, with AI-powered summary.
>
> 从 Git 提交记录自动生成周报，支持 AI 智能总结。告别"我这周干了啥"的灵魂拷问。

## 功能

- 扫描指定时间范围内的所有 Git 提交
- 自动分析 diff，归类为：新功能、Bug 修复、重构、文档、测试等
- 生成结构化周报（Markdown / 终端输出）
- 支持多仓库聚合
- 代码统计（新增 / 删除 / 修改的文件数）
- **多语言支持**：中文 / English（`--lang en`）
- **交互式配置**：`git-weekly init` 一键配置 AI 参数
- **AI 智能总结**：接入 OpenAI 兼容 API，基于 commit + diff 内容生成连贯的工作总结
- **Cursor Agent Skill**：在 Cursor IDE 中直接让 AI 助手生成周报

## 安装

```bash
pip install git-weekly
```

如需 AI 总结功能：

```bash
pip install "git-weekly[ai]"
```

或从源码安装：

```bash
git clone https://github.com/woaichilajiaochaorou/git-weekly.git
cd git-weekly
pip install -e ".[ai]"
```

## 快速开始

```bash
# 1. 安装
pip install git-weekly

# 2. 生成周报
git-weekly

# 3. (可选) 配置 AI 总结
pip install "git-weekly[ai]"
git-weekly init
git-weekly --ai
```

## 使用

```bash
# 生成本周周报（默认当前仓库）
git-weekly

# 交互式配置 AI 参数
git-weekly init

# 指定时间范围
git-weekly --since "2025-02-24" --until "2025-02-28"

# 指定仓库路径
git-weekly --repo /path/to/your/project

# 多仓库聚合
git-weekly --repo ./project-a --repo ./project-b

# 输出为 Markdown 文件
git-weekly -o weekly-report.md

# 指定作者（默认为 git config 中的用户）
git-weekly --author "your-name"

# AI 智能总结（需要安装 git-weekly[ai]）
git-weekly --ai
git-weekly --ai --api-key sk-xxx
git-weekly --ai --base-url https://api.deepseek.com/v1 --model deepseek-chat

# AI 总结但跳过 diff 采集（更快，总结不够细致）
git-weekly --ai --no-diff

# English output / 英文输出
git-weekly --lang en
git-weekly --lang en --ai
```

## 输出示例

```
──────────────────────────────────────────────────
 📋 周报 (02/24 - 02/28)
──────────────────────────────────────────────────

本周工作

  🚀 新功能
    • 用户登录模块：实现 JWT 鉴权
    • 添加文件上传接口，支持图片和 PDF

  🐛 Bug 修复
    • 修复分页查询在最后一页返回空数据的问题
    • 修复并发请求下 session 丢失

  ♻️ 重构
    • 将数据库操作抽取为 Repository 层

  📝 文档
    • 更新 API 接口文档

代码统计

  提交次数  12 次
  文件变更  23 个文件
  新增行数  +847
  删除行数  -312

🤖 AI 总结

  本周主要完成了用户登录模块的 JWT 鉴权实现和文件上传接口开发，
  同时修复了分页查询和并发 session 相关的两个稳定性问题。
  技术层面对数据库操作进行了 Repository 层抽取，提升了代码可维护性。
```

### English Output (`--lang en`)

```
──────────────────────────────────────────────────
 📋 Weekly Report (02/24 - 02/28)
──────────────────────────────────────────────────

Work Summary

  🚀 Features
    • Implement JWT authentication for user login
    • Add file upload endpoint with image and PDF support

  🐛 Bug Fixes
    • Fix pagination returning empty data on last page

Statistics

  Commits  12
  Files Changed  23 files
  Insertions  +847
  Deletions  -312
```

## AI 配置

### 快速配置（推荐）

运行交互式配置向导，一步到位：

```bash
git-weekly init
```

会引导你选择 LLM 服务商、输入 API Key、选择模型和默认语言，自动生成配置文件。

```
git-weekly init

选择 LLM 服务商:

  1) OpenAI      https://api.openai.com/v1
  2) DeepSeek    https://api.deepseek.com/v1
  3) 通义千问     https://dashscope.aliyuncs.com/compatible-mode/v1
  4) Ollama      http://localhost:11434/v1
  5) Custom

请输入编号 [1-5] (默认 1): 2
Base URL [https://api.deepseek.com/v1]:
API Key: sk-xxx
Model [deepseek-chat]:
默认语言 zh/en [zh]:

✔ 配置已保存至 ~/.config/git-weekly/config.toml
```

### 手动配置

API Key 也支持以下方式（优先级从高到低）：

**1. 命令行参数**

```bash
git-weekly --ai --api-key sk-xxx
```

**2. 环境变量**

```bash
export GIT_WEEKLY_API_KEY=sk-xxx
export GIT_WEEKLY_BASE_URL=https://api.deepseek.com/v1  # 可选
export GIT_WEEKLY_MODEL=deepseek-chat                    # 可选
```

**3. 配置文件** `~/.config/git-weekly/config.toml`

```toml
[ai]
api_key = "sk-xxx"
base_url = "https://api.openai.com/v1"
model = "gpt-4o-mini"

[general]
lang = "zh"
```

### Diff 分析

使用 `--ai` 时，工具会自动采集每个 commit 的代码 diff 内容并发送给 LLM，让 AI 能够理解实际的代码变更而不仅仅是 commit message。Diff 内容会自动截断以控制 token 用量（单个 commit 最多 2KB，总计最多 12KB）。

如果不需要 diff 分析（例如 commit 数量很大时加速），可以使用 `--no-diff`：

```bash
git-weekly --ai --no-diff
```

### 支持的 LLM 服务

任何兼容 OpenAI API 的服务都可以使用，例如：

| 服务 | base_url | 推荐模型 |
|------|----------|----------|
| OpenAI | `https://api.openai.com/v1` (默认) | `gpt-4o-mini` |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` |
| Ollama (本地) | `http://localhost:11434/v1` | `llama3` |

## Cursor Agent Skill

本项目内置了 Cursor Agent Skill（`.cursor/skills/git-weekly/`），在 Cursor IDE 中可以直接让 AI 助手帮你生成周报：

- "帮我生成本周周报"
- "generate my weekly report"
- "用 AI 总结一下我这周的工作"

Cursor 会自动识别 Skill 并调用 `git-weekly` 命令。

如需在所有项目中使用，可将 Skill 复制到个人目录：

```bash
cp -r .cursor/skills/git-weekly ~/.cursor/skills/
```

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码检查
ruff check .
```

## License

MIT
