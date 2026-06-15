from __future__ import annotations

import argparse
import importlib.util
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
SLIDE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".wma"}
PDF_EXTENSIONS = {".pdf"}
TEMP_DIR = PROJECT_ROOT / "temp"


def natural_key(path: Path) -> list[object]:
    parts = re.split(r"(\d+)", path.stem.lower())
    return [int(part) if part.isdigit() else part for part in parts]


def enable_packaged_ffmpeg() -> None:
    if shutil.which("ffmpeg"):
        return

    try:
        import imageio_ffmpeg
    except ImportError:
        return

    ffmpeg_path = Path(imageio_ffmpeg.get_ffmpeg_exe()).resolve()
    bin_dir = TEMP_DIR / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    local_ffmpeg = bin_dir / "ffmpeg.exe"
    if not local_ffmpeg.exists():
        shutil.copy2(ffmpeg_path, local_ffmpeg)
    os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")


def require_ffmpeg() -> None:
    if shutil.which("ffmpeg"):
        return
    raise SystemExit(
        "FFmpeg was not found. Install dependencies with: pip install -r requirements.txt"
    )


def run(command: list[str]) -> None:
    print(">", " ".join(command))
    completed = subprocess.run(command, check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def collect_files(directory: Path, extensions: set[str] | None = None) -> list[Path]:
    if not directory.exists():
        raise SystemExit(f"Directory not found: {directory}")

    files = [path for path in directory.iterdir() if path.is_file()]
    if extensions is not None:
        files = [path for path in files if path.suffix.lower() in extensions]
    return sorted(files, key=natural_key)


def require_python_module(name: str, install_hint: str) -> None:
    if importlib.util.find_spec(name):
        return
    raise SystemExit(f"Missing required Python module: {name}\n{install_hint}")


def render_pdf_to_slides(pdf_path: Path, output_dir: Path, dpi: int) -> list[Path]:
    require_python_module(
        "fitz",
        "Install dependencies with: pip install -r requirements.txt",
    )
    import fitz

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    document = fitz.open(pdf_path)
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    rendered: list[Path] = []

    for page_index in range(document.page_count):
        page = document.load_page(page_index)
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        slide_path = output_dir / f"{page_index + 1:02d}.png"
        pixmap.save(slide_path)
        rendered.append(slide_path)

    document.close()
    return rendered


def resolve_slides(args: argparse.Namespace) -> tuple[list[Path], Path | None]:
    slides_dir = args.slides_dir.resolve()
    render_dir = TEMP_DIR / "pdf_slides"

    if args.pdf:
        pdf_path = args.pdf.resolve()
        if not pdf_path.exists():
            raise SystemExit(f"PDF not found: {pdf_path}")
        return render_pdf_to_slides(pdf_path, render_dir, args.pdf_dpi), render_dir

    slides = collect_files(slides_dir, SLIDE_EXTENSIONS)
    if slides:
        return slides, None

    pdfs = collect_files(slides_dir, PDF_EXTENSIONS)
    if len(pdfs) == 1:
        return render_pdf_to_slides(pdfs[0], render_dir, args.pdf_dpi), render_dir
    if len(pdfs) > 1:
        raise SystemExit(
            f"Found multiple PDFs in {slides_dir}. Use --pdf to choose one explicitly."
        )

    raise SystemExit(f"No slide images or PDF found in: {slides_dir}")


def escape_srt_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def format_srt_time(seconds: float) -> str:
    milliseconds = int(round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def get_media_duration(path: Path) -> float:
    completed = subprocess.run(
        ["ffmpeg", "-i", str(path)],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    output = completed.stderr + completed.stdout
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", output)
    if not match:
        raise SystemExit(f"Could not read media duration: {path}")
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def chunk_script_text(text: str, max_words: int = 16) -> list[str]:
    normalized = " ".join(text.split())
    if not normalized:
        return [" "]

    sentence_parts = re.split(r"(?<=[.!?])\s+", normalized)
    chunks: list[str] = []
    for sentence in sentence_parts:
        words = sentence.split()
        current: list[str] = []
        for word in words:
            current.append(word)
            if len(current) >= max_words:
                chunks.append(" ".join(current))
                current = []
        if current:
            chunks.append(" ".join(current))
    return chunks or [" "]


def write_segment_srt(
    script_path: Path,
    srt_path: Path,
    duration: float,
    subtitle_offset: float,
) -> None:
    text = escape_srt_text(script_path.read_text(encoding="utf-8"))
    chunks = chunk_script_text(text)
    seconds_per_chunk = max(duration / len(chunks), 1.0)
    entries: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        start = max(0.0, (index - 1) * seconds_per_chunk + subtitle_offset)
        end = duration if index == len(chunks) else index * seconds_per_chunk
        end = min(duration, max(start + 0.25, end + subtitle_offset))
        entries.append(
            f"{index}\n{format_srt_time(start)} --> {format_srt_time(end)}\n{chunk}\n"
        )
    srt_path.write_text("\n".join(entries), encoding="utf-8")


def parse_srt_timings(srt_path: Path) -> list[tuple[str, str]]:
    text = srt_path.read_text(encoding="utf-8", errors="replace")
    timings: list[tuple[str, str]] = []
    for line in text.splitlines():
        if " --> " in line:
            start, end = line.split(" --> ", 1)
            timings.append((start.strip(), end.strip()))
    return timings


def chunk_script_by_count(text: str, count: int) -> list[str]:
    words = " ".join(text.split()).split()
    if not words:
        return [" "] * count
    if count <= 1:
        return [" ".join(words)]

    chunks: list[str] = []
    for index in range(count):
        start = round(index * len(words) / count)
        end = round((index + 1) * len(words) / count)
        chunk = " ".join(words[start:end]).strip()
        chunks.append(chunk or " ")
    return chunks


def write_aligned_script_srt(script_path: Path, timing_srt: Path, output_srt: Path) -> None:
    timings = parse_srt_timings(timing_srt)
    if not timings:
        raise SystemExit(f"No timings found in Whisper SRT: {timing_srt}")

    script_text = script_path.read_text(encoding="utf-8")
    chunks = chunk_script_by_count(script_text, len(timings))
    entries: list[str] = []
    for index, ((start, end), chunk) in enumerate(zip(timings, chunks), start=1):
        entries.append(f"{index}\n{start} --> {end}\n{chunk}\n")
    output_srt.write_text("\n".join(entries), encoding="utf-8")


def ffmpeg_subtitle_path(path: Path) -> str:
    value = path.resolve().as_posix()
    if len(value) >= 3 and value[1] == ":":
        value = value[0] + r"\:" + value[2:]
    return value.replace("'", r"\'")


def make_clip(
    index: int,
    slide: Path,
    audio: Path,
    script: Path | None,
    args: argparse.Namespace,
    clip_dir: Path,
) -> Path:
    clip_path = clip_dir / f"{index:02d}.mp4"
    filters = [
        (
            f"scale={args.width}:{args.height}:force_original_aspect_ratio=decrease,"
            f"pad={args.width}:{args.height}:(ow-iw)/2:(oh-ih)/2,"
            "format=yuv420p"
        )
    ]

    if args.burn_scripts:
        if args.subtitle_source == "whisper":
            srt_path = make_whisper_srt(index, audio, args)
        elif args.subtitle_source == "aligned-script":
            if script is None:
                raise SystemExit(
                    "Aligned script subtitle mode requires one .txt file per slide in scripts/."
                )
            timing_srt = make_whisper_srt(index, audio, args)
            srt_path = clip_dir / f"{index:02d}_aligned_script.srt"
            write_aligned_script_srt(script, timing_srt, srt_path)
        else:
            if script is None:
                raise SystemExit(
                    "Script subtitle mode requires one .txt file per slide in scripts/."
                )
            srt_path = clip_dir / f"{index:02d}.srt"
            write_segment_srt(
                script,
                srt_path,
                get_media_duration(audio),
                args.subtitle_offset,
            )
        filters.append(
            "subtitles='"
            + ffmpeg_subtitle_path(srt_path)
            + f"':force_style='Fontsize={args.font_size},Outline=1,Shadow=0,MarginV={args.margin_v}'"
        )

    run(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            str(slide),
            "-i",
            str(audio),
            "-vf",
            ",".join(filters),
            "-c:v",
            "libx264",
            "-tune",
            "stillimage",
            "-c:a",
            "aac",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-b:a",
            args.audio_bitrate,
            "-shortest",
            str(clip_path),
        ]
    )
    return clip_path


def make_whisper_srt(index: int, audio: Path, args: argparse.Namespace) -> Path:
    whisper_root = TEMP_DIR / "whisper_subtitles"
    segment_dir = whisper_root / f"{index:02d}"
    segment_dir.mkdir(parents=True, exist_ok=True)

    srt_path = segment_dir / f"{audio.stem}.srt"
    if srt_path.exists() and not args.force_whisper:
        return srt_path

    command = [
        sys.executable,
        "-m",
        "whisper",
        str(audio),
        "--model",
        args.whisper_model,
        "--output_dir",
        str(segment_dir),
        "--output_format",
        "srt",
    ]
    if args.whisper_language.lower() != "auto":
        command.extend(["--language", args.whisper_language])

    run(command)
    if not srt_path.exists():
        raise SystemExit(f"Whisper did not create expected SRT: {srt_path}")
    return srt_path


def concat_file_line(path: Path) -> str:
    value = path.resolve().as_posix().replace("'", r"'\''")
    return f"file '{value}'"


def concatenate_clips(clips: list[Path], output: Path) -> None:
    concat_path = TEMP_DIR / "concat.txt"
    concat_path.write_text(
        "\n".join(concat_file_line(clip) for clip in clips) + "\n",
        encoding="utf-8",
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_path),
            "-c",
            "copy",
            str(output),
        ]
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Combine slide images and per-slide audio into a presentation video."
    )
    parser.add_argument("--slides-dir", type=Path, default=PROJECT_ROOT / "slides")
    parser.add_argument(
        "--pdf",
        type=Path,
        help="Optional PDF deck. Each page will be rendered as one slide image.",
    )
    parser.add_argument("--pdf-dpi", type=int, default=200)
    parser.add_argument("--audio-dir", type=Path, default=PROJECT_ROOT / "audio")
    parser.add_argument("--scripts-dir", type=Path, default=PROJECT_ROOT / "scripts")
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "output" / "final_presentation.mp4",
    )
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--font-size", type=int, default=12)
    parser.add_argument("--margin-v", type=int, default=36)
    parser.add_argument(
        "--subtitle-offset",
        type=float,
        default=0.0,
        help="Shift burned script subtitles in seconds. Negative values show subtitles earlier.",
    )
    parser.add_argument(
        "--subtitle-source",
        choices=["script", "whisper", "aligned-script"],
        default="script",
        help="Use script text timing or Whisper-generated audio timing for burned subtitles.",
    )
    parser.add_argument("--whisper-model", default="base")
    parser.add_argument("--whisper-language", default="English")
    parser.add_argument(
        "--force-whisper",
        action="store_true",
        help="Regenerate Whisper SRT files even if cached files already exist.",
    )
    parser.add_argument("--audio-bitrate", default="192k")
    parser.add_argument(
        "--burn-scripts",
        action="store_true",
        help="Burn each script text file into its matching slide segment.",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep intermediate clips in temp/clips.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    enable_packaged_ffmpeg()
    require_ffmpeg()

    slides, rendered_slide_dir = resolve_slides(args)
    audio_files = collect_files(args.audio_dir.resolve(), AUDIO_EXTENSIONS)
    scripts = collect_files(args.scripts_dir.resolve(), {".txt"})

    if not slides:
        raise SystemExit(f"No slide images found in: {args.slides_dir}")
    if not audio_files:
        raise SystemExit(f"No audio files found in: {args.audio_dir}")
    if len(slides) != len(audio_files):
        raise SystemExit(
            f"Slide/audio count mismatch: {len(slides)} slides, {len(audio_files)} audio files."
        )
    if (
        args.burn_scripts
        and args.subtitle_source in {"script", "aligned-script"}
        and len(scripts) != len(slides)
    ):
        raise SystemExit(
            f"Script count mismatch: expected {len(slides)} txt files, found {len(scripts)}."
        )

    clip_dir = TEMP_DIR / "clips"
    if clip_dir.exists() and not args.keep_temp:
        shutil.rmtree(clip_dir)
    clip_dir.mkdir(parents=True, exist_ok=True)

    clips: list[Path] = []
    for index, (slide, audio) in enumerate(zip(slides, audio_files), start=1):
        script = scripts[index - 1] if index <= len(scripts) else None
        print(f"\nSegment {index}: {slide.name} + {audio.name}")
        clips.append(make_clip(index, slide, audio, script, args, clip_dir))

    concatenate_clips(clips, args.output.resolve())

    if not args.keep_temp:
        shutil.rmtree(clip_dir, ignore_errors=True)
        if rendered_slide_dir is not None:
            shutil.rmtree(rendered_slide_dir, ignore_errors=True)

    print()
    print(f"Done. Video: {args.output.resolve()}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        raise SystemExit(130)
