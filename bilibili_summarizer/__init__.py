"""
Bilibili Video Summarizer — Fetch subtitles from Bilibili and generate
structured learning notes via LLM.

Usage:
    bilibili-summarize --url "https://www.bilibili.com/video/BV1xx..." --strategy quick
    bilibili-summarize --bvid BV1xx --strategy deep -o ./my_notes

For programmatic use:
    from bilibili_summarizer import Summarizer
    s = Summarizer(strategy="deep")
    s.run("https://www.bilibili.com/video/BV1xx...")
"""

__version__ = "0.1.0"
