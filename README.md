# git-weekly

从 Git 提交记录自动生成周报。告别"我这周干了啥"的灵魂拷问。

## 功能

- 扫描指定时间范围内的所有 Git 提交
- 自动分析 diff，归类为：新功能、Bug 修复、重构、文档、测试等
- 生成结构化周报（Markdown / 终端输出）
- 支持多仓库聚合
- 代码统计（新增 / 删除 / 修改的文件数）

## 安装

```bash
pip install git-weekly
```

或从源码安装：

```bash
git clone https://github.com/woaichilajiaochaorou/git-weekly.git
cd git-weekly
pip install -e .
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
```

## 输出示例

```
╭──────────────────────────────────────────╮
│           📋 周报 (02/24 - 02/28)        │
╰──────────────────────────────────────────╯

## 本周工作

### 🚀 新功能
- 用户登录模块：实现 JWT 鉴权 (3 commits)
- 添加文件上传接口，支持图片和 PDF (1 commit)

### 🐛 Bug 修复
- 修复分页查询在最后一页返回空数据的问题
- 修复并发请求下 session 丢失

### ♻️ 重构
- 将数据库操作抽取为 Repository 层

### 📝 文档
- 更新 API 接口文档

## 代码统计

  文件变更: 23 个文件
  新增行数: +847
  删除行数: -312
  提交次数: 12 次
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
