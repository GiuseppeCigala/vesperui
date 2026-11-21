"""Native message boxes and file/folder dialogs.

The dialogs come from the Win32 common dialog library, so they follow the
current system theme and language. Every function accepts an optional
``parent`` (an ``App`` instance or an HWND) and returns ``None`` (or an empty
list) when the user cancels.
"""
import os

from .common import *

MB_OK = 0x00000000
MB_OKCANCEL = 0x00000001
MB_YESNO = 0x00000004
MB_YESNOCANCEL = 0x00000003
MB_ICONERROR = 0x00000010
MB_ICONQUESTION = 0x00000020
MB_ICONWARNING = 0x00000030
MB_ICONINFORMATION = 0x00000040
MB_DEFBUTTON2 = 0x00000100

IDOK, IDCANCEL, IDYES, IDNO = 1, 2, 6, 7

OFN_OVERWRITEPROMPT = 0x00000002
OFN_HIDEREADONLY = 0x00000004
OFN_NOCHANGEDIR = 0x00000008
OFN_ALLOWMULTISELECT = 0x00000200
OFN_PATHMUSTEXIST = 0x00000800
OFN_FILEMUSTEXIST = 0x00001000
OFN_EXPLORER = 0x00080000

BIF_RETURNONLYFSDIRS = 0x00000001
BIF_EDITBOX = 0x00000010
BIF_NEWDIALOGSTYLE = 0x00000040

DEFAULT_FILTERS = [('All files', '*.*')]

__all__ = [
    'message_box', 'info', 'warning', 'error', 'question', 'ok_cancel',
    'open_file', 'open_files', 'save_file', 'select_folder',
    'DEFAULT_FILTERS', 'MB_OK', 'MB_OKCANCEL', 'MB_YESNO', 'MB_YESNOCANCEL',
    'MB_ICONERROR', 'MB_ICONQUESTION', 'MB_ICONWARNING',
    'MB_ICONINFORMATION', 'MB_DEFBUTTON2', 'IDOK', 'IDCANCEL', 'IDYES',
    'IDNO',
]


def _owner(parent):
    if parent is None:
        return None
    return getattr(parent, 'hwnd', parent)


def _filter_string(filters):
    """Build the double-NUL-terminated filter string used by Windows."""
    if not filters:
        return None
    parts = []
    for description, pattern in filters:
        parts.extend((description, pattern))
    return '\x00'.join(parts) + '\x00\x00'


def _parse_multi_selection(raw):
    """Turn the multi-select buffer into full file paths."""
    parts = [part for part in raw.split('\x00') if part]
    if not parts:
        return []
    if len(parts) == 1:
        return parts
    directory = parts[0]
    return [os.path.join(directory, name) for name in parts[1:]]


def _make_ofn(owner, title, filters, initial_dir, buffer, flags,
              default_ext=None):
    ofn = OPENFILENAMEW()
    ofn.lStructSize = ctypes.sizeof(OPENFILENAMEW)
    ofn.hwndOwner = owner
    ofn.lpstrFilter = _filter_string(filters)
    ofn.nFilterIndex = 1
    ofn.lpstrFile = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_wchar))
    ofn.nMaxFile = len(buffer)
    ofn.lpstrTitle = title
    ofn.lpstrInitialDir = initial_dir
    ofn.Flags = flags
    if default_ext:
        ofn.lpstrDefExt = default_ext
    return ofn


def message_box(text, title='VesperUI', style=MB_OK, parent=None):
    """Show a native message box and return the button identifier."""
    return user32.MessageBoxW(_owner(parent), text, title, style)


def info(text, title='Information', parent=None):
    return message_box(text, title, MB_OK | MB_ICONINFORMATION, parent)


def warning(text, title='Warning', parent=None):
    return message_box(text, title, MB_OK | MB_ICONWARNING, parent)


def error(text, title='Error', parent=None):
    return message_box(text, title, MB_OK | MB_ICONERROR, parent)


def question(text, title='Question', parent=None):
    """Ask a Yes/No question and return True for Yes."""
    return message_box(text, title, MB_YESNO | MB_ICONQUESTION,
                       parent) == IDYES


def ok_cancel(text, title='Confirm', parent=None):
    """Show an OK/Cancel box and return True for OK."""
    return message_box(text, title, MB_OKCANCEL | MB_ICONQUESTION,
                       parent) == IDOK


def open_file(title='Open File', filters=None, initial_dir=None, parent=None):
    """Return one selected file path, or None when cancelled."""
    filters = DEFAULT_FILTERS if filters is None else filters
    buffer = ctypes.create_unicode_buffer(1024)
    flags = (OFN_EXPLORER | OFN_FILEMUSTEXIST | OFN_PATHMUSTEXIST
             | OFN_NOCHANGEDIR | OFN_HIDEREADONLY)
    ofn = _make_ofn(_owner(parent), title, filters, initial_dir, buffer, flags)
    if not comdlg32.GetOpenFileNameW(ctypes.pointer(ofn)):
        return None
    return buffer.value


def open_files(title='Open Files', filters=None, initial_dir=None,
               parent=None):
    """Return every selected file path, or an empty list when cancelled."""
    filters = DEFAULT_FILTERS if filters is None else filters
    buffer = ctypes.create_unicode_buffer(65536)
    flags = (OFN_EXPLORER | OFN_FILEMUSTEXIST | OFN_PATHMUSTEXIST
             | OFN_NOCHANGEDIR | OFN_HIDEREADONLY | OFN_ALLOWMULTISELECT)
    ofn = _make_ofn(_owner(parent), title, filters, initial_dir, buffer, flags)
    if not comdlg32.GetOpenFileNameW(ctypes.pointer(ofn)):
        return []
    return _parse_multi_selection(buffer[:])


def save_file(title='Save File', default_name='', default_ext='',
              filters=None, initial_dir=None, parent=None):
    """Return the chosen save path, or None when cancelled.

    ``default_ext`` is just the extension (for example ``'txt'``); Windows
    appends it when the user does not type one.
    """
    filters = DEFAULT_FILTERS if filters is None else filters
    buffer = ctypes.create_unicode_buffer(default_name, 1024)
    flags = (OFN_EXPLORER | OFN_OVERWRITEPROMPT | OFN_PATHMUSTEXIST
             | OFN_NOCHANGEDIR)
    ofn = _make_ofn(_owner(parent), title, filters, initial_dir, buffer,
                    flags, default_ext)
    if not comdlg32.GetSaveFileNameW(ctypes.pointer(ofn)):
        return None
    return buffer.value


def select_folder(title='Select Folder', parent=None):
    """Return the chosen directory, or None when cancelled."""
    display = ctypes.create_unicode_buffer(260)
    browse = BROWSEINFOW()
    browse.hwndOwner = _owner(parent)
    browse.pszDisplayName = ctypes.cast(display, wintypes.LPWSTR)
    browse.lpszTitle = title
    browse.ulFlags = BIF_RETURNONLYFSDIRS | BIF_NEWDIALOGSTYLE | BIF_EDITBOX
    pidl = shell32.SHBrowseForFolderW(ctypes.pointer(browse))
    if not pidl:
        return None
    try:
        path = ctypes.create_unicode_buffer(260)
        if not shell32.SHGetPathFromIDListW(pidl, path):
            return None
        return path.value
    finally:
        ole32.CoTaskMemFree(pidl)
