import ctypes
import os
import unittest
from unittest import mock

import pywinui as ui
from pywinui import dialogs
from tests.helpers import WidgetTestCase


class FilterTests(unittest.TestCase):
    def test_filter_string(self):
        self.assertEqual(
            dialogs._filter_string([('Text', '*.txt'), ('All', '*.*')]),
            'Text\x00*.txt\x00All\x00*.*\x00\x00')

    def test_empty_filters(self):
        self.assertIsNone(dialogs._filter_string(None))
        self.assertIsNone(dialogs._filter_string([]))

    def test_parse_single_selection(self):
        self.assertEqual(
            dialogs._parse_multi_selection('C:\\dir\\a.txt\x00\x00'),
            ['C:\\dir\\a.txt'])

    def test_parse_multiple_selection(self):
        raw = 'C:\\dir\x00a.txt\x00b.txt\x00\x00'
        self.assertEqual(
            dialogs._parse_multi_selection(raw),
            [os.path.join('C:\\dir', 'a.txt'),
             os.path.join('C:\\dir', 'b.txt')])

    def test_parse_empty(self):
        self.assertEqual(dialogs._parse_multi_selection('\x00\x00'), [])


class OwnerTests(unittest.TestCase):
    def test_app_is_unwrapped(self):
        class Parent:
            hwnd = 123

        self.assertEqual(dialogs._owner(Parent()), 123)
        self.assertEqual(dialogs._owner(456), 456)
        self.assertIsNone(dialogs._owner(None))


class DialogCancelTests(unittest.TestCase):
    def test_open_file_cancel(self):
        with mock.patch.object(ui.comdlg32, 'GetOpenFileNameW', return_value=0):
            self.assertIsNone(dialogs.open_file())

    def test_open_files_cancel(self):
        with mock.patch.object(ui.comdlg32, 'GetOpenFileNameW', return_value=0):
            self.assertEqual(dialogs.open_files(), [])

    def test_save_file_cancel(self):
        with mock.patch.object(ui.comdlg32, 'GetSaveFileNameW', return_value=0):
            self.assertIsNone(dialogs.save_file())

    def test_select_folder_cancel(self):
        with mock.patch.object(ui.shell32, 'SHBrowseForFolderW',
                               return_value=None):
            self.assertIsNone(dialogs.select_folder())


class DialogSuccessTests(unittest.TestCase):
    @staticmethod
    def _write(ofn_ptr, text):
        ofn = ofn_ptr.contents
        ctypes.memmove(ofn.lpstrFile, ctypes.create_unicode_buffer(text),
                       (len(text) + 1) * ctypes.sizeof(ctypes.c_wchar))

    def test_open_file_builds_struct_and_returns_path(self):
        captured = {}

        def fake(ofn_ptr):
            ofn = ofn_ptr.contents
            captured['size'] = ofn.lStructSize
            captured['flags'] = ofn.Flags
            captured['filter'] = ofn.lpstrFilter
            captured['max'] = ofn.nMaxFile
            self._write(ofn_ptr, 'C:\\temp\\report.txt')
            return 1

        with mock.patch.object(ui.comdlg32, 'GetOpenFileNameW',
                               side_effect=fake):
            path = dialogs.open_file('Open', [('Text', '*.txt')])

        self.assertEqual(path, 'C:\\temp\\report.txt')
        self.assertEqual(captured['size'], ctypes.sizeof(ui.OPENFILENAMEW))
        self.assertEqual(captured['filter'], 'Text')
        self.assertGreaterEqual(captured['max'], 260)
        for flag in (dialogs.OFN_EXPLORER, dialogs.OFN_FILEMUSTEXIST,
                     dialogs.OFN_PATHMUSTEXIST):
            self.assertTrue(captured['flags'] & flag)

    def test_open_files_returns_every_selection(self):
        raw = 'C:\\temp\x00a.txt\x00b.txt\x00\x00'

        with mock.patch.object(ui.comdlg32, 'GetOpenFileNameW',
                               side_effect=lambda ptr: (self._write(ptr, raw), 1)[1]):
            paths = dialogs.open_files()

        self.assertEqual(paths, [os.path.join('C:\\temp', 'a.txt'),
                                 os.path.join('C:\\temp', 'b.txt')])

    def test_save_file_returns_path_and_extension(self):
        def fake(ofn_ptr):
            self._write(ofn_ptr, 'C:\\temp\\note.txt')
            return 1

        with mock.patch.object(ui.comdlg32, 'GetSaveFileNameW',
                               side_effect=fake) as save:
            path = dialogs.save_file(default_name='note.txt',
                                     default_ext='txt')

        self.assertEqual(path, 'C:\\temp\\note.txt')
        self.assertEqual(save.call_args[0][0].contents.lpstrDefExt, 'txt')

    def test_select_folder_returns_path(self):
        def fake_path(pidl, out):
            text = 'C:\\temp'
            ctypes.memmove(out, ctypes.create_unicode_buffer(text),
                           (len(text) + 1) * ctypes.sizeof(ctypes.c_wchar))
            return 1

        with mock.patch.object(ui.shell32, 'SHBrowseForFolderW',
                               return_value=1), \
                mock.patch.object(ui.shell32, 'SHGetPathFromIDListW',
                                  side_effect=fake_path), \
                mock.patch.object(ui.ole32, 'CoTaskMemFree') as free:
            path = dialogs.select_folder()

        self.assertEqual(path, 'C:\\temp')
        free.assert_called_once_with(1)


