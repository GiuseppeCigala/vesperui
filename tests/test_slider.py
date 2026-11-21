import pywinui as ui
from tests.helpers import WidgetTestCase


class SliderTests(WidgetTestCase):
    def test_set_value_clamps_and_notifies(self):
        values = []
        slider = self.add(ui.Slider(0.5, on_change=values.append))
        slider.set_value(1.5)
        self.assertEqual(slider.value, 1.0)
        slider.set_value(-1.0)
        self.assertEqual(slider.value, 0.0)
        self.assertEqual(values, [1.0, 0.0])
        slider.set_value(0.25, notify=False)
        self.assertEqual(values, [1.0, 0.0])

    def test_mouse_drag_updates_value(self):
        slider = self.add(ui.Slider(0.0))
        y = slider.y + slider.h // 2
        slider.on_mouse_down(slider.x + 1, y)
        slider.on_mouse_move(slider.x + slider.w // 2, y)
        self.assertAlmostEqual(slider.value, 0.5, delta=0.15)
        slider.on_mouse_up(slider.x + slider.w // 2, y)

    def test_keyboard_and_draw(self):
        slider = self.add(ui.Slider(0.5))
        self.app.focus(slider)
        self.app.press_key(ui.VK_RIGHT)
        self.assertGreater(slider.value, 0.5)
        self.paint(slider)
