"""
Whisper-based fallback subtitle fetcher.

When a Bilibili video has no subtitles via the API, this module:
  1. Downloads the audio stream via Bilibili API
  2. Transcribes it with faster-whisper (local model)

Requires: pip install faster-whisper yt-dlp
"""

import os
import sys
import time
from pathlib import Path


def _download_audio(bvid: str, output_path: str, sessdata: str) -> str:
    """Download audio stream from Bilibili via API. Returns video title."""
    import requests

    session = requests.Session()
    session.headers.update({
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36'
        ),
        'Referer': 'https://www.bilibili.com',
    })
    session.cookies.set('SESSDATA', sessdata)

    # Get video info
    resp = session.get(
        'https://api.bilibili.com/x/web-interface/view',
        params={'bvid': bvid}, timeout=15
    )
    data = resp.json()
    if data['code'] != 0:
        raise RuntimeError(f"Failed to get video info: {data['message']}")

    title = data['data']['title']
    cid = data['data']['cid']

    # Get play URL
    resp = session.get(
        'https://api.bilibili.com/x/player/playurl',
        params={'bvid': bvid, 'cid': cid, 'fnval': 16, 'fourk': 1},
        timeout=15
    )
    data = resp.json()

    audio_streams = data.get('data', {}).get('dash', {}).get('audio', [])
    if not audio_streams:
        raise RuntimeError("No audio streams found")

    audio_url = audio_streams[0].get('baseUrl') or audio_streams[0].get('base_url', '')
    if not audio_url:
        raise RuntimeError("Audio URL is empty")

    bw = audio_streams[0].get('bandwidth', 0) // 1000
    print(f"  Downloading audio (~{bw}kbps)...")
    resp = session.get(
        audio_url,
        headers={'Referer': 'https://www.bilibili.com'},
        timeout=120
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'wb') as f:
        f.write(resp.content)

    size_mb = len(resp.content) / 1024 / 1024
    print(f"  Saved: {output_path} ({size_mb:.1f} MB)")
    return title


def _transcribe(audio_path: str, model_size: str = 'medium',
                language: str = 'zh', output_dir: str = 'subtitles') -> str:
    """Transcribe audio with faster-whisper. Returns plain text."""
    from faster_whisper import WhisperModel

    print(f"  Loading Whisper model '{model_size}' (first run downloads)...")
    t0 = time.time()
    model = WhisperModel(model_size, device='cuda', compute_type='int8')
    print(f"  Model loaded ({time.time() - t0:.1f}s)")

    print("  Transcribing...")
    t0 = time.time()
    segments, info = model.transcribe(
        audio_path,
        language=language,
        beam_size=5,
        initial_prompt=(
            "以下是普通话的句子。" if language == 'zh' else ""
        ),
        vad_filter=True,
    )
    print(f"  Detected language: {info.language} "
          f"(probability={info.language_probability:.2f})")

    plain_lines = []
    ts_lines = []
    for seg in segments:
        text = seg.text.strip()
        if not text:
            continue
        plain_lines.append(text)
        ts_lines.append(f"[{seg.start:.1f}s - {seg.end:.1f}s] {text}")

    elapsed = time.time() - t0
    speed = info.duration / elapsed if elapsed > 0 else 0
    print(f"  Transcription complete! {elapsed:.1f}s "
          f"(audio {info.duration:.0f}s, {speed:.1f}x realtime)")

    # Save
    os.makedirs(output_dir, exist_ok=True)
    bvid = Path(audio_path).stem
    plain_path = os.path.join(output_dir, f"{bvid}.txt")
    ts_path = os.path.join(output_dir, f"{bvid}_timestamp.txt")

    with open(plain_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(plain_lines))
    with open(ts_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(ts_lines))

    print(f"  Plain text saved: {plain_path}")
    print(f"  Timestamped saved: {ts_path}")
    return '\n'.join(plain_lines)


def fetch_subtitle_whisper(
    bvid: str,
    model: str = 'medium',
    language: str = 'zh',
    output_dir: str = 'subtitles',
    sessdata: str = "",
) -> dict | None:
    """
    Fetch subtitles by downloading audio and transcribing with Whisper.

    Args:
        bvid: Bilibili BV number.
        model: Whisper model size (tiny/base/small/medium/large-v3/large-v3-turbo).
        language: Audio language code (zh, en, ja, etc.).
        output_dir: Where to save audio and transcript files.
        sessdata: Override Bilibili SESSDATA cookie.

    Returns:
        dict with keys: text, lang, subtitle_type='whisper', bvid
        None if transcription fails.
    """
    from ..config import Config

    sessdata = sessdata or Config.BILI_SESSDATA

    if not sessdata:
        print("Warning: No Bilibili SESSDATA set. Whisper fallback may not work "
              "without audio download.")
        # Fall through — user might provide --audio-file separately

    os.makedirs(output_dir, exist_ok=True)
    audio_path = os.path.join(output_dir, f"{bvid}.m4a")

    try:
        if not os.path.exists(audio_path):
            title = _download_audio(bvid, audio_path, sessdata)
        else:
            print(f"  Audio already cached: {audio_path}")
            title = ""
    except Exception as e:
        print(f"  API download failed: {e}")
        print("  Trying yt-dlp fallback...")
        import subprocess
        result = subprocess.run([
            'yt-dlp', '-f', 'bestaudio',
            '-o', audio_path,
            '--cookies-from-browser', 'chrome',
            f'https://www.bilibili.com/video/{bvid}'
        ], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  yt-dlp also failed: {result.stderr}")
            return None
        title = ""

    try:
        text = _transcribe(audio_path, model, language, output_dir)
        return {
            'text': text,
            'lang': language,
            'subtitle_type': 'whisper',
            'bvid': bvid,
            'model': model,
        }
    except Exception as e:
        print(f"  Transcription failed: {e}")
        return None
