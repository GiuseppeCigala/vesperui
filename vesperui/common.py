"""Shared Win32 bindings, constants, drawing helpers and base widget classes.

This module holds everything the per-widget modules import: ctypes bindings,
Win32 structures and constants, GDI drawing helpers, DPI utilities and the
Widget/Container base classes.

Fixes since v5.1:
- ctrl_id assigned in _NativeWidget.realize (works no matter how it was added)
- WM_COMMAND / WM_NOTIFY match widgets by HWND (no id collisions ever)
- ScrollView clips native descendants to the viewport with SetWindowRgn so they
  never spill past the ScrollView borders (previously only fully-offscreen
  controls were hidden, partially-overlapping ones overflowed the edges)
- Theme changes propagate to native controls (WM_CTLCOLOR*, refresh_theme)
"""
import ctypes
import traceback
from ctypes import wintypes

user32   = ctypes.WinDLL('user32',   use_last_error=True)
gdi32    = ctypes.WinDLL('gdi32',    use_last_error=True)
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
comctl32 = ctypes.WinDLL('comctl32', use_last_error=True)
msimg32  = ctypes.WinDLL('msimg32',  use_last_error=True)   # GradientFill lives here
uxtheme  = ctypes.WinDLL('uxtheme',  use_last_error=True)
dwmapi   = ctypes.WinDLL('dwmapi',   use_last_error=True)
comdlg32 = ctypes.WinDLL('comdlg32', use_last_error=True)
shell32  = ctypes.WinDLL('shell32',  use_last_error=True)
ole32    = ctypes.WinDLL('ole32',    use_last_error=True)

LRESULT = ctypes.c_ssize_t
WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT,
                              wintypes.WPARAM, wintypes.LPARAM)

# ============================================================================
# STRUCTURES
# ============================================================================
class WNDCLASSEXW(ctypes.Structure):
    _fields_ = [('cbSize', wintypes.UINT), ('style', wintypes.UINT),
                ('lpfnWndProc', WNDPROC), ('cbClsExtra', ctypes.c_int),
                ('cbWndExtra', ctypes.c_int), ('hInstance', wintypes.HINSTANCE),
                ('hIcon', wintypes.HICON), ('hCursor', wintypes.HANDLE),
                ('hbrBackground', wintypes.HBRUSH), ('lpszMenuName', wintypes.LPCWSTR),
                ('lpszClassName', wintypes.LPCWSTR), ('hIconSm', wintypes.HICON)]

class PAINTSTRUCT(ctypes.Structure):
    _fields_ = [('hdc', wintypes.HDC), ('fErase', wintypes.BOOL),
                ('rcPaint', wintypes.RECT), ('fRestore', wintypes.BOOL),
                ('fIncUpdate', wintypes.BOOL), ('rgbReserved', ctypes.c_byte * 32)]

class MSG(ctypes.Structure):
    _fields_ = [('hwnd', wintypes.HWND), ('message', wintypes.UINT),
                ('wParam', wintypes.WPARAM), ('lParam', wintypes.LPARAM),
                ('time', wintypes.DWORD), ('pt', wintypes.POINT)]

class INITCOMMONCONTROLSEX(ctypes.Structure):
    _fields_ = [('dwSize', wintypes.DWORD), ('dwICC', wintypes.DWORD)]

class NMHDR(ctypes.Structure):
    _fields_ = [('hwndFrom', wintypes.HWND), ('idFrom', ctypes.c_size_t),
                ('code', wintypes.UINT)]

class LVCOLUMNW(ctypes.Structure):
    _fields_ = [('mask', wintypes.UINT), ('fmt', ctypes.c_int),
                ('cx', ctypes.c_int), ('pszText', wintypes.LPWSTR),
                ('cchTextMax', ctypes.c_int), ('iSubItem', ctypes.c_int),
                ('iImage', ctypes.c_int), ('iOrder', ctypes.c_int),
                ('cxMin', ctypes.c_int), ('cxDefault', ctypes.c_int),
                ('cxIdeal', ctypes.c_int)]

class LVITEMW(ctypes.Structure):
    _fields_ = [('mask', wintypes.UINT), ('iItem', ctypes.c_int),
                ('iSubItem', ctypes.c_int), ('state', wintypes.UINT),
                ('stateMask', wintypes.UINT), ('pszText', wintypes.LPWSTR),
                ('cchTextMax', ctypes.c_int), ('iImage', ctypes.c_int),
                ('lParam', wintypes.LPARAM), ('iIndent', ctypes.c_int),
                ('iGroupId', ctypes.c_int), ('cColumns', wintypes.UINT),
                ('puColumns', ctypes.c_void_p), ('piColFmt', ctypes.c_void_p),
                ('iGroup', ctypes.c_int)]

class NMLISTVIEW(ctypes.Structure):
    _fields_ = [('hdr', NMHDR), ('iItem', ctypes.c_int),
                ('iSubItem', ctypes.c_int), ('uNewState', wintypes.UINT),
                ('uOldState', wintypes.UINT), ('uChanged', wintypes.UINT),
                ('ptAction', wintypes.POINT), ('lParam', wintypes.LPARAM)]

