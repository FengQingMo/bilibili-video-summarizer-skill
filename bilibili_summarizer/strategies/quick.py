"""
Quick summary strategy — one LLM call, fast results.

Best for: "summarize this video for me", quick overviews.
Not for: deep research, academic notes, comprehensive coverage.
"""

import json
from .base import BaseStrategy, VideoContext, SummaryResult
from ..llm import call_llm

QUICK_SYSTEM_PROMPT = """\
You are a skilled note-taker. Your task is to summarize a learning video
based on its subtitle transcript.

Output language: {language}

Your summary should be a well-structured Markdown note with:
1. A clear title (based on video content, NOT the raw video title)
2. ## Overview — what this video is about in 2-3 sentences
3. ## Key Points — 5-10 bullet points of the main ideas
4. ## Key Concepts — explain any important technical terms mentioned
5. ## Notable Examples or Cases — if the video gave concrete examples
6. ## Quick Takeaways — 3-5 actionable or memorable conclusions

Rules:
- Use the subtitle content as the primary source
- Do NOT make up facts not present in the subtitles
- If the subtitle is AI-generated (subtitle_type=ai/whisper), note that some
  details may be inaccurate
- Keep it concise but informative (target: 500-1500 words)
- Use Chinese as the primary language; keep technical terms in English

Format as clean Markdown with proper headings, lists, and emphasis."""


class QuickStrategy(BaseStrategy):
    """One-shot LLM summarization. Fast but less thorough."""

    name = "quick"
    description = "One-shot LLM summary — fast (~30s), good for quick overviews"

    def __init__(self, model: str = "", language: str = "zh"):
        from ..config import Config
        self.model = model or Config.LLM_MODEL
        self.language = language or Config.NOTE_LANGUAGE

    def summarize(self, ctx: VideoContext) -> SummaryResult:
        if not ctx.subtitle_text:
            return SummaryResult(
                markdown=f"# {ctx.title}\n\n"
                         f"**Author**: {ctx.author} | **Views**: {ctx.views}\n\n"
                         f"> ⚠️ No subtitle available for this video. "
                         f"Cannot generate a summary.\n\n"
                         f"## Video Description\n\n{ctx.description}",
                metadata={'status': 'no_subtitle'}
            )

        # Truncate very long subtitles to fit context window
        max_chars = 30000
        subtitle = ctx.subtitle_text
        if len(subtitle) > max_chars:
            subtitle = subtitle[:max_chars] + "\n\n[... transcript truncated ...]"

        system_prompt = QUICK_SYSTEM_PROMPT.format(
            language="Chinese (中文)" if self.language == 'zh' else self.language
        )

        user_prompt = f"""\
## Video Information
- Title: {ctx.title}
- Author: {ctx.author}
- Duration: {ctx.duration // 60}min {ctx.duration % 60}s
- Subtitle type: {ctx.subtitle_type} ({ctx.subtitle_lang})

## Subtitle Transcript
{subtitle}

---
Please generate a structured learning note based on the above transcript."""

        note = call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=self.model,
        )

        return SummaryResult(markdown=note, metadata={'strategy': 'quick'})
