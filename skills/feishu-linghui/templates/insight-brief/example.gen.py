# Insight Brief specimen: LLM training in three stages (same content as the gallery).
HUES = {
    "rose": dict(main="#fe2c55", text="#e0244b", tint="#ffedf1"),
    "teal": dict(main="#00a8a3", text="#008c88", tint="#e4fbfa"),
    "ink":  dict(main="#161823", text="#161823", tint="#f1f1f3"),
}
AMBER = dict(main="#d9941e", text="#b5770f", tint="#fff8e6")
BODY, MUTED, LINE = "#1f2329", "#6b6e76", "#9a9ca3"

stages = [
    ("rose", "1", "预训练", "Pre-training", "在海量文本里学语言与知识",
     [("数据", "海量互联网文本", None), ("方法", "自监督：预测下一个词", None), ("产出", "Base 基座模型", "最耗算力")],
     "「会续写，但不一定听话」"),
    ("teal", "2", "监督微调", "SFT", "用示范教模型按指令回答",
     [("数据", "高质量「指令–回答」示范", None), ("方法", "监督学习，模仿示范", None), ("产出", "SFT 指令模型", None)],
     "「学会听懂并遵循指令」"),
    ("ink", "3", "人类反馈对齐", "RLHF", "用偏好信号把回答调得更好",
     [("数据", "人类对回答的偏好排序", None), ("方法", "奖励模型 + 强化学习", None), ("产出", "对齐的 AI 助手", "标注成本高")],
     "「更有用、更诚实、更安全」"),
]

W, PAD = 1000, 40
out = []
add = out.append

def text(x, y, s, size=16, color=BODY, bold=False, anchor="start"):
    w = ' font-weight="700"' if bold else ""
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    add(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}"{w}{a}>{s}</text>')

def width_of(s, size):
    return sum(size if ord(c) > 0x2E7F else size * 0.6 for c in s)

def pill(x, y, s, hue, size=14):
    w = width_of(s, size) + 20
    add(f'<rect x="{x}" y="{y}" width="{w:.0f}" height="24" rx="12" fill="#ffffff" stroke="{hue["main"]}" stroke-width="1.5"/>')
    text(x + 10, y + 17, s, size, hue["text"])
    return w

add(f'<rect x="0" y="0" width="{W}" height="H" fill="#f7f8fa"/>')
text(PAD, 64, "LLM 训练三阶段：先学语言，再学听话，最后学人类偏好", 26, "#161823", True)
text(PAD, 98, "预训练 → 监督微调 → 人类反馈对齐 · 每一阶段都在上一阶段的模型上继续训练", 16, MUTED)

col_w, gap, top = 280, 40, 132
panel_h = 392
for i, (hk, num, title, en, lead, cards, quote) in enumerate(stages):
    hue = HUES[hk]
    x = PAD + i * (col_w + gap)
    add(f'<rect x="{x}" y="{top}" width="{col_w}" height="{panel_h}" rx="8" fill="{hue["tint"]}" stroke="{hue["main"]}" stroke-width="2"/>')
    add(f'<circle cx="{x + 34}" cy="{top + 38}" r="16" fill="{hue["main"]}"/>')
    text(x + 34, top + 44, num, 16, "#ffffff", True, "middle")
    text(x + 60, top + 45, title, 18, hue["text"], True)
    text(x + 60 + width_of(title, 18) + 10, top + 45, en, 14, MUTED)
    text(x + 18, top + 84, lead, 16, MUTED)
    cy = top + 104
    for label, body, tag in cards:
        add(f'<rect x="{x + 16}" y="{cy}" width="{col_w - 32}" height="68" rx="6" fill="#ffffff" stroke="{hue["main"]}" stroke-width="1.5"/>')
        text(x + 32, cy + 28, label, 16, BODY, True)
        if tag:
            pill(x + 32 + width_of(label, 16) + 10, cy + 10, tag, AMBER)
        text(x + 32, cy + 54, body, 16, BODY)
        cy += 80
    text(x + 18, cy + 30, quote, 16, hue["text"], True)
    if i < len(stages) - 1:
        ay = top + panel_h / 2
        add(f'<line x1="{x + col_w + 4}" y1="{ay}" x2="{x + col_w + gap - 6}" y2="{ay}" stroke="{LINE}" stroke-width="2" marker-end="url(#arrow)"/>')

# range brackets under the panels
by = top + panel_h + 28
def bracket(x1, x2, label):
    add(f'<polyline points="{x1},{by - 10} {x1},{by} {x2},{by} {x2},{by - 10}" fill="none" stroke="#161823" stroke-width="1.5"/>')
    lw = width_of(label, 16) + 24
    mid = (x1 + x2) / 2
    add(f'<rect x="{mid - lw / 2:.0f}" y="{by - 14}" width="{lw:.0f}" height="28" fill="#f7f8fa"/>')
    text(mid, by + 6, label, 16, "#161823", True, "middle")
bracket(PAD + 4, PAD + col_w - 4, "能力：学会语言")
bracket(PAD + col_w + gap + 4, PAD + 3 * col_w + 2 * gap - 4, "对齐：学会做一个好助手")

ly = by + 32
pw = pill(PAD, ly, "最耗算力", AMBER)
text(PAD + pw + 10, ly + 17, "琥珀标签 = 成本最高的环节", 14, MUTED)

ty = ly + 44
add(f'<rect x="{PAD}" y="{ty}" width="{W - 2 * PAD}" height="80" rx="8" fill="{AMBER["tint"]}" stroke="{AMBER["main"]}" stroke-width="2"/>')
text(PAD + 24, ty + 32, "要点：预训练决定模型“知道什么”，SFT 与 RLHF 决定它“怎么回答”。", 16, "#161823", True)
text(PAD + 24, ty + 60, "最终得到一个能对话、会遵循指令、贴合人类偏好的 AI 助手。", 16, BODY)

H = ty + 80 + PAD
svg = "\n".join(out).replace('height="H"', f'height="{H}"', 1)
print(f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs><marker id="arrow" markerWidth="12" markerHeight="12" refX="9" refY="4" orient="auto" markerUnits="strokeWidth"><path d="M0 0 L10 4 L0 8 z" fill="{LINE}"/></marker></defs>
{svg}
</svg>''')
