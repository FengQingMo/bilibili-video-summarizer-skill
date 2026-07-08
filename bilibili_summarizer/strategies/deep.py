"""
Deep research strategy — 3-phase pipeline (Research → Write → Review).

Inspired by the learn-new-tech skill workflow. Each phase is a separate
LLM call that builds on the previous one.

Best for: deep learning, comprehensive notes, academic-level quality.
Cost: 3-4 LLM calls (~3-5x more than quick mode).
"""

import json
from datetime import datetime
from .base import BaseStrategy, VideoContext, SummaryResult
from ..llm import call_llm

# ---------------------------------------------------------------------------
# Phase 1: Researcher
# ---------------------------------------------------------------------------

RESEARCHER_SYSTEM = """\
You are a research analyst. Your job is to examine a video transcript and
produce a structured research brief that will be used by a note-writer.

Output language: {language}

## Your Task

Analyze the video transcript carefully and produce a **research brief**
covering these sections:

### 1. Overview
- One-sentence summary of what this video teaches
- What problem does it address?
- Who is the target audience?

### 2. Core Concepts
- List every technical term, concept, or jargon mentioned
- For each: a brief definition (from the transcript context)
- Flag concepts that might need external verification

### 3. Key Arguments & Ideas
- What are the main claims or arguments made?
- What evidence or examples are provided?
- Any notable quotes (verbatim from transcript if possible)

### 4. Practical Takeaways
- What actionable advice is given?
- What workflows, tools, or methods are demonstrated?
- What pitfalls or warnings are mentioned?

### 5. Knowledge Gaps
- What does the transcript NOT cover that would be valuable?
- What prerequisite knowledge is assumed?
- What would you need to research externally to fully understand this?

### 6. Suggested Note Structure
- Propose an outline for the final learning note (heading hierarchy)
- This will guide the note-writer in the next phase

Rules:
- Be thorough — flag everything potentially useful
- Mark uncertainties clearly
- Quote the transcript when possible (use "> blockquote format")
- If subtitle is AI-generated, be extra cautious about technical terms"""


# ---------------------------------------------------------------------------
# Phase 2: Note Writer
# ---------------------------------------------------------------------------

NOTE_WRITER_SYSTEM = """\
You are a technical note writer. You will receive a research brief about
a learning video, and your job is to turn it into a polished, structured
learning note suitable for a knowledge base (Obsidian / Notion).

Output language: {language}

## Note Structure

{template}

## Writing Guidelines

1. **Depth first** — explain the "why" and "how", not just the "what"
2. **Clear hierarchy** — use proper heading levels (H2 → H3 → H4)
3. **Mermaid diagrams** — include at least 1 Mermaid diagram if applicable
   (flowchart, sequence diagram, or mindmap)
4. **Code blocks** — if the video demonstrates code, include properly
   formatted code snippets with language tags
5. **Compare & contrast** — when multiple approaches are discussed,
   use comparison tables
6. **Practical examples** — ground abstract concepts with concrete examples
7. **Language**: Use {language} as primary; keep technical terms in English

## Important

- Every claim must be traceable to the research brief (or transcript)
- Do NOT invent facts, URLs, or references
- Mark AI-transcribed content with a note if applicable
- Add a "⚠️ AI Transcription Note" callout at the top if subtitle_type is
  "ai" or "whisper"
- Format: clean Markdown, Obsidian-compatible (with frontmatter)"""


# ---------------------------------------------------------------------------
# Phase 3: Reviewer
# ---------------------------------------------------------------------------

REVIEWER_SYSTEM = """\
You are a strict academic reviewer. Your job is to review a learning note
generated from a video transcript and identify issues.

## Review Dimensions

Score each dimension 1-5 and explain:

1. **Factual Accuracy** — Are the technical claims consistent with the
   transcript? Any invented facts?
2. **Completeness** — Are all key concepts from the research brief covered?
3. **Structure** — Is the heading hierarchy logical? Sections well-balanced?
4. **Clarity** — Would a reader understand this without watching the video?
5. **Actionability** — Can the reader apply what they learned?

## Output Format

```json
{{
  "scores": {{
    "accuracy": 4,
    "completeness": 3,
    "structure": 5,
    "clarity": 4,
    "actionability": 3
  }},
  "total": 19,
  "issues": [
    {{
      "severity": "critical|major|minor",
      "location": "Section name or paragraph",
      "problem": "What's wrong",
      "fix": "How to fix it"
    }}
  ],
  "verdict": "pass|conditional|fail",
  "summary": "One-paragraph review summary"
}}
```

Rules:
- Be strict — you are the last quality gate
- Every issue must have a concrete fix suggestion
- "conditional" = fix critical issues, then pass
- "fail" = needs rewrite"""


