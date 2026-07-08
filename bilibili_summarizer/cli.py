"""
CLI entry point for Bilibili Video Summarizer.

Usage:
    bilibili-summarize --url "https://www.bilibili.com/video/BV1xx..." --strategy quick
    bilibili-summarize --bvid BV1xx --strategy deep -o ./my_notes
    bilibili-summarize --bvid BV1xx --strategy deep --whisper-fallback
"""

import argparse
import os
import sys
from pathlib import Path

from .config import Config
from .subtitle import fetch_subtitle, fetch_video_info, fetch_subtitle_whisper
from .strategies.base import VideoContext
from .strategies import get_strategy, BUILTIN_STRATEGIES


def _build_context(args) -> VideoContext:
    """Gather video data: info + subtitle."""
    from .subtitle.fetcher import extract_bvid

    # Resolve BV number
    bvid = None
    if args.bvid:
        bvid = extract_bvid(args.bvid)
    elif args.url:
        bvid = extract_bvid(args.url)

    if not bvid:
        print("Error: Could not extract BV number from input.")
        sys.exit(1)

    ctx = VideoContext(
        bvid=bvid,
        url=args.url or f"https://www.bilibili.com/video/{bvid}",
    )

    # Fetch video info
    print(f"📺 Fetching video info: {bvid}")
    info = fetch_video_info(bvid)
    if info:
        ctx.title = info['title']
        ctx.author = info['author']
        ctx.duration = info.get('duration', 0)
        ctx.views = info.get('view', 0)
        ctx.description = info.get('description', '')
        print(f"   Title: {ctx.title}")
        print(f"   Author: {ctx.author}")
    else:
        print("   ⚠️ Could not fetch video info (credentials needed)")

    # Fetch subtitle
    print("📝 Fetching subtitle...")
    sub = fetch_subtitle(bvid)
    if sub:
        ctx.subtitle_text = sub['text']
        ctx.subtitle_lang = sub['lang']
        ctx.subtitle_type = sub['subtitle_type']
        print(f"   Got {sub['subtitle_type']} subtitle ({sub['lang']}), "
              f"{len(sub['text'])} chars")
    elif args.whisper_fallback:
        print("   No API subtitle found. Falling back to Whisper...")
        whisper_sub = fetch_subtitle_whisper(
            bvid,
            model=args.whisper_model or 'medium',
            language=args.whisper_language or 'zh',
            output_dir=args.output or Config.OUTPUT_DIR,
        )
        if whisper_sub:
            ctx.subtitle_text = whisper_sub['text']
            ctx.subtitle_lang = whisper_sub['lang']
            ctx.subtitle_type = whisper_sub['subtitle_type']
            print(f"   Whisper transcription complete, "
                  f"{len(whisper_sub['text'])} chars")
        else:
            print("   ⚠️ Whisper fallback also failed.")
    else:
        print("   ⚠️ No subtitle available. "
              "Use --whisper-fallback for audio transcription.")

    return ctx


def main():
    parser = argparse.ArgumentParser(
        description='Bilibili Video Summarizer — fetch subtitles & generate learning notes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  bilibili-summarize --bvid BV1xx --strategy quick
  bilibili-summarize --url "https://www.bilibili.com/video/BV1xx" --strategy deep
  bilibili-summarize --bvid BV1xx --strategy deep --whisper-fallback
  bilibili-summarize --bvid BV1xx --strategy deep -o ./my_notes

Available strategies: {', '.join(BUILTIN_STRATEGIES.keys())}

To use a custom strategy:
  BILI_SUMMARIZE_STRATEGY=/path/to/my_strategy.py bilibili-summarize --bvid BV1xx --strategy custom

Setup:
  1. Copy .env.example to .env
  2. Fill in Bilibili credentials (BILI_SESSDATA, etc.)
  3. Fill in LLM credentials (LLM_API_KEY, etc.)
        """
    )

    # Input
    parser.add_argument('--bvid', help='Bilibili BV number')
    parser.add_argument('--url', help='Bilibili video URL')

    # Strategy
    parser.add_argument(
        '--strategy', '-s',
        default='quick',
        choices=list(BUILTIN_STRATEGIES.keys()) + ['custom'],
        help='Summarization strategy (default: quick)'
    )

    # Output
    parser.add_argument('--output', '-o', default='', help='Output directory')

    # Whisper fallback
    parser.add_argument(
        '--whisper-fallback',
        action='store_true',
        help='Use Whisper if no API subtitle available'
    )
    parser.add_argument('--whisper-model', default='medium',
                        help='Whisper model size (default: medium)')
    parser.add_argument('--whisper-language', default='zh',
                        help='Audio language for Whisper (default: zh)')

    # LLM override
    parser.add_argument('--model', default='', help='Override LLM model')

    args = parser.parse_args()

    if not args.bvid and not args.url:
        parser.print_help()
        sys.exit(1)

    output_dir = args.output or Config.OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)

    # ---- Gather context ----
    ctx = _build_context(args)

    # ---- Summarize ----
    strategy_name = args.strategy
    print(f"\n🤖 Summarizing with strategy: {strategy_name}")

    strategy = get_strategy(strategy_name)
    if args.model:
        strategy.model = args.model

    result = strategy.summarize(ctx)

    # ---- Save ----
    safe_title = "".join(
        c for c in ctx.title if c.isalnum() or c in ' _-'
    ).rstrip()[:80] or ctx.bvid

    filepath = os.path.join(output_dir, f"{safe_title}.md")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(result.markdown)

    print(f"\n✅ Note saved to: {filepath}")
    print(f"   Characters: {len(result.markdown)}")
    if result.metadata:
        print(f"   Metadata: {result.metadata}")


if __name__ == '__main__':
    main()
