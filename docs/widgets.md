# Widget reference

Every widget derives from `vesperui.common.Widget` (containers derive from
`Container`) and shares a few attributes:

- `x`, `y`, `w`, `h` — bounds in device-independent pixels (DIPs).
- `visible`, `enabled`, `focused`, `hovered` — interaction state.
- `stretch` — weight used by `VBoxLayout` / `HBoxLayout`.
- `measure(app)` — preferred size.
- `set_bounds(x, y, w, h)` — explicit placement, bypassing layout.

Callbacks follow a simple rule: value widgets receive the new value, action
widgets receive no arguments.

## Containers

### `Panel(layout=None, padding=0, bg=None, radius=0, shadow=False, gradient=None, border=None)`

Base container. Assign a `VBoxLayout` or `HBoxLayout` to `layout` and call
`add(widget)` for each child. `shadow=True` draws a soft shadow, `radius`
controls corner rounding.

### `GroupBox(title='', layout=None, padding=8, bg=None, border=None, radius=None)`

Draws a titled frame around its children. `add()` is forwarded to the inner
panel.

### `ScrollView(padding=8, spacing=8, bg=(245, 245, 245))`

Vertical scrolling container with owner-drawn scrollbars. Mouse wheel, drag
and keyboard scrolling are handled internally. Native Win32 children are
clipped to the viewport so they never overlap the scrollbars.

## Text and labels

### `Label(text='', size=14, bold=False, color=None, align='left')`

Owner-drawn text. `align` accepts `'left'`, `'center'` or `'right'`.

### `Hyperlink(text='', on_click=None, size=13, color=None)`

Underlined link-like widget with hover and keyboard activation.

### `Separator(orientation='h', color=None)`

One-pixel divider, horizontal or vertical.

## Input

### `TextBox(text='', multiline=False, on_change=None)`

Native `EDIT` control.

- `on_change(text)` is called with the new contents.
- `get_text()` / `set_text(text, notify=True)`
- `type_text(text)` — simulate typing, useful in tests.
- `multiline=True` adds a vertical scrollbar.

### `CheckBox(text='', checked=False, on_change=None)`

- `is_checked()` / `set_checked(value, notify=True)`

### `RadioButton(text='', checked=False, on_change=None, group=None)`

Pass the same `group` object to several radio buttons to make them mutually
exclusive.

### `ComboBox(items=None, on_change=None, index=0)`

Native combo box. `on_change(index, text)` is called when the selection
changes.

- `current_index()`, `current_text()`
- `set_index(index)`, `select(index)` — `select` also fires `on_change`.

### `Stepper(value=0, min=0, max=100, step=1, on_change=None, prefix='', suffix='')`

Numeric control with decrement/increment buttons and keyboard support.

- `set_value(value, notify=True)`, `increment()`, `decrement()`
- `prefix` and `suffix` surround the displayed value.

### `ColorPicker(color=(0, 214, 255), on_change=None)`

Hue/saturation/value picker.

- `get_color()`, `set_color(rgb, notify=True)`
- `set_hsv(hue, saturation, value, notify=True)`

Helper functions are exported as `hsv_to_rgb`, `rgb_to_hsv` and `rgb_to_hex`.

## Actions

### `Button(text='', on_click=None, accent=None)`

Owner-drawn button with hover, press, focus ring and Enter/Space activation.
A custom `accent` color overrides the palette highlight.

### `ToggleSwitch(checked=False, on_change=None, accent=None)`

Animated on/off switch.

- `is_checked()` / `set_checked(value, notify=True)`

### `MediaButton(icon='play', on_click=None, size=40, accent=None, active=False)`

Transport button. Icons: `'play'`, `'pause'`, `'stop'`, `'ff'`, `'rew'`.
Set the `active` attribute to highlight the current command.

### `TransportBar(on_command=None, on_play=None, on_pause=None, on_stop=None, on_ff=None, on_rew=None, spacing=8, button_size=40)`

A `Panel` containing the five media buttons. Per-command callbacks receive no
arguments; `on_command(name)` receives the command name.

- `set_active(name)` — highlight one command, `None` clears it.

## Values

### `Slider(value=0.0, on_change=None, accent=None, orientation='h')`