class NMCUSTOMDRAW(ctypes.Structure):
    _fields_ = [('hdr', NMHDR), ('dwDrawStage', wintypes.DWORD),
                ('hdc', wintypes.HDC), ('rc', wintypes.RECT),
                ('dwItemSpec', ctypes.c_size_t), ('uItemState', wintypes.UINT),
                ('lItemlParam', wintypes.LPARAM)]

class NMLVCUSTOMDRAW(ctypes.Structure):
    _fields_ = [('nmcd', NMCUSTOMDRAW), ('clrText', wintypes.COLORREF),
                ('clrTextBk', wintypes.COLORREF), ('iSubItem', ctypes.c_int),
                ('dwItemType', wintypes.DWORD), ('clrFace', wintypes.COLORREF),
                ('iIconEffect', ctypes.c_int), ('iIconPhase', ctypes.c_int),
                ('iPartId', ctypes.c_int), ('iStateId', ctypes.c_int),
                ('rcText', wintypes.RECT), ('uAlign', wintypes.UINT)]

class DRAWITEMSTRUCT(ctypes.Structure):
    _fields_ = [('CtlType', wintypes.UINT), ('CtlID', wintypes.UINT),
                ('itemID', wintypes.UINT), ('itemAction', wintypes.UINT),
                ('itemState', wintypes.UINT), ('hwndItem', wintypes.HWND),
                ('hDC', wintypes.HDC), ('rcItem', wintypes.RECT),
                ('itemData', ctypes.c_size_t)]

class MEASUREITEMSTRUCT(ctypes.Structure):
    _fields_ = [('CtlType', wintypes.UINT), ('CtlID', wintypes.UINT),
                ('itemID', wintypes.UINT), ('itemWidth', wintypes.UINT),
                ('itemHeight', wintypes.UINT), ('itemData', ctypes.c_size_t)]

class OPENFILENAMEW(ctypes.Structure):
    _fields_ = [('lStructSize', wintypes.DWORD),
                ('hwndOwner', wintypes.HWND),
                ('hInstance', wintypes.HINSTANCE),
                ('lpstrFilter', wintypes.LPCWSTR),
                ('lpstrCustomFilter', wintypes.LPWSTR),
                ('nMaxCustFilter', wintypes.DWORD),
                ('nFilterIndex', wintypes.DWORD),
                ('lpstrFile', ctypes.POINTER(ctypes.c_wchar)),
                ('nMaxFile', wintypes.DWORD),
                ('lpstrFileTitle', wintypes.LPWSTR),
                ('nMaxFileTitle', wintypes.DWORD),
                ('lpstrInitialDir', wintypes.LPCWSTR),
                ('lpstrTitle', wintypes.LPCWSTR),
                ('Flags', wintypes.DWORD),
                ('nFileOffset', wintypes.WORD),
                ('nFileExtension', wintypes.WORD),
                ('lpstrDefExt', wintypes.LPCWSTR),
                ('lCustData', wintypes.LPARAM),
                ('lpfnHook', ctypes.c_void_p),
                ('lpTemplateName', wintypes.LPCWSTR),
                ('pvReserved', ctypes.c_void_p),
                ('dwReserved', wintypes.DWORD),
                ('FlagsEx', wintypes.DWORD)]

class BROWSEINFOW(ctypes.Structure):
    _fields_ = [('hwndOwner', wintypes.HWND),
                ('pidlRoot', ctypes.c_void_p),
                ('pszDisplayName', wintypes.LPWSTR),
                ('lpszTitle', wintypes.LPCWSTR),
                ('ulFlags', wintypes.UINT),
                ('lpfn', ctypes.c_void_p),
                ('lParam', wintypes.LPARAM),
                ('iImage', ctypes.c_int)]

class TRIVERTEX(ctypes.Structure):
    _fields_ = [('x', wintypes.LONG), ('y', wintypes.LONG),
                ('Red', wintypes.USHORT), ('Green', wintypes.USHORT),
                ('Blue', wintypes.USHORT), ('Alpha', wintypes.USHORT)]

class GRADIENT_RECT(ctypes.Structure):
    _fields_ = [('UpperLeft', wintypes.ULONG), ('LowerRight', wintypes.ULONG)]

class BLENDFUNCTION(ctypes.Structure):
    _fields_ = [('BlendOp', ctypes.c_ubyte), ('BlendFlags', ctypes.c_ubyte),
                ('SourceConstantAlpha', ctypes.c_ubyte), ('AlphaFormat', ctypes.c_ubyte)]

