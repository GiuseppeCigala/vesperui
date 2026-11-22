# Architecture

VesperUI is deliberately small. This page describes how the pieces fit
together so contributors can extend it without surprises.

## Module map

| Module | Responsibility |
| --- | --- |
| `vesperui/common.py` | Cross-cutting foundation for every other module: shared Win32 ctypes bindings, constants, structures, color helpers, GDI drawing primitives, DPI utilities, base `Widget` and `Container` classes |
| `vesperui/app.py` | Window class, window procedure, message loop, double buffering, layout orchestration, focus and hover tracking, timers, dialog helpers, test-injection helpers |
| `vesperui/native.py` | `_NativeWidget` base class for real Win32 child controls |
| `vesperui/layouts.py` | `VBoxLayout` and `HBoxLayout` |
| `vesperui/style.py` | `AURORA`, `FUSION`, `make_style` and `style_of` |
| `vesperui/*.py` | One owner-drawn widget per module |
| `vesperui/__init__.py` | Public re-exports; this is the only module users need to import |

`App` and the widgets import `common` with a star import. This is intentional:
`common` exposes the Win32 bindings and helpers that every widget needs, and
it keeps widget modules short.

## Object model

Everything visible is a `Widget` with `x`, `y`, `w`, `h`, `visible`,
`focusable`, `stretch` and interaction flags. Containers add a `children`
list, a `layout` attribute (on `Panel` and `GroupBox`) and forward `add()`.

Widgets implement two drawing-related methods:

- `measure(app)` returns the preferred `(width, height)` in pixels.
- `draw(hdc, app)` paints into the device context. It must only use the
  provided `hdc`.

Optional interaction hooks are `on_mouse_move`, `on_mouse_down`,
`on_mouse_up`, `on_key` and `on_wheel`.

## Layout pass

`App.layout()` arranges the root panel and then realizes any native children
that do not have an HWND yet. `Container.arrange()` recursively positions
children:

1. Each child reports its preferred size with `measure(app)`.
2. The layout distributes available space, honoring `padding`, `spacing` and
   `stretch`.
3. `set_bounds()` updates the child's rectangle. For native widgets this also
   repositions the underlying HWND.

`ScrollView` overrides the pass: it stacks children vertically, applies
`scroll_x` / `scroll_y`, and keeps native descendants clipped to the viewport
with `SetWindowRgn`.

## Painting

`WM_PAINT` is handled in `App._handle`:

1. The update region is captured.
2. A memory DC sized to the client area is reused as a back buffer.
3. The background is filled with `app.bg`.
4. The root container draws the whole tree into the memory DC.
5. The result is blitted to the window with `BitBlt`.

Owner-drawn widgets simply draw into the memory DC. Native widgets do not draw
their content; Windows paints them directly into the window, while the owner
draws their border and focus glow around the HWND. Partial repaints are
supported: `Container.draw` skips children that do not intersect the update
region, and `invalidate_rect` marks only the changed rectangle.

## Input, focus and capture

The window procedure hit-tests the widget tree from the root. The deepest
matching child receives mouse events. A mouse-down captures the target so
drags keep working outside the widget's bounds; mouse-up releases capture.
Hover state is tracked on `App.hovered` and mirrored to `widget.hovered`.

Tab and Shift+Tab cycle through `focusable` widgets. Enter and Space are
dispatched to `on_key` for activation, while arrows, Page Up/Down, Home/End and
the mouse wheel are handled by value widgets.

## Native controls

`_NativeWidget` creates a real `WS_CHILD` window of the class in `_win_class`
(for example `EDIT`, `COMBOBOX` or `SysListView32`). Every control gets a
unique child ID, and parent notifications are matched by HWND rather than by
ID, so collisions are impossible. Theme changes propagate through
`refresh_theme` and the `WM_CTLCOLOR*` handlers.

## DPI

`enable_dpi_awareness()` is called before the window is created. `app.scale`
holds the resulting scale factor (`DPI / 96`). Widgets multiply pixel metrics
by `app.scale` in `measure()` and `draw()`; fonts are created at the scaled
pixel size.

## Testability

The test suite has two levels:

- **Headless widget tests** paint into a memory DC created from the screen DC.
  This exercises layout, GDI calls and drawing code without showing a window.
- **Window tests** create a hidden real window (`app.create(show=False)`),
  pump messages and interact through `App.click`, `App.press_key` and
  `App.type_char`.

Both patterns live in `tests/helpers.py`.

## Adding a widget

1. Create `vesperui/yourwidget.py`.
2. Subclass `Widget` (or `Container`) and implement `measure` and `draw`.
3. Add `on_mouse_*`, `on_key` or `on_wheel` if the widget is interactive.
4. Re-export the class from `vesperui/__init__.py`.
5. Add a test under `tests/` using the memory-DC helper.
6. Document the constructor in `docs/widgets.md`.

Follow the existing modules for style: short functions, star import from
`common`, and colors read through `style_of(app)` rather than hard-coded.
