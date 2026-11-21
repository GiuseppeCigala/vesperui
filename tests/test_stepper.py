import vesperui as ui
from tests.helpers import WidgetTestCase


class StepperTests(WidgetTestCase):
    def test_initial_value_clamps(self):
        self.assertEqual(ui.Stepper(5, 0, 10).value, 5.0)
        self.assertEqual(ui.Stepper(50, 0, 10).value, 10.0)
        self.assertEqual(ui.Stepper(-1, 0, 10).value, 0.0)

    def test_min_max_are_normalised(self):
        stepper = ui.Stepper(5, 10, 0)
        self.assertEqual((stepper.min, stepper.max), (0.0, 10.0))

    def test_set_value_notifies_and_clamps(self):
        events = []
        stepper = self.add(ui.Stepper(5, 0, 10, step=2,
                                      on_change=events.append))
        self.assertTrue(stepper.set_value(100))
        self.assertEqual(stepper.value, 10.0)
        self.assertTrue(stepper.set_value(-5))
        self.assertEqual(stepper.value, 0.0)
        self.assertEqual(events, [10.0, 0.0])
        self.assertFalse(stepper.set_value(0))
        self.assertTrue(stepper.set_value(1, notify=False))
        self.assertEqual(events, [10.0, 0.0])

    def test_increment_decrement_and_bounds(self):
        stepper = ui.Stepper(2, 0, 3, step=1)
        self.assertTrue(stepper.increment())
        self.assertEqual(stepper.value, 3.0)
        self.assertFalse(stepper.increment())
        self.assertTrue(stepper.decrement())
        self.assertEqual(stepper.value, 2.0)

    def test_click_buttons(self):
        events = []
        stepper = self.add(ui.Stepper(5, 0, 10, on_change=events.append))
        y = stepper.y + stepper.h // 2
        self.app.click(stepper.x + stepper.w - 4, y)
        self.assertEqual(stepper.value, 6.0)
        self.assertEqual(events, [6.0])
        self.assertIs(self.app.focused, stepper)
        self.app.click(stepper.x + 4, y)
        self.assertEqual(stepper.value, 5.0)
        self.assertEqual(events, [6.0, 5.0])

    def test_center_click_does_nothing(self):
        stepper = self.add(ui.Stepper(5, 0, 10))
        self.app.click(stepper.x + stepper.w // 2,
                       stepper.y + stepper.h // 2)
        self.assertEqual(stepper.value, 5.0)

    def test_disabled_side_ignores_click(self):
        events = []
        stepper = self.add(ui.Stepper(10, 0, 10, on_change=events.append))
        self.app.click(stepper.x + stepper.w - 4,
                       stepper.y + stepper.h // 2)
        self.assertEqual(stepper.value, 10.0)
        self.assertEqual(events, [])

    def test_keyboard(self):
        stepper = self.add(ui.Stepper(5, 0, 10))
        self.app.focus(stepper)
        self.app.press_key(ui.VK_RIGHT)
        self.app.press_key(ui.VK_UP)
        self.assertEqual(stepper.value, 7.0)
        self.app.press_key(ui.VK_LEFT)
        self.app.press_key(ui.VK_DOWN)
        self.assertEqual(stepper.value, 5.0)

    def test_wheel(self):
        stepper = self.add(ui.Stepper(5, 0, 10))
        self.assertTrue(stepper.on_wheel(120))
        self.assertEqual(stepper.value, 6.0)
        self.assertTrue(stepper.on_wheel(-120))
        self.assertEqual(stepper.value, 5.0)
        stepper.set_value(10, notify=False)
        self.assertFalse(stepper.on_wheel(120))
        stepper.set_value(0, notify=False)
        self.assertFalse(stepper.on_wheel(-120))

    def test_hover_parts(self):
        stepper = self.add(ui.Stepper(5, 0, 10))
        y = stepper.y + stepper.h // 2
        self.app.move_mouse(stepper.x + 4, y)
        self.assertEqual(stepper._hover_part, 'dec')
        self.app.move_mouse(stepper.x + stepper.w - 4, y)
        self.assertEqual(stepper._hover_part, 'inc')
        self.app.move_mouse(stepper.x + stepper.w // 2, y)
        self.assertIsNone(stepper._hover_part)

    def test_value_text(self):
        stepper = ui.Stepper(3, 0, 10, prefix='Qty ', suffix=' pcs')
        self.assertEqual(stepper._value_text(), 'Qty 3 pcs')
        stepper.set_value(3.5, notify=False)
        self.assertEqual(stepper._value_text(), 'Qty 3.5 pcs')

    def test_measure_and_draw_states(self):
        stepper = self.add(ui.Stepper(5, 0, 10))
        self.assertEqual(stepper.measure(self.app), (120, 28))
        stepper.focused = True
        stepper.hovered = True
        stepper._hover_part = 'inc'
        stepper._pressed_part = 'dec'
        self.paint(stepper)
        stepper.set_value(stepper.min, notify=False)
        self.paint(stepper)
        stepper.set_value(stepper.max, notify=False)
        self.paint(stepper)

    def test_stepper_button_alias(self):
        self.assertIs(ui.StepperButton, ui.Stepper)
