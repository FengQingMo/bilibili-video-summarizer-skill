# Bilibili Video Summarizer Skill — B站学习视频总结 Skill

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

> 一个给 **AI Agent** 用的 Skill，让它能自动从 B站视频提取字幕并生成结构化学习笔记。内置快速总结和深度研究两种策略，也支持自定义。

## 使用环境

| 要求 | 说明 |
|------|------|
| **AI Agent 环境** | Proma / Claude Code / 任何支持 Skill 机制的 AI Agent 平台 |
| **Python 3.8+** | 字幕获取脚本的运行环境 |

## 需要安装的依赖

基础字幕获取只需要 `requests`，Whisper 降级按需安装额外依赖。

### 基础（必装）

```bash
pip install requests
```

### Whisper 降级（视频无字幕时需要）

```bash
pip install faster-whisper yt-dlp
```

还需要 `ffmpeg` 用于音频解码：

```bash
# Windows (Scoop)
scoop install ffmpeg
# Windows (Chocolatey)
choco install ffmpeg
# macOS
brew install ffmpeg
# Linux (Ubuntu/Debian)
sudo apt install ffmpeg
```

首次使用 Whisper 降级时，模型会自动下载到本 Skill 目录下的 `models/` 中，后续复用。推荐 `small` 模型（约 2.4GB，性价比最高）。

## 你需要提供什么

使用这个 Skill 只需要一样东西：

> **B站视频的 BV 号或视频链接**

例如：
- `BV16XDYBXEdb` — 纯 BV 号
- `https://www.bilibili.com/video/BV16XDYBXEdb` — 完整链接
- `https://b23.tv/xxxxx` — 短链接也支持

然后告诉 AI Agent 你想要什么程度的总结（不指定则默认用 `quick` 快速总结）。

## 快速开始

对你的 AI Agent 说：

> 安装这个 skill：https://github.com/FengQingMo/bilibili-video-summarizer-skill

Agent 会自动完成安装。

### 开始使用

直接告诉 Agent 你要总结哪个视频：

> 帮我总结这个视频 https://www.bilibili.com/video/BV16XDYBXEdb

或者指定策略：

> 用 deep 策略认真学习这个视频 https://www.bilibili.com/video/BV16XDYBXEdb

> ⚠️ 首次使用时，Agent 会自动安装 Python 依赖（`requests` 等），如果用 Whisper 降级还会下载语音模型（约 2.4GB），请耐心等待。后续使用无需重复下载。

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
├── strategies/                     # 总结策略（Prompt 模板）
│   ├── quick.md                    #   快速总结 — 一次对话搞定
│   ├── deep.md                     #   深度研究 — 三阶段（调研→撰写→审阅）
│   └── customize.md                #   如何编写自己的策略
└── examples/                       # 示例输出
    ├── example-quick.md            #   quick 策略输出示例
    └── example-deep.md             #   deep 策略输出示例（含审阅报告）
```

## 内置策略

| 策略 | 做法 | 适合场景 |
|------|------|---------|
| **quick** | AI Agent 一次调用，按模板生成概览 | "帮我总结一下"、"快速看看" |
| **deep** | 外部调研（学术论文→官方文档→博客→社区）→ 笔记撰写 → 审阅，CS 学习专用 | "认真学习"、"做笔记" |

### quick 示例

Agent 输出：
```markdown
# 一个 Token 怎么变成 MoE？— 混合专家模型全图解

## 概述
这个视频用通俗易懂的方式（从 4 维向量开始举例），
一步步讲清楚了"混合专家模型（MoE）"是什么、为什么需要它。

## 核心要点
- MoE（Mixture of Experts）是混合专家模型，用多个"专家子网络"替代单一 FFN 层
- MoE 只替换 Transformer 中的 FFN 层，自注意力层不受影响
- 核心思路：参数量翻倍，但计算量不用翻那么多——每个 token 只激活少数专家
- 两个关键步骤：① Router 挑专家（Top-K）② 加权求和计算
- Qwen3-235B-A22B 的 235B 是总参数，22B 是激活参数
...
```

### deep 示例

Agent 会先搜索学术论文（arXiv、Google Scholar）、官方文档、技术博客，与视频字幕交叉验证后再撰写笔记。输出带完整 frontmatter 的结构化笔记，包含 Mermaid 图表、代码示例、对比表格，以及审阅评分（如 `review_score: 21/25`）。

📄 完整示例：[examples/example-quick.md](examples/example-quick.md) · [examples/example-deep.md](examples/example-deep.md)（以 BV16XDYBXEdb "MoE 混合专家模型"视频为例）

## 许可

MIT — 详见 [LICENSE](LICENSE)。
