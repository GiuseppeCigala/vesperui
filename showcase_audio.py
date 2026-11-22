"""Interactive showcase for the VesperUI audio controls.

Run ``python showcase_audio.py`` to open the window. Pass ``--check`` to
build the interface, paint it into an off-screen bitmap and exit.

Left column: transport, spectrum analyzer and analog VU meter.
Right column: segmented bar meters, mixer fader and rotary knob.
"""
import math
import os
import sys
import time

import vesperui as ui

AUDIO_FILTERS = [
    ('Audio files', '*.wav;*.mp3;*.flac;*.ogg;*.m4a'),
    ('All files', '*.*'),
]


def caption(text, style):
    return ui.Label(text, 12, True, color=style['mid'])


def synthetic_spectrum(bins, t):
    """Build a plausible log-spaced spectrum for the showcase animation."""
    values = []
    for i in range(bins):
        f = i / max(1, bins - 1)
        slope = 0.72 - 0.40 * f
        waves = (0.16 * math.sin(t * 1.7 + f * 9.0)
                 + 0.11 * math.sin(t * 0.9 + f * 23.0)
                 + 0.06 * math.sin(t * 2.3 + f * 41.0))
        ripple = 0.025 * math.sin(t * 6.0 + i * 1.7)
        spike = 0.24 * max(0.0, math.sin(t * 0.55 + f * 5.0)) ** 12
        values.append(max(0.0, min(1.0, slope + waves + ripple + spike)))
    return values


