# Examples / 示例

This folder is for small public examples only. Do not place private coursework files, unreleased slides, or personal recordings here if you plan to publish the repository.

这个文件夹只建议放公开示例。准备发布仓库时，不要把私人课程材料、未公开 slides 或个人录音放在这里。

## Minimal Test Layout / 最小测试结构

```text
slides/
└── presentation.pdf

audio/
├── 01.m4a
└── 02.m4a

scripts/
├── 01.txt
└── 02.txt
```

Run:

运行：

```powershell
python .\make_video.py --burn-scripts
```
