#!/usr/bin/env bash
# Generates tiny triangle-wave SFX for the mod. No sampled/copyrighted audio.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/mod/Sounds"
FF="${FFMPEG:-ffmpeg}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$OUT"

note() {
  local freq="$1" dur="$2" out="$3"
  "$FF" -hide_banner -loglevel error -f lavfi \
    -i "aevalsrc=0.30*(2*abs(2*(t*${freq}+0.25-floor(t*${freq}+0.75)))-1)*min(1\\,t/0.005)*min(1\\,(${dur}-t)/0.01):d=${dur}:s=44100" \
    -ac 1 -c:a pcm_s16le -y "$out"
}

note 880 0.07 "$OUT/blip.wav"
note 600 0.05 "$OUT/ui.wav"
note 200 0.18 "$OUT/hurt.wav"

note 660 0.07 "$TMP/coin1.wav"
note 990 0.10 "$TMP/coin2.wav"
"$FF" -hide_banner -loglevel error -i "$TMP/coin1.wav" -i "$TMP/coin2.wav" \
  -filter_complex "[0:a][1:a]concat=n=2:v=0:a=1" -c:a pcm_s16le -y "$OUT/coin.wav"

note 392 0.08 "$TMP/end1.wav"
note 523 0.08 "$TMP/end2.wav"
note 659 0.12 "$TMP/end3.wav"
"$FF" -hide_banner -loglevel error -i "$TMP/end1.wav" -i "$TMP/end2.wav" -i "$TMP/end3.wav" \
  -filter_complex "[0:a][1:a][2:a]concat=n=3:v=0:a=1" -c:a pcm_s16le -y "$OUT/end.wav"

echo "generated:"
ls -l "$OUT"/*.wav
