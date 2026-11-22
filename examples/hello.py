"""Minimal VesperUI application.

Run it from a clone with::

    python examples/hello.py

Pass ``--check`` to create the window without showing it, run one layout pass
and exit. This is used by CI as a smoke test.

The example shows a native text box updating an owner-drawn label, a toggle, a
slider and a button that opens a native message box.
"""
import os
import sys

# Allow running the example directly from a source checkout.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import vesperui as ui


def build_app():
    app = ui.App('Hello VesperUI', 560, 440)
    app.root.layout = ui.VBoxLayout(padding=18, spacing=12)

    app.root.add(ui.Label('Hello, VesperUI!', 22, True))
    app.root.add(ui.Label('A small native window built with ctypes and Win32.',
                          13, color=ui.AURORA['mid']))
    app.root.add(ui.Separator())

    form = ui.Panel(layout=ui.HBoxLayout(padding=0, spacing=10))
    form.add(ui.Label('Your name', 14))
    name = ui.TextBox('Ada Lovelace')
    name.stretch = 1
    form.add(name)
    app.root.add(form)

    greeting = ui.Label('Hello, Ada Lovelace!', 15, True,
                        color=ui.AURORA['highlight'])
    app.root.add(greeting)

    def update_greeting(value):
        who = value.strip() or 'stranger'
        greeting.text = 'Hello, %s!' % who
        app.invalidate()

    name.on_change = update_greeting

    controls = ui.Panel(layout=ui.HBoxLayout(padding=0, spacing=10))
    controls.add(ui.Label('Notifications', 14))
    controls.add(ui.ToggleSwitch(checked=True))
    controls.add(ui.Label('Volume', 14))
    slider = ui.Slider(value=0.6)
    slider.stretch = 1
    controls.add(slider)
    app.root.add(controls)

    app.root.add(ui.Button('Say hello', on_click=lambda: app.info(
        greeting.text, 'Hello'), accent=ui.AURORA['highlight']))
    return app


def main(argv):
    app = build_app()
    if '--check' in argv:
        app.create(show=False)
        app.pump()
        app.destroy()
        print('hello example: window created and laid out.')
        return 0
    app.run()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
