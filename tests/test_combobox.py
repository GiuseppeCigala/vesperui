import pywinui as ui
from tests.helpers import WidgetTestCase, WindowTestCase, memory_dc


class ComboBoxHeadlessTests(WidgetTestCase):
    def test_items_and_initial_selection(self):
        box = self.add(ui.ComboBox(['a', 'b', 'c'], index=1))
        self.assertEqual(box.items, ['a', 'b', 'c'])
        self.assertEqual(box.current_index(), 1)
        self.assertEqual(box.current_text(), 'b')

    def test_select_notifies(self):
        events = []
        box = self.add(ui.ComboBox(
            ['a', 'b'], on_change=lambda i, text: events.append((i, text))))
        box.select(1)
        self.assertEqual(events, [(1, 'b')])
        self.assertEqual(box.current_text(), 'b')


class ComboBoxNativeTests(WindowTestCase):
    def test_populates_and_selects_initial_item(self):
        self.create()
        events = []
        box = self.add(ui.ComboBox(
            ['red', 'green', 'blue'], index=2,
            on_change=lambda i, text: events.append((i, text))))
        self.assertIsNotNone(box.hwnd)
        self.assertEqual(box.current_index(), 2)
        self.assertEqual(box.current_text(), 'blue')
        self.assertEqual(events, [])

    def test_set_index_is_silent(self):
        self.create()
        events = []
        box = self.add(ui.ComboBox(
            ['red', 'green'], on_change=lambda i, text: events.append((i, text))))
        box.set_index(1)
        self.assertEqual(box.current_text(), 'green')
        self.assertEqual(events, [])

    def test_select_notifies_once(self):
        self.create()
        events = []
        box = self.add(ui.ComboBox(
            ['red', 'green', 'blue'],
            on_change=lambda i, text: events.append((i, text))))
        box.select(1)
        self.assertEqual(box.current_text(), 'green')
        self.assertEqual(events, [(1, 'green')])

    def test_owner_draw_paths(self):
        self.create()
        box = self.add(ui.ComboBox(['red', 'green', 'blue'], index=1))
        with memory_dc(240, 40) as mdc:
            field = ui.DRAWITEMSTRUCT()
            field.CtlType = ui.ODT_COMBOBOX
            field.hwndItem = box.hwnd
            field.hDC = mdc
            field.itemID = 0xFFFFFFFF
            field.rcItem = ui.wintypes.RECT(0, 0, 180, 28)
            box._draw_item(field)

            selected = ui.DRAWITEMSTRUCT()
            selected.CtlType = ui.ODT_COMBOBOX
            selected.hwndItem = box.hwnd
            selected.hDC = mdc
            selected.itemID = 2
            selected.itemState = ui.ODS_SELECTED
            selected.rcItem = ui.wintypes.RECT(0, 0, 180, 24)
            box._draw_item(selected)
        self.assertEqual(box.current_text(), 'green')
