#!/usr/bin/env python3
"""
Re-encode a voiceover pack's .ogg files smaller, with ffmpeg.

Default: mono, 22050 Hz, Vorbis quality 0.5 - the same format as the English pack.
TTS voices (e.g. XTTS-v2, which generates 24 kHz audio) have practically nothing
above 11 kHz, so 44.1 kHz files lose nothing audible and shrink to roughly half.

Each file is encoded to a temporary file and checked: it must decode, keep its
duration and actually be smaller. Only then does it replace the original (or get
written to --output). Files already at or below the target sample rate are skipped,
so the script is safe to re-run.

Requires ffmpeg (with libvorbis) on PATH, e.g. `winget install ffmpeg`.

Usage:
    uv run compress_voiceovers.py ChattyLittleNpc_Vanilla_deDE_voiceovers --output ../compressed_test --limit 50
    uv run compress_voiceovers.py ChattyLittleNpc_Vanilla_deDE_voiceovers --in-place
    uv run generate_voiceovers_list.py ChattyLittleNpc_Vanilla_deDE_voiceovers   # durations change slightly
"""

import argparse
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from mutagen.oggvorbis import OggVorbis

# Allowed duration difference between original and re-encoded file, in seconds.
DURATION_TOLERANCE = 0.1


def encode(src, dst, sample_rate, quality):
    """Encode src to dst with ffmpeg. Returns an error message, or None on success."""
    cmd = ['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', src,
           '-map_metadata', '-1', '-vn', '-ac', '1', '-ar', str(sample_rate),
           '-c:a', 'libvorbis', '-q:a', str(quality), '-f', 'ogg', dst]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if result.returncode != 0:
        return result.stderr.strip() or f"ffmpeg exited with {result.returncode}"
    return None


def process(src, dst, sample_rate, quality):
    """Compress one file. Returns (status, bytes_before, bytes_after, message); never raises OSError."""
    try:
        before = os.path.getsize(src)
    except OSError as e:
        return 'error', 0, 0, str(e)
    try:
        return _process(src, dst, sample_rate, quality, before)
    except OSError as e:
        # e.g. the file is locked by WoW or a virus scanner; the original is left as it was
        return 'error', before, before, str(e)


def _process(src, dst, sample_rate, quality, before):
    try:
        info = OggVorbis(src).info
    except Exception as e:
        return 'error', before, before, f"cannot read: {e}"

    if info.sample_rate <= sample_rate:
        if dst != src:
            shutil.copy2(src, dst)
        return 'skipped', before, before, None

    tmp = dst + '.tmp'
    try:
        error = encode(src, tmp, sample_rate, quality)
        if error:
            return 'error', before, before, error
        try:
            new_length = OggVorbis(tmp).info.length
        except Exception as e:
            return 'error', before, before, f"re-encoded file unreadable: {e}"
        if abs(new_length - info.length) > DURATION_TOLERANCE:
            return 'error', before, before, f"duration changed {info.length:.2f}s -> {new_length:.2f}s"
        after = os.path.getsize(tmp)
        if after >= before:
            if dst != src:
                shutil.copy2(src, dst)
            return 'skipped', before, before, None
        os.replace(tmp, dst)
        return 'compressed', before, after, None
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def main():
    parser = argparse.ArgumentParser(description="Re-encode a voiceover pack's .ogg files smaller")
    parser.add_argument('pack', help='Addon folder, e.g. ChattyLittleNpc_Vanilla_deDE_voiceovers')
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument('--in-place', action='store_true', help='Replace the original files')
    target.add_argument('--output', metavar='DIR', help='Write the compressed files to DIR instead')
    parser.add_argument('--sample-rate', type=int, default=22050, help='Target sample rate in Hz (default 22050)')
    parser.add_argument('--quality', type=float, default=0.5,
                        help='Vorbis quality, -1 (smallest) to 10 (best); default 0.5')
    parser.add_argument('--limit', type=int, help='Only process the first N files (for trying settings out)')
    parser.add_argument('--jobs', type=int, default=os.cpu_count() or 4, help='Parallel ffmpeg processes')
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error('--limit must be at least 1')

    if not shutil.which('ffmpeg'):
        print("Error: ffmpeg not found on PATH. Install it, e.g. `winget install ffmpeg`.")
        sys.exit(1)

    src_dir = os.path.join(args.pack, 'voiceovers')
    if not os.path.isdir(src_dir):
        print(f"Error: {src_dir} not found")
        sys.exit(1)
    dst_dir = src_dir if args.in_place else args.output
    os.makedirs(dst_dir, exist_ok=True)

    files = sorted(f for f in os.listdir(src_dir) if f.lower().endswith('.ogg'))
    if args.limit is not None:
        files = files[:args.limit]
    print(f"{len(files)} files in {src_dir} -> {dst_dir} "
          f"(mono, {args.sample_rate} Hz, Vorbis q{args.quality}, {args.jobs} jobs)")

    counts = {'compressed': 0, 'skipped': 0, 'error': 0}
    total_before = total_after = 0
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = {pool.submit(process, os.path.join(src_dir, f), os.path.join(dst_dir, f),
                               args.sample_rate, args.quality): f for f in files}
        for done, future in enumerate(as_completed(futures), start=1):
            status, before, after, message = future.result()
            counts[status] += 1
            total_before += before
            total_after += after
            if message:
                print(f"  {futures[future]}: {message}")
            if done % 500 == 0 or done == len(files):
                print(f"  {done}/{len(files)}  {total_before / 1e6:.0f} MB -> {total_after / 1e6:.0f} MB")

    ratio = total_before / total_after if total_after else 0
    print(f"\nCompressed {counts['compressed']}, skipped {counts['skipped']} (already small enough), "
          f"failed {counts['error']}.")
    print(f"Total: {total_before / 1e6:.1f} MB -> {total_after / 1e6:.1f} MB ({ratio:.2f}x smaller)")
    if counts['error']:
        print("Failed files were left unchanged.")
    if args.in_place and counts['compressed']:
        print(f"\nDurations changed slightly. Regenerate the list:\n"
              f"  uv run generate_voiceovers_list.py {args.pack}")
    sys.exit(1 if counts['error'] else 0)


if __name__ == '__main__':
    main()
