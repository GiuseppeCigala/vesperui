# Changelog

All notable changes to VesperUI are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-11-22

### Added

- Pure-Python Win32 toolkit built on `ctypes`, with no runtime dependencies.
- `App` window class, message loop, double-buffered painting, DPI awareness,
  timers, focus/hover tracking and test-injection helpers.
- Containers and layouts: `Panel`, `GroupBox`, `ScrollView`, `VBoxLayout`,
  `HBoxLayout`.
- Native controls: `TextBox`, `ComboBox`, `ListView` with in-place cell
  editing.
- Owner-drawn controls: `Button`, `Label`, `CheckBox`, `RadioButton`,
  `ToggleSwitch`, `Slider`, `ProgressBar`, `Stepper`, `ColorPicker`,
  `Hyperlink`, `Separator`, `TabBar`, `Knob`, `MixerSlider`.
- Audio widgets: `VUMeter`, `LevelMeter` (`BarVUMeter` alias),
  `SpectrumAnalyzer`, `MediaButton`, `TransportBar`.
- Graphics: retained-mode `Canvas` with line, rect, ellipse, circle and text
  primitives.
- Menus: `MenuBar` and `Menu`.
- Native dialogs: `info`, `warning`, `error`, `question`, `ok_cancel`,
  `open_file`, `open_files`, `save_file`, `select_folder`.
- `AURORA` and `FUSION` palettes plus `make_style` for deriving themes.
- Classic and audio showcases with a headless `--check` smoke mode.
- Automated `unittest` suite with 218 tests.
- Packaging metadata, MIT license, documentation and GitHub workflows.

### Fixed

- Fixed scroll repaint seams and hid native controls while dragging
  scrollbars.

[Unreleased]: https://github.com/GiuseppeCigala/vesperui/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/GiuseppeCigala/vesperui/releases/tag/v0.1.0
