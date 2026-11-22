# Getting started

This guide walks through a first VesperUI application and the concepts shared
by every widget.

## Install

```bash
python -m pip install vesperui
```

For development, clone the repository and install it in editable mode:

```bash
git clone https://github.com/GiuseppeCigala/vesperui.git
cd vesperui
python -m pip install -e ".[dev]"
```

VesperUI targets Windows 10/11 and Python 3.8+. Importing it on another
platform raises an `ImportError` with an explanatory message.

## Your first window

```python
import vesperui as ui

app = ui.App('Hello VesperUI', 640, 480)
app.root.add(ui.Label('Hello, world!', 20, True))
app.run()
```

`ui.App` creates the window class, the message loop and a root `Panel`.
`app.root` already uses a `VBoxLayout` with 12 px padding and 8 px spacing, so
children are stacked vertically by default.

`app.run()` is blocking: it creates the window and pumps Windows messages
until the user closes it. Use `app.create()` and `app.pump()` when you want to
drive the window yourself (for example in tests).

A complete runnable version of this first window is in
[`examples/hello.py`](../examples/hello.py); run it with
`python examples/hello.py`.

## Containers and layouts

A layout is an object assigned to a container's `layout` attribute. It
positions the container's children when the window is created or resized.

```python
app.root.layout = ui.VBoxLayout(padding=16, spacing=10)

row = ui.Panel(layout=ui.HBoxLayout(padding=0, spacing=10))
row.add(ui.Label('Name', 14))
row.add(ui.TextBox('VesperUI'))
row.add(ui.Button('OK'))

app.root.add(row)
```

- `VBoxLayout(padding=8, spacing=8)` stacks children vertically.
- `HBoxLayout(padding=8, spacing=8)` places children side by side.
- Containers are `Panel`, `GroupBox`, `ScrollView` and the root panel.
- `GroupBox` forwards `add()` to an inner panel, so an optional title and
  border are drawn around the group automatically.
- `ScrollView` gives its children a vertical stack and adds scrollbars when
  the content overflows. Native controls are clipped to the viewport.

Widgets have a `stretch` attribute used by the layouts; setting
`widget.stretch = 1` lets it absorb the remaining space in the main axis.

## Controls and callbacks

Callbacks are ordinary Python callables. Widgets that hold a value receive the
new value; buttons and links receive no arguments.

```python
slider = ui.Slider(value=0.25, on_change=lambda v: print('slider', v))
toggle = ui.ToggleSwitch(checked=True, on_change=lambda v: print('toggle', v))
combo = ui.ComboBox(['One', 'Two', 'Three'],
                    on_change=lambda index, text: print('combo', index, text))
button = ui.Button('Run', on_click=lambda: print('clicked'))
```

Most value widgets receive the new value (`Slider`, `Stepper`, `ColorPicker`,
`TabBar`, toggles and check boxes), and `TextBox` receives the new text.
`ComboBox` receives `(index, text)` and `ListView` receives `(index, row)`.
Widgets also expose state accessors such as `set_checked`/`is_checked`,
`set_value`, `set_index`/`current_index` and `select`. Pass `notify=False` to
setters when you do not want to fire the change callback.

Focusable widgets (buttons, text boxes, sliders, toggles) participate in Tab
navigation automatically.

## Dialogs

Dialogs are available both as functions and as `App` methods. They use the
native Windows common dialogs, so they follow the system theme and language.

```python
app.info('Saved successfully.')
app.warning('Disk is almost full.')
if app.question('Delete the selected row?'):
    ...

path = app.open_file('Open', [('Text files', '*.txt'), ('All files', '*.*')])
path = app.save_file('Save as', default_name='notes.txt')
folder = app.select_folder('Choose a folder')
```

The module-level functions (`ui.open_file(...)`, `ui.info(...)`) accept an
optional `parent` and return `None` (or an empty list) when the user cancels.

## Menus

```python
file_menu = app.menubar.add('File')
file_menu.add_item('Open...', lambda: app.open_file())
file_menu.add_item('Save', lambda: print('save'))
file_menu.add_separator()
file_menu.add_item('Exit', app.destroy)
```

The menu bar is attached to the window when it is created, so build menus
before calling `app.run()` or `app.create()`.

## Timers

`App.set_timer(ms, callback)` registers a repeating Win32 timer. Callbacks
take no arguments and are stored in registration order.

```python
app.set_timer(500, lambda: print('tick'))
```

## Testing without a visible window

The package is designed to be testable headlessly:

```python
app = ui.App('Test', 640, 480)
app.create(show=False)
app.pump()

button = ui.Button('OK', on_click=lambda: print('clicked'))
app.add(button)
app.layout()
app.click_widget(button)

app.destroy()
```

Owner-drawn widgets can also be painted into a memory DC, which is what the
bundled test suite does. See `tests/helpers.py` for a compact example.

## High DPI

DPI awareness is enabled before the window is created. `app.scale` holds the
current scale factor and should be used when custom drawing code needs
pixel-accurate metrics. VesperUI's own widgets already account for it.

## Next steps

- [Widget reference](widgets.md)
- [Styling and themes](styling.md)
- [Architecture](architecture.md)
