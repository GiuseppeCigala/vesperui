"""pywinui - component test suite.

Exercises every public component and feature provided by pywinui.py:

  - App lifecycle, DPI scaling, invalidation, timers, theme refresh
  - Panel, VBoxLayout, HBoxLayout (padding, spacing, stretch)
  - Label (size, bold, color, alignment)
  - Button (default and custom accent, click callbacks)
  - TextBox (single-line, multi-line, get_text / set_text, on_change)
  - CheckBox (is_checked / set_checked, on_change)
  - RadioButton (native group, on_change)
  - ComboBox (items, current_index / current_text / set_index, on_change)
  - ListView (columns, rows, selection, set_rows, get_selected_row)
  - Canvas (line, rect, ellipse, circle, text) driven by a timer
  - ScrollView (vertical + horizontal scrolling, clipped native children)
  - ProgressBar (determinate + indeterminate)
  - Slider (mouse drag and keyboard)
  - ToggleSwitch (checked / set_checked, on_change)
  - GroupBox (titled container with layout)
  - Separator (horizontal / vertical)
  - Hyperlink (clickable label)
  - TabBar (tabs with selection)
  - MenuBar / Menu (items, separators, callbacks)
  - Theme switching (refresh_theme) across all themed widgets

Run with:  python test_all.py
"""
import pywinui as ui


THEMES = {
    'Aurora': {
        'bg': (18, 20, 28),
        'fg': (236, 240, 248),
        'card': (26, 29, 39),
        'panel': (22, 25, 34),
        'accent': ((0, 214, 255), (124, 92, 255)),
    },
    'Aurora Light': {
        'bg': (244, 246, 251),
        'fg': (22, 26, 36),
        'card': (255, 255, 255),
        'panel': (238, 242, 248),
        'accent': ((16, 120, 255), (124, 92, 255)),
    },
    'Nebula': {
        'bg': (24, 16, 38),
        'fg': (240, 232, 255),
        'card': (34, 24, 52),
        'panel': (28, 20, 44),
        'accent': ((190, 80, 255), (255, 80, 180)),
    },
    'Cyber': {
        'bg': (10, 24, 26),
        'fg': (220, 255, 246),
        'card': (16, 36, 38),
        'panel': (13, 30, 32),
        'accent': ((0, 255, 180), (0, 180, 255)),
    },
}

ROWS = [
    ['Ada Lovelace', '36', 'London'],
    ['Alan Turing', '41', 'Manchester'],
    ['Grace Hopper', '45', 'New York'],
    ['Linus Torvalds', '34', 'Helsinki'],
    ['Margaret Hamilton', '38', 'Boston'],
    ['Guido van Rossum', '47', 'Amsterdam'],
]


