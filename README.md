# Bilibili Video Summarizer Skill — B站学习视频总结 Skill

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

> 一个给 **AI Agent** 用的 Skill，让它能自动从 B站视频提取字幕并生成结构化学习笔记。内置快速总结和深度研究两种策略，也支持自定义。

## 这是什么

这是一个 **AI Agent Skill**（技能文件），不是传统的独立软件。它告诉 AI Agent（如 Claude Code、Proma 等）如何：

1. 从 B站视频获取字幕（**无需登录**）
2. 按照你选的"策略"，将字幕总结为结构化笔记
3. 保存为 Obsidian/Notion 兼容的 Markdown 文件

**核心理念**：AI Agent 自己就有 LLM 能力，这个 Skill 不需要额外的 API Key，只提供字幕获取工具 + 策略提示词。

## 快速开始

### 1. 安装为 Skill

**Proma 用户**：
```bash
# 克隆到 Proma skills 目录
git clone https://github.com/FengQingMo/bilibili-video-summarizer-skill.git \
  ~/.proma/agent-workspaces/default/skills/bilibili-video-summarizer
```

**Claude Code 用户**：
将 SKILL.md 放到你的 skills 目录即可。

### 2. 安装依赖（仅字幕获取脚本需要）

```bash
pip install requests
# 可选：Whisper 降级方案（视频无字幕时）
# pip install faster-whisper yt-dlp
```

### 3. 使用

直接对 AI Agent 说：

> 帮我总结这个视频 https://www.bilibili.com/video/BV1LUJP6REUf

或者指定策略：

> 用 deep 策略认真学习这个视频 https://www.bilibili.com/video/BV1LUJP6REUf

## 无需登录 B站 ✅

字幕获取用的是 B站公开 API，**不需要登录、不需要 Cookie**。给 BV 号就能用。

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

## 两种内置策略

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