# ============================================================================
# CONSTANTS
# ============================================================================
CW_USEDEFAULT = -2147483648
WS_OVERLAPPEDWINDOW = 0x00CF0000
WS_CLIPCHILDREN = 0x02000000
WS_CHILD, WS_VISIBLE, WS_VSCROLL, WS_TABSTOP, WS_BORDER = 0x40000000, 0x10000000, 0x00200000, 0x00010000, 0x00800000
WS_GROUP = 0x00020000
ES_LEFT, ES_MULTILINE, ES_AUTOHSCROLL, ES_AUTOVSCROLL = 0, 0x0004, 0x0080, 0x0040
BS_AUTOCHECKBOX, BS_AUTORADIOBUTTON = 0x0003, 0x0009
CBS_DROPDOWNLIST = 0x0003
CBS_OWNERDRAWFIXED, CBS_HASSTRINGS = 0x0010, 0x0200
CS_HREDRAW, CS_VREDRAW = 0x0002, 0x0001
SW_SHOW, SW_HIDE, SW_SHOWNA, IDC_ARROW = 5, 0, 8, 32512
SWP_NOZORDER, SWP_NOACTIVATE = 0x0004, 0x0010
SWP_NOREDRAW = 0x0008
SW_SCROLLCHILDREN, SW_INVALIDATE, SW_ERASE = 0x0001, 0x0002, 0x0004
WM_CREATE, WM_SIZE, WM_DESTROY, WM_CLOSE = 0x0001, 0x0005, 0x0002, 0x0010
WM_PAINT, WM_COMMAND, WM_NOTIFY, WM_ERASEBKGND, WM_TIMER = 0x000F, 0x0111, 0x004E, 0x0014, 0x0113
WM_DRAWITEM, WM_MEASUREITEM = 0x002B, 0x002C
WM_MOUSEMOVE, WM_LBUTTONDOWN, WM_LBUTTONUP, WM_MOUSEWHEEL = 0x0200, 0x0201, 0x0202, 0x020A
WM_KEYDOWN, WM_CHAR, WM_SETFOCUS, WM_DPICHANGED = 0x0100, 0x0102, 0x0007, 0x02E0
WM_SETFONT, WM_CTLCOLORSTATIC, WM_CTLCOLORBTN, WM_CTLCOLORLISTBOX, WM_CTLCOLOREDIT = \
    0x0030, 0x0138, 0x0135, 0x0134, 0x0133
WM_QUIT = 0x0012
PM_NOREMOVE, PM_REMOVE = 0x0000, 0x0001
EN_CHANGE, BN_CLICKED, CBN_SELCHANGE = 0x0300, 0x0000, 0x0001
EM_GETSEL, EM_SETSEL = 0x00B0, 0x00B1
BM_GETCHECK, BM_SETCHECK, BST_CHECKED, BST_UNCHECKED = 0x00F0, 0x00F1, 1, 0
CB_ADDSTRING, CB_GETCURSEL, CB_SETCURSEL = 0x0143, 0x0147, 0x014E
MF_STRING, MF_POPUP, MF_SEPARATOR = 0x0000, 0x0010, 0x0800
DT_CENTER, DT_VCENTER, DT_SINGLELINE, DT_LEFT = 0x0001, 0x0004, 0x0020, 0
TRANSPARENT, NULL_BRUSH, SRCCOPY, LOGPIXELSX = 1, 5, 0x00CC0020, 88
# Gradient / alpha-blending constants
GRADIENT_FILL_RECT_H, GRADIENT_FILL_RECT_V = 0x00000000, 0x00000001
AC_SRC_OVER, AC_SRC_ALPHA = 0x00, 0x01
ULW_ALPHA = 0x00000002
PS_SOLID = 0
BS_SOLID = 0
RGN_AND = 1
SPI_GETWORKAREA = 0x0030
# Text rendering quality
CLEARTYPE_QUALITY = 5
DEFAULT_CHARSET = 1
FW_NORMAL, FW_BOLD = 400, 700
VK_SHIFT, VK_TAB, VK_RETURN, VK_SPACE = 0x10, 0x09, 0x0D, 0x20
VK_LEFT, VK_UP, VK_RIGHT, VK_DOWN = 0x25, 0x26, 0x27, 0x28
GWLP_WNDPROC = -4
GWL_STYLE = -16
ICC_LISTVIEW_CLASSES = 0x00000001
LVS_REPORT, LVS_SINGLESEL, LVS_SHOWSELALWAYS = 0x0001, 0x0004, 0x0008
LVS_EX_FULLROWSELECT = 0x00000020
LVM_FIRST = 0x1000
LVM_INSERTCOLUMNW            = LVM_FIRST + 97
LVM_INSERTITEMW              = LVM_FIRST + 77
LVM_SETITEMTEXTW             = LVM_FIRST + 116
LVM_SETCOLUMNWIDTH           = LVM_FIRST + 30
LVM_GETNEXTITEM              = LVM_FIRST + 12
LVM_SETITEMSTATE             = LVM_FIRST + 43
LVM_GETHEADER                = LVM_FIRST + 31
LVM_DELETEALLITEMS           = LVM_FIRST + 9
LVM_SETEXTENDEDLISTVIEWSTYLE = LVM_FIRST + 54
LVM_SETBKCOLOR              = LVM_FIRST + 44
LVM_SETTEXTCOLOR            = LVM_FIRST + 36
LVM_SETTEXTBKCOLOR          = LVM_FIRST + 38
LVCF_TEXT, LVCF_WIDTH, LVCF_FMT = 0x0004, 0x0002, 0x0001
LVCFMT_LEFT = 0
LVIF_TEXT, LVIF_STATE, LVIS_SELECTED, LVNI_SELECTED = 0x0001, 0x0008, 0x0002, 0x0002
LVIS_FOCUSED = 0x0001
LVN_ITEMCHANGED = -101
NM_CUSTOMDRAW = -12
CDDS_PREPAINT = 0x00000001
CDDS_ITEMPREPAINT = 0x00010001
CDDS_SUBITEM = 0x00020000
CDRF_DODEFAULT = 0x00000000
CDRF_NEWFONT = 0x00000002
CDRF_SKIPDEFAULT = 0x00000004
CDRF_NOTIFYITEMDRAW = 0x00000020
CDRF_NOTIFYSUBITEMDRAW = 0x00000020
ODT_COMBOBOX = 3
ODS_SELECTED = 0x0001

