#!/usr/bin/env bash
# 一键构建：依赖 → 逐帧渲染 → 无声视频 → 合成配乐 → 母带 → 混流 out.mp4
# 本脚本可与 index.html 放在同一目录，也可放在其下的 scripts/。
# audio/ 放在 index.html 同级。输出（frames/、out.mp4）也写到该目录，与当前工作目录无关。
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [[ -f "$SCRIPT_DIR/index.html" ]]; then
  ROOT="$SCRIPT_DIR"
elif [[ -f "$SCRIPT_DIR/../index.html" ]]; then
  ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
else
  echo "找不到 index.html。请把 build.sh 与 index.html 放在同一目录，或放在 index.html 下的 scripts/。" >&2
  exit 1
fi
if [[ -f "$ROOT/audio/score.py" && -f "$ROOT/audio/master.py" ]]; then
  AUDIO="$ROOT/audio"
else
  echo "找不到 $ROOT/audio/score.py。请把 skill 的 audio/ 复制到 index.html 同级。" >&2
  exit 1
fi

if [[ ! -d "$SCRIPT_DIR/node_modules/playwright" ]]; then
  (cd "$SCRIPT_DIR" && npm install --no-audit --no-fund playwright)
fi
(cd "$SCRIPT_DIR" && npx playwright install chromium >/dev/null)
rm -rf "$ROOT/frames" && mkdir -p "$ROOT/frames"
node "$SCRIPT_DIR/capture.js" --out "$ROOT/frames"   # frames/0000.png – 1199.png
ffmpeg -y -loglevel error -framerate 30 -i "$ROOT/frames/%04d.png" -c:v libx264 -pix_fmt yuv420p -crf 18 "$ROOT/out_silent.mp4"
python3 "$AUDIO/score.py"                            # numpy-only original score -> audio/premaster.wav
python3 "$AUDIO/master.py"                           # -14 LUFS, TP < -1 dBTP -> audio/score.wav
ffmpeg -y -loglevel error -i "$ROOT/out_silent.mp4" -i "$AUDIO/score.wav" -map 0:v:0 -map 1:a:0 \
  -c:v copy -c:a aac -b:a 192k -ar 48000 -t 40 -movflags +faststart "$ROOT/out.mp4"
ffprobe -v error -count_frames -show_entries stream=codec_type,codec_name,width,height,r_frame_rate,nb_read_frames,sample_rate,channels,bit_rate:format=duration -of default=nw=1 "$ROOT/out.mp4"
