import os
import unittest
from unittest import mock

import pywinui as ui
from pywinui import dialogs


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


class MessageBoxTests(unittest.TestCase):
    def test_question_yes(self):
        with mock.patch.object(ui.user32, 'MessageBoxW',
                               return_value=ui.IDYES) as box:
            self.assertTrue(dialogs.question('Proceed?'))
        self.assertEqual(box.call_args[0][3], ui.MB_YESNO | ui.MB_ICONQUESTION)

    def test_question_no(self):
        with mock.patch.object(ui.user32, 'MessageBoxW', return_value=ui.IDNO):
            self.assertFalse(dialogs.question('Proceed?'))

    def test_ok_cancel(self):
        with mock.patch.object(ui.user32, 'MessageBoxW', return_value=ui.IDOK):
            self.assertTrue(dialogs.ok_cancel('Continue?'))
        with mock.patch.object(ui.user32, 'MessageBoxW', return_value=ui.IDCANCEL):
            self.assertFalse(dialogs.ok_cancel('Continue?'))

    def test_info_style_and_text(self):
        with mock.patch.object(ui.user32, 'MessageBoxW',
                               return_value=ui.IDOK) as box:
            self.assertEqual(dialogs.info('hello', 'Title', None), ui.IDOK)
        args = box.call_args[0]
        self.assertEqual(args[1], 'hello')
        self.assertEqual(args[2], 'Title')
        self.assertEqual(args[3], ui.MB_OK | ui.MB_ICONINFORMATION)
