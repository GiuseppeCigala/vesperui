# VesperUI

Native Windows widgets with an evening glow.

VesperUI is a pure-Python Windows GUI toolkit built on `ctypes` and the Win32
API. It combines native controls (TextBox, ComboBox, ListView) with
owner-drawn Aurora widgets (buttons, panels, tabs, toggles, sliders, canvas,
scroll views, progress bars) under one consistent dark visual style.

## Quick start

```python
import vesperui as ui

app = ui.App('Hello VesperUI', 640, 480)
app.root.add(ui.Label('Hello, world!', 20, True))
app.run()
```

## Widgets

- Containers: `Panel`, `GroupBox`, `ScrollView`, `VBoxLayout`, `HBoxLayout`
- Controls: `Button`, `Label`, `TextBox`, `CheckBox`, `RadioButton`,
  `ComboBox`, `ListView`, `Slider`, `ToggleSwitch`, `ProgressBar`, `TabBar`,
  `Hyperlink`, `Separator`
- Graphics: `Canvas`
- Menus: `MenuBar`, `Menu`
- Dialogs: `open_file`, `open_files`, `save_file`, `select_folder`, `info`,
  `warning`, `error`, `question`, `ok_cancel`

## Showcase

```bash
python showcase.py
python showcase.py --check   # off-screen layout and paint smoke test
```

## Tests

```bash
python run_tests.py
python run_tests.py -v
python run_tests.py test_dialogs
```

VesperUI requires Windows and Python 3.8+.
