#!/usr/bin/env python3
"""Original score for the BotMux × 飞书 × AI brand film (40.0 s).
Pure numpy synthesis (no samples, no downloads) -> audio/premaster.wav (48 kHz stereo, 16-bit).
Grid: 112.5 BPM => 1 beat = 16 video frames @30fps, 1 bar = 64 frames.
Sync points are video frame numbers taken from index.html.
"""
import numpy as np, wave, os

SR = 48000
DUR = 40.0
N = int(SR * DUR)
FPB = 16                      # video frames per beat
rng = np.random.default_rng(20261103)
def fs(frame): return int(round(frame / 30 * SR))   # video frame -> sample
def bt(beat): return fs(beat * FPB)

# ---------- scene sync points (video frames, from index.html) ----------
F_BUBBLE_POP = 14; F_TYPING = 30; F_MORPH = 56; F_HEADLINE = 70
F_CONTRACT = 150; F_HUB = 160; F_S2_REPLY = 312; F_S2_EXIT = 392
BEATS3 = [410, 504, 598]                     # request bubbles; dot enters hub at +42, card pops at +46
F_S4 = 700; F_NODES = [738, 748, 758]; F_CONV = 826; F_IMPACT = 852; F_OUTS = [860, 865, 870, 875]
F_GROOVE2 = 896; F_S5 = 958; F_M1 = 984; F_M2 = 1022; F_SYNC_ARRIVE = 1044; F_RESULT = 1050; F_RESULT_PH = 1062
F_S6 = 1088; F_TITLE = 1110; F_CREDIT = 1126

# ---------- dsp helpers ----------
def midi(m): return 440.0 * 2 ** ((m - 69) / 12)
def env_adsr(n, a, d, s, r, sustain_len):
    a, d, r = int(a * SR), int(d * SR), int(r * SR)
    e = np.zeros(n)
    hold = max(0, sustain_len - a - d)
    seg = [np.linspace(0, 1, max(a, 1), endpoint=False), np.linspace(1, s, max(d, 1), endpoint=False), np.full(hold, s)]
    head = np.concatenate(seg)[:n]
    e[:len(head)] = head
    if len(head) < n:
        last = head[-1] if len(head) else 0
        tail = last * np.exp(-np.arange(n - len(head)) / max(r / 4, 1))
        e[len(head):] = tail
    return e
def place(buf, x, start, gain=1.0):
    if start >= buf.shape[-1]: return
    if start < 0: x = x[..., -start:]; start = 0
    n = min(x.shape[-1], buf.shape[-1] - start)
    buf[..., start:start + n] += gain * x[..., :n]
def fft_filter(x, mag_fn):
    n = x.shape[-1]; L = 1 << int(np.ceil(np.log2(n + 1)))
    X = np.fft.rfft(x, L); fr = np.fft.rfftfreq(L, 1 / SR)
    return np.fft.irfft(X * mag_fn(fr), L)[..., :n]
