"""
Subtitle fetching sub-module.

Provides two methods:
    - fetch_subtitle()      — via Bilibili API (needs credentials, ~10-30% videos)
    - fetch_subtitle_whisper() — audio download + local Whisper transcription (100% coverage)
"""

from .fetcher import fetch_subtitle, fetch_video_info
from .whisper_fallback import fetch_subtitle_whisper
