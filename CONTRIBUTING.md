# Contributing to VesperUI

Thanks for your interest in improving VesperUI! This document explains how to
set up the project, run the checks and submit changes.

## Before you start

- VesperUI runs on Windows 10/11 with Python 3.8+.
- The runtime package must stay dependency-free: only the Python standard
  library, `ctypes` and DLLs that ship with Windows.
- For larger changes, open an issue first so the approach can be discussed.
- By participating you agree to follow the
  [Code of Conduct](CODE_OF_CONDUCT.md).

## Development setup

```bash
git clone https://github.com/GiuseppeCigala/vesperui.git
cd vesperui
python -m pip install -e ".[dev]"
```

This installs the package in editable mode plus `build` and `twine` for
release checks. The test suite itself only needs the standard library.

## Running the checks

```bash
python run_tests.py -v
python showcase_common.py --check
python showcase_audio.py --check
```

- `run_tests.py` runs the `unittest` suite. Pass a module name
  (`python run_tests.py test_slider`) to focus on one area.
- `--check` builds the showcase interface and paints it into an off-screen
  bitmap without opening a window, which catches layout and GDI errors.

If you changed packaging metadata, also run:

```bash
python -m build
python -m twine check dist/*
```

After visual changes, regenerate the README screenshots with:

```bash
python tools/capture_screenshots.py
```

This renders both showcases off-screen and writes `docs/images/*.png`. It
requires Pillow, which is installed by the `dev` extra.

## Code style

- Follow the existing style: one widget per module, short methods, and
  `from .common import *` plus `from .style import style_of` in widget files.
- Use 4-space indentation and keep lines reasonably short.
- Read colors through `style_of(app)`; do not hard-code palette colors.
- Scale pixel metrics with `app.scale` so high-DPI displays keep working.
- Do not add comments that merely restate the code. Explain intent,
  constraints or Win32 quirks instead.
- Keep new runtime dependencies out of the package. Add development tools to
  the `dev` extra in `pyproject.toml` only if they are really needed.

## Adding or changing a widget

1. Implement `measure(app)` and `draw(hdc, app)`.
2. Implement interaction hooks (`on_mouse_*`, `on_key`, `on_wheel`) only when
   the widget needs them.
3. Re-export the class from `vesperui/__init__.py`.
4. Add a test under `tests/` using the memory-DC helper in
   `tests/helpers.py`.
5. Update `docs/widgets.md` and, if the behavior is user-visible, the README.
6. Add an entry to `CHANGELOG.md` under `Unreleased`.

## Tests

- Use `tests.helpers.WidgetTestCase` for owner-drawn widgets that can be
  painted off-screen.
- Use `tests.helpers.WindowTestCase` when a real (hidden) Win32 window is
  required, for example native controls.
- Prefer assertions on state and behavior over screenshots. Tests must not
  depend on timing, animations or the current desktop theme.
- Keep tests deterministic: see the DPI overrides at the top of
  `tests/helpers.py`.

## Submitting a change

1. Fork the repository and create a topic branch from `main`.
2. Make focused commits with imperative subject lines
   (for example, `Add peak-hold reset to LevelMeter`).
3. Run the full test suite and both showcase smoke checks.
4. Open a pull request that describes the problem, the change and how you
   validated it. Link any related issue.
5. Keep pull requests small when possible. Unrelated refactors should be
   separate.

## Reporting bugs

Please include:

- Windows version, Python version and VesperUI version.
- Whether the issue happens in a showcase, a test or your own application.
- A minimal reproduction, if possible.
- The full traceback, or the Win32 error code when one is reported.

Security issues should be reported privately; see [SECURITY.md](SECURITY.md).

## Feature requests

Describe the use case before the proposed API. Screenshots or mockups are
helpful for visual changes. New widgets should explain why an existing widget
or composition cannot solve the problem.

## License

By contributing, you agree that your contributions are licensed under the
[MIT License](LICENSE).
