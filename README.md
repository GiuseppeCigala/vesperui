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
  `Hyperlink`, `Separator`, `Stepper`, `ColorPicker`, `VUMeter`,
  `LevelMeter`, `MixerSlider`, `Knob`, `MediaButton`, `TransportBar`
- Graphics: `Canvas`
- Menus: `MenuBar`, `Menu`
- `ListView` cells can be edited in place by double-clicking them.
- Dialogs: `open_file`, `open_files`, `save_file`, `select_folder`, `info`,
  `warning`, `error`, `question`, `ok_cancel`

Sliders and progress bars support `orientation="h"` and
`orientation="v"`. The `VUMeter` is an analog needle meter that can be
dragged with the mouse or adjusted with the arrow keys; it also shows a
peak-hold marker that falls back to the needle after a short hold. The
`LevelMeter` (alias `BarVUMeter`) draws one or two segmented bars with a
dB scale in either orientation, with the same peak-hold behaviour. The
`MixerSlider` is a mixer-style fader with a large cap and a non-linear dB
scale (6, 0, 5, 10, 15, 20, 30, 40, ∞). The `Knob` is a rotary control with
a dark bezel, an accent ring, a white pointer and a value plate below.
`MediaButton` draws play, pause, stop, rewind and fast-forward icons, and
`TransportBar` groups the five buttons with per-command callbacks.

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
