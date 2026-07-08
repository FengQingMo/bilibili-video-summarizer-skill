#!/usr/bin/env python3
"""
B站视频字幕获取 — Whisper 语音识别降级方案

当 B站 API 没有可用字幕时，下载音频并用本地 Whisper 模型转录。
需要额外依赖: pip install faster-whisper yt-dlp

用法:
  python get_subtitle_fallback.py --bvid BV1pt7h6TEA6
  python get_subtitle_fallback.py --bvid BV1pt7h6TEA6 --model medium
  python get_subtitle_fallback.py --bvid BV1pt7h6TEA6 --model small -o ./subs
  python get_subtitle_fallback.py --bvid BV1pt7h6TEA6 --prepare-only  # 只下载音频
"""

import os
import sys
import re
import time
import argparse
from pathlib import Path

# 模型缓存目录：skill 目录下的 models/
SKILL_DIR = Path(__file__).resolve().parent.parent
os.environ['HF_HUB_CACHE'] = str(SKILL_DIR / 'models')
# 国内用户可选 HF 镜像加速
os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')


def download_audio(bvid, output_path):
    """通过 B站 API 下载音频流"""
    import requests

    session = requests.Session()
    session.headers.update({
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        ),
        'Referer': 'https://www.bilibili.com',
    })

    # 获取视频信息
    resp = session.get(
        'https://api.bilibili.com/x/web-interface/view',
        params={'bvid': bvid}, timeout=15
    )
    data = resp.json()
    if data['code'] != 0:
        raise RuntimeError(f'获取视频信息失败: {data["message"]}')

    title = data['data']['title']
    cid = data['data']['cid']
    print(f'标题: {title}')

    # 获取播放地址
    resp = session.get(
        'https://api.bilibili.com/x/player/playurl',
        params={'bvid': bvid, 'cid': cid, 'fnval': 16, 'fourk': 1},
        timeout=15
    )
    data = resp.json()

    audio_streams = data.get('data', {}).get('dash', {}).get('audio', [])
    if not audio_streams:
        raise RuntimeError('未找到音频流')

    audio_url = audio_streams[0].get('baseUrl') or audio_streams[0].get('base_url', '')
    if not audio_url:
        raise RuntimeError('音频 URL 为空')

    bw = audio_streams[0].get('bandwidth', 0) // 1000
    print(f'下载音频 (~{bw}kbps)...')
    resp = session.get(
        audio_url,
        headers={'Referer': 'https://www.bilibili.com'},
        timeout=300
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'wb') as f:
        f.write(resp.content)

    size_mb = len(resp.content) / 1024 / 1024
    print(f'已保存: {output_path} ({size_mb:.1f} MB)')
    return title


def transcribe(audio_path, model_size='medium', language='zh', output_dir='subtitles'):
    """用 faster-whisper 转录音频"""
    from faster_whisper import WhisperModel

    print(f"加载 Whisper 模型 '{model_size}'（首次需下载，后续缓存复用）...")
    t0 = time.time()
    model = WhisperModel(model_size, device='cuda', compute_type='int8')
    print(f'模型加载完成 ({time.time()-t0:.1f}s)')

    print('正在转录...')
    t0 = time.time()
    segments, info = model.transcribe(
        audio_path,
        language=language,
        beam_size=5,
        initial_prompt='以下是普通话的句子。' if language == 'zh' else '',
        vad_filter=True,
    )
    print(f'检测语言: {info.language} (概率={info.language_probability:.2f})')

    plain_lines = []
    ts_lines = []
    for seg in segments:
        text = seg.text.strip()
        if not text:
            continue
        plain_lines.append(text)
        ts_lines.append(f'[{seg.start:.1f}s - {seg.end:.1f}s] {text}')
        print(f'  [{seg.start:6.1f}s -> {seg.end:6.1f}s] {text}', flush=True)

    elapsed = time.time() - t0
    speed = info.duration / elapsed if elapsed > 0 else 0
    print(f'转录完成! 耗时 {elapsed:.1f}s '
          f'(音频 {info.duration:.0f}s, {speed:.1f}x 实时)')

    # 保存
    os.makedirs(output_dir, exist_ok=True)
    bvid = Path(audio_path).stem
    plain_path = os.path.join(output_dir, f'{bvid}.txt')
    ts_path = os.path.join(output_dir, f'{bvid}_timestamp.txt')

    with open(plain_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(plain_lines))
    with open(ts_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(ts_lines))

    print(f'纯文本: {plain_path}')
    print(f'时间戳: {ts_path}')
    return '\n'.join(plain_lines)


def main():
    parser = argparse.ArgumentParser(
        description='B站视频字幕获取 — Whisper 语音识别降级',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --bvid BV1pt7h6TEA6
  %(prog)s --bvid BV1pt7h6TEA6 --model small
  %(prog)s --bvid BV1pt7h6TEA6 --model medium -o my_subs
  %(prog)s --bvid BV1pt7h6TEA6 --prepare-only  # 只下载不转录
        """
    )
    parser.add_argument('--bvid', required=True, help='视频 BV 号')
    parser.add_argument('--model', default='medium',
                        choices=['tiny', 'base', 'small', 'medium',
                                 'large-v3', 'large-v3-turbo'],
                        help='Whisper 模型大小（默认 medium）')
    parser.add_argument('--language', default='zh', help='音频语言（默认 zh）')
    parser.add_argument('-o', '--output', default='subtitles', help='输出目录')
    parser.add_argument('--cpu', action='store_true', help='强制使用 CPU')
    parser.add_argument('--prepare-only', action='store_true',
                        help='只下载音频，不转录')
    parser.add_argument('--audio-file', help='直接转录已有音频文件（跳过下载）')

    args = parser.parse_args()
    bvid = args.bvid

    if args.audio_file:
        audio_path = args.audio_file
        if not os.path.exists(audio_path):
            print(f'错误: 文件不存在: {audio_path}')
            sys.exit(1)
    else:
        os.makedirs(args.output, exist_ok=True)
        audio_path = os.path.join(args.output, f'{bvid}.m4a')

        if os.path.exists(audio_path):
            print(f'音频已缓存，跳过下载: {audio_path}')
        else:
            try:
                download_audio(bvid, audio_path)
            except Exception as e:
                print(f'API 下载失败: {e}')
                print('尝试 yt-dlp 降级...')
                import subprocess
                result = subprocess.run([
                    'yt-dlp', '-f', 'bestaudio',
                    '-o', audio_path,
                    '--cookies-from-browser', 'chrome',
                    f'https://www.bilibili.com/video/{bvid}'
                ], capture_output=True, text=True)
                if result.returncode != 0:
                    print(f'yt-dlp 也失败了: {result.stderr}')
                    sys.exit(1)

    if args.prepare_only:
        print(f'音频已就绪: {audio_path}')
        return

    try:
        text = transcribe(audio_path, args.model, args.language, args.output)
        print(f'\n{"="*50}')
        print(f'字幕全文（共 {len(text)} 字符）:')
        print(f'{"="*50}')
        print(text)
    except Exception as e:
        print(f'转录失败: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
