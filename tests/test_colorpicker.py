import unittest

import vesperui as ui
from tests.helpers import WidgetTestCase
from vesperui.colorpicker import hsv_to_rgb, rgb_to_hex, rgb_to_hsv


class ColorConversionTests(unittest.TestCase):
    def test_hsv_primaries(self):
        self.assertEqual(hsv_to_rgb(0.0, 1.0, 1.0), (255, 0, 0))
        self.assertEqual(hsv_to_rgb(1.0 / 3.0, 1.0, 1.0), (0, 255, 0))
        self.assertEqual(hsv_to_rgb(2.0 / 3.0, 1.0, 1.0), (0, 0, 255))
        self.assertEqual(hsv_to_rgb(0.0, 0.0, 1.0), (255, 255, 255))
        self.assertEqual(hsv_to_rgb(0.0, 0.0, 0.0), (0, 0, 0))

    def test_rgb_to_hsv(self):
        hue, sat, val = rgb_to_hsv(0, 214, 255)
        self.assertAlmostEqual(hue, 0.5268, places=3)
        self.assertEqual((sat, val), (1.0, 1.0))
        self.assertEqual(rgb_to_hsv(255, 255, 255), (0.0, 0.0, 1.0))
        self.assertEqual(rgb_to_hsv(0, 0, 0), (0.0, 0.0, 0.0))

    def test_round_trip(self):
        for rgb in ((0, 214, 255), (255, 255, 255), (0, 0, 0),
                    (123, 45, 67), (17, 200, 90)):
            result = hsv_to_rgb(*rgb_to_hsv(*rgb))
            for actual, expected in zip(result, rgb):
                self.assertLessEqual(abs(actual - expected), 1)

    def test_hex(self):
        self.assertEqual(rgb_to_hex((0, 214, 255)), '#00D6FF')
        self.assertEqual(rgb_to_hex((300, -5, 999)), '#FF00FF')


class ColorPickerTests(WidgetTestCase):
    def _picker(self, color=(255, 0, 0)):
        return self.add(ui.ColorPicker(color))

    def test_initial_color(self):
        picker = self._picker((0, 214, 255))
        self.assertEqual(picker.get_color(), (0, 214, 255))
        self.assertAlmostEqual(picker.hue, 0.5268, places=3)
        self.assertEqual(picker.measure(self.app), (240, 170))

    def test_set_color_notifies_and_clamps(self):
        events = []
        picker = self.add(ui.ColorPicker((255, 0, 0),
                                         on_change=events.append))
        self.assertTrue(picker.set_color((0, 255, 0)))
        self.assertEqual(picker.get_color(), (0, 255, 0))
        self.assertFalse(picker.set_color((0, 255, 0)))
        picker.set_color((300, -5, 999))
        self.assertEqual(picker.get_color(), (255, 0, 255))
        picker.set_color((0, 0, 255), notify=False)
        self.assertEqual(events, [(0, 255, 0), (255, 0, 255)])

    def test_set_hsv(self):
        picker = self._picker()
        self.assertTrue(picker.set_hsv(1.0 / 3.0, 1.0, 1.0))
        self.assertEqual(picker.get_color(), (0, 255, 0))
        self.assertAlmostEqual(picker.hue, 1.0 / 3.0, places=3)

    def test_click_sv_corners(self):
        picker = self._picker()
        sx, sy, sw, sh = picker._sv_rect()

        self.app.click(sx, sy)
        self.assertEqual(picker.get_color(), (255, 255, 255))

        self.app.click(sx + sw - 1, sy)
        self.assertEqual(picker.get_color(), (255, 0, 0))

        self.app.click(sx, sy + sh - 1)
        self.assertEqual(picker.get_color(), (0, 0, 0))

    def test_click_hue_strip(self):
        picker = self._picker((0, 214, 255))
        hx, hy, hw, hh = picker._hue_rect()

        self.app.click(hx + 2, hy)
        self.assertEqual(picker.get_color(), (255, 0, 0))

        self.app.click(hx + 2, hy + int(hh / 3.0))
        self.assertEqual(picker.get_color(), (0, 255, 0))

    def test_drag_sv_square(self):
        picker = self._picker()
        sx, sy, sw, sh = picker._sv_rect()
        picker.on_mouse_down(sx + 1, sy + 1)
        picker.on_mouse_move(sx + sw // 2, sy + sh // 2)
        picker.on_mouse_up(sx + sw // 2, sy + sh // 2)
        self.assertAlmostEqual(picker.sat, 0.5, delta=0.03)
        self.assertAlmostEqual(picker.val, 0.5, delta=0.03)
        self.assertIsNone(picker._drag)

    def test_click_preview_does_nothing(self):
        picker = self._picker()
        before = picker.get_color()
        px, py, pw, ph = picker._preview_rect()
        self.app.click(px + pw // 2, py + ph // 2)
        self.assertEqual(picker.get_color(), before)

    def test_keyboard(self):
        picker = self._picker()
        self.app.focus(picker)
        self.app.press_key(ui.VK_RIGHT)
        self.assertAlmostEqual(picker.hue, 1.0 / 60.0, places=3)

        picker.set_color((128, 0, 0), notify=False)
        self.app.press_key(ui.VK_UP)
        self.assertGreater(picker.val, 0.5)

    def test_wheel_is_not_consumed(self):
        picker = self._picker()
        self.assertFalse(picker.on_wheel(120))

    def test_draw_states(self):
        picker = self._picker((0, 214, 255))
        picker.focused = True
        picker._drag = 'sv'
        self.paint(picker)
        picker.set_color((0, 0, 0), notify=False)
        self.paint(picker)
        picker.set_color((255, 255, 255), notify=False)
        self.paint(picker)
