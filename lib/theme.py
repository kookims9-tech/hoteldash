"""Design tokens — single source of truth for CSS (:root) and Altair charts."""

from __future__ import annotations


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    value = hex_color.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def mix(c1: str, c2: str, t: float) -> str:
    """Blend two hex colors. t=0 → c1, t=1 → c2."""
    r1, g1, b1 = _hex_to_rgb(c1)
    r2, g2, b2 = _hex_to_rgb(c2)
    return (
        f"#{round(r1 + (r2 - r1) * t):02X}"
        f"{round(g1 + (g2 - g1) * t):02X}"
        f"{round(b1 + (b2 - b1) * t):02X}"
    )


def rgba(hex_color: str, alpha: float) -> str:
    r, g, b = _hex_to_rgb(hex_color)
    return f"rgba({r}, {g}, {b}, {alpha})"


# Core palette
NAVY = "#0E2F6B"
GOLD = "#C9A15A"
PAPER = "#F7F7F8"
GOOD = "#1E9E5A"
BAD = "#D64545"
LINE = "#E4E4E7"
WHITE = "#FFFFFF"

# Category tones (room → spa → fb lightness steps)
CAT_ROOM = NAVY
CAT_SPA = GOLD
CAT_FB = mix(NAVY, LINE, 0.55)

# Derived UI tokens
NAVY_MUTED = mix(NAVY, LINE, 0.45)
GOLD_TINT = mix(GOLD, WHITE, 0.9)
GOLD_BORDER = mix(GOLD, LINE, 0.35)
GOOD_TINT = mix(GOOD, WHITE, 0.88)
BAD_TINT = mix(BAD, WHITE, 0.88)
NEUTRAL_TINT = mix(PAPER, LINE, 0.4)
PRIOR = mix(NAVY, LINE, 0.65)

# Chart helpers
CHART_GRID = rgba(NAVY, 0.12)
CHART_GRID_STRONG = rgba(NAVY, 0.28)
SHADOW = rgba(NAVY, 0.08)

CSS_ROOT = f"""
    :root {{
        --navy: {NAVY};
        --gold: {GOLD};
        --paper: {PAPER};
        --good: {GOOD};
        --bad: {BAD};
        --line: {LINE};
        --white: {WHITE};
        --navy-muted: {NAVY_MUTED};
        --gold-tint: {GOLD_TINT};
        --gold-border: {GOLD_BORDER};
        --good-tint: {GOOD_TINT};
        --bad-tint: {BAD_TINT};
        --neutral-tint: {NEUTRAL_TINT};
        --cat-room: {CAT_ROOM};
        --cat-spa: {CAT_SPA};
        --cat-fb: {CAT_FB};
        --shadow: {SHADOW};
    }}
"""