def COLORREF(r, g, b): return r | (g << 8) | (b << 16)

# ============================================================================
# COLOR / DRAWING HELPERS (glossy theme)
# ============================================================================
def _clamp(v, lo=0, hi=255): return max(lo, min(hi, int(v)))

def mix(c1, c2, t):
    """Linear blend between two RGB tuples. t=0 -> c1, t=1 -> c2."""
    return (_clamp(c1[0] + (c2[0] - c1[0]) * t),
            _clamp(c1[1] + (c2[1] - c1[1]) * t),
            _clamp(c1[2] + (c2[2] - c1[2]) * t))

def lighten(c, t): return mix(c, (255, 255, 255), t)
def darken(c, t):  return mix(c, (0, 0, 0), t)
def is_dark(color): return sum(color) > 380

def _tri(x, y, rgb, alpha=0):
    return TRIVERTEX(x, y, rgb[0] << 8, rgb[1] << 8, rgb[2] << 8, alpha << 8)

def fill_gradient_v(hdc, x, y, w, h, top, bottom):
    """Vertical linear gradient (top -> bottom)."""
    if w <= 0 or h <= 0: return
    verts = (TRIVERTEX * 2)(_tri(x, y, top), _tri(x + w, y + h, bottom))
    rect = (GRADIENT_RECT * 1)(GRADIENT_RECT(0, 1))
    msimg32.GradientFill(hdc, verts, 2, ctypes.byref(rect), 1, GRADIENT_FILL_RECT_V)

def fill_gradient_h(hdc, x, y, w, h, left, right):
    """Horizontal linear gradient (left -> right)."""
    if w <= 0 or h <= 0: return
    verts = (TRIVERTEX * 2)(_tri(x, y, left), _tri(x + w, y + h, right))
    rect = (GRADIENT_RECT * 1)(GRADIENT_RECT(0, 1))
    msimg32.GradientFill(hdc, verts, 2, ctypes.byref(rect), 1, GRADIENT_FILL_RECT_H)

def fill_round_rect(hdc, app, x, y, w, h, radius, color):
    """Fill a rounded rectangle with a solid color."""
    rgn = gdi32.CreateRoundRectRgn(x, y, x + w + 1, y + h + 1, radius, radius)
    saved = gdi32.SaveDC(hdc)
    gdi32.ExtSelectClipRgn(hdc, rgn, RGN_AND)
    rc = wintypes.RECT(x, y, x + w, y + h)
    user32.FillRect(hdc, ctypes.byref(rc), app.get_brush(color))
    gdi32.RestoreDC(hdc, saved)
    gdi32.DeleteObject(rgn)

def fill_round_gradient_v(hdc, app, x, y, w, h, radius, top, bottom):
    """Fill a rounded rectangle with a vertical gradient."""
    rgn = gdi32.CreateRoundRectRgn(x, y, x + w + 1, y + h + 1, radius, radius)
    saved = gdi32.SaveDC(hdc)
    gdi32.ExtSelectClipRgn(hdc, rgn, RGN_AND)
    fill_gradient_v(hdc, x, y, w, h, top, bottom)
    gdi32.RestoreDC(hdc, saved)
    gdi32.DeleteObject(rgn)

def fill_round_gradient_h(hdc, app, x, y, w, h, radius, left, right):
    """Fill a rounded rectangle with a horizontal gradient."""
    rgn = gdi32.CreateRoundRectRgn(x, y, x + w + 1, y + h + 1, radius, radius)
    saved = gdi32.SaveDC(hdc)
    gdi32.ExtSelectClipRgn(hdc, rgn, RGN_AND)
    fill_gradient_h(hdc, x, y, w, h, left, right)
    gdi32.RestoreDC(hdc, saved)
    gdi32.DeleteObject(rgn)