class MessageBoxTests(unittest.TestCase):
    def test_question_yes(self):
        with mock.patch.object(ui.user32, 'MessageBoxW',
                               return_value=ui.IDYES) as box:
            self.assertTrue(dialogs.question('Proceed?'))
        self.assertEqual(box.call_args[0][3], ui.MB_YESNO | ui.MB_ICONQUESTION)

    def test_question_no(self):
        with mock.patch.object(ui.user32, 'MessageBoxW',
                               return_value=ui.IDNO):
            self.assertFalse(dialogs.question('Proceed?'))

    def test_ok_cancel(self):
        with mock.patch.object(ui.user32, 'MessageBoxW',
                               return_value=ui.IDOK):
            self.assertTrue(dialogs.ok_cancel('Continue?'))
        with mock.patch.object(ui.user32, 'MessageBoxW',
                               return_value=ui.IDCANCEL):
            self.assertFalse(dialogs.ok_cancel('Continue?'))

    def test_info_style_and_text(self):
        with mock.patch.object(ui.user32, 'MessageBoxW',
                               return_value=ui.IDOK) as box:
            self.assertEqual(dialogs.info('hello', 'Title', None), ui.IDOK)
        args = box.call_args[0]
        self.assertEqual(args[1], 'hello')
        self.assertEqual(args[2], 'Title')
        self.assertEqual(args[3], ui.MB_OK | ui.MB_ICONINFORMATION)


class AppDialogHelperTests(WidgetTestCase):
    def test_message_box_helpers_pass_app(self):
        with mock.patch.object(dialogs, 'message_box',
                               return_value=ui.IDOK) as box:
            self.assertEqual(self.app.message_box('text', 'title', ui.MB_OK),
                             ui.IDOK)
        box.assert_called_once_with('text', 'title', ui.MB_OK, self.app)

        with mock.patch.object(dialogs, 'info', return_value=ui.IDOK) as info:
            self.assertEqual(self.app.info('text', 'title'), ui.IDOK)
        info.assert_called_once_with('text', 'title', self.app)

        with mock.patch.object(dialogs, 'warning',
                               return_value=ui.IDOK) as warning:
            self.assertEqual(self.app.warning('text', 'title'), ui.IDOK)
        warning.assert_called_once_with('text', 'title', self.app)

        with mock.patch.object(dialogs, 'error', return_value=ui.IDOK) as err:
            self.assertEqual(self.app.error('text', 'title'), ui.IDOK)
        err.assert_called_once_with('text', 'title', self.app)

        with mock.patch.object(dialogs, 'question',
                               return_value=True) as question:
            self.assertTrue(self.app.question('text', 'title'))
        question.assert_called_once_with('text', 'title', self.app)

        with mock.patch.object(dialogs, 'ok_cancel',
                               return_value=True) as ok_cancel:
            self.assertTrue(self.app.ok_cancel('text', 'title'))
        ok_cancel.assert_called_once_with('text', 'title', self.app)

    def test_file_helpers_pass_app(self):
        with mock.patch.object(dialogs, 'open_file',
                               return_value='C:\\a.txt') as open_file:
            self.assertEqual(self.app.open_file('T', None, None), 'C:\\a.txt')
        open_file.assert_called_once_with('T', None, None, self.app)

        with mock.patch.object(dialogs, 'open_files',
                               return_value=['C:\\a.txt']) as open_files:
            self.assertEqual(self.app.open_files('T', None, None),
                             ['C:\\a.txt'])
        open_files.assert_called_once_with('T', None, None, self.app)

        with mock.patch.object(dialogs, 'save_file',
                               return_value='C:\\a.txt') as save_file:
            self.assertEqual(
                self.app.save_file('T', 'a.txt', 'txt', None, None),
                'C:\\a.txt')
        save_file.assert_called_once_with('T', 'a.txt', 'txt', None, None,
                                          self.app)

        with mock.patch.object(dialogs, 'select_folder',
                               return_value='C:\\temp') as select_folder:
            self.assertEqual(self.app.select_folder('T'), 'C:\\temp')
        select_folder.assert_called_once_with('T', self.app)