# ---------------------------------------------------------------------------
# Note Template
# ---------------------------------------------------------------------------

NOTE_TEMPLATE = """---
tags: [learning, {tags}]
created: {date}
source: {source_url}
author: {author}
---

# {title}

{ai_note}

## 1. Overview

### 1.1 What This Video Covers
(One-paragraph summary)

### 1.2 Why It Matters
(Context and significance)

### 1.3 Target Audience
(Who should watch this)

## 2. Core Concepts

### 2.1 <Concept A>
(Definition, explanation, examples from the video)

### 2.2 <Concept B>
...

## 3. Key Ideas & Arguments

(Detailed breakdown of the main points made in the video)

## 4. Architecture / Workflow

(If applicable — Mermaid diagram + explanation)

## 5. Practical Guide

### 5.1 Steps / Workflow
### 5.2 Code Examples (if any)
### 5.3 Pitfalls & Warnings

## 6. Key Takeaways

- Takeaway 1
- Takeaway 2
- ...

## 7. Personal Reflections

(Optional — space for the learner to add their own thoughts)

---

## Source

- **Video**: [{title}]({source_url})
- **Author**: {author}
- **Subtitle**: {subtitle_info}
"""


# ---------------------------------------------------------------------------
# Strategy Class
# ---------------------------------------------------------------------------

