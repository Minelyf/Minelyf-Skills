"""改已有飞书画板里的文字，不动样式和布局。

  python3 edit_text.py export <token> cur.json              导出 raw 节点，列出全部文字（id 和内容）
  python3 edit_text.py apply  <token> cur.json edits.json   按 {旧文字: 新文字} 替换并覆盖写回

edits.json 里的键可以是完整文字，也可以写成 "~片段" 表示只替换包含该片段的部分。
改完会按新字数调整文字框宽度（居中的保持中心不动）。加一行这类结构改动，自己在 cur.json 里复制节点后再 apply 一个空的 edits。
"""
import json
import subprocess
import sys
import time

from board import est


def export(token, path):
    p = subprocess.run(['lark-cli', 'whiteboard', '+export', '--whiteboard-token', token, '--output-type', 'raw',
                        '--output', path, '--overwrite', '--as', 'user'], capture_output=True, text=True)
    if '"ok": true' not in p.stdout:
        sys.exit(p.stdout[-500:])
    for n in sorted(json.load(open(path))['nodes'], key=lambda n: (round(n['y']), n['x'])):
        t = (n.get('text') or {}).get('text')
        if t:
            print(n['id'], f"y={n['y']:.0f}", repr(t))


def apply(token, path, edits_path):
    d = json.load(open(path))
    edits = json.load(open(edits_path)) if edits_path else {}
    hit = 0
    for n in d['nodes']:
        t = (n.get('text') or {}).get('text')
        if not t:
            continue
        new = edits.get(t)
        for k, v in edits.items():
            if new is None and k.startswith('~') and k[1:] in t:
                new = t.replace(k[1:], v)
        if new is None:
            continue
        n['text']['text'] = new
        w = est(new, n['text']['font_size']) * 1.05 + 8
        if n['text'].get('horizontal_align') == 'center':
            cx = n['x'] + n['width'] / 2
            n['width'] = max(n['width'], w)
            n['x'] = cx - n['width'] / 2
        else:
            n['width'] = w
        hit += 1
    out = path.replace('.json', '.new.json')
    json.dump(d, open(out, 'w'), ensure_ascii=False)
    # 走 stdin：lark-cli 的 @file 只认当前目录下的相对路径
    p = subprocess.run(['lark-cli', 'whiteboard', '+update', '--whiteboard-token', token, '--source', '-',
                        '--input_format', 'raw', '--overwrite', '--idempotent-token', f'edit-{token}-{int(time.time())}',
                        '--as', 'user'], input=open(out).read(), capture_output=True, text=True)
    print(f'改了 {hit} 处文字；写回', '成功' if '"ok": true' in p.stdout else '失败：' + p.stdout[-300:])


if __name__ == '__main__':
    if sys.argv[1] == 'export':
        export(sys.argv[2], sys.argv[3])
    else:
        apply(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)
