#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站视频字幕获取脚本（公开 API，无需登录）

用法:
  python get_subtitle.py --bvid BV1LUJP6REUf
  python get_subtitle.py --url "https://www.bilibili.com/video/BV1LUJP6REUf"
  python get_subtitle.py --bvid BV1LUJP6REUf -o ./subtitles
"""

import requests
import json
import os
import re
import argparse
import sys


def extract_bvid(input_str):
    """从 B站链接或 BV 号中提取 BV 号"""
    if re.match(r'^BV[0-9A-Za-z]+$', input_str):
        return input_str
    match = re.search(r'(BV[0-9A-Za-z]+)', input_str)
    return match.group(1) if match else None


def create_session():
    """创建请求会话（无需登录 cookie）"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        ),
        'Referer': 'https://www.bilibili.com',
    })
    return session


def get_video_info(session, bvid):
    """获取视频信息（公开接口）"""
    resp = session.get(
        'https://api.bilibili.com/x/web-interface/view',
        params={'bvid': bvid}, timeout=15
    )
    data = resp.json()
    if data.get('code') != 0:
        return None, data.get('message', '未知错误')

    v = data['data']
    return {
        'title': v.get('title', ''),
        'author': v.get('owner', {}).get('name', ''),
        'cid': v.get('cid'),
        'bvid': bvid,
        'duration': v.get('duration', 0),
        'view': v.get('stat', {}).get('view', 0),
    }, None


def get_subtitle_list(session, bvid, cid):
    """获取字幕列表（公开接口）"""
    resp = session.get(
        'https://api.bilibili.com/x/player/v2',
        params={'bvid': bvid, 'cid': cid}, timeout=15
    )
    data = resp.json()
    if data.get('code') != 0:
        return None, data.get('message', '未知错误')

    return data.get('data', {}).get('subtitle', {}).get('subtitles', []), None


def select_best_subtitle(subtitles):
    """选择最佳字幕：中文人工 > 中文AI > 英文 > 其他"""
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
        lang = sub.get('lan_doc', '未知')
        pri = lang_priority.get(lang, 999)
        if sub.get('type', 0) == 0:  # 人工字幕
            pri -= 0.5
        scored.append((pri, sub))

    scored.sort(key=lambda x: x[0])
    return scored[0][1]


def download_subtitle(session, subtitle_url):
    """下载字幕 JSON 并转为纯文本"""
    if subtitle_url.startswith('//'):
        subtitle_url = 'https:' + subtitle_url

    resp = session.get(subtitle_url, timeout=15)
    if resp.status_code != 200:
        return None

    body = resp.json().get('body', [])
    lines = [item['content'] for item in body if item.get('content')]
    return '\n'.join(lines)


def save_subtitle(bvid, text, lang, output_dir='subtitles'):
    """保存字幕到文件"""
    os.makedirs(output_dir, exist_ok=True)
    safe_lang = re.sub(r'[^\w\- ]', '', lang).strip()
    filepath = os.path.join(output_dir, f'{bvid}_{safe_lang}.txt')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(text)
    return filepath


def main():
    parser = argparse.ArgumentParser(
        description='B站视频字幕获取工具（无需登录）')
    parser.add_argument('--bvid', type=str, help='视频 BV 号')
    parser.add_argument('--url', type=str, help='视频 URL')
    parser.add_argument('-o', '--output', type=str, default='subtitles',
                        help='输出目录（默认 subtitles/）')
    args = parser.parse_args()

    # 解析 BV 号
    bvid = None
    if args.bvid:
        bvid = extract_bvid(args.bvid)
    elif args.url:
        bvid = extract_bvid(args.url)

    if not bvid:
        print('错误：请通过 --bvid 或 --url 提供视频 BV 号')
        sys.exit(1)

    session = create_session()

    # Step 1: 获取视频信息
    print(f'正在获取视频信息: {bvid}')
    video_info, err = get_video_info(session, bvid)
    if not video_info:
        print(f'获取视频信息失败: {err}')
        sys.exit(1)

    print(f'标题: {video_info["title"]}')
    print(f'作者: {video_info["author"]}')
    print(f'播放量: {video_info["view"]}')

    # Step 2: 获取字幕列表
    print('正在获取字幕列表...')
    subtitles, err = get_subtitle_list(session, bvid, video_info['cid'])

    if not subtitles:
        print(f'该视频没有可用字幕')
        sys.exit(0)

    print(f'找到 {len(subtitles)} 个字幕:')
    for i, sub in enumerate(subtitles):
        lang = sub.get('lan_doc', '未知')
        stype = '人工' if sub.get('type', 0) == 0 else 'AI'
        print(f'  {i+1}. {lang} ({stype})')

    # Step 3: 下载最佳字幕
    best = select_best_subtitle(subtitles)
    lang = best.get('lan_doc', '未知')
    print(f'\n正在下载: {lang}')

    text = download_subtitle(session, best.get('subtitle_url', ''))
    if not text:
        print('字幕下载失败')
        sys.exit(1)

    # 保存并输出
    filepath = save_subtitle(bvid, text, lang, args.output)
    print(f'\n字幕已保存: {filepath}')
    print(f'\n{"="*50}')
    print(f'字幕内容（共 {len(text)} 字符）:')
    print(f'{"="*50}')
    print(text)


if __name__ == '__main__':
    main()
