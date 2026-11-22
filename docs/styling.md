# Styling and themes

VesperUI ships with one dark palette, `AURORA`, and a `make_style` helper that
derives a coherent palette from four colors. Widgets never hard-code colors:
they read them from the `App` style through `style_of(app)`.

## Applying a palette

`App` starts with `AURORA`. To switch palette at runtime, assign the style and
the two cached background/text colors, then refresh the theme:

```python
import vesperui as ui

palette = ui.make_style({
    'bg': (250, 250, 252),
    'fg': (24, 28, 38),
    'card': (255, 255, 255),
    'panel': (242, 244, 248),
    'accent': ((0, 140, 255), (124, 92, 255)),
})

app.style = palette
app.bg = palette['window']
app.theme_fg = palette['windowText']
app.refresh_theme()
```

`refresh_theme()` clears cached brushes, updates dark-mode support for the
title bar and native controls, and invalidates the window.

## `make_style(palette)`

Accepted keys:

| Key | Required | Meaning |
| --- | --- | --- |
| `bg` | yes | Window background |
| `fg` | yes | Window text |
| `card` | no | Surface for native inputs and cards (defaults to `bg`) |
| `panel` | no | Surface for panels and buttons (defaults to `bg`) |
| `accent` | no | One RGB tuple or a `(start, end)` pair for gradients |
| `radius` | no | Default corner radius in DIPs (default `10`) |
| `inputRadius` | no | Native input corner radius (default `6`) |

The helper fills in hover, pressed, border, mid-tone, disabled, focus and glow
colors, and chooses readable text on top of the accent automatically.

## `AURORA` palette keys

A full style dictionary contains:

| Key | Purpose |
| --- | --- |
| `window`, `windowText` | Window background and text |
| `base`, `alternateBase` | Input/list backgrounds |
| `button`, `buttonText`, `buttonHover`, `buttonPressed` | Button states |
| `highlight`, `highlight2` | Primary and secondary accents |
| `highlightedText` | Text drawn on the accent |
| `border`, `mid`, `dark` | Borders and secondary strokes |
| `disabled`, `focus` | Disabled and focus-ring colors |
| `card`, `panel` | Surface colors |
| `radius`, `inputRadius` | Corner radii |
| `glow` | Outer glow for focused/hovered elements |

Every value except the radii is an `(r, g, b)` tuple with components in
`0`–`255`.

## Per-widget overrides

Most widgets accept an `accent` argument for a local highlight color:

```python
ui.Button('Primary', accent=(0, 200, 140))
ui.Slider(value=0.4, accent=(255, 120, 40))
ui.ToggleSwitch(checked=True, accent=(0, 200, 140))
```

Panels and group boxes accept `bg`, `border` and `radius`; `Label` and
`Hyperlink` accept `color`.

## Reading the active style

Custom widgets can use the same helpers as the built-in ones:

```python
from vesperui import style_of, mix, lighten, darken

def draw(self, hdc, app):
    st = style_of(app)
    background = st['panel']
    border = mix(st['border'], st['highlight'], 0.3)
```

`is_dark(color)` returns whether a color is perceptually dark; it is used to
pick shadows, contrast and dark-mode behavior.