Continuous slider in the `0.0`–`1.0` range.

- `set_value(value, notify=True)`

### `ProgressBar(value=0.0, indeterminate=False, show_text=False, accent=None, orientation='h')`

- `set_value(value)`
- `tick(dt=0.03)` — advance the marquee when `indeterminate=True`; call it from
  an `App` timer.

### `Knob(value=0.0, on_change=None, show_value=True, formatter=None, accent=None)`

Rotary control in the `0.0`–`1.0` range.

- `set_value(value, notify=True)`
- `value_text()` — formatted display value.
- Mouse drag, mouse wheel and arrow keys adjust the value.

### `MixerSlider(value=0.0, on_change=None, orientation='v', min_db=-60.0, max_db=6.0)`

Mixer-style fader with a large cap and a non-linear dB scale.

- `db_to_fraction(db)` / `fraction_to_db(fraction)` (also module-level)
- `value_text()` — formatted dB display value.
- `vesperui.mixerslider` also provides `fader_db_to_fraction` and
  `fader_fraction_to_db`.

### `TabBar(items=None, index=0, on_change=None, accent=None)`

Segmented tab strip.

- `set_index(index, notify=True)`, `select(index)`

## Data

### `ListView(columns=None, rows=None, on_select=None, height=200, on_edit=None)`

Native `SysListView32` report view.

- `columns` is a list of `(title, width)` tuples.
- `rows` is a list of lists, one value per column.
- `on_select(index, row)` is called when a row is selected.
- `set_rows(rows)`, `get_selected_index()`, `get_selected_row()`,
  `select(index)` — `select` also fires `on_select`.
- Double-clicking a cell starts in-place editing. `on_edit(item, subitem, text)`
  is called when the edit is committed.

## Audio

### `VUMeter(value=0.0, on_change=None, label='VU', channel='L', scale=None, peak_hold=True, peak_hold_time=1.1, peak_decay=0.30)`

Analog needle meter with colored zones. The needle can be dragged or adjusted
with the arrow keys and mouse wheel.

- `set_value(value, notify=True)`, `reset_peak()`
- `tick(dt=0.05)` — advance peak-hold decay; call it from a timer.

### `LevelMeter(levels=(0.0, 0.0), orientation='v', labels=('L', 'R'), peak_hold=True, peak_hold_time=1.1, peak_decay=0.30, on_change=None, show_db=True)`

One or two segmented bars with a dB scale. `BarVUMeter` is an alias.

- `set_level(index, value, notify=True)`
- `set_levels(values, notify=True)`, `reset_peaks()`
- `tick(dt=0.05)` — advance peak hold.

### `SpectrumAnalyzer(bins=96, min_db=-60.0, max_db=-12.0, min_hz=20.0, max_hz=20000.0, attack=0.60, release=0.22, peak_hold_frames=10, peak_decay=0.01, body_color=None, cap_color=None, hot_color=None)`

Animated log-frequency spectrum with a dB grid, smoothed levels, transients and
peak caps.

- `set_spectrum(values, notify=True)` — normalized `0.0`–`1.0` values.
- `set_spectrum_db(db_values, notify=True)` — dB values.
- `db_to_fraction(db)`, `reset()`

## Graphics

### `Canvas(bg=(255, 255, 255), width=300, height=200)`

Retained-mode drawing surface. Coordinates are local to the canvas.

- `clear()`
- `line(x1, y1, x2, y2, color=(0, 0, 0), width=1)`
- `rect(x, y, w, h, color=(0, 0, 0), width=1, fill=None)`
- `ellipse(x, y, w, h, color=(0, 0, 0), width=1, fill=None)`
- `circle(cx, cy, r, color=(0, 0, 0), width=1, fill=None)`
- `text(x, y, text, size=14, color=(0, 0, 0), bold=False)`

Subclass `Canvas` and override `draw(hdc, app)` to run custom GDI code; call
`super().draw(hdc, app)` to render the retained items first.

## Menus and dialogs

See [Getting started](getting-started.md#menus) for `MenuBar` and `Menu`.
Dialogs are exposed as `App` methods and as module-level functions:

- `info`, `warning`, `error`, `question`, `ok_cancel`
- `open_file`, `open_files`, `save_file`, `select_folder`
