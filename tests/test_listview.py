import ctypes

import vesperui as ui
from tests.helpers import WidgetTestCase, WindowTestCase, memory_dc


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

    def test_begin_edit_requires_a_window(self):
        view = self.add(ui.ListView(rows=ROWS))
        self.assertFalse(view.begin_edit(0, 0))
        self.assertIsNone(view._edit_hwnd)


class ListViewNativeTests(WindowTestCase):
    def setUp(self):
        super().setUp()
        self.events = []
        self.edits = []

    def _make(self):
        self.create()
        return self.add(ui.ListView(
            columns=[('Name', 120), ('Value', 80)],
            rows=ROWS,
            height=160,
            on_select=lambda i, row: self.events.append((i, row)),
            on_edit=lambda i, sub, text: self.edits.append((i, sub, text))))

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

    def test_custom_draw_paths(self):
        view = self._make()
        with memory_dc(400, 200) as mdc:
            cd = ui.NMLVCUSTOMDRAW()
            cd.nmcd.hdc = mdc
            cd.nmcd.rc = ui.wintypes.RECT(0, 0, 400, 200)
            cd.nmcd.dwDrawStage = ui.CDDS_PREPAINT
            self.assertEqual(view._draw_list(ctypes.addressof(cd)),
                             ui.CDRF_NOTIFYITEMDRAW)

            view.select(1)
            cd.nmcd.dwDrawStage = ui.CDDS_PREPAINT
            view._draw_list(ctypes.addressof(cd))
            cd.nmcd.dwDrawStage = ui.CDDS_ITEMPREPAINT | ui.CDDS_SUBITEM
            cd.nmcd.dwItemSpec = 1
            cd.iSubItem = 0
            cd.nmcd.rc = ui.wintypes.RECT(0, 20, 400, 40)
            self.assertEqual(view._draw_list(ctypes.addressof(cd)),
                             ui.CDRF_SKIPDEFAULT)

            view.set_rows([])
            cd.nmcd.dwDrawStage = ui.CDDS_PREPAINT
            self.assertEqual(view._draw_list(ctypes.addressof(cd)),
                             ui.CDRF_SKIPDEFAULT)

    def test_begin_edit_commits_on_enter(self):
        view = self._make()
        self.assertTrue(view.begin_edit(1, 0))
        edit = view._edit_hwnd
        self.assertIsNotNone(edit)
        ui.user32.SetWindowTextW(edit, 'Renamed')
        ui.user32.SendMessageW(edit, ui.WM_KEYDOWN, ui.VK_RETURN, 0)
        self.assertIsNone(view._edit_hwnd)
        self.assertEqual(view.rows[1], ['Renamed', '2'])
        self.assertEqual(self.edits, [(1, 0, 'Renamed')])

    def test_begin_edit_commits_subitem(self):
        view = self._make()
        self.assertTrue(view.begin_edit(2, 1))
        ui.user32.SetWindowTextW(view._edit_hwnd, '33')
        ui.user32.SendMessageW(view._edit_hwnd, ui.WM_KEYDOWN,
                               ui.VK_RETURN, 0)
        self.assertEqual(view.rows[2], ['three', '33'])
        self.assertEqual(self.edits, [(2, 1, '33')])

    def test_escape_cancels_edit(self):
        view = self._make()
        before = [list(row) for row in view.rows]
        self.assertTrue(view.begin_edit(0, 1))
        ui.user32.SetWindowTextW(view._edit_hwnd, 'ignored')
        ui.user32.SendMessageW(view._edit_hwnd, ui.WM_KEYDOWN,
                               ui.VK_ESCAPE, 0)
        self.assertIsNone(view._edit_hwnd)
        self.assertEqual(view.rows, before)
        self.assertEqual(self.edits, [])

    def test_kill_focus_commits_edit(self):
        view = self._make()
        self.assertTrue(view.begin_edit(0, 0))
        ui.user32.SetWindowTextW(view._edit_hwnd, 'focus')
        ui.user32.SendMessageW(view._edit_hwnd, ui.WM_KILLFOCUS, 0, 0)
        self.assertEqual(view.rows[0], ['focus', '1'])
        self.assertEqual(self.edits, [(0, 0, 'focus')])

    def test_unchanged_edit_does_not_notify(self):
        view = self._make()
        self.assertTrue(view.begin_edit(1, 0))
        ui.user32.SendMessageW(view._edit_hwnd, ui.WM_KEYDOWN,
                               ui.VK_RETURN, 0)
        self.assertEqual(view.rows[1], ['two', '2'])
        self.assertEqual(self.edits, [])

    def test_begin_edit_rejects_invalid_item(self):
        view = self._make()
        self.assertFalse(view.begin_edit(-1, 0))
        self.assertFalse(view.begin_edit(9, 0))

    def test_double_click_notification_opens_editor(self):
        view = self._make()
        rect = ui.wintypes.RECT()
        rect.left = ui.LVIR_BOUNDS
        rect.top = 0
        ui.SendMessagePtrW(view.hwnd, ui.LVM_GETSUBITEMRECT, 0,
                           ctypes.addressof(rect))
        note = ui.NMITEMACTIVATE()
        note.hdr.hwndFrom = view.hwnd
        note.hdr.code = ctypes.c_uint(ui.NM_DBLCLK).value
        note.ptAction.x = (rect.left + rect.right) // 2
        note.ptAction.y = (rect.top + rect.bottom) // 2
        view._handle_notify(ui.NM_DBLCLK, ctypes.addressof(note))
        self.assertIsNotNone(view._edit_hwnd)
        self.assertEqual(view._edit_item, 0)
        view._end_edit(commit=False)

    def test_set_rows_cancels_edit(self):
        view = self._make()
        self.assertTrue(view.begin_edit(1, 0))
        view.set_rows([['only', '0']])
        self.assertIsNone(view._edit_hwnd)
        self.assertEqual(view.rows, [['only', '0']])
        self.assertEqual(self.edits, [])
