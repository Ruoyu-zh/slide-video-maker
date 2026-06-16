# Slide Video Maker / 幻灯片演讲视频生成器

Turn a slide deck, per-slide narration audio, and optional scripts into one MP4 presentation video.

把一份幻灯片、逐页录音和可选台词合成为一个演讲视频。

## Features / 功能

- Supports one PDF deck or numbered slide images.
- No fixed page count. Any number of slides is fine as long as slides and audio match.
- Supports common audio formats, including `.m4a`, `.mp3`, `.wav`, `.aac`, `.flac`, `.ogg`, and `.wma`.
- Matches slides, audio, and scripts by natural filename order.
- Burns subtitles into the video so they work in any player.
- Offers multiple subtitle timing modes:
  - `script`: split each script across its slide duration.
  - `whisper`: use Whisper transcription text and timestamps.
  - `aligned-script`: use Whisper timestamps with the original script text split by count.
  - `content-aligned-script`: use Whisper speech timing to place original script chunks by speech progress. This is better when one slide has uneven speaking speed.
- Allows per-slide subtitle overrides by placing SRT files in `subtitle_overrides/`.
- Allows per-slide subtitle position, font size, offset, and audio speed adjustments.

- 支持直接放入一个 PDF，也支持按编号排列的幻灯片图片。
- 没有固定页数要求，只要幻灯片和音频数量一致即可。
- 支持常见音频格式，包括 `.m4a`、`.mp3`、`.wav`、`.aac`、`.flac`、`.ogg`、`.wma`。
- 按文件名自然排序匹配 slides、audio 和 scripts。
- 可以把字幕直接烧录进视频，任何播放器打开都能看到。
- 支持多种字幕时间轴模式：
  - `script`：把每页台词按该页音频时长切分。
  - `whisper`：使用 Whisper 自动识别出的文字和时间。
  - `aligned-script`：使用 Whisper 时间轴，但显示你提供的原始台词。
  - `content-aligned-script`：按 Whisper 的语音进度分配原始台词，更适合一页内语速不均、普通平均切分会乱轴的情况。
- 支持在 `subtitle_overrides/` 中放入单页 SRT，对某一页做手工精修。
- 支持逐页调整字幕位置、字号、时间偏移和音频速度。

## Project Structure / 项目结构

```text
slide-video-maker/
|-- make_video.py
|-- requirements.txt
|-- slides/
|   `-- .gitkeep
|-- audio/
|   `-- .gitkeep
|-- scripts/
|   `-- .gitkeep
|-- subtitle_overrides/
|   `-- .gitkeep
|-- output/
|   `-- .gitkeep
`-- temp/
    `-- .gitkeep
```

For privacy and repository size, local media files, generated videos, Whisper cache files, and intermediate clips are ignored by Git.

为了保护隐私并避免仓库过大，本地媒体文件、生成视频、Whisper 缓存和中间片段默认不会被 Git 跟踪。

## Installation / 安装

Python 3.10+ is recommended.

建议使用 Python 3.10 或更高版本。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

The project uses FFmpeg. If FFmpeg is already installed on your system, the script will use it. Otherwise, `imageio-ffmpeg` provides a packaged FFmpeg binary.

本项目依赖 FFmpeg。如果系统已经安装 FFmpeg，脚本会直接使用；否则会尝试使用 `imageio-ffmpeg` 提供的打包版 FFmpeg。

## Input Files / 输入文件

Option A: use one PDF deck.

方案 A：使用一个完整 PDF。

```text
slides/
`-- presentation.pdf

audio/
|-- 01.m4a
|-- 02.m4a
`-- ...

scripts/
|-- 01.txt
|-- 02.txt
`-- ...
```

Option B: use slide images.

方案 B：使用逐页图片。

```text
slides/
|-- 01.png
|-- 02.png
`-- ...

audio/
|-- 01.m4a
|-- 02.m4a
`-- ...

scripts/
|-- 01.txt
|-- 02.txt
`-- ...
```

Use two-digit filenames such as `01`, `02`, and `03` to keep ordering predictable.

建议使用 `01`、`02`、`03` 这种两位编号，避免排序出错。

## Basic Usage / 基础用法

Create a video without subtitles:

生成不带字幕的视频：

```powershell
python .\make_video.py
```

Burn script subtitles into the video:

把台词烧录成字幕：

```powershell
python .\make_video.py --burn-scripts
```

Use a PDF explicitly:

手动指定 PDF：

```powershell
python .\make_video.py --pdf .\slides\presentation.pdf --burn-scripts
```

Choose a custom output path:

指定输出文件：

```powershell
python .\make_video.py --output .\output\presentation.mp4 --burn-scripts
```

## Better Subtitle Timing / 更好的字幕时间轴

The default `script` mode is simple and fast, but it distributes script text by duration. If speaking speed changes within a slide, subtitles can appear early or late.

默认的 `script` 模式简单快速，但它按时长分配台词。如果同一页内语速变化明显，字幕可能局部提前或滞后。

For better timing while keeping your original script text, use:

如果想保留原始台词，同时获得更好的时间轴，推荐使用：

```powershell
python .\make_video.py --burn-scripts --subtitle-source content-aligned-script --whisper-model base --whisper-language English
```

This mode uses Whisper timestamps to estimate speech progress, then places your original script chunks along that timing. It usually works better than evenly splitting the script by subtitle count.

这个模式会先用 Whisper 估计语音时间进度，再把你的原始台词按语音进度放到对应时间点。它通常比按字幕条数平均切分更稳。

If you want pure Whisper transcription:

如果想直接使用 Whisper 自动识别文字：

```powershell
python .\make_video.py --burn-scripts --subtitle-source whisper --whisper-model base --whisper-language English
```

Whisper model names such as `tiny`, `base`, `small`, and `medium` can be used. Larger models are usually more accurate but slower.

Whisper 模型可以使用 `tiny`、`base`、`small`、`medium` 等。模型越大通常越准，但速度也越慢。

## Manual Subtitle Overrides / 手工精修字幕

If one slide still needs manual timing, put an SRT file in `subtitle_overrides/`.

如果某一页仍然需要手工精修，把 SRT 文件放进 `subtitle_overrides/`。

Example:

示例：

```text
subtitle_overrides/
`-- 07.srt
```