def build_app():
    app = ui.App('VesperUI - Audio Controls', 1120, 820)
    style = ui.AURORA
    app.root.layout = ui.VBoxLayout(padding=14, spacing=10)

    # ------------------------------------------------------------- status/header
    status_label = ui.Label(
        'Ready. Drag the audio controls to explore them.', 13)
    status_label.stretch = 1

    def set_status(text):
        status_label.text = text
        app.invalidate()

    title = ui.Label('VesperUI - Audio Controls', 22, True)
    title.stretch = 1
    header = ui.Panel(layout=ui.HBoxLayout(padding=0, spacing=10))
    header.add(title)
    header.add(ui.Label('AUDIO MODULE', 11, True,
                        color=style['highlight']))
    header.add(ui.Hyperlink(
        'About this demo',
        on_click=lambda: set_status(
            'Transport, meters, fader, knob and spectrum analyzer.')))

    # ---------------------------------------------------------------- two columns
    main = ui.Panel(layout=ui.HBoxLayout(padding=0, spacing=12))
    main.stretch = 1
    left = ui.ScrollView(padding=10, spacing=10, bg=style['panel'])
    left.stretch = 1
    right = ui.ScrollView(padding=10, spacing=10, bg=style['panel'])
    right.stretch = 1
    main.add(left)
    main.add(right)

    # ---------------------------------------------------------------- transport
    transport_group = ui.GroupBox('Transport', bg=style['card'],
                                  layout=ui.VBoxLayout(padding=10, spacing=8))
    left.add(transport_group)
    transport_info = ui.Label('No track loaded.')

    def on_transport(command):
        transport.set_active(command if command in ('play', 'pause') else None)
        transport_info.text = 'Transport: %s' % command.upper()
        app.invalidate()
        set_status('Transport command: %s.' % command)

    def on_load_audio():
        path = app.open_file('Open audio file', AUDIO_FILTERS)
        if path:
            name = os.path.basename(path)
            transport_info.text = 'Track: %s' % name
            set_status('Loaded audio file: %s.' % name)
            app.invalidate()
        else:
            set_status('Audio open cancelled.')

    transport = ui.TransportBar(on_command=on_transport)
    transport_row = ui.Panel(layout=ui.HBoxLayout(padding=0, spacing=16))
    transport_row.add(transport)
    transport_side = ui.Panel(layout=ui.VBoxLayout(padding=0, spacing=8))
    transport_side.stretch = 1
    transport_side.add(transport_info)
    transport_side.add(ui.Hyperlink('Load audio file...',
                                    on_click=on_load_audio))
    transport_row.add(transport_side)
    transport_group.add(caption('REW / PLAY / PAUSE / STOP / FF', style))
    transport_group.add(transport_row)

    # ----------------------------------------------------------------- spectrum
    spectrum_group = ui.GroupBox('Spectrum analyzer', bg=style['card'],
                                 layout=ui.VBoxLayout(padding=10, spacing=8))
    left.add(spectrum_group)
    spectrum = ui.SpectrumAnalyzer(bins=96)
    spectrum_group.add(caption(
        'LOG FREQUENCY - AVERAGE / TRANSIENT / PEAK', style))
    spectrum_group.add(spectrum)

    # ---------------------------------------------------------------- analog VU
    vu_group = ui.GroupBox('Analog VU meter', bg=style['card'],
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
    vu_side.add(caption('LEVEL', style))
    vu_side.add(vu_slider)
    vu_side.add(vu_label)
    vu_row.add(vu_side)
    vu_group.add(caption('NEEDLE + PEAK HOLD - DRAG OR USE THE SLIDER',
                         style))
    vu_group.add(vu_row)

    # -------------------------------------------------------------- bar meters
    bar_group = ui.GroupBox('Bar VU meters', bg=style['card'],
                            layout=ui.VBoxLayout(padding=10, spacing=8))
    right.add(bar_group)
    bar_v = ui.LevelMeter((0.55, 0.72), orientation='v')
    bar_h = ui.LevelMeter((0.55, 0.72), orientation='h')
    bar_both_label = ui.Label('Channels: 55% / 72%')

    def on_bar_both(value):
        percent = int(round(value * 100))
        bar_v.set_levels((value, value))
        bar_h.set_levels((value, value))
        bar_both_label.text = 'Channels: %d%% / %d%%' % (percent, percent)
        set_status('Bar meters: %d%%.' % percent)

    bar_both_slider = ui.Slider(0.55, on_change=on_bar_both)
    bar_row = ui.Panel(layout=ui.HBoxLayout(padding=0, spacing=16))
    bar_row.add(bar_v)
    bar_side = ui.Panel(layout=ui.VBoxLayout(padding=0, spacing=8))
    bar_side.stretch = 1
    bar_side.add(bar_h)
    bar_side.add(bar_both_slider)
    bar_side.add(bar_both_label)
    bar_side.add(ui.Label('Drag a single bar to set that channel.', 12,
                          color=style['mid']))
    bar_row.add(bar_side)
    bar_group.add(caption('VERTICAL / HORIZONTAL + PEAK HOLD', style))
    bar_group.add(bar_row)

    # --------------------------------------------------------------- mixer fader
    mixer_group = ui.GroupBox('Mixer fader', bg=style['card'],
                              layout=ui.VBoxLayout(padding=10, spacing=8))
    right.add(mixer_group)
    mixer_label = ui.Label('Fader: 0.0 dB')

    def on_mixer(db):
        mixer_label.text = 'Fader: %s' % mixer.value_text()
        app.invalidate()
        set_status('Mixer fader: %s.' % mixer.value_text())

    mixer = ui.MixerSlider(0.0, on_change=on_mixer)
    mixer_row = ui.Panel(layout=ui.HBoxLayout(padding=0, spacing=16))
    mixer_row.add(mixer)
    mixer_side = ui.Panel(layout=ui.VBoxLayout(padding=0, spacing=8))
    mixer_side.stretch = 1
    mixer_side.add(mixer_label)
    mixer_side.add(ui.Label('Drag the cap or click on the rail.', 12,
                            color=style['mid']))
    mixer_side.add(ui.Label('Scale: +6 dB down to -∞ dB.', 12,
                            color=style['mid']))
    mixer_row.add(mixer_side)
    mixer_group.add(caption('MIXER FADER - DB TAPER', style))
    mixer_group.add(mixer_row)

    # --------------------------------------------------------------------- knob
    knob_group = ui.GroupBox('Rotary knob', bg=style['card'],
                             layout=ui.VBoxLayout(padding=10, spacing=8))
    right.add(knob_group)
    knob_label = ui.Label('Knob: 50.0 %')

    def on_knob(value):
        knob_label.text = 'Knob: %s' % knob.value_text()
        app.invalidate()
        set_status('Knob: %s.' % knob.value_text())

    knob = ui.Knob(0.5, on_change=on_knob)
    knob_row = ui.Panel(layout=ui.HBoxLayout(padding=0, spacing=16))
    knob_row.add(knob)
    knob_side = ui.Panel(layout=ui.VBoxLayout(padding=0, spacing=8))
    knob_side.stretch = 1
    knob_side.add(knob_label)
    knob_side.add(ui.Label('Drag around the dial to rotate it.', 12,
                           color=style['mid']))
    knob_row.add(knob_side)
    knob_group.add(caption('RING + POINTER + VALUE PLATE', style))
    knob_group.add(knob_row)

    # ------------------------------------------------------------------ status
    status = ui.Panel(layout=ui.HBoxLayout(padding=8, spacing=10),
                      bg=style['card'], radius=8, border=style['border'],
                      gradient=(ui.lighten(style['card'], 0.045),
                                style['card']))
    status.add(status_label)
    status.add(ui.Hyperlink('Reset', on_click=lambda: reset_all()))

    app.root.add(header)
    app.root.add(main)
    app.root.add(status)

    # ---------------------------------------------------------------- actions
    def reset_all():
        transport.set_active(None)
        transport_info.text = 'No track loaded.'
        vu_meter.set_value(0.35, notify=False)
        vu_meter.reset_peak()
        vu_slider.set_value(0.35, notify=False)
        vu_label.text = 'Level: 35%'
        bar_v.set_levels((0.55, 0.72), notify=False)
        bar_h.set_levels((0.55, 0.72), notify=False)
        bar_v.reset_peaks()
        bar_h.reset_peaks()
        bar_both_slider.set_value(0.55, notify=False)
        bar_both_label.text = 'Channels: 55% / 72%'
        mixer.set_value(0.0, notify=False)
        mixer_label.text = 'Fader: 0.0 dB'
        knob.set_value(0.5, notify=False)
        knob_label.text = 'Knob: 50.0 %'
        spectrum.reset()
        left.scroll_to(0, 0)
        right.scroll_to(0, 0)
        app.invalidate()
        set_status('Audio controls reset to their initial state.')

    def exit_app():
        if app.hwnd:
            ui.user32.PostMessageW(app.hwnd, ui.WM_CLOSE, 0, 0)

    file_menu = app.menubar.add('File')
    file_menu.add_item('Open audio...', on_load_audio)
    file_menu.add_separator()
    file_menu.add_item('Exit', exit_app)

    view_menu = app.menubar.add('View')
    view_menu.add_item('Reset', reset_all)
    view_menu.add_item('Scroll to top', lambda: (
        left.scroll_to(0, 0), right.scroll_to(0, 0),
        set_status('Scrolled to top.')))

    help_menu = app.menubar.add('Help')
    help_menu.add_item('About', lambda: app.info(
        'VesperUI audio controls: transport, meters, fader, knob and '
        'spectrum analyzer.', 'About VesperUI Audio'))

    # ------------------------------------------------------------ animation
    def tick():
        spectrum.set_spectrum(synthetic_spectrum(spectrum.bins,
                                                 time.monotonic()))

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


def run(factory, argv):
    """Build the showcase, honour ``--check`` and run the message loop."""
    app = factory()
    if '--check' in argv:
        return smoke_check(app)
    app.run()
    return 0


if __name__ == '__main__':
    sys.exit(run(build_app, sys.argv))
