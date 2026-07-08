"""
Bilibili API subtitle fetcher.

Fetches subtitles via the official Bilibili API. Requires login credentials.
Supports BV numbers, full URLs, and automatic language selection.
"""

import re
import os
import sys

import requests


def extract_bvid(input_str: str) -> str | None:
    """Extract BV number from various Bilibili URL formats."""
    if re.match(r'^BV[0-9A-Za-z]+$', input_str):
        return input_str
    match = re.search(r'(BV[0-9A-Za-z]+)', input_str)
    return match.group(1) if match else None


def _create_session(sessdata: str, bili_jct: str, dede_user_id: str) -> requests.Session:
    """Create a requests session with Bilibili login cookies."""
    session = requests.Session()
    session.headers.update({
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        ),
        'Referer': 'https://www.bilibili.com',
        'Origin': 'https://www.bilibili.com',
    })
    session.cookies.set('SESSDATA', sessdata)
    session.cookies.set('bili_jct', bili_jct)
    session.cookies.set('DedeUserID', dede_user_id)
    return session


def fetch_video_info(bvid: str, sessdata: str = "", bili_jct: str = "",
                     dede_user_id: str = "") -> dict | None:
    """
    Fetch video metadata: title, author, CID, duration, views.

    Returns a dict, or None if the request fails.
    """
    from ..config import Config

    sessdata = sessdata or Config.BILI_SESSDATA
    bili_jct = bili_jct or Config.BILI_JCT
    dede_user_id = dede_user_id or Config.BILI_DEDE_USER_ID

    session = _create_session(sessdata, bili_jct, dede_user_id)
    resp = session.get(
        "https://api.bilibili.com/x/web-interface/view",
        params={'bvid': bvid}, timeout=15
    )
    data = resp.json()
    if data.get('code') != 0:
        return None

    video = data['data']
    return {
        'title': video.get('title', ''),
        'author': video.get('owner', {}).get('name', ''),
        'cid': video.get('cid'),
        'bvid': bvid,
        'duration': video.get('duration', 0),
        'view': video.get('stat', {}).get('view', 0),
        'description': video.get('desc', ''),
    }


def _select_best_subtitle(subtitles: list) -> dict | None:
    """
    Choose the best subtitle by language priority:
    Chinese human > Chinese AI > English > Japanese > Other.
    """
    if not subtitles:
        return None

    lang_priority = {
        '中文': 1, '中文（中国）': 1, '中文（简体）': 1, '中文（繁體）': 1,
        'Chinese': 1, 'Chinese (China)': 1,
        'Chinese (Simplified)': 1, 'Chinese (Traditional)': 1,
        'English': 2, '英文': 2,
        '日本語': 3, '日语': 3, 'Japanese': 3,
    }

    scored = []
    for sub in subtitles:
        lang = sub.get('lan_doc', 'Unknown')
        pri = lang_priority.get(lang, 999)
        if sub.get('type', 0) == 0:  # Human subtitle
            pri -= 0.5
        scored.append((pri, sub))

    scored.sort(key=lambda x: x[0])
    return scored[0][1]


def _download_subtitle_text(session: requests.Session, subtitle_url: str) -> str | None:
    """Download subtitle JSON and return plain text content."""
    if subtitle_url.startswith('//'):
        subtitle_url = 'https:' + subtitle_url

    resp = session.get(subtitle_url, timeout=15)
    if resp.status_code != 200:
        return None

    body = resp.json().get('body', [])
    lines = [item['content'] for item in body if item.get('content')]
    return '\n'.join(lines)


def fetch_subtitle(bvid: str, sessdata: str = "", bili_jct: str = "",
                   dede_user_id: str = "") -> dict | None:
    """
    Fetch the best available subtitle for a Bilibili video.

    Args:
        bvid: Bilibili BV number.
        sessdata, bili_jct, dede_user_id: Override credentials from config.

    Returns:
        dict with keys: text, lang, subtitle_type (human/ai), bvid
        None if no subtitle is available or request fails.
    """
    from ..config import Config

    sessdata = sessdata or Config.BILI_SESSDATA
    bili_jct = bili_jct or Config.BILI_JCT
    dede_user_id = dede_user_id or Config.BILI_DEDE_USER_ID

    session = _create_session(sessdata, bili_jct, dede_user_id)

    # 1. Get video info (for CID)
    info = fetch_video_info(bvid, sessdata, bili_jct, dede_user_id)
    if not info:
        return None

    # 2. Get subtitle list
    resp = session.get(
        "https://api.bilibili.com/x/player/v2",
        params={'bvid': bvid, 'cid': info['cid']}, timeout=15
    )
    data = resp.json()
    if data.get('code') != 0:
        return None

    subtitles = data.get('data', {}).get('subtitle', {}).get('subtitles', [])
    if not subtitles:
        return None

    # 3. Pick best and download
    best = _select_best_subtitle(subtitles)
    if not best:
        return None

    text = _download_subtitle_text(session, best.get('subtitle_url', ''))
    if not text:
        return None

    return {
        'text': text,
        'lang': best.get('lan_doc', 'Unknown'),
        'subtitle_type': 'human' if best.get('type', 0) == 0 else 'ai',
        'bvid': bvid,
    }