def stroke_round_rect(hdc, app, x, y, w, h, radius, color, width=1):
    """Draw the outline of a rounded rectangle."""
    pen = app.get_pen(color, width)
    old = gdi32.SelectObject(hdc, pen)
    ob = gdi32.SelectObject(hdc, gdi32.GetStockObject(NULL_BRUSH))
    gdi32.RoundRect(hdc, x, y, x + w, y + h, radius, radius)
    gdi32.SelectObject(hdc, old); gdi32.SelectObject(hdc, ob)

def draw_shadow(hdc, app, x, y, w, h, radius, spread=4, alpha_steps=10):
    """Soft drop shadow: stacked rounded rects blended toward black. On dark
    backgrounds the blend is stronger so the blur still reads clearly."""
    dark = is_dark(app.theme_fg)
    for i in range(alpha_steps, 0, -1):
        t = i / (alpha_steps + 1)
        strength = (0.08 + 0.62 * (1 - t)) if dark else (0.05 + 0.30 * (1 - t))
        col = mix(app.bg, (0, 0, 0), strength)
        fill_round_rect(hdc, app, x - i + spread, y - i + spread + 2,
                        w + 2 * i, h + 2 * i, radius + i, col)

def draw_gloss(hdc, app, x, y, w, h, radius, base):
    """Draw a glossy highlight: a lighter band across the top half."""
    top = lighten(base, 0.55)
    mid = lighten(base, 0.18)
    rgn = gdi32.CreateRoundRectRgn(x, y, x + w + 1, y + h + 1, radius, radius)
    saved = gdi32.SaveDC(hdc)
    gdi32.ExtSelectClipRgn(hdc, rgn, RGN_AND)
    half = max(1, int(h * 0.5))
    fill_gradient_v(hdc, x, y, w, half, top, mid)
    gdi32.RestoreDC(hdc, saved)
    gdi32.DeleteObject(rgn)

# ============================================================================
# DPI
# ============================================================================
def enable_dpi_awareness():
    try:
        user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)); return
    except (AttributeError, OSError): pass
    try: user32.SetProcessDPIAware()
    except (AttributeError, OSError): pass


def _uxtheme_ordinal(index):
    try:
        return uxtheme[index]
    except (AttributeError, OSError):
        return None


def enable_dark_mode():
    """Best-effort opt-in to dark native controls (Windows 10 1903+)."""
    fn = _uxtheme_ordinal(135)          # SetPreferredAppMode
    if fn is None:
        return
    try:
        fn.argtypes = [ctypes.c_int]
        fn.restype = ctypes.c_int
        fn(2)                            # ForceDark
    except OSError:
        pass


def allow_dark_window(hwnd):
    """Let a window use the dark Explorer theme (Windows 10 1903+)."""
    fn = _uxtheme_ordinal(133)           # AllowDarkModeForWindow
    if fn is None or not hwnd:
        return
    try:
        fn.argtypes = [wintypes.HWND, wintypes.BOOL]
        fn.restype = wintypes.BOOL
        fn(hwnd, True)
    except OSError:
        pass


def flush_menu_themes():
    """Redraw open menus with the current dark setting."""
    fn = _uxtheme_ordinal(136)           # FlushMenuThemes
    if fn is None:
        return
    try:
        fn.argtypes = []
        fn.restype = None
        fn()
    except OSError:
        pass


def set_dark_title_bar(hwnd, bg=None, fg=None):
    """Ask DWM for a dark title bar (Windows 10 2004+ / Windows 11)."""
    if not hwnd:
        return
    try:
        dwmapi.DwmSetWindowAttribute.argtypes = [
            wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
        dwmapi.DwmSetWindowAttribute.restype = ctypes.c_long
        flag = wintypes.BOOL(1)
        ptr = ctypes.cast(ctypes.byref(flag), ctypes.c_void_p)
        # 20 = DWMWA_USE_IMMERSIVE_DARK_MODE (19 on some older builds).
        dwmapi.DwmSetWindowAttribute(hwnd, 19, ptr, ctypes.sizeof(flag))
        dwmapi.DwmSetWindowAttribute(hwnd, 20, ptr, ctypes.sizeof(flag))
        if bg is None or fg is None:
            return
        # Windows 11 also honors explicit caption, border and text colours.
        for attribute, color in ((34, bg), (35, bg), (36, fg)):
            value = ctypes.c_uint(COLORREF(*color))
            dwmapi.DwmSetWindowAttribute(
                hwnd, attribute,
                ctypes.cast(ctypes.byref(value), ctypes.c_void_p),
                ctypes.sizeof(value))
    except (AttributeError, OSError):
        pass

def get_window_dpi(hwnd):
    try:
        d = user32.GetDpiForWindow(hwnd)
        if d: return d
    except (AttributeError, OSError): pass
    hdc = user32.GetDC(hwnd)
    dpi = gdi32.GetDeviceCaps(hdc, LOGPIXELSX)
    user32.ReleaseDC(hwnd, hdc)
    return dpi or 96

# ============================================================================
# API SIGNATURES
# ============================================================================
user32.RegisterClassExW.argtypes = [ctypes.POINTER(WNDCLASSEXW)]
user32.RegisterClassExW.restype = wintypes.ATOM
user32.UnregisterClassW.argtypes = [wintypes.LPCWSTR, wintypes.HINSTANCE]
user32.UnregisterClassW.restype = wintypes.BOOL
user32.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR,
    wintypes.DWORD, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID]