def main():
    app = ui.App('pywinui - component test suite', 1120, 780)

    state = {
        'theme': 'Aurora',
        'grid': True,
        'ticks': 0,
        'frame': 0,
        'ball': {'x': 40.0, 'y': 40.0, 'vx': 2.4, 'vy': 1.7, 'r': 12},
    }

    # Widgets whose colors follow the active theme.
    themed_labels = []
    themed_cards = []
    themed_panels = []
    themed_gradients = []

    def themed_label(text='', **kwargs):
        label = ui.Label(text, **kwargs)
        themed_labels.append(label)
        return label

    status = themed_label('Ready.', size=13)

    def set_status(text):
        status.text = text
        app.invalidate_rect(status.x, status.y, status.w, status.h)

    def apply_theme(name):
        palette = THEMES[name]
        state['theme'] = name
        app.bg = palette['bg']
        app.theme_fg = palette['fg']
        app.style = ui.make_style(palette)
        for label in themed_labels:
            label.color = palette['fg']
        for panel in themed_cards:
            panel.bg = palette['card']
        for panel in themed_panels:
            panel.bg = palette['panel']
        for panel in themed_gradients:
            panel.gradient = palette['accent']
        app.refresh_theme()

    # -----------------------------------------------------------------------
    # Header
    # -----------------------------------------------------------------------
    title = themed_label('pywinui - component test suite', size=22, bold=True)
    subtitle = ui.Label('Every public widget in one window. Press Tab to cycle focus.',
                        size=12, color=(110, 116, 126))
    app.add(title)
    app.add(subtitle)

    # -----------------------------------------------------------------------
    # Form controls: ComboBox, CheckBox, Buttons, Label
    # -----------------------------------------------------------------------
    controls = ui.Panel(layout=ui.HBoxLayout(padding=0, spacing=10))
    controls.add(themed_label('Theme:', size=14))

    theme_combo = ui.ComboBox(
        items=list(THEMES.keys()), index=0,
        on_change=lambda index, text: (apply_theme(text),
                                       set_status(f'Theme: {text}')))
    controls.add(theme_combo)

    def on_grid_change(checked):
        state['grid'] = checked
        set_status(f'Grid: {"on" if checked else "off"}')
        app.invalidate_rect(ball_canvas.x, ball_canvas.y,
                            ball_canvas.w, ball_canvas.h)

    grid_check = ui.CheckBox('Animate grid', checked=True, on_change=on_grid_change)
    controls.add(grid_check)

    def toggle_grid():
        new_value = not grid_check.is_checked()
        grid_check.set_checked(new_value, notify=False)
        on_grid_change(new_value)

    controls.add(ui.Button('Toggle grid', on_click=toggle_grid))
    controls.add(ui.Button('Reset', accent=(124, 92, 255), on_click=lambda: reset_all()))

    ticks_label = themed_label('Timer: 0', size=12)
    ticks_label.measure = lambda a: (a.measure_text('Timer: 0000', 12)[0] + int(4 * a.scale),
                                     a.measure_text('Ag', 12)[1] + int(4 * a.scale))
    controls.add(ticks_label)
    app.add(controls)

    # -----------------------------------------------------------------------
    # Label alignment
    # -----------------------------------------------------------------------
    align_row = ui.Panel(layout=ui.HBoxLayout(padding=0, spacing=8))
    align_row.add(themed_label('align=left', size=12, align='left'))
    centered = themed_label('align=center', size=12, align='center')
    centered.stretch = 1
    align_row.add(centered)
    align_row.add(themed_label('align=right', size=12, align='right'))
    app.add(align_row)

    # -----------------------------------------------------------------------
    # Split: ListView + multi-line TextBox | ScrollView
    # -----------------------------------------------------------------------
    split = ui.Panel(layout=ui.HBoxLayout(padding=0, spacing=12))
    split.stretch = 1

    list_view = ui.ListView(
        columns=[('Name', 170), ('Age', 70), ('City', 150)],
        rows=ROWS,
        on_select=lambda index, row: set_status(f'ListView row {index}: {row}'),
        height=260,
    )
    list_view.stretch = 1

    notes = ui.TextBox(
        text='Multi-line TextBox.\nType here and watch the status bar.',
        multiline=True,
        on_change=lambda text: set_status(f'Notes changed: {len(text)} chars'),
    )

    left = ui.Panel(layout=ui.VBoxLayout(padding=0, spacing=8))
    left.stretch = 1
    left.add(list_view)
    left.add(notes)
    left.add(ui.Button('Read notes',
                       on_click=lambda: set_status(f'Notes: "{notes.get_text()}"')))
    split.add(left)

    scroll = ui.ScrollView(padding=8, spacing=8, bg=THEMES['Aurora']['panel'])
    scroll.stretch = 1
    themed_panels.append(scroll)
    split.add(scroll)

    # Wide Canvas: exercises horizontal scrolling and Canvas primitives.
    wide = ui.Canvas(bg=(16, 20, 30))
    wide.measure = lambda a: (int(640 * a.scale), int(88 * a.scale))

    def draw_wide(hdc, a):
        s = a.scale
        wide.clear()
        wide.line(int(14 * s), int(44 * s), int(626 * s), int(44 * s),
                  color=(0, 160, 220), width=max(1, int(2 * s)))
        for i in range(9):
            cx = int((40 + i * 72) * s)
            wide.circle(cx, int(44 * s), int(18 * s),
                        color=(0, 220, 255), width=max(1, int(2 * s)),
                        fill=(16, 56, 76))
            wide.text(cx - int(10 * s), int(16 * s), f'#{i + 1}',
                      size=12, bold=True, color=(170, 240, 255))
        ui.Canvas.draw(wide, hdc, a)

    wide.draw = draw_wide
    scroll.add(wide)

    # Panels demonstrating radius, shadow, gradient and border.
    styled = ui.Panel(layout=ui.HBoxLayout(padding=8, spacing=8))

    def styled_card(text, **panel_kwargs):
        panel = ui.Panel(layout=ui.VBoxLayout(padding=8, spacing=0), **panel_kwargs)
        panel.add(themed_label(text, size=12, bold=True))
        return panel

    gradient_card = styled_card('gradient', gradient=THEMES['Aurora']['accent'], radius=10)
    themed_gradients.append(gradient_card)
    styled.add(gradient_card)

    shadow_card = styled_card('shadow', bg=THEMES['Aurora']['card'],
                              radius=10, shadow=True)
    themed_cards.append(shadow_card)
    styled.add(shadow_card)

    border_card = styled_card('border', bg=THEMES['Aurora']['card'],
                              radius=10, border=(0, 214, 255))
    themed_cards.append(border_card)
    styled.add(border_card)

    rounded_card = styled_card('rounded', bg=THEMES['Aurora']['card'], radius=10)
    themed_cards.append(rounded_card)
    styled.add(rounded_card)

    scroll.add(styled)

    # -----------------------------------------------------------------------
    # Extra components: GroupBox, RadioButton, TabBar, Slider, ToggleSwitch,
    # ProgressBar, Hyperlink, Separator
    # -----------------------------------------------------------------------
    extra = ui.Panel(layout=ui.HBoxLayout(padding=8, spacing=12))

    radio_group = ui.GroupBox('Radio group',
                              layout=ui.VBoxLayout(padding=6, spacing=4),
                              bg=THEMES['Aurora']['card'])
    themed_cards.append(radio_group)

    def radio_handler(name):
        def handler(checked):
            if checked:
                set_status(f'Radio: {name}')
        return handler

    for i, label in enumerate(('Option A', 'Option B', 'Option C')):
        radio_group.add(ui.RadioButton(label, checked=(i == 0),
                                       group='demo',
                                       on_change=radio_handler(label)))
    extra.add(radio_group)
    extra.add(ui.Separator('v'))

    right = ui.Panel(layout=ui.VBoxLayout(padding=0, spacing=8))
    tabs = ui.TabBar(['Overview', 'Details', 'Settings'], index=0,
                     on_change=lambda index: set_status(f'Tab: {tabs.items[index]}'))
    right.add(tabs)
    slider = ui.Slider(0.35, on_change=lambda v: set_status(f'Slider: {int(v * 100)}%'))
    right.add(slider)
    toggle_row = ui.Panel(layout=ui.HBoxLayout(padding=0, spacing=8))
    toggle = ui.ToggleSwitch(
        checked=True,
        on_change=lambda checked: set_status(f'Toggle: {"on" if checked else "off"}'))
    toggle_row.add(toggle)
    toggle_row.add(themed_label('Toggle switch', size=12))
    right.add(toggle_row)
    progress = ui.ProgressBar(0.30, show_text=True)
    right.add(progress)
    indeterminate = ui.ProgressBar(indeterminate=True)
    right.add(indeterminate)
    right.add(ui.Hyperlink(
        'Open the About dialog',
        on_click=lambda: ui.user32.MessageBoxW(
            None, 'This is a clickable Hyperlink widget.', 'Hyperlink', 0)))
    extra.add(right)
    scroll.add(extra)

    # Rows with native children (Label + TextBox + Button) to test clipping.
    for i in range(15):
        card = ui.Panel(layout=ui.HBoxLayout(padding=8, spacing=8),
                        bg=THEMES['Aurora']['card'])
        themed_cards.append(card)
        card.add(themed_label(f'Row {i + 1:02d}', size=13, bold=True))
        textbox = ui.TextBox(
            text=f'item {i + 1}',
            on_change=lambda text, row=i + 1: set_status(f'Row {row:02d} text: "{text}"'),
        )
        textbox.stretch = 1
        card.add(textbox)
        card.add(ui.Button(
            'OK',
            on_click=lambda row=i + 1, box=textbox:
                set_status(f'Row {row:02d} OK: "{box.get_text()}"')))
        scroll.add(card)

    app.add(split)

    # -----------------------------------------------------------------------
    # Animated Canvas: grid, rectangle, circle and text via timer
    # -----------------------------------------------------------------------
    canvas_label = themed_label(
        'Canvas: line, rect, ellipse, circle, text (animated by a timer)', size=13)
    app.add(canvas_label)

    ball_canvas = ui.Canvas(bg=(12, 16, 24))
    ball_canvas.measure = lambda a: (int(1080 * a.scale), int(150 * a.scale))

    def redraw_canvas(a):
        s = a.scale
        w = ball_canvas.w / s if s else 0
        h = ball_canvas.h / s if s else 0
        ball_canvas.clear()
        ball_canvas.rect(0, 0, ball_canvas.w, ball_canvas.h,
                         color=(36, 48, 66), width=max(1, int(s)))
        if state['grid']:
            step = 24
            x = 0
            while x <= w:
                ball_canvas.line(int(x * s), 0, int(x * s), ball_canvas.h,
                                 color=(26, 34, 48), width=1)
                x += step
            y = 0
            while y <= h:
                ball_canvas.line(0, int(y * s), ball_canvas.w, int(y * s),
                                 color=(26, 34, 48), width=1)
                y += step
        b = state['ball']
        cx, cy, r = int(b['x'] * s), int(b['y'] * s), int(b['r'] * s)
        ball_canvas.circle(cx, cy, r + int(10 * s), color=(0, 0, 0),
                           width=0, fill=(14, 46, 66))
        ball_canvas.circle(cx, cy, r, color=(140, 245, 255),
                           width=max(1, int(2 * s)), fill=(0, 200, 240))

    def draw_ball(hdc, a):
        redraw_canvas(a)
        ui.Canvas.draw(ball_canvas, hdc, a)

    ball_canvas.draw = draw_ball
    app.add(ball_canvas)

    # -----------------------------------------------------------------------
    # Status bar
    # -----------------------------------------------------------------------
    app.add(status)
    set_status('Ready. Change theme, scroll both panes, edit text, watch the animation.')

    # -----------------------------------------------------------------------
    # Timers: animation (30 ms) and a 1-second counter
    # -----------------------------------------------------------------------
    def tick():
        s = app.scale or 1.0
        w = ball_canvas.w / s
        h = ball_canvas.h / s
        if w <= 0 or h <= 0:
            return
        b = state['ball']
        r = b['r']
        b['x'] += b['vx']
        b['y'] += b['vy']
        if b['x'] - r < 0:
            b['x'] = r
            b['vx'] = -b['vx']
        if b['x'] + r > w:
            b['x'] = w - r
            b['vx'] = -b['vx']
        if b['y'] - r < 0:
            b['y'] = r
            b['vy'] = -b['vy']
        if b['y'] + r > h:
            b['y'] = h - r
            b['vy'] = -b['vy']
        state['frame'] += 1
        scrolling = getattr(app, 'scrolling', False)
        if state['frame'] % 3 == 0:
            progress.set_value((progress.value + 0.012) % 1.0)
            indeterminate.tick(0.15)
            if not scrolling:
                app.invalidate_rect(progress.x, progress.y,
                                    progress.w, progress.h)
                app.invalidate_rect(indeterminate.x, indeterminate.y,
                                    indeterminate.w, indeterminate.h)
        if not scrolling:
            app.invalidate_rect(ball_canvas.x, ball_canvas.y,
                                ball_canvas.w, ball_canvas.h)

    def on_timer_tick():
        state['ticks'] += 1
        ticks_label.text = f'Timer: {state["ticks"]}'
        app.invalidate_rect(ticks_label.x, ticks_label.y,
                            ticks_label.w, ticks_label.h)

    app.set_timer(50, tick)
    app.set_timer(1000, on_timer_tick)

    # -----------------------------------------------------------------------
    # Reset helper
    # -----------------------------------------------------------------------
    def reset_all():
        list_view.set_rows(ROWS)
        grid_check.set_checked(True, notify=False)
        on_grid_change(True)
        notes.set_text('Multi-line TextBox.\nType here and watch the status bar.')
        theme_combo.set_index(0)
        apply_theme('Aurora')
        tabs.set_index(0)
        slider.set_value(0.35)
        toggle.set_checked(True)
        progress.set_value(0.30)
        indeterminate.phase = 0.0
        state['ball'].update({'x': 40.0, 'y': 40.0, 'vx': 2.4, 'vy': 1.7, 'r': 12})
        set_status('Everything reset.')

    # -----------------------------------------------------------------------
    # Menus
    # -----------------------------------------------------------------------
    file_menu = app.menubar.add('File')
    file_menu.add_item('Reload list',
                       lambda: (list_view.set_rows(ROWS), set_status('ListView reloaded.')))
    file_menu.add_item('Clear list',
                       lambda: (list_view.set_rows([]), set_status('ListView cleared.')))
    file_menu.add_item('Show selection',
                       lambda: set_status(f'Selected row: {list_view.get_selected_row()}'))
    file_menu.add_separator()
    file_menu.add_item('Reset all', reset_all)
    file_menu.add_separator()
    file_menu.add_item('Exit', lambda: ui.user32.PostMessageW(app.hwnd, ui.WM_CLOSE, 0, 0))

    view_menu = app.menubar.add('View')

    def select_theme(name):
        theme_combo.set_index(list(THEMES).index(name))
        apply_theme(name)
        set_status(f'Theme: {name}')

    for theme_name in THEMES:
        view_menu.add_item(f'{theme_name} theme', lambda n=theme_name: select_theme(n))

    help_menu = app.menubar.add('Help')
    help_menu.add_item('About', lambda: ui.user32.MessageBoxW(
        None,
        'pywinui - component test suite\n'
        'Pure Python Win32 + GDI widgets (ctypes only).',
        'About', 0))

    app.run()


if __name__ == '__main__':
    main()
