import vesperui as ui
from tests.helpers import WidgetTestCase


class KnobTests(WidgetTestCase):
    def test_measure(self):
        self.assertEqual(ui.Knob().measure(self.app), (120, 150))

    def test_initial_value_clamps(self):
        self.assertEqual(ui.Knob(2.0).value, 1.0)
        self.assertEqual(ui.Knob(-0.5).value, 0.0)

    def test_set_value_clamps_and_notifies(self):
        events = []
        knob = self.add(ui.Knob(0.5, on_change=events.append))
        self.assertTrue(knob.set_value(1.5))
        self.assertEqual(knob.value, 1.0)
        self.assertTrue(knob.set_value(-1.0))
        self.assertEqual(knob.value, 0.0)
        self.assertEqual(events, [1.0, 0.0])
        self.assertFalse(knob.set_value(0.0))
        self.assertTrue(knob.set_value(0.25, notify=False))
        self.assertEqual(events, [1.0, 0.0])

    def test_angle_mapping(self):
        knob = self.add(ui.Knob(0.0))
        cx, cy, radius = knob._geometry()
        for fraction in (0.0, 0.5, 1.0):
            x, y = knob._point(cx, cy, radius, fraction)
            knob.on_mouse_down(x, y)
            self.assertAlmostEqual(knob.value, fraction, delta=0.02)

    def test_gap_snaps_to_nearest_end(self):
        knob = self.add(ui.Knob(0.5))
        cx, cy, radius = knob._geometry()
        knob.on_mouse_down(*knob._point(cx, cy, radius, -0.1))
        self.assertEqual(knob.value, 0.0)
        knob.on_mouse_down(*knob._point(cx, cy, radius, 1.1))
        self.assertEqual(knob.value, 1.0)

    def test_drag_updates_value(self):
        knob = self.add(ui.Knob(0.0))
        cx, cy, radius = knob._geometry()
        knob.on_mouse_down(*knob._point(cx, cy, radius, 0.2))
        self.assertTrue(knob._dragging)
        knob.on_mouse_move(*knob._point(cx, cy, radius, 0.8))
        self.assertAlmostEqual(knob.value, 0.8, delta=0.02)
        knob.on_mouse_up(*knob._point(cx, cy, radius, 0.8))
        self.assertFalse(knob._dragging)

    def test_keyboard(self):
        knob = self.add(ui.Knob(0.5))
        self.app.focus(knob)
        self.app.press_key(ui.VK_RIGHT)
        self.assertAlmostEqual(knob.value, 0.55, delta=1e-6)
        self.app.press_key(ui.VK_UP)
        self.assertAlmostEqual(knob.value, 0.6, delta=1e-6)
        self.app.press_key(ui.VK_LEFT)
        self.app.press_key(ui.VK_DOWN)
        self.assertAlmostEqual(knob.value, 0.5, delta=1e-6)

    def test_wheel_is_not_consumed(self):
        self.assertFalse(self.add(ui.Knob()).on_wheel(120))

    def test_value_text(self):
        knob = ui.Knob(0.5)
        self.assertEqual(knob.value_text(), '50.0 %')
        knob.formatter = lambda v: '%.1f' % (v * 100)
        self.assertEqual(knob.value_text(), '50.0')

    def test_paint_states(self):
        knob = self.add(ui.Knob(0.0))
        for value in (0.0, 0.5, 1.0):
            knob.set_value(value, notify=False)
            self.paint(knob, 130, 160)
        knob.focused = True
        knob.hovered = True
        knob._dragging = True
        self.paint(knob, 130, 160)
        plain = self.add(ui.Knob(0.25, show_value=False))
        self.paint(plain, 130, 160)
        custom = self.add(ui.Knob(0.75, accent=(255, 96, 200),
                                  formatter=lambda v: 'X'))
        self.paint(custom, 130, 160)
