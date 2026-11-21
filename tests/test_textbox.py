import pywinui as ui
from tests.helpers import WidgetTestCase, WindowTestCase


class TextBoxHeadlessTests(WidgetTestCase):
    def test_set_text_without_window(self):
        events = []
        box = self.add(ui.TextBox('abc', on_change=events.append))
        self.assertEqual(box.get_text(), 'abc')

        box.set_text('xyz')
        self.assertEqual(box.get_text(), 'xyz')
        self.assertEqual(events, ['xyz'])

        box.set_text('quiet', notify=False)
        self.assertEqual(box.get_text(), 'quiet')
        self.assertEqual(events, ['xyz'])

        box.type_text('!')
        self.assertEqual(box.get_text(), 'quiet!')
        self.assertEqual(events, ['xyz', 'quiet!'])

    def test_measure_single_and_multiline(self):
        single = self.add(ui.TextBox())
        multi = self.add(ui.TextBox(multiline=True))
        self.assertEqual(single.measure(self.app), (240, 28))
        self.assertEqual(multi.measure(self.app), (240, 80))


class TextBoxNativeTests(WindowTestCase):
    def test_realize_keeps_initial_text(self):
        self.create()
        box = self.add(ui.TextBox('hello'))
        self.assertIsNotNone(box.hwnd)
        self.assertEqual(box.get_text(), 'hello')

    def test_set_text_notifies_parent(self):
        self.create()
        events = []
        box = self.add(ui.TextBox('a', on_change=events.append))
        box.set_text('b')
        self.app.pump()
        self.assertEqual(box.get_text(), 'b')
        self.assertEqual(events, ['b'])

    def test_type_char_appends(self):
        self.create()
        events = []
        box = self.add(ui.TextBox(on_change=events.append))
        self.app.focus(box)
        for ch in 'hey':
            self.app.type_char(ch)
        self.assertEqual(box.get_text(), 'hey')
        self.assertEqual(events[-1], 'hey')

    def test_type_text_appends(self):
        self.create()
        box = self.add(ui.TextBox())
        box.type_text('ok')
        self.assertEqual(box.get_text(), 'ok')

    def test_multiline_accepts_text(self):
        self.create()
        box = self.add(ui.TextBox(multiline=True))
        box.type_text('line')
        self.assertEqual(box.get_text(), 'line')
