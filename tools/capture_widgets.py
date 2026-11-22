"""Generate one documentation screenshot per VesperUI widget class.

Usage (from the repository root, on Windows):

    python tools/capture_widgets.py

Images are written to ``docs/images/widgets/``. The script reuses the
off-screen capture pipeline from ``capture_screenshots.py`` so native Win32
controls are composited too. Pillow is used only to save PNGs.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import vesperui as ui
from capture_screenshots import capture
import showcase_audio

STYLE = ui.AURORA
MID = STYLE["mid"]
ACCENT = STYLE["highlight"]
ACCENT2 = STYLE["highlight2"]


class GalleryScrollView(ui.ScrollView):
    """Larger ScrollView used only for the gallery screenshot."""

    def measure(self, app):
        return (int(320 * app.scale), int(220 * app.scale))


class GalleryCanvas(ui.Canvas):
    """Canvas that seeds a sample scene once it knows its final size."""

    def __init__(self):
        super().__init__(bg=STYLE["base"], width=620, height=220)
        self._seeded = False

    def draw(self, hdc, app):
        if not self._seeded and self.w > 0 and self.h > 0:
            w, h = self.w, self.h
            self.rect(14, 14, w - 28, h - 28, color=STYLE["border"])
            self.line(24, h - 24, w - 24, 24, color=STYLE["mid"], width=2)
            self.circle(int(w * 0.30), int(h * 0.52), 36,
                        color=STYLE["highlight"], fill=STYLE["panel"])
            self.ellipse(int(w * 0.60), int(h * 0.28), 130, 86,
                         color=STYLE["highlight2"], fill=STYLE["card"])
            self.text(24, 18, "Canvas primitives", size=14, bold=True,
                      color=STYLE["windowText"])
            self._seeded = True
        super().draw(hdc, app)


def _page(app, title, subtitle):
    app.root.layout = ui.VBoxLayout(padding=22, spacing=12)
    app.root.add(ui.Label(title, 20, True))
    app.root.add(ui.Label(subtitle, 12, color=MID))
    app.root.add(ui.Separator())


def _row(spacing=12):
    return ui.Panel(layout=ui.HBoxLayout(padding=0, spacing=spacing))


def _spacer(row, stretch=1):
    spacer = ui.Panel()
    spacer.stretch = stretch
    row.add(spacer)
    return spacer


def build_button(app):
    row = _row()
    row.add(ui.Button("Default"))
    row.add(ui.Button("Primary", accent=ACCENT))
    row.add(ui.Button("Secondary", accent=ACCENT2))
    _spacer(row)
    app.root.add(row)
    app.root.add(ui.Label("Hover, press, focus ring and Enter/Space activation.",
                          12, color=MID))


def build_label(app):
    app.root.add(ui.Label("Display text", 24, True))
    app.root.add(ui.Label("Secondary text in the muted palette.", 14,
                          color=MID))
    app.root.add(ui.Label("Right aligned", 14, align="right"))


def build_textbox(app):
    app.root.add(ui.Label("Single line", 12, True, color=MID))
    app.root.add(ui.TextBox("Ada Lovelace"))
    app.root.add(ui.Label("Multiline", 12, True, color=MID))
    app.root.add(ui.TextBox(
        "Write a few lines here...\r\n"
        "The native EDIT control keeps clipboard, IME and accessibility "
        "support.", multiline=True))


def build_checkbox(app):
    app.root.add(ui.CheckBox("Enable notifications", checked=True))
    app.root.add(ui.CheckBox("Show grid lines"))
    app.root.add(ui.CheckBox("Start with the last document"))


def build_radio(app):
    group = object()
    app.root.add(ui.RadioButton("Compact", group=group))
    app.root.add(ui.RadioButton("Comfortable", checked=True, group=group))
    app.root.add(ui.RadioButton("Spacious", group=group))
    app.root.add(ui.Label("Buttons with the same group are mutually exclusive.",
                          12, color=MID))


def build_combobox(app):
    row = _row()
    row.add(ui.Label("Theme", 14))
    row.add(ui.ComboBox(["Aurora Dark", "Fusion", "Light"], index=0))
    _spacer(row)
    app.root.add(row)
    app.root.add(ui.Label("on_change(index, text) fires on CBN_SELCHANGE.",
                          12, color=MID))


def build_listview(app):
    rows = [
        ["Button", "owner-drawn", "click, hover, keyboard"],
        ["TextBox", "native", "typing, EN_CHANGE"],
        ["ComboBox", "native", "CBN_SELCHANGE"],
        ["ListView", "native", "row selection, in-place edit"],
        ["ToggleSwitch", "owner-drawn", "animated knob"],
        ["Knob", "owner-drawn", "drag, wheel, arrow keys"],
    ]
    app.root.add(ui.ListView(
        columns=[("Widget", 180), ("Kind", 110), ("Behaviour", 260)],
        rows=rows, height=220))
    app.root.add(ui.Label("Double-click a cell to edit it in place.",
                          12, color=MID))


def build_slider(app):
    row = _row()
    row.add(ui.Label("Horizontal", 13))
    horizontal = ui.Slider(value=0.45)
    horizontal.stretch = 1
    row.add(horizontal)
    row.add(ui.Label("45%", 13, color=ACCENT))
    app.root.add(row)

    row = _row()
    row.add(ui.Label("Vertical", 13))
    vertical = ui.Slider(value=0.65, orientation="v")
    row.add(vertical)
    _spacer(row)
    app.root.add(row)
    app.root.add(ui.Label("Drag, click the track, use the wheel or arrow keys.",
                          12, color=MID))


def build_toggle(app):
    for label, checked in (("Wi-Fi", True), ("Bluetooth", False)):
        row = _row()
        row.add(ui.Label(label, 14))
        row.add(ui.ToggleSwitch(checked=checked))
        _spacer(row)
        app.root.add(row)
    app.root.add(ui.Label("Animated on/off switch with Space/Enter activation.",
                          12, color=MID))


def build_progress(app):
    app.root.add(ui.Label("Horizontal", 12, True, color=MID))
    app.root.add(ui.ProgressBar(value=0.62, show_text=True))
    app.root.add(ui.Label("Vertical", 12, True, color=MID))
    row = _row()
    row.add(ui.ProgressBar(value=0.40, orientation="v"))
    _spacer(row)
    app.root.add(row)


def build_tabbar(app):
    app.root.add(ui.TabBar(["Overview", "Details", "Diagnostics"], index=0))
    app.root.add(ui.Label("Selected tab: Overview", 13, color=MID))


def build_hyperlink(app):
    app.root.add(ui.Hyperlink("Open the documentation", on_click=lambda: None))
    app.root.add(ui.Hyperlink("Report an issue", on_click=lambda: None,
                              color=ACCENT2))
    app.root.add(ui.Label("Clickable, focusable and activated with Enter/Space.",
                          12, color=MID))


def build_separator(app):
    app.root.add(ui.Label("Horizontal separator", 13))
    app.root.add(ui.Separator())
    row = _row()
    row.add(ui.Label("Left", 13))
    row.add(ui.Separator(orientation="v"))
    row.add(ui.Label("Right", 13))
    _spacer(row)
    app.root.add(row)


def build_stepper(app):
    row = _row()
    row.add(ui.Label("Quantity", 14))
    row.add(ui.Stepper(value=3, min=0, max=10, suffix=" items"))
    _spacer(row)
    app.root.add(row)
    app.root.add(ui.Label("Click the arrows or use the arrow keys.",
                          12, color=MID))


def build_colorpicker(app):
    row = _row()
    row.add(ui.ColorPicker((0, 214, 255)))
    _spacer(row)
    app.root.add(row)
    app.root.add(ui.Label("Selected color: %s" % ui.rgb_to_hex((0, 214, 255)),
                          13, color=ACCENT))


def build_vumeter(app):
    row = _row()
    meter = ui.VUMeter(value=0.62, label="VU")
    row.add(meter)
    _spacer(row)
    app.root.add(row)
    app.root.add(ui.Label("Analog needle with peak hold, drag and arrow keys.",
                          12, color=MID))


def build_levelmeter(app):
    row = _row()
    row.add(ui.LevelMeter(levels=(0.55, 0.72), labels=("L", "R")))
    _spacer(row)
    app.root.add(row)

    row = _row()
    row.add(ui.LevelMeter(levels=(0.42, 0.68, 0.51), orientation="h",
                          labels=("L", "C", "R")))
    _spacer(row)
    app.root.add(row)
    app.root.add(ui.Label("Segmented dB meters in vertical and horizontal "
                          "orientations.", 12, color=MID))


def build_mixerslider(app):
    row = _row()
    row.add(ui.MixerSlider(value=0.0))
    _spacer(row)
    app.root.add(row)
    app.root.add(ui.Label("Non-linear dB fader with a large cap.",
                          12, color=MID))


def build_knob(app):
    row = _row()
    row.add(ui.Knob(value=0.65))
    _spacer(row)
    app.root.add(row)
    app.root.add(ui.Label("Rotary control: drag, wheel or arrow keys.",
                          12, color=MID))


def build_media_button(app):
    row = _row(spacing=22)
    for icon in ("rew", "play", "pause", "stop", "ff"):
        column = ui.Panel(layout=ui.VBoxLayout(padding=0, spacing=6))
        column.add(ui.MediaButton(icon, size=44, active=(icon == "play")))
        column.add(ui.Label(icon.upper(), 11, align="center", color=MID))
        row.add(column)
    _spacer(row)
    app.root.add(row)
    app.root.add(ui.Label("Five transport icons with an active highlight.",
                          12, color=MID))


def build_transport_bar(app):
    bar = ui.TransportBar(button_size=44)
    bar.set_active("play")
    app.root.add(bar)
    app.root.add(ui.Label("on_command receives play, pause, stop, rew or ff.",
                          12, color=MID))


def build_spectrum(app):
    spectrum = ui.SpectrumAnalyzer(bins=72)
    spectrum.set_spectrum(showcase_audio.synthetic_spectrum(72, 1.7),
                          notify=False)
    app.root.add(spectrum)
    app.root.add(ui.Label("Log-frequency bars with dB grid, transient and "
                          "peak caps.", 12, color=MID))


def build_canvas(app):
    app.root.add(GalleryCanvas())


def build_panel(app):
    card = ui.Panel(
        layout=ui.VBoxLayout(padding=16, spacing=8),
        gradient=(STYLE["card"], STYLE["panel"]),
        radius=14, shadow=True, border=STYLE["border"])
    card.add(ui.Label("Panel card", 16, True))
    card.add(ui.Label("Rounded corners, soft shadow and a border.", 12,
                      color=MID))
    card.add(ui.Button("Action"))
    app.root.add(card)


def build_groupbox(app):
    group = ui.GroupBox("Account", bg=STYLE["card"],
                        layout=ui.VBoxLayout(padding=12, spacing=8))
    group.add(ui.Label("Signed in as Ada Lovelace", 14))
    group.add(ui.CheckBox("Remember this device", checked=True))
    group.add(ui.Button("Sign out"))
    app.root.add(group)


def build_scrollview(app):
    view = GalleryScrollView(padding=10, spacing=8, bg=STYLE["panel"])
    for index in range(10):
        view.add(ui.Label("Row %02d - scroll with the wheel, drag the bar or "
                          "use the arrow keys." % (index + 1), 12))
    app.root.add(view)


WIDGETS = [
    ("button", "Button", "Owner-drawn button with hover, press and focus "
     "states.", (720, 300), build_button),
    ("label", "Label", "Owner-drawn text with size, weight, color and "
     "alignment.", (720, 300), build_label),
    ("textbox", "TextBox", "Native single-line and multiline EDIT controls.",
     (720, 430), build_textbox),
    ("checkbox", "CheckBox", "Check box with a label and change callback.",
     (720, 300), build_checkbox),
    ("radio-button", "RadioButton", "Radio buttons sharing a group token.",
     (720, 340), build_radio),
    ("combo-box", "ComboBox", "Native combo box with an on_change callback.",
     (720, 300), build_combobox),
    ("list-view", "ListView", "Native report view with editable cells.",
     (760, 450), build_listview),
    ("slider", "Slider", "Horizontal and vertical sliders in the 0-1 range.",
     (720, 480), build_slider),
    ("toggle-switch", "ToggleSwitch", "Animated on/off switch in both states.",
     (720, 320), build_toggle),
    ("progress-bar", "ProgressBar", "Horizontal and vertical progress bars.",
     (720, 520), build_progress),
    ("tab-bar", "TabBar", "Segmented tab strip with selection callback.",
     (720, 300), build_tabbar),
    ("hyperlink", "Hyperlink", "Clickable and keyboard-activated link text.",
     (720, 280), build_hyperlink),
    ("separator", "Separator", "Horizontal and vertical separator lines.",
     (720, 360), build_separator),
    ("stepper", "Stepper", "Numeric stepper with prefix and suffix support.",
     (720, 300), build_stepper),
    ("color-picker", "ColorPicker", "Hue, saturation and value picker.",
     (720, 420), build_colorpicker),
    ("vu-meter", "VUMeter", "Analog needle meter with peak hold.",
     (720, 420), build_vumeter),
    ("level-meter", "LevelMeter", "Segmented dB meters, vertical and "
     "horizontal.", (760, 620), build_levelmeter),
    ("mixer-slider", "MixerSlider", "Non-linear dB fader with a large cap.",
     (720, 560), build_mixerslider),
    ("knob", "Knob", "Rotary control with an accent ring and value plate.",
     (720, 400), build_knob),
    ("media-button", "MediaButton", "All five transport icons.",
     (760, 340), build_media_button),
    ("transport-bar", "TransportBar", "Rewind, play, pause, stop and "
     "fast-forward.", (720, 320), build_transport_bar),
    ("spectrum-analyzer", "SpectrumAnalyzer", "Log-frequency spectrum with "
     "dB grid and peaks.", (780, 440), build_spectrum),
    ("canvas", "Canvas", "Retained-mode line, rect, ellipse, circle and text "
     "primitives.", (760, 440), build_canvas),
    ("panel", "Panel", "Rounded surface with gradient, shadow and border.",
     (720, 380), build_panel),
    ("group-box", "GroupBox", "Titled container that forwards add() to its "
     "content.", (720, 400), build_groupbox),
    ("scroll-view", "ScrollView", "Scrollable container with custom "
     "scrollbars.", (720, 440), build_scrollview),
]


def main():
    out_dir = os.path.join(ROOT, "docs", "images", "widgets")
    os.makedirs(out_dir, exist_ok=True)
    for name, title, subtitle, size, build in WIDGETS:
        app = ui.App(title, size[0], size[1])
        _page(app, title, subtitle)
        build(app)
        capture(app, os.path.join(out_dir, name + ".png"), max_width=2000,
                trim=True)
    print("generated %d widget screenshots" % len(WIDGETS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