user32.CreateWindowExW.restype = wintypes.HWND
user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.DefWindowProcW.restype = LRESULT
user32.CallWindowProcW.argtypes = [ctypes.c_void_p, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.CallWindowProcW.restype = LRESULT
user32.GetMessageW.argtypes = [ctypes.POINTER(MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
user32.GetMessageW.restype = ctypes.c_int
user32.PeekMessageW.argtypes = [ctypes.POINTER(MSG), wintypes.HWND, wintypes.UINT,
                                wintypes.UINT, wintypes.UINT]
user32.PeekMessageW.restype = wintypes.BOOL
user32.IsWindow.argtypes = [wintypes.HWND]; user32.IsWindow.restype = wintypes.BOOL
user32.TranslateMessage.argtypes = [ctypes.POINTER(MSG)]
user32.DispatchMessageW.argtypes = [ctypes.POINTER(MSG)]
user32.DispatchMessageW.restype = LRESULT
user32.PostQuitMessage.argtypes = [ctypes.c_int]
user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.SendMessageW.restype = LRESULT
user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.UpdateWindow.argtypes = [wintypes.HWND]
user32.SetFocus.argtypes = [wintypes.HWND]; user32.SetFocus.restype = wintypes.HWND
user32.SetCapture.argtypes = [wintypes.HWND]; user32.SetCapture.restype = wintypes.HWND
user32.ReleaseCapture.argtypes = []
user32.ScreenToClient.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]
user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
                                ctypes.c_int, ctypes.c_int, wintypes.UINT]
user32.BeginPaint.argtypes = [wintypes.HWND, ctypes.POINTER(PAINTSTRUCT)]
user32.BeginPaint.restype = wintypes.HDC
user32.EndPaint.argtypes = [wintypes.HWND, ctypes.POINTER(PAINTSTRUCT)]
user32.InvalidateRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT), wintypes.BOOL]
user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.FillRect.argtypes = [wintypes.HDC, ctypes.POINTER(wintypes.RECT), wintypes.HBRUSH]
user32.DrawFocusRect.argtypes = [wintypes.HDC, ctypes.POINTER(wintypes.RECT)]
user32.DrawTextW.argtypes = [wintypes.HDC, wintypes.LPCWSTR, ctypes.c_int,
                             ctypes.POINTER(wintypes.RECT), wintypes.UINT]
user32.MessageBoxW.argtypes = [wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.UINT]
user32.MessageBoxW.restype = ctypes.c_int
user32.GetKeyState.argtypes = [ctypes.c_int]; user32.GetKeyState.restype = ctypes.c_short
user32.GetDC.argtypes = [wintypes.HWND]; user32.GetDC.restype = wintypes.HDC
user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
user32.GetDpiForSystem.argtypes = []; user32.GetDpiForSystem.restype = wintypes.UINT
user32.GetSystemMetrics.argtypes = [ctypes.c_int]; user32.GetSystemMetrics.restype = ctypes.c_int
user32.ScrollWindowEx.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_int,
                                   ctypes.POINTER(wintypes.RECT), ctypes.POINTER(wintypes.RECT),
                                   wintypes.HRGN, ctypes.POINTER(wintypes.RECT),
                                   wintypes.UINT]
user32.ScrollWindowEx.restype = ctypes.c_int
user32.GetUpdateRgn.argtypes = [wintypes.HWND, wintypes.HRGN, wintypes.BOOL]
user32.GetUpdateRgn.restype = ctypes.c_int
gdi32.RectInRegion.argtypes = [wintypes.HRGN, ctypes.POINTER(wintypes.RECT)]
gdi32.RectInRegion.restype = wintypes.BOOL
user32.BeginDeferWindowPos.argtypes = [ctypes.c_int]; user32.BeginDeferWindowPos.restype = wintypes.HANDLE
user32.DeferWindowPos.argtypes = [wintypes.HANDLE, wintypes.HWND, wintypes.HWND,
                                   ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                   ctypes.c_int, wintypes.UINT]
user32.DeferWindowPos.restype = wintypes.HANDLE
user32.EndDeferWindowPos.argtypes = [wintypes.HANDLE]
user32.EndDeferWindowPos.restype = wintypes.BOOL
user32.SystemParametersInfoW.argtypes = [wintypes.UINT, wintypes.UINT,
                                         ctypes.c_void_p, wintypes.UINT]
