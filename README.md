# git-weekly

从 Git 提交记录自动生成周报，支持 AI 智能总结。告别"我这周干了啥"的灵魂拷问。

## 功能

- 扫描指定时间范围内的所有 Git 提交
- 自动分析 diff，归类为：新功能、Bug 修复、重构、文档、测试等
- 生成结构化周报（Markdown / 终端输出）
- 支持多仓库聚合
- 代码统计（新增 / 删除 / 修改的文件数）
- **AI 智能总结**：接入 OpenAI 兼容 API，自动生成连贯的工作总结

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

## 使用

```bash
# 生成本周周报（默认当前仓库）
git-weekly

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

## AI 配置

API Key 支持三种配置方式（优先级从高到低）：

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
```

### 支持的 LLM 服务

任何兼容 OpenAI API 的服务都可以使用，例如：

| 服务 | base_url | 推荐模型 |
|------|----------|----------|
| OpenAI | `https://api.openai.com/v1` (默认) | `gpt-4o-mini` |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` |
| Ollama (本地) | `http://localhost:11434/v1` | `llama3` |

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