class DeepStrategy(BaseStrategy):
    """
    3-phase deep research pipeline:

    Phase 1 — Researcher: analyzes transcript → research brief
    Phase 2 — Note Writer: brief → structured markdown note
    Phase 3 — Reviewer: reviews note → fixes issues → final output
    """

    name = "deep"
    description = (
        "3-phase deep research (research → write → review). "
        "High quality, 3-4 LLM calls."
    )

    def __init__(self, model: str = "", language: str = "zh"):
        from ..config import Config
        self.model = model or Config.LLM_MODEL
        self.language = language or Config.NOTE_LANGUAGE

    def summarize(self, ctx: VideoContext) -> SummaryResult:
        if not ctx.subtitle_text:
            return SummaryResult(
                markdown=f"# {ctx.title}\n\n"
                         f"**Author**: {ctx.author} | **Views**: {ctx.views}\n\n"
                         f"> ⚠️ No subtitle available. Deep research requires "
                         f"a transcript.\n\n"
                         f"## Video Description\n\n{ctx.description}",
                metadata={'status': 'no_subtitle'}
            )

        lang_name = "Chinese (中文)" if self.language == 'zh' else self.language

        # Truncate for context window
        max_chars = 30000
        subtitle = ctx.subtitle_text
        truncated = len(subtitle) > max_chars
        if truncated:
            subtitle = subtitle[:max_chars] + "\n\n[... transcript truncated ...]"

        # ---- Phase 1: Research ----
        print("[Phase 1/3] Researching transcript...")
        research_brief = call_llm(
            system_prompt=RESEARCHER_SYSTEM.format(language=lang_name),
            user_prompt=self._research_prompt(ctx, subtitle),
            model=self.model,
        )

        # ---- Phase 2: Write Note ----
        print("[Phase 2/3] Writing learning note...")

        ai_note = ""
        if ctx.subtitle_type in ('ai', 'whisper'):
            ai_note = (
                "> ⚠️ **AI Transcription Note**: This video's transcript was "
                "generated by AI speech recognition. Technical terms and "
                "proper nouns may contain errors. Verify critical details "
                "against the original video.\n"
            )

        tags = self._infer_tags(ctx)
        date = datetime.now().strftime('%Y-%m-%d')
        template = NOTE_TEMPLATE.format(
            tags=', '.join(tags),
            date=date,
            source_url=ctx.url or f"https://www.bilibili.com/video/{ctx.bvid}",
            author=ctx.author,
            title=ctx.title,
            ai_note=ai_note,
            subtitle_info=f"{ctx.subtitle_type} ({ctx.subtitle_lang})",
        )

        draft_note = call_llm(
            system_prompt=NOTE_WRITER_SYSTEM.format(
                language=lang_name,
                template=template,
            ),
            user_prompt=f"""\
## Video Context
- Title: {ctx.title}
- Author: {ctx.author}
- Subtitle type: {ctx.subtitle_type} ({ctx.subtitle_lang})

## Research Brief
{research_brief}

## Full Transcript (for fact-checking)
{subtitle}

---
Please write the final learning note based on the research brief above.
Follow the template structure. Include at least 1 Mermaid diagram if applicable.""",
            model=self.model,
        )

        # ---- Phase 3: Review ----
        print("[Phase 3/3] Reviewing and refining...")

        review_raw = call_llm(
            system_prompt=REVIEWER_SYSTEM,
            user_prompt=f"""\
## Research Brief
{research_brief}

## Draft Note
{draft_note}

---
Review the draft note against the research brief. Output valid JSON.""",
            model=self.model,
        )

        # Parse review
        review = self._parse_review(review_raw)

        # If conditional pass, try to fix issues
        verdict = review.get('verdict', 'pass')
        issues = review.get('issues', [])

        if verdict in ('conditional', 'fail') and issues:
            critical_issues = [
                i for i in issues if i.get('severity') == 'critical'
            ]
            if critical_issues:
                print(f"  Found {len(critical_issues)} critical issues. "
                      f"Attempting to fix...")
                draft_note = self._fix_note(
                    draft_note, critical_issues, research_brief
                )

        # Build frontmatter with review scores
        scores = review.get('scores', {})
        frontmatter = (
            f"---\n"
            f"tags: [learning, {', '.join(tags)}]\n"
            f"created: {date}\n"
            f"source: {ctx.url or f'https://www.bilibili.com/video/{ctx.bvid}'}\n"
            f"author: {ctx.author}\n"
            f"review_score: {review.get('total', 'N/A')}/25\n"
            f"review_verdict: {verdict}\n"
            f"---\n\n"
        )

        # If the note already has frontmatter, replace it
        if draft_note.strip().startswith('---'):
            # Find second ---
            parts = draft_note.split('---', 2)
            if len(parts) >= 3:
                draft_note = frontmatter + parts[2].strip()

        final_note = draft_note

        return SummaryResult(
            markdown=final_note,
            metadata={
                'strategy': 'deep',
                'review_scores': scores,
                'review_total': review.get('total'),
                'verdict': verdict,
            }
        )

    # ---- helpers ----

    def _research_prompt(self, ctx: VideoContext, subtitle: str) -> str:
        return f"""\
## Video Information
- Title: {ctx.title}
- Author: {ctx.author}
- Duration: {ctx.duration // 60}min {ctx.duration % 60}s
- Views: {ctx.views}
- Subtitle type: {ctx.subtitle_type} ({ctx.subtitle_lang})
- Description: {ctx.description or 'N/A'}

## Full Transcript
{subtitle}

---
Please produce a research brief following the system prompt guidelines."""

    def _infer_tags(self, ctx: VideoContext) -> list[str]:
        """Simple tag inference from title — can be improved with LLM."""
        title_lower = ctx.title.lower()
        tags = []
        # Common technical keywords
        keywords = {
            'ai': 'AI', 'agent': 'Agent', 'llm': 'LLM', 'rag': 'RAG',
            'python': 'Python', 'machine learning': 'Machine-Learning',
            'deep learning': 'Deep-Learning', 'nlp': 'NLP',
            'transformer': 'Transformer', 'gpu': 'GPU', 'cuda': 'CUDA',
            'linux': 'Linux', 'docker': 'Docker', 'kubernetes': 'Kubernetes',
            '前端': 'Frontend', '后端': 'Backend', 'react': 'React',
            'vue': 'Vue', 'golang': 'Go', 'rust': 'Rust',
            '论文': 'Paper', '论文精读': 'Paper-Reading',
        }
        for kw, tag in keywords.items():
            if kw in title_lower:
                tags.append(tag)
        if not tags:
            tags.append('General')
        return tags

    def _parse_review(self, raw: str) -> dict:
        """Try to extract JSON from the review LLM output."""
        # Find JSON block
        import re
        match = re.search(r'\{[\s\S]*\}', raw)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        return {
            'scores': {},
            'total': 0,
            'issues': [],
            'verdict': 'pass',
            'summary': 'Could not parse review output.',
        }

    def _fix_note(self, note: str, issues: list, research_brief: str) -> str:
        """Ask the LLM to fix critical issues in the note."""
        issues_text = '\n'.join(
            f"- [{i['severity']}] {i.get('location', 'unknown')}: "
            f"{i['problem']} → {i['fix']}"
            for i in issues
        )

        fixed = call_llm(
            system_prompt="You are an editor. Fix the issues in the note.",
            user_prompt=f"""\
## Issues to Fix
{issues_text}

## Research Brief (ground truth)
{research_brief}

## Current Note
{note}

---
Please fix all the issues above and output the corrected full note.""",
            model=self.model,
        )
        return fixed