user32.SystemParametersInfoW.restype = wintypes.BOOL
user32.CreateMenu.restype = wintypes.HMENU
user32.CreatePopupMenu.restype = wintypes.HMENU
user32.AppendMenuW.argtypes = [wintypes.HMENU, wintypes.UINT, ctypes.c_size_t, wintypes.LPCWSTR]
user32.SetMenu.argtypes = [wintypes.HWND, wintypes.HMENU]
user32.LoadCursorW.argtypes = [wintypes.HINSTANCE, ctypes.c_void_p]
user32.LoadCursorW.restype = wintypes.HANDLE
user32.SetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPCWSTR]
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
user32.GetWindowTextLengthW.restype = ctypes.c_int
user32.SetTimer.argtypes = [wintypes.HWND, ctypes.c_size_t, wintypes.UINT, ctypes.c_void_p]
user32.SetTimer.restype = ctypes.c_size_t
user32.KillTimer.argtypes = [wintypes.HWND, ctypes.c_size_t]
comdlg32.GetOpenFileNameW.argtypes = [ctypes.POINTER(OPENFILENAMEW)]
comdlg32.GetOpenFileNameW.restype = wintypes.BOOL
comdlg32.GetSaveFileNameW.argtypes = [ctypes.POINTER(OPENFILENAMEW)]
comdlg32.GetSaveFileNameW.restype = wintypes.BOOL
shell32.SHBrowseForFolderW.argtypes = [ctypes.POINTER(BROWSEINFOW)]
shell32.SHBrowseForFolderW.restype = ctypes.c_void_p
shell32.SHGetPathFromIDListW.argtypes = [ctypes.c_void_p, wintypes.LPWSTR]
shell32.SHGetPathFromIDListW.restype = wintypes.BOOL
ole32.CoTaskMemFree.argtypes = [ctypes.c_void_p]
ole32.CoTaskMemFree.restype = None
user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
user32.GetWindowLongW.restype = wintypes.LONG
uxtheme.SetWindowTheme.argtypes = [wintypes.HWND, wintypes.LPCWSTR,
                                   wintypes.LPCWSTR]
uxtheme.SetWindowTheme.restype = ctypes.c_long

_SetWndPtr = getattr(user32, 'SetWindowLongPtrW', user32.SetWindowLongW)
_SetWndPtr.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_void_p]
_SetWndPtr.restype = ctypes.c_void_p

SendMessageStrW = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT,
                                     wintypes.WPARAM, wintypes.LPCWSTR)(('SendMessageW', user32))
SendMessagePtrW = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT,
                                     wintypes.WPARAM, ctypes.c_void_p)(('SendMessageW', user32))

gdi32.CreateSolidBrush.argtypes = [wintypes.COLORREF]; gdi32.CreateSolidBrush.restype = wintypes.HBRUSH
gdi32.CreatePen.argtypes = [ctypes.c_int, ctypes.c_int, wintypes.COLORREF]
gdi32.CreatePen.restype = wintypes.HPEN
gdi32.CreateFontW.argtypes = [ctypes.c_int] * 5 + [wintypes.DWORD] * 8 + [wintypes.LPCWSTR]
gdi32.CreateFontW.restype = wintypes.HFONT
gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
gdi32.SelectObject.restype = wintypes.HGDIOBJ
gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
gdi32.DeleteObject.restype = wintypes.BOOL
gdi32.RoundRect.argtypes = [wintypes.HDC] + [ctypes.c_int] * 6
gdi32.Rectangle.argtypes = [wintypes.HDC] + [ctypes.c_int] * 4
gdi32.Ellipse.argtypes = [wintypes.HDC] + [ctypes.c_int] * 4
gdi32.MoveToEx.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int, ctypes.POINTER(wintypes.POINT)]
gdi32.LineTo.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
gdi32.SetBkMode.argtypes = [wintypes.HDC, ctypes.c_int]
gdi32.SetTextColor.argtypes = [wintypes.HDC, wintypes.COLORREF]
gdi32.GetStockObject.argtypes = [ctypes.c_int]; gdi32.GetStockObject.restype = wintypes.HGDIOBJ
gdi32.GetTextExtentPoint32W.argtypes = [wintypes.HDC, wintypes.LPCWSTR, ctypes.c_int, ctypes.POINTER(wintypes.SIZE)]
gdi32.GetDeviceCaps.argtypes = [wintypes.HDC, ctypes.c_int]; gdi32.GetDeviceCaps.restype = ctypes.c_int
gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]; gdi32.CreateCompatibleDC.restype = wintypes.HDC
gdi32.CreateCompatibleBitmap.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP
gdi32.BitBlt.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                         wintypes.HDC, ctypes.c_int, ctypes.c_int, wintypes.DWORD]
gdi32.DeleteDC.argtypes = [wintypes.HDC]
gdi32.SaveDC.argtypes = [wintypes.HDC]; gdi32.SaveDC.restype = ctypes.c_int
gdi32.RestoreDC.argtypes = [wintypes.HDC, ctypes.c_int]
gdi32.IntersectClipRect.argtypes = [wintypes.HDC] + [ctypes.c_int] * 4
gdi32.IntersectClipRect.restype = ctypes.c_int
gdi32.CreateRectRgn.argtypes = [ctypes.c_int] * 4
gdi32.CreateRectRgn.restype = wintypes.HRGN

