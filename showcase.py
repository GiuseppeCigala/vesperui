"""Interactive showcase for every VesperUI widget.

Run ``python showcase.py`` to open the window. Pass ``--check`` to build the
whole interface, paint it into an off-screen bitmap and exit; this is a fast
smoke test that catches layout and GDI errors without showing anything.

The window is organised in two columns:

* left  - a ScrollView with input, selection, action and overflow groups;
* right - a TabBar, a ListView, a Canvas, a shadow card and shortcuts.

Every callback writes a message to the status bar, so interacting with a
control makes its behaviour immediately visible.
"""
import os
import sys

import vesperui as ui

DEFAULT_ROWS = [
    ['Button', 'owner-drawn', 'click, hover, keyboard'],
    ['TextBox', 'native', 'typing, EN_CHANGE'],
    ['ComboBox', 'native', 'CBN_SELCHANGE'],
    ['ListView', 'native', 'row selection'],
    ['ToggleSwitch', 'owner-drawn', 'animated knob'],
    ['Stepper', 'owner-drawn', 'increment and decrement'],
    ['ColorPicker', 'owner-drawn', 'hue, saturation, value'],
    ['VUMeter', 'owner-drawn', 'needle, zones, peak hold'],
    ['Slider', 'owner-drawn', 'horizontal and vertical'],
    ['ProgressBar', 'owner-drawn', 'horizontal and vertical'],
    ['Canvas', 'owner-drawn', 'line, rect, ellipse, text'],
    ['ScrollView', 'owner-drawn', 'wheel, drag, clipping'],
]

FILE_FILTERS = [
    ('Python files', '*.py'),
    ('Text files', '*.txt;*.md'),
    ('All files', '*.*'),
]


