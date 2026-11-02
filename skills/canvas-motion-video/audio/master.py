#!/usr/bin/env python3
"""Loudness master: premaster.wav -> score.wav at ~-14 LUFS, true peak < -1 dBTP (ffmpeg)."""
import json, subprocess, re, os, sys
d = os.path.dirname(os.path.abspath(__file__))
pre, out = os.path.join(d, 'premaster.wav'), os.path.join(d, 'score.wav')
def measure(path):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', path, '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'], capture_output=True, text=True)
    return json.loads(re.search(r'\{[^{}]*"input_i"[^{}]*\}', r.stderr, re.S).group(0))
m = measure(pre)
gain = -14.0 - float(m['input_i'])
# linear gain, then brickwall limiter at -2 dBFS sample peak (4x oversampled) for TP headroom
af = f"volume={gain:.2f}dB,aresample=192000,alimiter=limit={10**(-2.2/20):.4f}:attack=2:release=60:level=disabled,aresample=48000"
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', pre, '-af', af, '-ar', '48000', '-ac', '2', '-c:a', 'pcm_s16le', '-t', '40', out], check=True)
f = measure(out)
print(json.dumps({'premaster_I': m['input_i'], 'gain_dB': round(gain, 2), 'final_I': f['input_i'], 'final_TP': f['input_tp'], 'final_LRA': f['input_lra']}))
