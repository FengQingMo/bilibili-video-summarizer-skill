"""
Example: Custom summarization strategy.

This shows how to create your own strategy that plugs into the
Bilibili Video Summarizer. Customize the prompt, add extra LLM calls,
or implement entirely different summarization logic.

Usage:
    BILI_SUMMARIZE_STRATEGY=examples/custom_strategy.py \\
        bilibili-summarize --bvid BV1xx --strategy custom

Or programmatically:
    from examples.custom_strategy import CustomStrategy
    from bilibili_summarizer.strategies.base import VideoContext
    from bilibili_summarizer.subtitle import fetch_subtitle, fetch_video_info

    strategy = CustomStrategy()
    info = fetch_video_info("BV1xx")
    sub = fetch_subtitle("BV1xx")
    ctx = VideoContext(bvid="BV1xx", title=info['title'], ..., subtitle_text=sub['text'])
    result = strategy.summarize(ctx)
    print(result.markdown)
"""

import sys
import os

# Make sure the package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bilibili_summarizer.strategies.base import BaseStrategy, VideoContext, SummaryResult
from bilibili_summarizer.llm import call_llm


# ============================================================================
# EDIT THIS: Define your custom system prompt
# ============================================================================

CUSTOM_SYSTEM_PROMPT = """\
You are a {role}.

Your task is to summarize a video transcript in {language}.

## Output Format

{output_format}

## Rules

{rules}
"""


class CustomStrategy(BaseStrategy):
    """
    A custom summarization strategy.

    To create your own:
    1. Copy this file
    2. Modify the prompts and logic below
    3. Run with: BILI_SUMMARIZE_STRATEGY=your_file.py bilibili-summarize ...
    """

    name = "custom"
    description = "User-defined custom strategy"

    def __init__(self, model: str = "", language: str = "zh"):
        from bilibili_summarizer.config import Config
        self.model = model or Config.LLM_MODEL
        self.language = language or Config.NOTE_LANGUAGE

    def summarize(self, ctx: VideoContext) -> SummaryResult:
        # ---- Customize these values ----
        role = "technical note writer who creates Obsidian-compatible notes"
        lang = "Chinese (中文)" if self.language == 'zh' else self.language
        output_format = """\
1. Title (H1)
2. ## Summary — 2-3 sentence overview
3. ## Key Points — bullet list
4. ## Detailed Notes — organized by topic
5. ## FAQ / Common Pitfalls — if applicable
6. ## References — list video source"""
        rules = """\
- Use the subtitle text as the primary source
- Do not invent facts
- Keep the note under 2000 words
- Use Chinese as the primary language"""

        system_prompt = CUSTOM_SYSTEM_PROMPT.format(
            role=role,
            language=lang,
            output_format=output_format,
            rules=rules,
        )

        # ---- Customize the user prompt ----
        user_prompt = f"""\
## Video Info
- Title: {ctx.title}
- Author: {ctx.author}
- URL: {ctx.url or f'https://www.bilibili.com/video/{ctx.bvid}'}
- Subtitle: {ctx.subtitle_type} ({ctx.subtitle_lang})

## Transcript
{ctx.subtitle_text[:20000]}

---
Generate the note."""

        # ---- Call LLM (add more calls for multi-phase workflows) ----
        note = call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=self.model,
        )

        # ---- Optional: Post-processing ----
        # Add frontmatter
        from datetime import datetime
        frontmatter = f"""---
title: "{ctx.title}"
source: "{ctx.url or f'https://www.bilibili.com/video/{ctx.bvid}'}"
author: "{ctx.author}"
created: "{datetime.now().strftime('%Y-%m-%d')}"
strategy: custom
---

"""
        final = frontmatter + note

        return SummaryResult(
            markdown=final,
            metadata={
                'strategy': 'custom',
                'length': len(note),
            }
        )


# ============================================================================
# Advanced: Multi-phase custom strategy example
# ============================================================================

class AdvancedCustomStrategy(BaseStrategy):
    """
    Example of a multi-phase strategy with two LLM calls:
    1. Extract key terms first
    2. Then write the note with the extracted terms
    """

    name = "advanced_custom"
    description = "Two-phase: extract terms → write note"

    def __init__(self, model: str = ""):
        from bilibili_summarizer.config import Config
        self.model = model or Config.LLM_MODEL

    def summarize(self, ctx: VideoContext) -> SummaryResult:
        # Phase 1: Extract key terms
        print("  [Phase 1] Extracting key terms...")
        terms = call_llm(
            system_prompt="Extract key technical terms from the transcript. "
                          "Output one term per line with a brief definition.",
            user_prompt=ctx.subtitle_text[:15000],
            model=self.model,
        )

        # Phase 2: Write full note
        print("  [Phase 2] Writing note...")
        note = call_llm(
            system_prompt="Write a structured learning note. Incorporate "
                          "the key terms provided.",
            user_prompt=f"""\
## Video: {ctx.title} by {ctx.author}

## Key Terms
{terms}

## Transcript
{ctx.subtitle_text[:20000]}

Write a comprehensive note.""",
            model=self.model,
        )

        return SummaryResult(
            markdown=note,
            metadata={'strategy': 'advanced_custom', 'terms_extracted': len(terms)}
        )
