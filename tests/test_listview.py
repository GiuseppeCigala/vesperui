import pywinui as ui
from tests.helpers import WidgetTestCase, WindowTestCase


ROWS = [['one', '1'], ['two', '2'], ['three', '3']]


class ListViewHeadlessTests(WidgetTestCase):
    def test_select_without_window_uses_callback(self):
        events = []
        view = self.add(ui.ListView(
            rows=ROWS, on_select=lambda i, row: events.append((i, row))))
        view.select(1)
        self.assertEqual(events, [(1, ['two', '2'])])

    def test_select_out_of_range_is_ignored(self):
        events = []
        view = self.add(ui.ListView(
            rows=ROWS, on_select=lambda i, row: events.append((i, row))))
        view.select(-1)
        view.select(3)
        self.assertEqual(events, [])


class ListViewNativeTests(WindowTestCase):
    def setUp(self):
        super().setUp()
        self.events = []

    def _make(self):
        self.create()
        return self.add(ui.ListView(
            columns=[('Name', 120), ('Value', 80)],
            rows=ROWS,
            height=160,
            on_select=lambda i, row: self.events.append((i, row))))

    def test_realizes_and_starts_empty(self):
        view = self._make()
        self.assertIsNotNone(view.hwnd)
        self.assertEqual(view.rows, ROWS)
        self.assertEqual(view.get_selected_index(), -1)
        self.assertIsNone(view.get_selected_row())
        self.assertEqual(self.events, [])

    def test_select_notifies_parent(self):
        view = self._make()
        view.select(1)
        self.assertEqual(view.get_selected_index(), 1)
        self.assertEqual(view.get_selected_row(), ['two', '2'])
        self.assertEqual(self.events, [(1, ['two', '2'])])

    def test_select_out_of_range_is_ignored(self):
        view = self._make()
        view.select(5)
        view.select(-1)
        self.assertEqual(view.get_selected_index(), -1)
        self.assertEqual(self.events, [])

    def test_set_rows_repopulates_and_clears_selection(self):
        view = self._make()
        view.select(2)
        view.set_rows([['only', '0']])
        self.assertEqual(view.rows, [['only', '0']])
        self.assertEqual(view.get_selected_index(), -1)
        view.select(0)
        self.assertEqual(view.get_selected_row(), ['only', '0'])