class ShowcaseCanvas(ui.Canvas):
    """Canvas that seeds its sample scene once it knows its real bounds."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._seeded = False

    def draw(self, hdc, app):
        if not self._seeded and self.w > 0 and self.h > 0:
            self.seed()
        super().draw(hdc, app)

    def seed(self):
        st = ui.AURORA
        self.clear()
        w, h = max(self.w, 300), max(self.h, 150)
        self.rect(10, 10, w - 20, h - 20, color=st['border'])
        self.line(20, h - 20, w - 20, 20, color=st['mid'], width=2)
        self.ellipse(int(w * 0.06), int(h * 0.38), int(w * 0.20),
                     int(h * 0.30), color=st['highlight'], fill=st['panel'])
        self.ellipse(int(w * 0.72), int(h * 0.25), int(w * 0.16),
                     int(h * 0.40), color=st['highlight2'], fill=st['base'])
        self.circle(int(w * 0.48), int(h * 0.52), int(h * 0.20),
                    color=st['highlight'], fill=st['panel'])
        self.text(16, 10, 'Canvas primitives', size=14, bold=True,
                  color=st['windowText'])
        self._seeded = True


def build_app():
    app = ui.App('VesperUI - Widget Showcase', 1180, 820)
    style = ui.AURORA
    app.root.layout = ui.VBoxLayout(padding=14, spacing=10)

    # ---------------------------------------------------------------- status
    status_label = ui.Label('Ready. Try clicking, typing, dragging and scrolling.',
                            13)
    status_label.stretch = 1

    def set_status(text):
        status_label.text = text
        app.invalidate()

    def caption(text):
        return ui.Label(text, 12, True, color=style['mid'])

    # ---------------------------------------------------------------- header
    title = ui.Label('VesperUI - Widget Showcase', 22, True)
    title.stretch = 1
    header = ui.Panel(layout=ui.HBoxLayout(padding=0, spacing=10))
    header.add(title)
    header.add(ui.Label('AURORA DARK', 11, True, color=style['highlight']))
    header.add(ui.Hyperlink(
        'About this demo',
        on_click=lambda: set_status(
            'All VesperUI widgets in one window: hover, click, type, drag, '
            'press Tab and scroll. Every action updates this status bar.')))

    # ------------------------------------------------------------ main frame
    main = ui.Panel(layout=ui.HBoxLayout(padding=0, spacing=12))
    main.stretch = 1
    left = ui.ScrollView(padding=10, spacing=10, bg=style['panel'])
    left.stretch = 1
    right = ui.Panel(layout=ui.VBoxLayout(padding=0, spacing=10))
    right.stretch = 1
    main.add(left)
    main.add(right)

    # ============================================================ left column
    echo = ui.Label('Echo: -')

    def on_text(field, value):
        echo.text = '%s: %s' % (field, value if value else '(empty)')
        app.invalidate()
        set_status('%s changed to "%s".' % (field, value))

    text_group = ui.GroupBox('Text input', bg=style['card'],
                             layout=ui.VBoxLayout(padding=10, spacing=8))
    left.add(text_group)
    name_box = ui.TextBox('Ada Lovelace',
                          on_change=lambda t: on_text('Name', t))
    notes_box = ui.TextBox('Write a few lines here...', multiline=True,
                           on_change=lambda t: on_text('Notes', t))

    def clear_text():
        name_box.set_text('', notify=False)
        notes_box.set_text('', notify=False)
        echo.text = 'Echo: -'
        app.invalidate()
        set_status('Text fields cleared.')

    text_group.add(caption('NAME'))
    text_group.add(name_box)
    text_group.add(caption('NOTES (MULTILINE)'))
    text_group.add(notes_box)
    text_group.add(echo)
    text_group.add(ui.Separator())
    text_group.add(ui.Hyperlink('Clear text fields', on_click=clear_text))

    # ---------------------------------------------------------- selection box
    selection = ui.GroupBox('Selection & values', bg=style['card'],
                            layout=ui.VBoxLayout(padding=10, spacing=8))
    left.add(selection)

    notify_check = ui.CheckBox(
        'Enable notifications', checked=True,
        on_change=lambda v: set_status(
            'Notifications %s.' % ('enabled' if v else 'disabled')))
    grid_check = ui.CheckBox(
        'Show grid lines',
        on_change=lambda v: set_status(
            'Grid lines %s.' % ('shown' if v else 'hidden')))

    def on_density(name):
        return lambda checked: checked and set_status('Density: %s.' % name)

    radios = []
    for label, checked in (('Compact', False),
                           ('Comfortable', True),
                           ('Spacious', False)):
        radios.append(ui.RadioButton(label, checked=checked, group='density',
                                     on_change=on_density(label)))

    animating = [True]

    def on_toggle(value):
        animating[0] = value
        set_status('Progress animation %s.' % ('running' if value else 'paused'))

    toggle_label = ui.Label('Animate progress')
    toggle_label.stretch = 1
    toggle = ui.ToggleSwitch(checked=True, on_change=on_toggle)
    toggle_row = ui.Panel(layout=ui.HBoxLayout(padding=0, spacing=10))
    toggle_row.add(toggle_label)
    toggle_row.add(toggle)

    volume_progress = ui.ProgressBar(0.35, show_text=True)
    slider_label = ui.Label('Volume: 35%')

    def on_slider(value):
        volume_progress.set_value(value)
        slider_label.text = 'Volume: %d%%' % int(value * 100)
        app.invalidate()
        set_status('Slider value: %d%%.' % int(value * 100))

    slider = ui.Slider(0.35, on_change=on_slider)
    combo = ui.ComboBox(['Comfortable', 'Dense', 'Relaxed'], index=0,
                        on_change=lambda i, text:
                        set_status('Combo box selection: %s.' % text))

    selection.add(notify_check)
    selection.add(grid_check)
    selection.add(ui.Separator())
    selection.add(caption('DENSITY (RADIO GROUP)'))
    for radio in radios:
        selection.add(radio)
    selection.add(ui.Separator())
    selection.add(toggle_row)
    selection.add(ui.Separator())
    selection.add(caption('SLIDER -> PROGRESS'))
    selection.add(slider)
    selection.add(slider_label)
    selection.add(volume_progress)
    selection.add(ui.Separator())
    selection.add(caption('COMBO BOX'))
    selection.add(combo)

    quantity_label = ui.Label('Quantity: 3')

    def on_stepper(value):
        quantity_label.text = 'Quantity: %d' % int(value)
        app.invalidate()
        set_status('Stepper value: %d.' % int(value))

    stepper = ui.Stepper(3, min=0, max=10, step=1, on_change=on_stepper)
    selection.add(ui.Separator())
    selection.add(caption('STEPPER (0-10)'))
    selection.add(stepper)
    selection.add(quantity_label)

    # ------------------------------------------------------------ color picker
    color_group = ui.GroupBox('Color picker', bg=style['card'],
                              layout=ui.VBoxLayout(padding=10, spacing=8))
    left.add(color_group)
    color_label = ui.Label('Color: #00D6FF')

    def on_color(rgb):
        hex_color = ui.rgb_to_hex(rgb)
        color_label.text = 'Color: %s' % hex_color
        app.invalidate()
        set_status('Color: %s.' % hex_color)

    color_picker = ui.ColorPicker((0, 214, 255), on_change=on_color)
    color_group.add(caption('HUE STRIP + SATURATION / VALUE'))
    color_group.add(color_picker)
    color_group.add(color_label)

    # -------------------------------------------------------------- actions
    actions = ui.GroupBox('Actions', bg=style['card'],
                          layout=ui.VBoxLayout(padding=10, spacing=8))
    left.add(actions)

    ping_count = [0]

    def on_ping():
        ping_count[0] += 1
        set_status('Ping pressed %d time(s).' % ping_count[0])

    def on_apply():
        set_status('Applied name "%s" with preset "%s".'
                   % (name_box.get_text(), combo.current_text()))

    action_buttons = ui.Panel(layout=ui.HBoxLayout(padding=0, spacing=8))
    action_buttons.add(ui.Button('Ping', on_click=on_ping))
    action_buttons.add(ui.Button('Apply', accent=style['highlight'],
                                 on_click=on_apply))
    action_buttons.add(ui.Button('Reset', on_click=lambda: reset_all()))

    marquee = ui.ProgressBar(indeterminate=True)
    actions.add(action_buttons)
    actions.add(ui.Separator())
    actions.add(caption('INDETERMINATE PROGRESS'))
    actions.add(marquee)

    # ------------------------------------------------------ vertical controls
    vertical_group = ui.GroupBox('Vertical orientation', bg=style['card'],
                                 layout=ui.VBoxLayout(padding=10, spacing=8))
    left.add(vertical_group)
    vertical_progress = ui.ProgressBar(0.6, show_text=True, orientation='v')
    vertical_label = ui.Label('Vertical: 60%')

    def on_vertical_slider(value):
        vertical_progress.set_value(value)
        vertical_label.text = 'Vertical: %d%%' % int(value * 100)
        app.invalidate()
        set_status('Vertical slider: %d%%.' % int(value * 100))

    vertical_slider = ui.Slider(0.6, orientation='v',
                                on_change=on_vertical_slider)
    vertical_row = ui.Panel(layout=ui.HBoxLayout(padding=0, spacing=16))
    vertical_row.add(vertical_slider)
    vertical_row.add(vertical_progress)
    vertical_group.add(caption('VERTICAL SLIDER / PROGRESS'))
    vertical_group.add(vertical_row)
    vertical_group.add(vertical_label)

    # ---------------------------------------------------------------- vu meter
    vu_group = ui.GroupBox('VU meter', bg=style['card'],
                           layout=ui.VBoxLayout(padding=10, spacing=8))
    left.add(vu_group)
    vu_label = ui.Label('Level: 35%')

    def on_vu(value):
        percent = int(round(value * 100))
        vu_slider.set_value(value, notify=False)
        vu_label.text = 'Level: %d%%' % percent
        app.invalidate()
        set_status('VU level: %d%%.' % percent)

    vu_meter = ui.VUMeter(0.35, on_change=on_vu)
    vu_slider = ui.Slider(0.35, on_change=lambda v: vu_meter.set_value(v))
    vu_row = ui.Panel(layout=ui.HBoxLayout(padding=0, spacing=12))
    vu_row.add(vu_meter)
    vu_side = ui.Panel(layout=ui.VBoxLayout(padding=0, spacing=8))
    vu_side.stretch = 1
    vu_side.add(caption('LEVEL'))
    vu_side.add(vu_slider)
    vu_side.add(vu_label)
    vu_row.add(vu_side)
    vu_group.add(caption('NEEDLE + PEAK HOLD - DRAG OR USE THE SLIDER'))
    vu_group.add(vu_row)

    # -------------------------------------------------------------- dialogs
    dialogs_group = ui.GroupBox('Dialogs', bg=style['card'],
                                layout=ui.VBoxLayout(padding=10, spacing=8))
    left.add(dialogs_group)
    dialog_info = ui.Label('No dialog opened yet.')

    def show_dialog_result(message):
        dialog_info.text = message
        app.invalidate()
        set_status(message)

    def on_info():
        app.info('This is a native information message box.', 'Information')
        show_dialog_result('Information message closed.')

    def on_warning():
        app.warning('This is a native warning message box.', 'Warning')
        show_dialog_result('Warning message closed.')

    def on_error():
        app.error('This is a native error message box.', 'Error')
        show_dialog_result('Error message closed.')

    def on_question():
        answer = app.question('Do you like the Aurora theme?', 'Question')
        show_dialog_result('Question answered %s.'
                           % ('Yes' if answer else 'No'))

    def on_open():
        path = app.open_file('Open a file', FILE_FILTERS)
        if path:
            name_box.set_text(path, notify=False)
            show_dialog_result('Opened: ' + path)
        else:
            show_dialog_result('Open dialog cancelled.')

    def on_save():
        default = os.path.basename(name_box.get_text().strip()) or 'untitled.txt'
        path = app.save_file('Save as', default_name=default,
                             default_ext='txt', filters=FILE_FILTERS)
        if path:
            show_dialog_result('Saved as: ' + path)
        else:
            show_dialog_result('Save dialog cancelled.')

    def on_folder():
        path = app.select_folder('Select a folder')
        if path:
            show_dialog_result('Folder: ' + path)
        else:
            show_dialog_result('Folder dialog cancelled.')

    dialog_row1 = ui.Panel(layout=ui.HBoxLayout(padding=0, spacing=8))
    dialog_row1.add(ui.Button('Info', on_click=on_info))
    dialog_row1.add(ui.Button('Warning', on_click=on_warning))
    dialog_row1.add(ui.Button('Error', on_click=on_error))
    dialog_row2 = ui.Panel(layout=ui.HBoxLayout(padding=0, spacing=8))
    dialog_row2.add(ui.Button('Yes / No', on_click=on_question))
    dialog_row2.add(ui.Button('Open file...', on_click=on_open))
    dialog_row2.add(ui.Button('Save as...', on_click=on_save))
    dialog_row3 = ui.Panel(layout=ui.HBoxLayout(padding=0, spacing=8))
    dialog_row3.add(ui.Button('Select folder...', on_click=on_folder))
    dialogs_group.add(caption('NATIVE MESSAGE BOXES & FILE DIALOGS'))
    dialogs_group.add(dialog_row1)
    dialogs_group.add(dialog_row2)
    dialogs_group.add(dialog_row3)
    dialogs_group.add(dialog_info)

    # ------------------------------------------------- horizontal overflow
    overflow = ui.GroupBox('Horizontal overflow - drag the bottom scrollbar',
                           bg=style['card'],
                           layout=ui.VBoxLayout(padding=10, spacing=8))
    left.add(overflow)
    wide_row = ui.Panel(layout=ui.HBoxLayout(padding=0, spacing=8))
    for i in range(1, 9):
        wide_row.add(ui.Button(
            'Row %02d' % i,
            on_click=lambda n=i: set_status('Wide row button %02d pressed.' % n)))
    overflow.add(wide_row)

    # =========================================================== right column
    tab_info = ui.Label('Tab: Overview')

    def on_tab(index):
        tab_info.text = 'Tab: ' + tab.items[index]
        app.invalidate()
        set_status('Tab selected: %s.' % tab.items[index])

    tab = ui.TabBar(['Overview', 'Details', 'Diagnostics'], on_change=on_tab)
    right.add(tab)
    right.add(tab_info)

    # -------------------------------------------------------------- list view
    list_group = ui.GroupBox('List view', bg=style['card'],
                             layout=ui.VBoxLayout(padding=10, spacing=8))
    list_group.stretch = 1
    right.add(list_group)

    list_view = ui.ListView(
        columns=[('Widget', 160), ('Kind', 100), ('Behaviour', 190)],
        rows=DEFAULT_ROWS, height=180,
        on_select=lambda i, row: set_status(
            'Selected row %d: %s.' % (i, row[0] if row else '-')),
        on_edit=lambda i, sub, text: set_status(
            'Edited row %d, column %d: %s.' % (i + 1, sub + 1, text)))
    list_view.stretch = 1

    def add_row():
        number = len(list_view.rows) + 1
        list_view.set_rows(list_view.rows + [
            ['Item %02d' % number, 'runtime', 'added from a Button']])
        list_view.select(number - 1)
        set_status('Added row %02d to the list.' % number)

    def next_row():
        if not list_view.rows:
            return
        index = (list_view.get_selected_index() + 1) % len(list_view.rows)
        list_view.select(index)

    def clear_rows():
        list_view.set_rows([])
        set_status('List view cleared.')

    list_buttons = ui.Panel(layout=ui.HBoxLayout(padding=0, spacing=8))
    list_buttons.add(ui.Button('Add row', on_click=add_row))
    list_buttons.add(ui.Button('Select next', on_click=next_row))
    list_buttons.add(ui.Button('Clear', on_click=clear_rows))
    list_group.add(list_view)
    list_group.add(list_buttons)
    list_group.add(ui.Label('Double-click a cell to edit it - Enter saves, Esc cancels.',
                            12, color=style['mid']))

    # ----------------------------------------------------------------- canvas
    canvas_group = ui.GroupBox('Canvas', bg=style['card'],
                               layout=ui.VBoxLayout(padding=10, spacing=8))
    right.add(canvas_group)
    canvas = ShowcaseCanvas(bg=style['base'], height=150)
    circle_count = [0]

    def draw_canvas():
        canvas.seed()

    def add_circle():
        index = circle_count[0]
        circle_count[0] += 1
        cx = 30 + (index * 47) % max(40, canvas.w - 60)
        cy = 30 + (index * 29) % max(40, canvas.h - 60)
        canvas.circle(cx, cy, 18, color=style['highlight'],
                      fill=style['highlight2'])
        app.invalidate()
        set_status('Circle added at (%d, %d).' % (cx, cy))

    def clear_canvas():
        circle_count[0] = 0
        draw_canvas()
        app.invalidate()
        set_status('Canvas cleared.')

    canvas_buttons = ui.Panel(layout=ui.HBoxLayout(padding=0, spacing=8))
    canvas_buttons.add(ui.Button('Add circle', on_click=add_circle))
    canvas_buttons.add(ui.Button('Clear', on_click=clear_canvas))
    canvas_group.add(canvas)
    canvas_group.add(canvas_buttons)

    # ------------------------------------------------------------ shadow card
    card = ui.Panel(layout=ui.VBoxLayout(padding=12, spacing=8),
                    bg=style['card'], radius=12, shadow=True,
                    border=style['border'])
    card.add(ui.Label('Shadow card', 15, True))
    card.add(ui.Label('Rounded corners, soft shadow.', 12,
                      color=style['mid']))
    card_buttons = ui.Panel(layout=ui.HBoxLayout(padding=0, spacing=8))
    card_buttons.add(ui.Button('Hover me'))
    card_buttons.add(ui.Button('Accent', accent=style['highlight2']))
    card.add(card_buttons)
    right.add(card)

    # ------------------------------------------------------------ status bar
    status = ui.Panel(layout=ui.HBoxLayout(padding=8, spacing=10),
                      bg=style['card'], radius=8, border=style['border'],
                      gradient=(ui.lighten(style['card'], 0.045),
                                style['card']))
    status.add(status_label)
    status.add(ui.Hyperlink('Reset', on_click=lambda: reset_all()))
    status.add(ui.Hyperlink(
        'Focus name',
        on_click=lambda: (app.focus(name_box),
                          set_status('Name field focused - start typing.'))))
    status.add(ui.Hyperlink('Clear', on_click=lambda: set_status('Ready.')))

    # ------------------------------------------------------------ root order
    app.root.add(header)
    app.root.add(main)
    app.root.add(status)

    # ---------------------------------------------------------------- actions
    def reset_all():
        name_box.set_text('Ada Lovelace', notify=False)
        notes_box.set_text('Write a few lines here...', notify=False)
        echo.text = 'Echo: -'
        notify_check.set_checked(True)
        grid_check.set_checked(False)
        for radio in radios:
            radio.set_checked(radio.text == 'Comfortable', notify=False)
        animating[0] = True
        toggle.set_checked(True, notify=False)
        slider.set_value(0.35)
        volume_progress.set_value(0.35)
        slider_label.text = 'Volume: 35%'
        stepper.set_value(3, notify=False)
        quantity_label.text = 'Quantity: 3'
        vertical_slider.set_value(0.6, notify=False)
        vertical_progress.set_value(0.6)
        vertical_label.text = 'Vertical: 60%'
        vu_meter.set_value(0.35, notify=False)
        vu_meter.reset_peak()
        vu_slider.set_value(0.35, notify=False)
        vu_label.text = 'Level: 35%'
        color_picker.set_color((0, 214, 255), notify=False)
        color_label.text = 'Color: #00D6FF'
        combo.select(0)
        tab.select(0)
        tab_info.text = 'Tab: ' + tab.items[0]
        list_view.set_rows(DEFAULT_ROWS)
        left.scroll_to(0, 0)
        ping_count[0] = 0
        circle_count[0] = 0
        dialog_info.text = 'No dialog opened yet.'
        draw_canvas()
        app.invalidate()
        set_status('All widgets reset to their initial state.')

    def exit_app():
        if app.hwnd:
            ui.user32.PostMessageW(app.hwnd, ui.WM_CLOSE, 0, 0)

    file_menu = app.menubar.add('File')
    file_menu.add_item('New / Reset', reset_all)
    file_menu.add_item('Open...', on_open)
    file_menu.add_item('Save as...', on_save)
    file_menu.add_item('Select folder...', on_folder)
    file_menu.add_separator()
    file_menu.add_item('Exit', exit_app)

    edit_menu = app.menubar.add('Edit')
    edit_menu.add_item('Undo', lambda: set_status('Undo clicked.'))
    edit_menu.add_item('Redo', lambda: set_status('Redo clicked.'))
    edit_menu.add_separator()
    edit_menu.add_item('Focus name field',
                       lambda: (app.focus(name_box),
                                set_status('Name field focused.')))
    edit_menu.add_item('Copy', lambda: set_status('Copy clicked.'))

    view_menu = app.menubar.add('View')
    view_menu.add_item('Refresh layout', lambda: (
        app.layout(), set_status('Layout refreshed.')))
    view_menu.add_item('Scroll to top', lambda: (
        left.scroll_to(0, 0), set_status('Scrolled to top.')))
    view_menu.add_item('Scroll to bottom', lambda: (
        left.scroll_to(0, 10 ** 9), set_status('Scrolled to bottom.')))

    help_menu = app.menubar.add('Help')
    help_menu.add_item('About', lambda: app.info(
        'VesperUI - every widget in a single window.', 'About VesperUI'))

    # ------------------------------------------------------------ animations
    def tick():
        if animating[0]:
            marquee.tick(0.06)
            app.invalidate_rect(marquee.x, marquee.y,
                                marquee.w, marquee.h)

    app.set_timer(60, tick)
    return app


def smoke_check(app):
    """Create the window hidden, paint all widgets off-screen, then close."""
    app.create(show=False)
    for _ in range(3):
        app.pump()

    width = max(1, app.root.w)
    height = max(1, app.root.h)
    screen = ui.user32.GetDC(None)
    mdc = ui.gdi32.CreateCompatibleDC(screen)
    bmp = ui.gdi32.CreateCompatibleBitmap(screen, width, height)
    old = ui.gdi32.SelectObject(mdc, bmp)
    try:
        app.root.draw(mdc, app)
    finally:
        ui.gdi32.SelectObject(mdc, old)
        ui.gdi32.DeleteObject(bmp)
        ui.gdi32.DeleteDC(mdc)
        ui.user32.ReleaseDC(None, screen)

    widgets = sum(1 for _ in app.root.all_widgets())
    app.destroy()
    print('showcase: %d widgets laid out and painted at %dx%d.'
          % (widgets, width, height))
    return 0


def main(argv):
    app = build_app()
    if '--check' in argv:
        return smoke_check(app)
    app.run()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
