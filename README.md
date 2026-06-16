# Slide Video Maker / 幻灯片演讲视频生成器

Turn a slide deck, per-slide narration audio, and optional scripts into a single presentation video.

把一份幻灯片、逐页录音和可选台词自动合成为一个演讲视频。

## Features / 功能

- Supports one PDF deck or numbered slide images.
- No fixed page count: use any number of slides as long as the matching audio files are provided.
- Supports common audio formats, including `.m4a`, `.mp3`, `.wav`, `.aac`, `.flac`, `.ogg`, and `.wma`.
- Matches slides, audio, and scripts by natural filename order.
- Exports a single `.mp4` presentation video.
- Can burn subtitles into the video so they are visible in every player.
- Supports three subtitle modes:
  - `script`: split each script across its slide audio duration.
  - `whisper`: use Whisper transcription text and timestamps.
  - `aligned-script`: use Whisper timestamps with your original script text.

- 支持直接放入一份 PDF，或放入按编号排列的 slide 图片。
- 没有固定页数要求：只要 slides 和对应音频数量匹配即可。
- 支持常见音频格式，包括 `.m4a`、`.mp3`、`.wav`、`.aac`、`.flac`、`.ogg`、`.wma`。
- 自动按文件名自然排序匹配 slides、audio 和 scripts。
- 输出一个完整的 `.mp4` 演讲视频。
- 可以把字幕直接烧录进视频，任何播放器打开都能看到。
- 支持三种字幕模式：
  - `script`：把每页台词按该页音频时长平均切分。
  - `whisper`：使用 Whisper 自动识别出来的文字和时间轴。
  - `aligned-script`：使用 Whisper 时间轴，但保留你提供的原始台词。

## Project Structure / 项目结构

```text
slide-video-maker/
├── make_video.py
├── requirements.txt
├── slides/
│   └── .gitkeep
├── audio/
│   └── .gitkeep
├── scripts/
│   └── .gitkeep
├── output/
│   └── .gitkeep
└── temp/
    └── .gitkeep
```

For privacy and repository size, local media files and generated outputs are ignored by Git.

为了保护隐私并避免仓库过大，本地媒体文件和生成视频默认不会被 Git 跟踪。

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

方案 A：使用一份完整 PDF。

```text
slides/
└── presentation.pdf

audio/
├── 01.m4a
├── 02.m4a
└── ...

scripts/
├── 01.txt
├── 02.txt
└── ...
```

Option B: use slide images.

方案 B：使用逐页图片。

```text
slides/
├── 01.png
├── 02.png
└── ...

audio/
├── 01.m4a
├── 02.m4a
└── ...

scripts/
├── 01.txt
├── 02.txt
└── ...
```

Use two-digit filenames such as `01`, `02`, and `03` to keep ordering predictable.

建议使用 `01`、`02`、`03` 这种两位编号，避免排序出错。

There is no required slide count. A 5-page deck needs 5 audio files; a 20-page deck needs 20 audio files. If script subtitles are enabled with `script` or `aligned-script`, provide the same number of `.txt` files as well.

本工具没有固定页数要求。5 页 slides 就放 5 段音频，20 页 slides 就放 20 段音频。如果使用 `script` 或 `aligned-script` 字幕模式，也需要提供相同数量的 `.txt` 台词文件。

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

The default `script` mode is simple and fast, but it distributes script text across each audio clip by length. If speech speed changes within a slide, some subtitles may appear slightly early or late.

默认的 `script` 模式简单快速，但它会按长度把文字分配到整段音频里。如果某一页内语速变化明显，字幕可能会局部提前或滞后。

For better timing while keeping your original script text, use:

如果想保留原始台词，同时获得更好的字幕时间轴，可以使用：

```powershell
python .\make_video.py --burn-scripts --subtitle-source aligned-script --whisper-model base --whisper-language English
```

This mode asks Whisper to estimate subtitle timestamps, then replaces Whisper's recognized text with your original script chunks.

这个模式会先用 Whisper 估计字幕时间点，再把识别文字替换成你提供的原始台词。

If you want pure Whisper transcription:

如果想直接使用 Whisper 自动识别文字：

```powershell
python .\make_video.py --burn-scripts --subtitle-source whisper --whisper-model base --whisper-language English
```

Whisper model names such as `tiny`, `base`, `small`, and `medium` can be used. Larger models are usually more accurate but slower.

Whisper 模型可以使用 `tiny`、`base`、`small`、`medium` 等。模型越大通常越准，但速度也越慢。

## Useful Options / 常用参数

```powershell
python .\make_video.py --width 1920 --height 1080
python .\make_video.py --font-size 12 --margin-v 36 --burn-scripts
python .\make_video.py --subtitle-offset 0.3 --burn-scripts
python .\make_video.py --subtitle-margin-map "3=8,5=8,9=8" --burn-scripts
python .\make_video.py --audio-speed-map "6=0.9,9=0.9,11=0.9"
python .\make_video.py --pdf-dpi 250 --burn-scripts
python .\make_video.py --keep-temp
```

- `--width`, `--height`: output video resolution.
- `--font-size`, `--margin-v`: burned subtitle appearance.
- `--subtitle-margin-map`: per-slide subtitle bottom margins. Smaller values move subtitles down; larger values move them up.
- `--subtitle-offset`: shift `script` subtitle timing in seconds.
- `--audio-speed-map`: per-slide audio speed. Values below `1.0` slow a segment down; values above `1.0` speed it up.
- `--pdf-dpi`: PDF rendering quality.
- `--keep-temp`: keep intermediate clips for debugging.

- `--width`、`--height`：输出视频分辨率。
- `--font-size`、`--margin-v`：烧录字幕的字号和底部距离。
- `--subtitle-margin-map`：逐页设置字幕离底部的距离。数值越小字幕越靠下，数值越大字幕越靠上。
- `--subtitle-offset`：调整 `script` 模式字幕整体提前或延后，单位是秒。
- `--audio-speed-map`：逐页设置音频速度。小于 `1.0` 会放慢该页，大于 `1.0` 会加快该页。
- `--pdf-dpi`：PDF 渲染清晰度。
- `--keep-temp`：保留中间片段，方便排查问题。

Example: move subtitles down on slides 3, 5, and 9, and slow slides 6, 9, and 11 to 90% speed:

示例：把第 3、5、9 页字幕下调，并把第 6、9、11 页音频放慢到 90%：

```powershell
python .\make_video.py --burn-scripts --subtitle-source aligned-script --subtitle-margin-map "3=8,5=8,9=8" --audio-speed-map "6=0.9,9=0.9,11=0.9"
```

## Privacy / 隐私说明

This repository is designed so that real coursework files, private audio, scripts, generated videos, and Whisper cache files are not committed by default.

这个仓库已经默认忽略真实课程材料、私人音频、台词文本、生成视频和 Whisper 缓存文件。

Before publishing, you can verify tracked files with:

发布前可以用下面命令检查将要上传的文件：

```powershell
git status --short
git ls-files
```

## License / 许可证

MIT License. See [LICENSE](LICENSE).

本项目使用 MIT 许可证。详见 [LICENSE](LICENSE)。
