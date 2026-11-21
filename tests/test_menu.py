import pywinui as ui
from tests.helpers import WindowTestCase


class MenuTests(WindowTestCase):
    def test_items_register_callbacks(self):
        events = []
        menu = self.app.menubar.add('File')
        self.assertTrue(menu.hmenu)

        open_cmd = self.app._next_cmd
        menu.add_item('Open', lambda: events.append('open'))
        menu.add_separator()
        exit_cmd = self.app._next_cmd
        menu.add_item('Exit', lambda: events.append('exit'))

        self.assertEqual(exit_cmd, open_cmd + 1)
        self.assertIn(open_cmd, self.app.menu_callbacks)
        self.assertIn(exit_cmd, self.app.menu_callbacks)
        self.assertNotIn(open_cmd + 2, self.app.menu_callbacks)

    def test_multiple_menus_are_distinct(self):
        file_menu = self.app.menubar.add('File')
        help_menu = self.app.menubar.add('Help')
        self.assertTrue(file_menu.hmenu)
        self.assertTrue(help_menu.hmenu)
        self.assertNotEqual(file_menu.hmenu, help_menu.hmenu)

    def test_wm_command_dispatches_callback(self):
        events = []
        menu = self.app.menubar.add('Edit')
        cmd = self.app._next_cmd
        menu.add_item('Undo', lambda: events.append('undo'))
        self.create()

        ui.user32.SendMessageW(self.app.hwnd, ui.WM_COMMAND, cmd, 0)
        self.assertEqual(events, ['undo'])

    def test_unknown_command_is_ignored(self):
        menu = self.app.menubar.add('Help')
        menu.add_separator()
        self.create()
        ui.user32.SendMessageW(self.app.hwnd, ui.WM_COMMAND, 9999, 0)
