"""Menu bar and popup menu wrappers."""

from .common import *  # noqa: F401,F403

# ============================================================================
# MENUS
# ============================================================================
class MenuBar:
    def __init__(self, app):
        self.app = app; self.hmenu = user32.CreateMenu()
    def add(self, title): return Menu(self.app, self.hmenu, title)

class Menu:
    def __init__(self, app, parent, title):
        self.app = app; self.hmenu = user32.CreatePopupMenu()
        user32.AppendMenuW(parent, MF_POPUP, self.hmenu, title)
    def add_item(self, text, callback=None):
        cmd = self.app._next_cmd; self.app._next_cmd += 1
        if callback: self.app.menu_callbacks[cmd] = callback
        user32.AppendMenuW(self.hmenu, MF_STRING, cmd, text)
    def add_separator(self):
        user32.AppendMenuW(self.hmenu, MF_SEPARATOR, 0, None)