def lp_mag(fc, order=2): return lambda f: 1 / np.sqrt(1 + (f / fc) ** (2 * order))
def hp_mag(fc, order=2): return lambda f: 1 / np.sqrt(1 + (fc / np.maximum(f, 1e-3)) ** (2 * order))
def bp_mag(fc, q=1.5): return lambda f: 1 / np.sqrt(1 + (q * (f / fc - fc / np.maximum(f, 1e-3))) ** 2)
def stft_filter(x, gain_fn, nfft=2048, hop=512):
    """time-varying filter; gain_fn(freqs, times)->(frames,bins)."""
    n = len(x); win = np.sqrt(np.hanning(nfft + 1)[:-1])
    pad = np.concatenate([np.zeros(nfft), x, np.zeros(nfft)])
    nfr = (len(pad) - nfft) // hop + 1
    idx = np.arange(nfft)[None, :] + hop * np.arange(nfr)[:, None]
    fr = np.fft.rfft(pad[idx] * win, axis=1)
    times = (np.arange(nfr) * hop + nfft / 2 - nfft) / SR
    fr *= gain_fn(np.fft.rfftfreq(nfft, 1 / SR)[None, :], times[:, None])
    y = np.fft.irfft(fr, nfft, axis=1) * win
    out = np.zeros(len(pad))
    np.add.at(out, idx.ravel(), y.ravel()) if False else None
    for k in range(nfft // hop):                      # overlap-add, vectorised per phase
        sel = np.arange(k, nfr, nfft // hop)
        blocks = y[sel]
        pos = sel[0] * hop
        flat = blocks.reshape(-1)
        out[pos:pos + flat.size] += flat[:len(out) - pos]
    return out[nfft:nfft + n] / 2.0
def interp_curve(points, times):
    pts = np.array(points, float)
    return np.interp(times, pts[:, 0], pts[:, 1])
def reverb_ir(sec=2.2, decay=1.1, seed=7):
    r = np.random.default_rng(seed); n = int(sec * SR); t = np.arange(n) / SR
    ir = r.standard_normal((2, n)) * np.exp(-t / decay * 3)
    ir[:, :int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR))
    ir = fft_filter(ir, lp_mag(6500, 1)); return ir / np.sqrt(np.sum(ir ** 2, axis=1, keepdims=True))
def convolve(x, ir):
    n = x.shape[-1] + ir.shape[-1]; L = 1 << int(np.ceil(np.log2(n)))
    return np.fft.irfft(np.fft.rfft(x, L) * np.fft.rfft(ir, L), L)[..., :x.shape[-1]]
def pan(x, p):  # p -1..1, equal power
    a = (p + 1) * np.pi / 4; return np.stack([x * np.cos(a), x * np.sin(a)])

# ---------- harmony (D major, 4-bar loop) ----------
CHORDS = [  # pad voicing, bass root, arp pool
    ([50, 57, 61, 64, 66], 38, [62, 66, 69, 73, 76]),   # Dmaj9
    ([47, 54, 57, 61, 62], 35, [59, 62, 66, 69, 73]),   # Bm9
    ([43, 50, 54, 57, 59], 31, [55, 59, 62, 66, 69]),   # Gmaj9
    ([45, 52, 59, 62, 64], 33, [57, 62, 64, 69, 71]),   # Asus(add9)
]
TONIC = CHORDS[0]
def chord_at_bar(b):
    f = b * 64
    if F_IMPACT - 64 < f + 64 and f < F_GROOVE2 and f >= 832: return TONIC      # hero tail rests on tonic
    if f >= F_S6: return TONIC
    return CHORDS[b % 4]
NBARS = int(np.ceil(1200 / 64))

pad = np.zeros((2, N)); pluck = np.zeros((2, N)); bass = np.zeros(N); drums = np.zeros((2, N))
bells = np.zeros((2, N)); sfx = np.zeros((2, N))
t_all = np.arange(N) / SR

# ---------- PAD: detuned supersaw, slow attack ----------
DET = np.array([-19, -12, -6, 0, 6, 12, 19])
for b in range(NBARS):
    voicing = chord_at_bar(b)[0]
    s0 = fs(b * 64); length = fs(64) + int(0.6 * SR)
    if b * 64 >= F_S6: length = N - s0                    # final chord rings out
    t = np.arange(length) / SR
    e = env_adsr(length, 0.35, 0.4, 0.85, 0.5, fs(64) if b * 64 < F_S6 else length)
    for m in voicing:
        for k, d in enumerate(DET):
            ph = rng.random()
            f0 = midi(m) * 2 ** (d / 1200)
            v = 2 * ((f0 * t + ph) % 1) - 1
            place(pad, pan(v * e * 0.055, -0.7 + 1.4 * k / 6), s0)
# pad brightness automation (Hz) — opens into the hub reveal, brightest in results/hero
cut_pts = [(0, 500), (F_HUB / 30, 2600), (400 / 30, 3600), (F_S4 / 30, 2400), (F_CONV / 30, 2600), (F_IMPACT / 30, 6000),
           (F_GROOVE2 / 30, 3800), (F_S6 / 30, 3000), (40, 900)]
for ch in range(2):
    pad[ch] = stft_filter(pad[ch], lambda f, tt: 1 / np.sqrt(1 + (f / interp_curve(cut_pts, tt)) ** 4))
pad = fft_filter(pad, hp_mag(140, 1))

# ---------- sections ----------
def in_range(f, a, b): return a <= f < b
def drum_section(f):
    if f < F_HUB: return 'none'
    if f < 400: return 'light'
    if f < F_S4: return 'full'
    if f < F_CONV: return 'half'
    if f < F_GROOVE2: return 'none'
    if f < F_S6 - 16: return 'full'
    return 'none'

# ---------- one-shots ----------
def kick():
    n = int(0.42 * SR); t = np.arange(n) / SR
    fr = 45 + 75 * np.exp(-t / 0.045); ph = 2 * np.pi * np.cumsum(fr) / SR
    x = np.sin(ph) * np.exp(-t / 0.16) + 0.25 * rng.standard_normal(n) * np.exp(-t / 0.004)
    return np.tanh(1.6 * x) * 0.9
def clap():
    n = int(0.35 * SR); t = np.arange(n) / SR; nz = rng.standard_normal(n)
    e = np.zeros(n)
    for o in (0, 0.011, 0.022): e += (t >= o) * np.exp(-np.maximum(t - o, 0) / 0.007)
    e += (t >= 0.03) * np.exp(-np.maximum(t - 0.03, 0) / 0.09) * 0.6
    return fft_filter(nz * e, bp_mag(1500, 1.2)) * 1.2
def hat(open_=False):
    n = int((0.25 if open_ else 0.07) * SR); t = np.arange(n) / SR
    x = rng.standard_normal(n) * np.exp(-t / (0.06 if open_ else 0.014))
    return fft_filter(x, hp_mag(7000, 2))
def tick():
    n = int(0.08 * SR); t = np.arange(n) / SR
    return fft_filter(rng.standard_normal(n) * np.exp(-t / 0.02), bp_mag(2500, 1.0)) + 0.3 * np.sin(2 * np.pi * 220 * t) * np.exp(-t / 0.02)
K, CL, HC, HO = kick(), clap(), hat(), hat(True)

kick_times = []
for beat in range(1200 // FPB):
    f = beat * FPB; sec = drum_section(f)
    if sec == 'none': continue
    pos = beat % 4
    if sec in ('light', 'full') or (sec == 'half' and pos in (0, 2)):
        place(drums, np.stack([K, K]), fs(f), 0.55 if sec != 'light' else 0.42); kick_times.append(fs(f))
    if sec in ('light', 'full') and pos in (1, 3): place(drums, pan(CL, 0.05), fs(f), 0.32 if sec == 'full' else 0.22)
    # hats: offbeat 8ths (+16ths in full)
    place(drums, pan(HO if sec == 'full' and pos == 3 else HC, 0.35), fs(f + 8), 0.16 if sec != 'half' else 0.10)
    if sec == 'full':
        place(drums, pan(HC, -0.3), fs(f + 4), 0.07); place(drums, pan(HC, -0.3), fs(f + 12), 0.07)
# soft snare-tick build into hub reveal (frames 112..160, 16ths accelerating) and riser roll into impact
for k, f in enumerate(np.arange(112, F_HUB, 4)): place(drums, pan(tick(), 0.0), fs(f), 0.05 + 0.10 * k / 12)
roll = []
f = F_CONV - 32.0; step = 8.0
while f < F_IMPACT - 1:
    roll.append(f); f += step; step = max(1.5, step * 0.86)
for k, f in enumerate(roll): place(drums, pan(tick(), 0.15 * np.sin(k)), fs(f), 0.05 + 0.20 * k / len(roll))

# sidechain envelope (pads/bass/plucks duck under kicks)
sc = np.ones(N)
for s in kick_times:
    n = min(int(0.4 * SR), N - s); tt = np.arange(n) / SR
    sc[s:s + n] = np.minimum(sc[s:s + n], 1 - 0.55 * np.exp(-tt / 0.11) * np.minimum(1, tt / 0.004 + 0.4))

# ---------- BASS: eighth-note pulses, rounded ----------
for b in range(NBARS):
    root = chord_at_bar(b)[1]
    for e8 in range(8):
        f = b * 64 + e8 * 8
        sec = drum_section(f)
        if sec == 'none' and not in_range(f, F_HUB - 32, F_HUB): continue
        if sec == 'half' and e8 % 2: continue
        if sec == 'light' and e8 % 2 == 0 and False: pass
        n = fs(8) + int(0.03 * SR); t = np.arange(n) / SR
        m = root + (12 if (e8 % 2 and sec == 'full') else 0)
        x = np.sin(2 * np.pi * midi(m) * t) + 0.35 * np.sin(4 * np.pi * midi(m) * t) + 0.15 * (2 * ((midi(m) * t) % 1) - 1)
        x *= np.minimum(1, t / 0.006) * np.exp(-t / 0.22)
        place(bass, x, fs(f), 0.30 if sec != 'light' else 0.24)
bass = fft_filter(bass, lp_mag(900, 2))

# ---------- PLUCK ARP (FM pluck) ----------
def fm_pluck(freq, dur=0.32, bright=2.2):
    n = int(dur * SR); t = np.arange(n) / SR
    I = bright * np.exp(-t / 0.05)
    x = np.sin(2 * np.pi * freq * t + I * np.sin(2 * np.pi * freq * 2 * t))
    return x * np.minimum(1, t / 0.002) * np.exp(-t / 0.12)
PATTERN = [0, 2, 1, 3, 2, 4, 1, 3]
for step16 in range(1200 // 4):
    f = step16 * 4
    b = f // 64
    if f < 32 or f >= F_S6 + 16: continue
    if in_range(f, F_IMPACT - 2, F_GROOVE2) : continue
    full = drum_section(f) == 'full' or in_range(f, F_S4, F_IMPACT)
    if not full and step16 % 2: continue                      # 8ths outside full sections
    pool = chord_at_bar(b)[2]
    note = pool[PATTERN[(step16 // (1 if full else 2)) % 8]]
    g = 0.11 if full else 0.07
    if f < F_HUB: g *= 0.55 + 0.45 * f / F_HUB
    p = 0.45 * np.sin(step16 * 0.9)
    place(pluck, pan(fm_pluck(midi(note), bright=2.6 if full else 1.6), p), fs(f), g)
# ping-pong delay (dotted 8th = 12 frames)
d = fs(12); dl = np.zeros_like(pluck)
for k, gk in enumerate([0.38, 0.24, 0.14]):
    src = pluck[(k + 1) % 2] if k % 2 == 0 else pluck[k % 2]
    sh = d * (k + 1)
    dl[k % 2, sh:] += gk * pluck.sum(0)[:-sh] * 0.5
pluck = pluck + fft_filter(dl, lp_mag(3500, 1))

# ---------- BELLS (hook + chimes) ----------
def bell(freq, dur=1.6, idx=3.0):
    n = int(dur * SR); t = np.arange(n) / SR
    I = idx * np.exp(-t / 0.25)
    x = np.sin(2 * np.pi * freq * t + I * np.sin(2 * np.pi * freq * 3.5 * t)) + 0.3 * np.sin(2 * np.pi * freq * 2 * t) * np.exp(-t / 0.3)
    return x * np.minimum(1, t / 0.003) * np.exp(-t / 0.55)
HOOK = [(0, 78), (6, 76), (8, 73), (12, 76)]          # (frame offset in bar/… 16=beat) : F#5 E5 C#5 E5
for b in range(NBARS):
    f0 = b * 64
    if (400 <= f0 < F_S4 or F_GROOVE2 <= f0 < F_S6) and b % 2 == 0:
        root_shift = {0: 0, 1: -3, 2: -7, 3: -5}[b % 4]
        for off, m in HOOK:
            place(bells, pan(bell(midi(m + root_shift + (0 if root_shift == 0 else 0))), 0.25), fs(f0 + off * 2), 0.05)
def chime(base=84, g=0.10, p=0.0):  # two-note sparkle
    x = bell(midi(base), 1.2, 2.0) + 0.6 * np.concatenate([np.zeros(int(0.06 * SR)), bell(midi(base + 7), 1.2, 2.0)])[:int(1.2 * SR)]
    place(bells, pan(x, p), 0, 0)  # (shape only)
    return pan(x, p) * g
def blip(f0=900, f1=1800, dur=0.09):
    n = int(dur * SR); t = np.arange(n) / SR
    fr = f0 * (f1 / f0) ** (t / dur); x = np.sin(2 * np.pi * np.cumsum(fr) / SR)
    return x * np.minimum(1, t / 0.003) * np.exp(-t / (dur / 3))

# ---------- SFX ----------
def whoosh(dur=0.9, f_lo=300, f_hi=5000, peak=0.5, seed=1):
    r = np.random.default_rng(seed); n = int(dur * SR); t = np.arange(n) / SR
    x = r.standard_normal(n)
    pk = peak * dur
    y = stft_filter(x, lambda f, tt: 1 / np.sqrt(1 + (2.0 * (f / np.maximum(interp_curve([(0, f_lo), (pk, f_hi), (dur, f_lo * 1.5)], np.clip(tt, 0, dur)), 1) - np.maximum(interp_curve([(0, f_lo), (pk, f_hi), (dur, f_lo * 1.5)], np.clip(tt, 0, dur)), 1) / np.maximum(f, 1))) ** 2))
    amp = np.where(t < pk, (t / pk) ** 2, np.exp(-(t - pk) / (0.18 * dur)))
    y = y * amp
    sweep = np.linspace(-0.8, 0.8, n)
    return np.stack([y * np.cos((sweep + 1) * np.pi / 4), y * np.sin((sweep + 1) * np.pi / 4)])
def place_whoosh(frame_peak, dur=0.9, gain=0.22, seed=1, f_hi=5000):
    w = whoosh(dur, f_hi=f_hi, seed=seed); place(sfx, w, fs(frame_peak) - int(0.5 * dur * SR), gain)
def boom(dur=1.8, f0=70, f1=32, g=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    fr = f1 + (f0 - f1) * np.exp(-t / 0.25); x = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t / 0.6)
    nz = fft_filter(rng.standard_normal(n) * np.exp(-t / 0.35), lp_mag(2200, 1)) * 0.5
    return (x + nz) * np.minimum(1, t / 0.002) * g
def shimmer(dur=2.4, g=0.1):
    n = int(dur * SR); t = np.arange(n) / SR
    x = fft_filter(rng.standard_normal((2, n)) * np.exp(-t / 0.7), hp_mag(5000, 2))
    return x * g
def riser(frame_start, frame_end, g=0.35):
    s0, s1 = fs(frame_start), fs(frame_end); n = s1 - s0; t = np.arange(n) / SR; T = n / SR
    nz = rng.standard_normal(n)
    y = stft_filter(nz, lambda f, tt: 1 / np.sqrt(1 + (np.maximum(interp_curve([(0, 400), (T, 9000)], np.clip(tt, 0, T)), 1) / np.maximum(f, 1)) ** 4))
    fr = 180 * (8 ** (t / T)); saw = 2 * ((np.cumsum(fr) / SR) % 1) - 1
    saw = fft_filter(saw, lp_mag(3000, 1))
    amp = (t / T) ** 2.2
    x = (0.8 * y + 0.25 * saw) * amp
    place(sfx, np.stack([x * (1 - 0.3 * t / T), x * (0.7 + 0.3 * t / T)]), s0, g)

# intro: user bubble pops, BotMux typing
place(sfx, pan(blip(1000, 1900), 0.2), fs(F_BUBBLE_POP), 0.16)
for k in range(3): place(sfx, pan(blip(1400, 1500, 0.05), -0.2), fs(F_TYPING + 8 * k), 0.05)
# morph transitions
place_whoosh(F_MORPH + 12, 1.0, 0.26, seed=2)             # bubble → full screen
riser(F_CONTRACT - 50, F_HUB, 0.18)                        # build into the hub
place_whoosh(F_CONTRACT + 8, 0.7, 0.20, seed=3, f_hi=3500) # full screen → orb
place(sfx, np.stack([boom(1.6, 80, 34, 0.55)] * 2), fs(F_HUB))   # hub reveal hit
place(sfx, shimmer(2.2, 0.08), fs(F_HUB))
place(bells, chime(81, 0.12, 0.0), fs(F_HUB))
place(sfx, pan(blip(700, 1400), -0.3), fs(F_S2_REPLY), 0.12)     # reply back into chat
place_whoosh(F_S2_EXIT + 6, 0.8, 0.20, seed=4)
# results: dot enters hub (blip) → card pops (chime)
for k, s in enumerate(BEATS3):
    place(sfx, pan(blip(900, 1300, 0.07), -0.4), fs(s), 0.07)                 # request bubble lands
    place(sfx, pan(blip(1200, 2600, 0.12), -0.1), fs(s + 42), 0.14)           # light-dot into hub
    place(bells, chime(84 + [0, 2, 4][k], 0.11, 0.35), fs(s + 46))            # card pops
place_whoosh(F_S4 - 2, 0.9, 0.22, seed=5)
for k, f in enumerate(F_NODES): place(sfx, pan(blip(600 + 150 * k, 1100 + 150 * k, 0.08), [-0.6, 0.6, 0][k]), fs(f), 0.09)
# HERO: riser + impact exactly on shockwave frame 852
riser(F_CONV - 40, F_IMPACT, 0.42)
place(sfx, np.stack([boom(2.4, 90, 30, 1.0)] * 2), fs(F_IMPACT))
place(sfx, shimmer(3.0, 0.16), fs(F_IMPACT))
for k, f in enumerate(F_OUTS): place(bells, chime([86, 88, 90, 93][k], 0.09, [-0.6, 0.6, -0.4, 0.4][k]), fs(f))
place_whoosh(F_S5 + 4, 0.8, 0.20, seed=6)
place(sfx, pan(blip(1000, 1900), 0.2), fs(F_M1), 0.12)
place(sfx, pan(blip(1000, 1900), 0.6), fs(F_M2), 0.12)
place(sfx, pan(blip(1500, 900, 0.14), 0.0), fs(1026), 0.08)
place(sfx, pan(blip(1200, 2600, 0.12), -0.4), fs(F_SYNC_ARRIVE), 0.12)
place(bells, chime(86, 0.11, -0.3), fs(F_RESULT))
place(bells, chime(93, 0.06, 0.5), fs(F_RESULT_PH))
place_whoosh(F_S6 + 8, 1.0, 0.20, seed=7, f_hi=3000)
# outro: resolving bell phrase on the title, sparkle on credit
for k, (off, m) in enumerate([(0, 74), (6, 78), (12, 81), (20, 86)]):
    place(bells, pan(bell(midi(m), 2.4, 2.4), [-0.3, 0.3, -0.15, 0.0][k]), fs(F_TITLE + off), 0.075)
place(bells, chime(90, 0.07, 0.0), fs(F_CREDIT))

# ---------- mix ----------
ir = reverb_ir()
pad *= sc; bass *= sc; pluck *= 0.6 + 0.4 * sc
bus_rev_send = 0.35 * pad + 0.45 * pluck + 0.6 * bells + 0.15 * drums + 0.25 * sfx
rev = convolve(bus_rev_send, ir)
mix = pad + pluck + np.stack([bass, bass]) + drums + bells + sfx + 0.55 * rev
mix = fft_filter(mix, hp_mag(28, 2))
# gentle bus compression (RMS, slow) + soft clip
rms = np.sqrt(fft_filter(np.mean(mix ** 2, axis=0), lp_mag(4, 1)).clip(1e-9))
thr = np.percentile(rms, 60)
gain = np.where(rms > thr, (thr / rms) ** 0.35, 1.0)
mix = mix * gain
mix = mix / np.max(np.abs(mix)) * 0.9
mix = np.tanh(mix * 1.2) / np.tanh(1.2)
# clean ending: fade final 2.2 s to exactly 0 at 40.0 s; tiny fade-in
fade = np.ones(N); fl = int(2.2 * SR); fade[-fl:] = np.cos(np.linspace(0, np.pi / 2, fl)) ** 2
fade[:int(0.02 * SR)] = np.linspace(0, 1, int(0.02 * SR))
mix *= fade
mix = mix / np.max(np.abs(mix)) * 10 ** (-3 / 20)

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'premaster.wav')
pcm = (np.clip(mix.T, -1, 1) * 32767).astype('<i2')
with wave.open(out, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('wrote', out, mix.shape, 'samples', N)
