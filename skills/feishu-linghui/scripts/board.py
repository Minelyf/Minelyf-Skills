"""飞书画板的版式部件和命令。

当库用：from board import Board, HUES, AMBER  → 拼出 SVG。
当命令用：
  python3 board.py render diagram.svg               本地渲染成 diagram.png，并跑一遍检查
  python3 board.py write <whiteboard_token> diagram.svg   写入飞书画板，再导出 board_export.png 供核对
"""
import json
from html import escape
import subprocess
import sys
import time
from pathlib import Path

HUES = {
    'rose': dict(main='#fe2c55', text='#e0244b', tint='#ffedf1'),
    'teal': dict(main='#00a8a3', text='#008c88', tint='#e4fbfa'),
    'ink':  dict(main='#161823', text='#161823', tint='#f1f1f3'),
}
AMBER = dict(main='#d9941e', text='#b5770f', tint='#fff8e6')
BODY, MUTED, LINE, TRACK, GROUND = '#1f2329', '#6b6e76', '#9a9ca3', '#eceef1', '#f7f8fa'
CLI = ['npx', '-y', '@larksuite/whiteboard-cli@^0.2.11']


def est(s, size):
    """估算文字宽度：中文约 1 个字号，英文数字约 0.6 个字号。"""
    return sum(size if ord(c) > 0x2E7F else size * 0.6 for c in s)


class Board:
    def __init__(self, width=1000, pad=40):
        self.W, self.PAD, self.out = width, pad, []

    # ── 基本元素
    def text(self, x, y, s, size=16, color=BODY, bold=False, anchor='start'):
        w = ' font-weight="700"' if bold else ''
        a = f' text-anchor="{anchor}"' if anchor != 'start' else ''
        self.out.append(f'<text x="{x:.0f}" y="{y:.0f}" font-size="{size}" fill="{color}"{w}{a}>{escape(str(s))}</text>')

    def rect(self, x, y, w, h, fill, stroke=None, sw=1.5, rx=6, dash=False):
        s = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ''
        d = ' stroke-dasharray="6 4"' if dash else ''
        self.out.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" rx="{rx}" fill="{fill}"{s}{d}/>')

    def arrow(self, points, color=LINE, sw=2, dash=False):
        """points: [(x,y), ...]，横平竖直；末端带实心箭头。"""
        d = ' stroke-dasharray="6 4"' if dash else ''
        pts = ' '.join(f'{x:.0f},{y:.0f}' for x, y in points)
        self.out.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{sw}"{d} marker-end="url(#arrow)"/>')

    # ── 部件
    def title(self, title, subtitle=None):
        self.text(self.PAD, 64, title, 26, '#161823', True)
        if subtitle:
            self.text(self.PAD, 98, subtitle, 16, MUTED)

    def panel(self, x, y, w, h, hue, num, title, sub=None):
        """分区面板：浅底色 + 同色框 + 编号圆点 + 标题（+ 一行灰字）。内容从 y+88 开始放。"""
        self.rect(x, y, w, h, hue['tint'], hue['main'], 2, 8)
        self.out.append(f'<circle cx="{x + 34}" cy="{y + 36}" r="16" fill="{hue["main"]}"/>')
        self.text(x + 34, y + 42, num, 16, '#ffffff', True, 'middle')
        self.text(x + 60, y + 43, title, 18, hue['text'], True)
        if sub:
            self.text(x + 60, y + 68, sub, 14, MUTED)

    def card(self, x, y, w, h, hue, title=None):
        self.rect(x, y, w, h, '#ffffff', hue['main'])
        if title:
            self.text(x + 18, y + 30, title, 16, BODY, True)

    def kpi(self, x, y, w, hue, big, label, meta=None, big_color=None):
        """数字卡：高 110。"""
        self.rect(x, y, w, 110, '#ffffff', hue['main'])
        self.text(x + 18, y + 42, big, 28, big_color or hue['text'], True)
        self.text(x + 18, y + 70, label, 16, BODY, True)
        if meta:
            self.text(x + 18, y + 94, meta, 14, MUTED)

    def bars(self, x, y, w, rows, hue, label_w, value_w=56, scale=100):
        """横向比例条。rows: (标签, 百分数, 是否黄色强调, 标签右侧灰字或 None)，每行 34 高。"""
        track_x = x + label_w
        track_w = w - label_w - value_w - 8
        for i, (label, pct, emph, note) in enumerate(rows):
            ry = y + i * 34
            self.text(x, ry + 17, label, 16, BODY)
            if note:
                self.text(x + label_w - 8, ry + 17, note, 14, MUTED, anchor='end')
            self.rect(track_x, ry + 4, track_w, 16, TRACK, rx=3)
            self.rect(track_x, ry + 4, max(3, track_w * pct / scale), 16, AMBER['main'] if emph else hue['main'], rx=3)
            self.text(x + w, ry + 17, f'{pct:.1f}%', 16, AMBER['text'] if emph else hue['text'], True, 'end')

    def columns(self, x, y, w, items, hue, height=76, muted_from=None):
        """柱状图。items: (底部标签, 数值, 柱顶标签)；y 是基线。muted_from 之后的柱子用灰色。"""
        top = max(v for _, v, _ in items)
        slot = w / len(items)
        self.out.append(f'<line x1="{x + 18:.0f}" y1="{y:.0f}" x2="{x + w - 18:.0f}" y2="{y:.0f}" stroke="{LINE}" stroke-width="1"/>')
        for i, (lab, v, toplab) in enumerate(items):
            mx = x + slot * i + slot / 2
            h = height * v / top
            grey = muted_from is not None and i >= muted_from
            self.rect(mx - 28, y - h, 56, h, LINE if grey else hue['main'], rx=2)
            self.text(mx, y - h - 8, toplab, 14, BODY, anchor='middle')
            self.text(mx, y + 22, lab, 14, MUTED, anchor='middle')

    def pill(self, x, y, s, hue, size=14):
        w = est(s, size) + 20
        self.rect(x, y, w, 24, '#ffffff', hue['main'], rx=12)
        self.text(x + 10, y + 17, s, size, hue['text'])
        return w

    def takeaway(self, y, line1, line2=None):
        """要点条：放在最后，高 88。"""
        self.rect(self.PAD, y, self.W - 2 * self.PAD, 88, AMBER['tint'], AMBER['main'], 2, 8)
        self.text(self.PAD + 24, y + 36, line1, 16, BODY, True)
        if line2:
            self.text(self.PAD + 24, y + 64, line2, 16, BODY)

    def save(self, path, height):
        body = '\n'.join(self.out)
        Path(path).write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.W}" height="{height:.0f}" viewBox="0 0 {self.W} {height:.0f}">\n'
            '<defs><marker id="arrow" markerWidth="12" markerHeight="12" refX="9" refY="4" orient="auto" markerUnits="strokeWidth">'
            f'<path d="M0 0 L10 4 L0 8 z" fill="{LINE}"/></marker></defs>\n'
            f'<rect x="0" y="0" width="{self.W}" height="{height:.0f}" fill="{GROUND}"/>\n{body}\n</svg>\n')


