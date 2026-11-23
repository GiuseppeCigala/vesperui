"""Modern "Aurora" visual style (dark-first, neon accents, soft glow)."""
from .common import is_dark, lighten, darken, mix

AURORA = {
    'window': (18, 20, 28),
    'windowText': (236, 240, 248),
    'base': (28, 31, 42),
    'alternateBase': (34, 38, 50),
    'button': (35, 39, 52),
    'buttonText': (236, 240, 248),
    'buttonHover': (45, 50, 68),
    'buttonPressed': (28, 32, 43),
    'highlight': (0, 214, 255),
    'highlight2': (124, 92, 255),
    'highlightedText': (6, 10, 18),
    'border': (58, 65, 84),
    'mid': (92, 102, 128),
    'dark': (146, 156, 182),
    'disabled': (110, 118, 138),
    'focus': (0, 214, 255),
    'card': (26, 29, 39),
    'panel': (22, 25, 34),
    'radius': 10,
    'inputRadius': 6,
    'glow': (18, 76, 96),
}

# Backwards-compatible alias.
FUSION = AURORA


# Separation point of the shared teal-to-violet scale (0 dB on the VU meter).
SCALE_SPLIT = 0.62


def scale_color(style, fraction):
    """Soft teal-to-violet color for a 0..1 level or scale position.

    The stops derive from the Aurora ``highlight`` and ``highlight2`` colors
    blended with the panel background, so meters and analyzers stay readable
    without glowing.
    """
    low = mix(style['highlight'], style['panel'], 0.30)
    mid = mix(mix(style['highlight'], style['highlight2'], 0.55),
              style['panel'], 0.18)
    high = mix(style['highlight2'], style['panel'], 0.24)
    fraction = max(0.0, min(1.0, float(fraction)))
    split = SCALE_SPLIT
    if fraction <= split:
        return mix(low, mid, fraction / split)
    return mix(mid, high, (fraction - split) / (1.0 - split))


def make_style(palette):
    """Build a coherent modern style from a simple theme palette."""
    bg = palette['bg']
    fg = palette['fg']
    card = palette.get('card', bg)
    panel = palette.get('panel', bg)
    accent = palette.get('accent', (AURORA['highlight'], AURORA['highlight2']))
    if isinstance(accent, (tuple, list)) and accent and isinstance(accent[0], (tuple, list)):
        h1 = tuple(accent[0])
        h2 = tuple(accent[1]) if len(accent) > 1 else h1
    else:
        h1 = h2 = tuple(accent)
    dark = is_dark(fg)
    return {
        'window': bg,
        'windowText': fg,
        'base': card,
        'alternateBase': mix(card, bg, 0.5),
        'button': panel if dark else mix(card, bg, 0.15),
        'buttonText': fg,
        'buttonHover': lighten(panel, 0.09) if dark else lighten(panel, 0.04),
        'buttonPressed': darken(panel, 0.08) if dark else darken(panel, 0.05),
        'highlight': h1,
        'highlight2': h2,
        'highlightedText': (8, 12, 20) if is_dark(h1) else (255, 255, 255),
        'border': lighten(panel, 0.22) if dark else darken(panel, 0.16),
        'mid': lighten(panel, 0.38) if dark else darken(panel, 0.30),
        'dark': lighten(panel, 0.55) if dark else darken(panel, 0.50),
        'disabled': mix(fg, bg, 0.55),
        'focus': h1,
        'card': card,
        'panel': panel,
        'radius': palette.get('radius', 10),
        'inputRadius': palette.get('inputRadius', 6),
        'glow': mix(bg, h1, 0.45),
    }


def style_of(app):
    return getattr(app, 'style', AURORA)
