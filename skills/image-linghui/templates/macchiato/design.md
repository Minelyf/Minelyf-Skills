---
version: 1.0
name: Macchiato
renderer: local-svg-image
description: >
  A warm monochrome palette with no accent color: a soft milky-almond page and a warm espresso
  near-black for everything, plus two warm taupe greys for quieter copy. Cozy, creamy, and
  understated, like espresso stirred into warm cream. Hierarchy comes from scale, weight, and spacing,
  never from color. Flat only, no gradients or shadows.

# ── COLOR ────────────────────────────────────────────────────
colors:
  cream:   "#EDE7DD"   # the default surface: warm milky almond, soft and putty, never white
  cream-2: "#E5DECF"   # a slightly deeper almond for inset surfaces or a placeholder; sparing
  ink:     "#25211B"   # ALL text, borders, rules, dividers: a warm espresso near-black, never pure #000
  ink-2:   "#6E6558"   # warm taupe-grey: secondary text (leads, body, labels)
  ink-3:   "#9A917F"   # pale warm taupe: tertiary text (kickers, axis labels, source notes, markers)
  # No accent. One warm almond surface, one espresso ink, two taupe greys. The whole color system.

# ── STROKE & CORNERS ─────────────────────────────────────────
stroke:
  structural: "1 to 2px solid ink for panels and rules"
  rule:       "1px solid ink for dividers"
  radius:     "low to soft (rx 0 to 14); quiet and warm, neither sharp nor bubbly"
---

# Macchiato — Local SVG Image Design System

One warm almond surface, one espresso ink, two taupe greys. No accent. The restraint is the point:
build the board so hierarchy comes from size, weight, and space, and let the milky almond and the warm
espresso ink do all the work. Reach for this when the content should feel cozy, calm, and uncluttered.

## Color

- **Cream** (`#EDE7DD`): The default surface. A warm milky almond, soft and putty. Every background is this or a near-identical variant, never white.
- **Cream Alt** (`#E5DECF`): A slightly deeper almond for an inset surface or a placeholder. Used sparingly; the difference from the default is gentle.
- **Ink** (`#25211B`): Every text run, rule, divider, and border. A warm espresso near-black, never pure black, chosen for warmth against the almond.
- **Ink 2** (`#6E6558`): A warm taupe-grey. Secondary text: leads, body paragraphs, and labels that should step back from headline weight.
- **Ink 3** (`#9A917F`): A pale warm taupe. Tertiary text: kickers, axis labels, source notes, and markers that should read as barely-present structure.

There is no accent color. Distinguish surfaces and sections by scale, weight, padding, and a thin ink
rule, not by color.

## Rules

This template defines the **palette + mood**. Read [../../RULES.md](../../RULES.md) for local image rendering and verification; platform import limitations do not apply.