# --- Gradient / rounded-region / alpha-blend APIs (for the glossy theme) ---
# Only the signatures not already declared above are listed here.
msimg32.GradientFill.argtypes = [wintypes.HDC, ctypes.POINTER(TRIVERTEX), wintypes.ULONG,
                                 ctypes.c_void_p, wintypes.ULONG, wintypes.ULONG]
msimg32.GradientFill.restype = wintypes.BOOL
gdi32.CreateRoundRectRgn.argtypes = [ctypes.c_int] * 6
gdi32.CreateRoundRectRgn.restype = wintypes.HRGN
gdi32.SelectClipRgn.argtypes = [wintypes.HDC, wintypes.HRGN]
gdi32.SelectClipRgn.restype = ctypes.c_int
gdi32.ExtSelectClipRgn.argtypes = [wintypes.HDC, wintypes.HRGN, ctypes.c_int]
gdi32.ExtSelectClipRgn.restype = ctypes.c_int
gdi32.SetPixel.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int, wintypes.COLORREF]
gdi32.SetPixel.restype = wintypes.COLORREF
gdi32.SetBkColor.argtypes = [wintypes.HDC, wintypes.COLORREF]
gdi32.SetBkColor.restype = wintypes.COLORREF

user32.SetWindowRgn.argtypes = [wintypes.HWND, wintypes.HRGN, wintypes.BOOL]
user32.SetWindowRgn.restype = ctypes.c_int
user32.UpdateLayeredWindow.argtypes = [wintypes.HWND, wintypes.HDC, ctypes.POINTER(wintypes.POINT),
                                       ctypes.POINTER(wintypes.SIZE), wintypes.HDC,
                                       ctypes.POINTER(wintypes.POINT), wintypes.COLORREF,
                                       ctypes.POINTER(BLENDFUNCTION), wintypes.DWORD]
user32.UpdateLayeredWindow.restype = wintypes.BOOL

kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
kernel32.GetModuleHandleW.restype = wintypes.HINSTANCE

comctl32.InitCommonControlsEx.argtypes = [ctypes.POINTER(INITCOMMONCONTROLSEX)]
comctl32.InitCommonControlsEx.restype = wintypes.BOOL

uxtheme.SetWindowTheme.argtypes = [wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR]
uxtheme.SetWindowTheme.restype = ctypes.c_long

def init_common_controls():
    icc = INITCOMMONCONTROLSEX()
    icc.dwSize = ctypes.sizeof(INITCOMMONCONTROLSEX)
    icc.dwICC = ICC_LISTVIEW_CLASSES
    comctl32.InitCommonControlsEx(ctypes.byref(icc))

# ============================================================================
# BASE WIDGET
# ============================================================================
class Widget:
    def __init__(self):
        self.x = self.y = self.w = self.h = 0
        self.parent = None
        self.visible = True
        self.focusable = False
        self.focused = False
        self.hovered = False
        self.pressed = False
        self.stretch = 0

    def measure(self, app): return (self.w or 100, self.h or 30)

    def set_bounds(self, x, y, w, h):
        changed = (x, y, w, h) != (self.x, self.y, self.w, self.h)
        self.x, self.y, self.w, self.h = int(x), int(y), int(w), int(h)
        if changed: self._on_bounds()

    def _on_bounds(self): pass
    def hit_test(self, x, y):
        if not self.visible: return None
        if self.x <= x < self.x + self.w and self.y <= y < self.y + self.h: return self
        return None
    def all_widgets(self): yield self
    def draw(self, hdc, app): pass
    def on_mouse_move(self, x, y): pass
    def on_mouse_down(self, x, y): pass
    def on_mouse_up(self, x, y): pass
    def on_key(self, vk, ch): pass
    def on_wheel(self, delta): return False

class Container(Widget):
    def __init__(self):
        super().__init__(); self.children = []
    def add(self, w):
        w.parent = self; self.children.append(w); return w
    def hit_test(self, x, y):
        if not self.visible: return None
        for c in reversed(self.children):
            r = c.hit_test(x, y)
            if r is not None: return r
        if self.x <= x < self.x + self.w and self.y <= y < self.y + self.h: return self
        return None
    def all_widgets(self):
        yield self
        for c in self.children: yield from c.all_widgets()
    def draw(self, hdc, app):
        rgn = getattr(app, '_paint_rgn', None)
        margin = int(16 * app.scale) if rgn else 0
        for c in self.children:
            if not c.visible:
                continue
            if rgn:
                rc = wintypes.RECT(c.x - margin, c.y - margin,
                                   c.x + c.w + margin, c.y + c.h + margin)
                if not gdi32.RectInRegion(rgn, ctypes.byref(rc)):
                    continue
            c.draw(hdc, app)

