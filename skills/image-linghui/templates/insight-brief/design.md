---
version: 1.0
name: Insight Brief
renderer: local-svg-image
description: >
  A dense, conclusion-first explainer style for turning a document, meeting, or analysis into one
  board per question. Cool light-grey ground, three category hues (rose, teal, ink) that each own one
  section, white cards inside tinted panels, amber reserved for judgment and the closing takeaway bar.
  Small schematic visuals (timeline strips, ratio bars, 2×2 matrices, before/after bars) carry the
  argument; quotes and numbers stay verbatim. Flat, crisp, editorial.

# ── COLOR ────────────────────────────────────────────────────
colors:
  ground:      "#F7F8FA"   # one full-canvas rect behind everything
  rose:        "#FE2C55"   # category hue A: borders, badges, fills of strips
  rose-text:   "#E0244B"   # rose text on white / rose-tint
  rose-tint:   "#FFEDF1"   # rose panel fill
  teal:        "#00A8A3"   # category hue B
  teal-text:   "#008C88"
  teal-tint:   "#E4FBFA"
  ink:         "#161823"   # category hue C, titles, identity badges
  ink-tint:    "#F1F1F3"   # ink panel fill; also neutral "supplement" panels
  amber:       "#D9941E"   # emphasis only: takeaway bar, gap / cost / risk tags
  amber-text:  "#B5770F"
  amber-tint:  "#FFF8E6"   # takeaway bar fill (#FFF6E3 for a larger amber panel)
  body:        "#1F2329"   # body text
  muted:       "#6B6E76"   # subtitle, meta, timestamps, legend
  line:        "#9A9CA3"   # connectors, axes, weak borders
  divider:     "#E3E4E8"   # thin separators, neutral bands
  # Three category hues at most, amber never used as a category.

# ── TYPE (logical px, canvas 1000 wide) ──────────────────────
type:
  title:   "26 bold, ink"           # a full conclusion sentence
  section: "18 bold, hue-text"      # panel and card titles
  body:    "16 regular, body"       # line step 24–28
  meta:    "14 regular, muted"      # legend, timestamps, axis labels; the floor

# ── STROKE & CORNERS ─────────────────────────────────────────
stroke:
  panel:     "2px hue, rx 8"
  card:      "1.5px hue, rx 6, white fill"
  connector: "1.5–2px line grey, filled arrowhead; 3px hue only for the one main chain"
  dashed:    "stroke-dasharray 6 4 for scope groups, projections, 'not yet'"
---

# Insight Brief — Local SVG Image Design System

Distilled from a set of hand-tuned meeting-summary boards. Use it when the board has to **argue
something**: a summary of a talk, a doc section, a decision, a comparison with a verdict. Each board
answers one question and says its answer in the title. Reach for a louder template when the content
is a poster or a single big idea. Use a node-and-connector layout for standard architecture / flow diagrams.

## Canvas

- **1000 logical px wide** (not the 1600–1700 of other templates); height follows content, usually
  800–1400. Outer margin 40, so content spans x 40–960 (width 920).
- One full-canvas `<rect>` in `ground` as the first element. Everything else sits on it.
- Vertical rhythm in multiples of 8: 16 between cards, 24–32 between panels, 40 to the canvas edge.

## Page skeleton (top to bottom)

1. **Title**, 26 bold ink, a complete claim in the shape `主题：结论` — e.g. *"只压缩写代码不提效：重塑
   workflow 才是 AI 提效的根本"*, never a bare topic like *"研发提效"*.
2. **Subtitle**, 16 muted, one line of navigation anchors joined by ` · `: which part / question,
   who is speaking, the time range or section in the source. Optional **identity legend** right-aligned
   on the same line (badge + name pairs).
3. **Body**: 2–4 panels in one of the layouts below.
4. **Legend line** (only if the board uses tags or schematic marks), 14 muted: `[tag] 含义`.
5. **Takeaway bar**, always last: amber-tint fill, 2px amber border, rx 8, full content width. First
   line bold `要点：…` / `一句话：…`, optional second line regular. It restates the title's claim with
   the supporting specifics.

## Color = category, consistently

