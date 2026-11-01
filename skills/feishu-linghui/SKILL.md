---
name: feishu-linghui
metadata:
  version: "0.1.1"
description: >
  在飞书文档里画或改飞书画板（可编辑的原生形状和文字，不是图片）：数据信息图、现状一图、规划图、流程/闭环图、
  把报告或 plan 画成一张图（画图、画板、信息图、一图看懂、把这段画出来、图里加一行、改一下图里的字）。
  统一一种清爽的"结论先行"风格；也负责改已有画板里的文字或加一行，且不丢文档评论。
---

# 飞书灵绘

画出来的是飞书画板里的原生形状和文字，双击就能改。一张图回答一个问题，标题就是答案。

## 环境依赖

- Python 3（脚本仅使用标准库）。
- Node.js 和 npx：用于调用 `@larksuite/whiteboard-cli` 转换与检查。
- 已安装并登录的 `lark-cli`，以及目标文档、画板的访问与编辑权限。
- 登录状态与凭据保存在各自工具的本机配置中，不写入 skill 或仓库。

## 先定是新画还是改旧图

| 情况 | 做法 |
|---|---|
| 新画一张 | 用 `scripts/board.py` 写一个小生成脚本 → 本地渲染看图 → 插进文档 → 导出再看一遍 |
| 只改已有画板里的字、加一行 | **不重画**。导出 raw 节点 → 改文字或复制一行 → raw 覆盖写回，样式布局原样保留（见下文） |
| 文档里有评论 | 先看「保住评论」一节再动正文 |

## 默认呈现约定

用户明确指定的格式和内容优先；以下作为默认值。

1. **图里不放人名和人员分工**，只讲事。
2. **路线图用表格，不用甘特图**；表格格子里有多项时按 1. 2. 3. 编号。
3. **说大白话，但用正式说法**：用户口头随口说的词（如"摸一下"）不要照搬进文档或图里，换成"调研""摸底结果→抽样结果"这类书面说法。
4. **数字照抄源头，写清口径和来源**（如"演示流程：指定周期抽样"）；拿不准的数不上图，写"待测"。
5. 只画内容，**不把需求、过程、风格名写到图上**（"按你的要求""整理自…""风格：…"都不要）。

## 新画一张

1. 想清楚这张图要回答哪一个问题，标题写成完整结论：`主题：结论`（如"任务处理：明确目标、逐项执行、检查结果"）。内容多就拆成几张。
2. 读 [`style.md`](style.md) 选版式，读 [`rules.md`](rules.md) 记住飞书画板的限制。
3. 复制 [`examples/data_brief.py`](examples/data_brief.py) 改内容；版式部件都在 `scripts/board.py` 里（标题、分区面板、白卡片、数字卡、横向比例条、柱状图、药丸标签、要点条、宽度估算）。
4. 渲染并**亲眼看图**，修掉文字溢出、贴边、重叠、截断，反复到干净为止：
   ```bash
   python3 scripts/board.py render diagram.svg      # 出 diagram.png，并跑 --check
   ```
5. 插进文档：在目标位置后面插一个空白画板块，拿到 token 再写入：
   ```bash
   lark-cli docs +update --doc <doc> --command block_insert_after --block-id <前一个块> \
     --content '<whiteboard type="blank"></whiteboard>' --as user        # 返回里有 block_token
   python3 scripts/board.py write <whiteboard_token> diagram.svg     # 写入并导出 board_export.png
   ```
6. 看 `board_export.png` 确认线上效果。导出偶尔报服务端错误，隔几秒重试即可。
7. 交付：给文档链接 + 渲染图，用一两句话说清图里讲了什么。

## 改已有画板（只改字或加一行）

```bash
python3 scripts/edit_text.py export <token> cur.json            # 导出 raw 节点并列出所有文字
# 写一个 {旧文字: 新文字} 的 json，或在脚本里复制整行节点、整体下移
python3 scripts/edit_text.py apply <token> cur.json edits.json  # 改字、按字数调宽度、覆盖写回
```

- 加一行：复制同类的一整行节点（底框、卡片、文字、标签），换新 id、整体 y 偏移；它下面的节点全部下移，背景框加高。
- 改之前先把 `cur.json` 备份到工作区，出问题可以写回原样。

## 保住文档评论

- 正文普通段落：`docs +update --command str_replace` 可以用。
- **表格里的字不要用 str_replace**：它会把整张表重写，评论锚点和单元格里的分段全丢。表格里只能找到那一段的 `<p id>`，用 `block_replace --block-id` 单段替换；往有评论的表里加行做不到，就在表格下面另起一段。
- 每改一步都 `docs +fetch --detail with-ids` 数一下 `comment-refs`；丢了就用 `docs +history-list` / `+history-revert` 回到改之前的版本再重做。
- 不用 `overwrite` 改别人有评论的文档。

## 示例与隐私

`examples/data_brief.py` 中的名称和数字均为虚构演示，不代表任何真实业务。使用时替换成用户授权使用的资料，不能把示例数字当事实。
不要把真实业务数据、账号、内部链接或个人反馈写回 skill 文件。需要长期记录偏好时先取得用户明确要求，并避免保存敏感内容。
