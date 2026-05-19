#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from datetime import timedelta

from faster_whisper import WhisperModel


def check_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg が見つかりません。sudo apt install ffmpeg を実行してください。")


def run_ffmpeg(input_path: Path, audio_path: Path) -> None:
    audio_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(input_path),
        "-map", "0:a:0",
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-c:a", "pcm_s16le",
        str(audio_path),
    ]

    subprocess.run(cmd, check=True)


def fmt_ts_srt(seconds: float) -> str:
    td = timedelta(seconds=max(seconds, 0))
    total_ms = int(td.total_seconds() * 1000)
    h = total_ms // 3_600_000
    m = (total_ms % 3_600_000) // 60_000
    s = (total_ms % 60_000) // 1000
    ms = total_ms % 1000
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def fmt_ts_vtt(seconds: float) -> str:
    return fmt_ts_srt(seconds).replace(",", ".")


def write_outputs(
    segments_data: list[dict],
    info,
    out_dir: Path,
    base: str,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    txt_path = out_dir / f"{base}.txt"
    md_path = out_dir / f"{base}.md"
    srt_path = out_dir / f"{base}.srt"
    vtt_path = out_dir / f"{base}.vtt"
    json_path = out_dir / f"{base}.json"

    # txt
    txt_path.write_text(
        "\n".join(s["text"].strip() for s in segments_data),
        encoding="utf-8",
    )

    # md
    md_lines = [
        f"# Transcript: {base}",
        "",
        f"- language: {info.language}",
        f"- language_probability: {info.language_probability:.3f}",
        "",
        "## Transcript",
        "",
    ]

    for s in segments_data:
        md_lines.append(
            f"- [{fmt_ts_vtt(s['start'])} - {fmt_ts_vtt(s['end'])}] {s['text'].strip()}"
        )

    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    # srt
    srt_blocks = []
    for i, s in enumerate(segments_data, start=1):
        srt_blocks.append(
            f"{i}\n"
            f"{fmt_ts_srt(s['start'])} --> {fmt_ts_srt(s['end'])}\n"
            f"{s['text'].strip()}\n"
        )
    srt_path.write_text("\n".join(srt_blocks), encoding="utf-8")

    # vtt
    vtt_lines = ["WEBVTT", ""]
    for s in segments_data:
        vtt_lines.append(
            f"{fmt_ts_vtt(s['start'])} --> {fmt_ts_vtt(s['end'])}\n"
            f"{s['text'].strip()}\n"
        )
    vtt_path.write_text("\n".join(vtt_lines), encoding="utf-8")

    # json
    payload = {
        "language": info.language,
        "language_probability": info.language_probability,
        "segments": segments_data,
    }
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("出力完了:")
    print(f"- {txt_path}")
    print(f"- {md_path}")
    print(f"- {srt_path}")
    print(f"- {vtt_path}")
    print(f"- {json_path}")


def transcribe(
    audio_path: Path,
    model_name: str,
    device: str,
    compute_type: str,
    language: str | None,
    beam_size: int,
    vad_filter: bool,
) -> tuple[list[dict], object]:
    model = WhisperModel(
        model_name,
        device=device,
        compute_type=compute_type,
    )

    segments, info = model.transcribe(
        str(audio_path),
        language=language,
        task="transcribe",
        beam_size=beam_size,
        vad_filter=vad_filter,
        vad_parameters={
            "min_silence_duration_ms": 500,
        },
        condition_on_previous_text=False,
    )

    # faster-whisper の segments は generator なので、iterate した時点で実処理される。
    # 公式PyPIにもこの点の注意あり。 
    segments_data = []
    for seg in segments:
        text = seg.text.strip()
        if not text:
            continue

        print(f"[{fmt_ts_vtt(seg.start)} - {fmt_ts_vtt(seg.end)}] {text}")

        segments_data.append(
            {
                "start": seg.start,
                "end": seg.end,
                "text": text,
            }
        )

    return segments_data, info


def main() -> None:
    parser = argparse.ArgumentParser(
        description="OBS .mkv を ffmpeg で音声化し、faster-whisper で文字起こしする"
    )

    parser.add_argument("input", type=Path, help="入力動画ファイル。例: meeting.mkv")
    parser.add_argument("--out-dir", type=Path, default=Path("output"))
    parser.add_argument("--work-dir", type=Path, default=Path("work_audio"))

    parser.add_argument("--model", default="medium", help="例: small, medium, large-v3")
    parser.add_argument("--language", default="ja", help="日本語なら ja。自動判定なら none")
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    parser.add_argument("--compute-type", default="int8", help="CPUなら int8、GPUなら float16 等")
    parser.add_argument("--beam-size", type=int, default=5)
    parser.add_argument("--no-vad", action="store_true", help="VADを無効化")

    args = parser.parse_args()

    input_path = args.input.expanduser().resolve()
    if not input_path.exists():
        raise FileNotFoundError(input_path)

    check_ffmpeg()

    base = input_path.stem
    audio_path = args.work_dir / f"{base}_16k_mono.wav"

    language = None if args.language.lower() == "none" else args.language

    print("音声抽出中...")
    run_ffmpeg(input_path, audio_path)

    print("文字起こし中...")
    segments_data, info = transcribe(
        audio_path=audio_path,
        model_name=args.model,
        device=args.device,
        compute_type=args.compute_type,
        language=language,
        beam_size=args.beam_size,
        vad_filter=not args.no_vad,
    )

    write_outputs(
        segments_data=segments_data,
        info=info,
        out_dir=args.out_dir,
        base=base,
    )


if __name__ == "__main__":
    main()