- Count the categories on the board (parts of the talk, speakers, before/after, phases) and give each
  one hue for the whole board: panel tint + panel border + card borders + title text + badges.
  Adjacent boards in the same doc reuse the same mapping.
- Two categories → rose + teal; three → rose + teal + ink. A neutral "supplement" panel (an aside,
  a second speaker's addition) uses ink-tint fill with ink border.
- **Amber is judgment, not a category**: the takeaway bar, tags that flag a gap / cost / risk /
  "still small", and at most one amber panel for a cautionary block (e.g. "护栏", "代价").
- Text on a tint uses the `-text` variant of that hue; body copy stays `body`, meta stays `muted`.

## Layering

Two levels, no more: **panel** (tint fill, 2px hue border) → **white cards** (1.5px same-hue border)
→ text. A card holds a bold 16–18 title line plus at most three body lines. Cards in a panel share
width and rhythm; the core panel may be larger than the side panel.

## Components

- **Number badge**: filled hue circle r 16, white bold number centred. Marks steps / levers / items.
- **Identity badge**: filled ink circle with a white initial for person A, outline ink circle with
  ink initial for person B. Place it at the top-right of each card to attribute who said it, and
  explain it once in the subtitle legend.
- **Tag pill**: white fill, 1.5px hue border, hue-text 14, `rx` = half height (24 high). Sits inline
  right after a card title and carries a short judgment ("还很小", "快速增长", "核心工作"). Tag
  colours need a legend line.
- **Quote line**: `「原话」` in hue-text bold 16, followed by a muted `（mm:ss）` or section anchor.
  Quotes are verbatim; the paraphrase goes in body text.
- **Logic connectors**: a short vertical/horizontal arrow between blocks with a 16 muted label on a
  ground-coloured rect that cuts the line — `差在哪`, `所以`, `三组抓手`, `但`. The label is the
  argument's conjunction.
- **Range bracket**: a `polyline` (down-tick, run, down-tick) under a group of columns with a bold 16
  label centred on a ground rect, to name what the group adds up to.
- **Schematic micro-visuals**, each built from rects / lines / circles only:
  proportional **timeline strip** (segment width ∝ duration, tick labels underneath);
  **ratio bar** (ink fill inside a white outlined track + two percentages); **before/after bars**;
  **2×2 matrix** with axis labels and chips placed in quadrants; **vertical ladder** with dots;
  **hub-and-spoke** ring of chips around a filled ink circle. When the geometry is not real data, say
  so in a muted 14 caption: `示意，非数据` / `按发言定性摆放，非数据坐标`.
- **Negation**: strike through the rejected option (`text-decoration="line-through"`, muted), or a
  `× 旧观念` card → `✓ 新观念` card pair with a heavy arrow between.

## Layouts that work

| Content | Layout |
|---|---|
| Overview of a whole talk / doc | timeline strip on top, then one panel per part with one card per question (title + one-line answer + ratio bar) |
| Goal → gap → levers | stacked chain: goal card → `差在哪` → current-state panel (two cards joined by `但`) → `所以` → core-work card → fan out to 2–4 lever columns with a range bracket |
| Two-sided argument | two side-by-side panels in different hues, each a vertical stack of cards, one neutral quote card at the bottom of the left panel |
| Before vs after | left panel `X 之前`, centre arrow labelled with the cause, right panel `X 之后`, optional third column for consequences |
| Principles + guardrails | top band of principle panels (hue A), a divider band, bottom band of risk panels (amber) |
| Signals / sources | hub-and-spoke on the left, case-study panels on the right |

## Density

- One board answers one question. Split a long section into several boards rather than shrinking type.
- Keep numbers, names, and quotes exactly as in the source; keep each body line ≤ ~26 CJK characters
  at 16px inside a 460-wide card, and wrap explicitly with `<tspan>`/separate `<text>` lines.

## Starting point

[`example.gen.py`](example.gen.py) generates the gallery specimen (`assets/styles/insight-brief.png`)
and shows the helpers worth copying: CJK-aware width estimate, pill, bracket, panel/card loop, takeaway
bar, and a filled arrow marker. Copy it into the working directory, replace the content, and render.

## Rules

This template is the **palette, grammar, and mood**. The local image rendering and
verification workflow live in **[`../../RULES.md`](../../RULES.md)** — read it before building.
