"""Shared helpers for the VesperUI showcase applications."""
import vesperui as ui


def caption(text, style):
    return ui.Label(text, 12, True, color=style['mid'])


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
