# Bilibili Video Summarizer Skill — B站学习视频总结 Skill

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

> 一个给 **AI Agent** 用的 Skill，让它能自动从 B站视频提取字幕并生成结构化学习笔记。内置快速总结和深度研究两种策略，也支持自定义。

## 使用环境

这个 Skill 运行在 **AI Agent** 环境中（如 Proma、Claude Code），需要以下条件：

| 要求 | 说明 |
|------|------|
| **AI Agent 环境** | Proma / Claude Code / 任何支持 Skill 机制的 AI Agent 平台 |
| **Python 3.8+** | 仅字幕获取脚本需要。Agent 会自动调用 |
| **Python 依赖** | `pip install requests`（必装）。可选：`faster-whisper` + `yt-dlp`（无字幕时的 Whisper 降级方案） |
| **B站账号** | ❌ **不需要**。字幕获取走公开 API，无需登录 |

## 你需要提供什么

使用这个 Skill 只需要一样东西：

> **B站视频的 BV 号或视频链接**

例如：
- `BV1LUJP6REUf` — 纯 BV 号
- `https://www.bilibili.com/video/BV1LUJP6REUf` — 完整链接
- `https://b23.tv/xxxxx` — 短链接也支持

然后告诉 AI Agent 你想要什么程度的总结（不指定则默认用 `quick` 快速总结）。

## 快速开始

### 1. 安装 Skill

**Proma 用户**：
```bash
git clone https://github.com/FengQingMo/bilibili-video-summarizer-skill.git \
  ~/.proma/agent-workspaces/default/skills/bilibili-video-summarizer
```

**Claude Code 用户**：
将本仓库克隆或复制到你的 skills 目录。

### 2. 安装 Python 依赖

```bash
pip install requests
# 可选：视频无字幕时用 Whisper 降级
# pip install faster-whisper yt-dlp
```

### 3. 开始使用

直接对 AI Agent 说：

> 帮我总结这个视频 https://www.bilibili.com/video/BV1LUJP6REUf

或者指定策略：

> 用 deep 策略认真学习这个视频 https://www.bilibili.com/video/BV1LUJP6REUf

## 项目结构

```
bilibili-video-summarizer-skill/
├── SKILL.md                        # 🔑 Agent 入口 — AI Agent 读这个就知道怎么做
├── README.md                       # 你正在看的文件
├── LICENSE
├── .gitignore
├── scripts/                        # 字幕获取工具
│   ├── get_subtitle.py             #   B站 API 字幕获取（公开接口，无需登录）
│   └── get_subtitle_fallback.py    #   Whisper 语音识别降级
└── strategies/                     # 总结策略（Prompt 模板）
    ├── quick.md                    #   快速总结 — 一次对话搞定
    ├── deep.md                     #   深度研究 — 三阶段（研究员→撰写→审阅）
    └── customize.md                #   如何编写自己的策略
```

## 内置策略

| 策略 | 做法 | 适合场景 |
|------|------|---------|
| **quick** | AI Agent 一次调用，按模板生成概览 | "帮我总结一下"、"快速看看" |
| **deep** | 三阶段流水线（研究员→笔记撰写员→审阅员），产出高质量笔记 | "认真学习"、"做笔记" |

### quick 示例

Agent 输出：
```markdown
# 用 LangChain 构建 AI Agent

## 概述
这个视频讲解了如何用 LangChain 框架构建 AI Agent，
从基础概念到完整实战，适合有 Python 基础的开发者。

## 核心要点
- Agent 的核心是"推理+行动"循环（ReAct 模式）
- LangChain 提供了统一的 Agent 接口，支持多种 LLM 后端
- 工具（Tools）是 Agent 的手和脚，需要精心设计
...
```

### deep 示例

Agent 输出带完整 frontmatter 的结构化笔记，包含 Mermaid 图表、代码示例、对比表格，以及审阅评分（如 `review_score: 21/25`）。

## 自定义策略

复制 `strategies/customize.md` 作为起点，写你自己的策略文件。然后告诉 AI Agent：

> 用我写的 my-strategy.md 策略，帮我总结这个视频 https://...

详见 [strategies/customize.md](strategies/customize.md)，里面有两个完整示例。

## 常见问题

**Q: 真的不需要登录 B站吗？**
A: 不需要。字幕获取走的是 `api.bilibili.com/x/player/v2` 公开接口。只有 Whisper 降级（下载音频流）可能需要。

**Q: 视频没有字幕怎么办？**
A: AI Agent 会告诉你，并询问是否用 Whisper 降级（需要安装 faster-whisper）。

**Q: 这和"把字幕扔给 ChatGPT 总结"有什么不同？**
A: 这个 Skill 提供了结构化的策略模板和预验证的提示词。deep 策略的三阶段流程（研究员→撰写→审阅）比一次性总结质量高得多，而且可以复用。

**Q: 怎么贡献新的策略？**
A: 把你写的策略文件 PR 到 `strategies/` 目录，格式参考已有的 `quick.md` 和 `deep.md`。

**Q: 支持其他视频平台吗？**
A: 目前只支持 B站。如果你需要 YouTube 等平台的支持，欢迎提 PR（核心是替换 `scripts/` 下的获取脚本，策略文件可以复用）。

## 许可

MIT — 详见 [LICENSE](LICENSE)。