# ── 命令
def render(svg):
    png = str(Path(svg).with_suffix('.png'))
    subprocess.run(CLI + ['-i', svg, '-o', png, '-f', 'svg'], check=True, capture_output=True)
    chk = subprocess.run(CLI + ['-i', svg, '-f', 'svg', '--check'], capture_output=True, text=True).stdout
    issues = [ln.strip() for ln in chk.splitlines() if '"message"' in ln]
    print(png)
    over = [i for i in issues if 'overlaps' in i]
    rest = [i for i in issues if 'overlaps' not in i]
    if over:  # 比例条的填色压在轨道上、卡片在面板里，这类重叠是有意的；以看图为准
        print(f'检查：{len(over)} 处重叠（比例条、卡片嵌套属正常，看图确认）')
    print('\n'.join(rest) if rest else '检查：没有文字溢出')


def write(token, svg):
    raw = subprocess.run(CLI + ['-i', svg, '--to', 'openapi', '--format', 'json'], check=True, capture_output=True, text=True).stdout
    p = subprocess.run(['lark-cli', 'whiteboard', '+update', '--whiteboard-token', token, '--source', '-',
                        '--input_format', 'raw', '--overwrite', '--idempotent-token', f'board-{token}-{int(time.time())}',
                        '--as', 'user'], input=raw, capture_output=True, text=True)
    if '"ok": true' not in p.stdout:
        sys.exit('写入失败：' + p.stdout[-500:] + p.stderr[-500:])
    out = Path(svg).with_name('board_export.svg')
    for _ in range(4):  # 导出偶尔报服务端错误，重试
        e = subprocess.run(['lark-cli', 'whiteboard', '+export', '--whiteboard-token', token, '--output-type', 'svg',
                            '--output', str(out), '--overwrite', '--as', 'user'], capture_output=True, text=True)
        if '"ok": true' in e.stdout:
            break
        time.sleep(5)
    else:
        sys.exit('已写入，但导出失败，稍后再导出核对')
    subprocess.run(CLI + ['-i', str(out), '-f', 'svg', '-o', str(out.with_suffix('.png'))], capture_output=True)
    print('已写入；线上效果：', out.with_suffix('.png'))


if __name__ == '__main__':
    {'render': lambda: render(sys.argv[2]), 'write': lambda: write(sys.argv[2], sys.argv[3])}[sys.argv[1]]()
