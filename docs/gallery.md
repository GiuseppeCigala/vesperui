# Widget gallery

Individual screenshots of every VesperUI widget class, rendered off-screen at
96 DPI from the code in this repository. Native Win32 controls are composited
into the same image, so `TextBox`, `ComboBox` and `ListView` appear exactly as
the library draws them.

Regenerate the whole gallery with:

```bash
python tools/capture_widgets.py
```

See the [widget reference](widgets.md) for constructors and methods. The
[classic](images/showcase-common.png) and [audio](images/showcase-audio.png)
showcases show complete interfaces built from these widgets.

> Menus and dialogs are native Win32 objects rather than widgets, so they are
> not part of this gallery. See [Getting started](getting-started.md#menus).

## Containers

### Panel

![Panel](images/widgets/panel.png)

Rounded surface with a gradient, soft shadow and border.

### GroupBox

![GroupBox](images/widgets/group-box.png)

Titled frame that forwards `add()` to its content panel.

### ScrollView

![ScrollView](images/widgets/scroll-view.png)

Scrollable container with custom scrollbars and native-control clipping.

## Text and labels

### Label

![Label](images/widgets/label.png)

Owner-drawn text with size, weight, color and alignment.

### Hyperlink

![Hyperlink](images/widgets/hyperlink.png)

Clickable, focusable link text with hover feedback.

### Separator

![Separator](images/widgets/separator.png)

Horizontal and vertical one-pixel dividers.

## Input

### TextBox

![TextBox](images/widgets/textbox.png)

Native single-line and multiline `EDIT` controls.

### CheckBox

![CheckBox](images/widgets/checkbox.png)

Check box with a label and change callback.

### RadioButton

![RadioButton](images/widgets/radio-button.png)

Radio buttons sharing a group token.

### ComboBox

![ComboBox](images/widgets/combo-box.png)

Native combo box with an `on_change(index, text)` callback.

### Stepper

![Stepper](images/widgets/stepper.png)

Numeric stepper with decrement/increment buttons and prefix/suffix support.

### ColorPicker

![ColorPicker](images/widgets/color-picker.png)

Hue, saturation and value picker with a color preview.

## Actions

### Button

![Button](images/widgets/button.png)

Owner-drawn button with hover, press, focus ring and keyboard activation.

### ToggleSwitch

![ToggleSwitch](images/widgets/toggle-switch.png)

Animated on/off switch, shown in both states.

### MediaButton

![MediaButton](images/widgets/media-button.png)

All five transport icons: rewind, play, pause, stop and fast-forward.

### TransportBar

![TransportBar](images/widgets/transport-bar.png)

Rewind, play, pause, stop and fast-forward in one panel.

## Values

### Slider

![Slider](images/widgets/slider.png)

Horizontal and vertical sliders in the `0.0`–`1.0` range.

### ProgressBar

![ProgressBar](images/widgets/progress-bar.png)

Horizontal and vertical progress bars, with optional text.

### Knob

![Knob](images/widgets/knob.png)

Rotary control with an accent ring, pointer and value plate.

### MixerSlider

![MixerSlider](images/widgets/mixer-slider.png)

Non-linear dB fader with a large gray-gradient cap.

### TabBar

![TabBar](images/widgets/tab-bar.png)

Segmented tab strip with a selection callback.

## Data

### ListView

![ListView](images/widgets/list-view.png)

Native report view with row selection and in-place cell editing.

## Audio

### VUMeter

![VUMeter](images/widgets/vu-meter.png)

Analog needle meter with peak hold, drag and arrow-key adjustment.

### LevelMeter

![LevelMeter](images/widgets/level-meter.png)

Segmented dB meters in vertical and horizontal orientations, using the soft
Aurora scale.

### SpectrumAnalyzer

![SpectrumAnalyzer](images/widgets/spectrum-analyzer.png)

Log-frequency bars with a dB grid, transients and peak caps. The bars use the
same teal-to-violet gradient vertically, from low levels to high levels.

## Graphics

### Canvas

![Canvas](images/widgets/canvas.png)

Retained-mode line, rectangle, ellipse, circle and text primitives.