Then run the usual command. The script will use `07.srt` for slide 7 and automatically generate subtitles for the other slides.

然后正常运行命令即可。脚本会对第 7 页使用 `07.srt`，其他页仍然自动生成字幕。

## Useful Options / 常用参数

```powershell
python .\make_video.py --width 1920 --height 1080
python .\make_video.py --font-size 12 --margin-v 36 --burn-scripts
python .\make_video.py --subtitle-source content-aligned-script --burn-scripts
python .\make_video.py --subtitle-offset-map "3=-0.6,8=-0.6" --burn-scripts
python .\make_video.py --subtitle-margin-map "3=8,5=8,9=8" --burn-scripts
python .\make_video.py --subtitle-font-size-map "3=9,8=9" --burn-scripts
python .\make_video.py --audio-speed-map "6=0.9,9=0.9,11=0.9"
python .\make_video.py --pdf-dpi 250 --burn-scripts
python .\make_video.py --keep-temp
```

- `--width`, `--height`: output video resolution.
- `--font-size`, `--margin-v`: burned subtitle appearance.
- `--subtitle-source`: choose subtitle timing mode.
- `--subtitle-max-words`: maximum words per generated subtitle chunk.
- `--subtitle-offset-map`: per-slide subtitle timing offsets. Negative values show subtitles earlier.
- `--subtitle-margin-map`: per-slide subtitle bottom margins. Smaller values move subtitles down; larger values move them up.
- `--subtitle-font-size-map`: per-slide subtitle font sizes.
- `--subtitle-alignment-map`, `--subtitle-left-margin-map`, `--subtitle-right-margin-map`: advanced ASS subtitle placement controls.
- `--audio-speed-map`: per-slide audio speed. Values below `1.0` slow a segment down; values above `1.0` speed it up.
- `--pdf-dpi`: PDF rendering quality.
- `--keep-temp`: keep intermediate clips for debugging.

- `--width`、`--height`：输出视频分辨率。
- `--font-size`、`--margin-v`：烧录字幕的字号和底部距离。
- `--subtitle-source`：选择字幕时间轴模式。
- `--subtitle-max-words`：每条自动字幕最多包含多少词。
- `--subtitle-offset-map`：逐页设置字幕提前或延后。负数表示提前显示。
- `--subtitle-margin-map`：逐页设置字幕离底部的距离。数值越小越靠下，数值越大越靠上。
- `--subtitle-font-size-map`：逐页设置字幕字号。
- `--subtitle-alignment-map`、`--subtitle-left-margin-map`、`--subtitle-right-margin-map`：高级 ASS 字幕位置控制。
- `--audio-speed-map`：逐页设置音频速度。小于 `1.0` 会放慢，大于 `1.0` 会加快。
- `--pdf-dpi`：PDF 渲染清晰度。
- `--keep-temp`：保留中间片段，方便排查问题。

Example: use content-aligned subtitles, move subtitles slightly on selected slides, and slow selected audio clips:

示例：使用内容对齐字幕，同时对部分页面微调字幕和音频速度：

```powershell
python .\make_video.py --burn-scripts --subtitle-source content-aligned-script --whisper-model base --whisper-language English --subtitle-margin-map "3=10,8=10" --audio-speed-map "6=0.9,9=0.9,11=0.9"
```

## Privacy / 隐私说明

This repository is designed so that real coursework files, private audio, scripts, generated videos, and Whisper cache files are not committed by default.

这个仓库默认忽略真实课程材料、私人音频、台词文本、生成视频和 Whisper 缓存文件。

Before publishing, verify tracked files with:

发布前可以用下面命令检查将要上传的文件：

```powershell
git status --short
git ls-files
```

## License / 许可证

MIT License. See [LICENSE](LICENSE).

本项目使用 MIT 许可证，详见 [LICENSE](LICENSE)。
