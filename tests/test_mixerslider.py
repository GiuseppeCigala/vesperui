import vesperui as ui
from tests.helpers import WidgetTestCase


class MixerSliderTests(WidgetTestCase):
    def test_defaults_and_measure(self):
        fader = ui.MixerSlider()
        self.assertEqual(fader.value, 0.0)
        self.assertEqual(fader.value_text(), '0.0 dB')
        self.assertEqual(fader.measure(self.app), (112, 340))
        self.assertEqual(ui.MixerSlider(orientation='h').measure(self.app),
                         (340, 84))

    def test_db_taper(self):
        self.assertEqual(ui.MixerSlider.db_to_fraction(6.0), 1.0)
        self.assertEqual(ui.MixerSlider.db_to_fraction(-60.0), 0.0)
        self.assertEqual(ui.MixerSlider.db_to_fraction(0.0), 0.76)
        self.assertEqual(ui.MixerSlider.fraction_to_db(0.76), 0.0)
        self.assertEqual(ui.MixerSlider.fraction_to_db(0.0), -60.0)
        self.assertEqual(ui.MixerSlider.fraction_to_db(1.0), 6.0)
        previous = -0.1
        for db in (-60.0, -40.0, -30.0, -20.0, -15.0, -10.0, -5.0, 0.0, 6.0):
            fraction = ui.MixerSlider.db_to_fraction(db)
            self.assertGreater(fraction, previous)
            previous = fraction

    def test_set_value_clamps_and_notifies(self):
        events = []
        fader = self.add(ui.MixerSlider(0.0, on_change=events.append))
        self.assertTrue(fader.set_value(10.0))
        self.assertEqual(fader.value, 6.0)
        self.assertTrue(fader.set_value(-100.0))
        self.assertEqual(fader.value, -60.0)
        self.assertEqual(fader.value_text(), '-∞ dB')
        self.assertEqual(events, [6.0, -60.0])
        self.assertFalse(fader.set_value(-60.0))
        self.assertTrue(fader.set_value(-12.5, notify=False))
        self.assertEqual(events, [6.0, -60.0])
        self.assertEqual(fader.value_text(), '-12.5 dB')

    def test_custom_range(self):
        fader = self.add(ui.MixerSlider(0.0, min_db=-20.0, max_db=0.0))
        fader.set_value(-100.0)
        self.assertEqual(fader.value, -20.0)
        self.assertEqual(fader.value_text(), '-20.0 dB')
        fader.set_value(10.0)
        self.assertEqual(fader.value, 0.0)

    def test_vertical_mouse_mapping(self):
        fader = self.add(ui.MixerSlider(0.0))
        low, high, center = fader._track_span()
        fader.on_mouse_down(center, high)
        self.assertEqual(fader.value, 6.0)
        fader.on_mouse_down(center, low)
        self.assertEqual(fader.value, -60.0)
        middle = (low + high) / 2.0
        fader.on_mouse_down(center, middle)
        expected = ui.MixerSlider.fraction_to_db(0.5)
        self.assertAlmostEqual(fader.value, expected, delta=0.6)
        fader.on_mouse_up(center, middle)
        self.assertFalse(fader._dragging)

    def test_drag_updates_value(self):
        fader = self.add(ui.MixerSlider(0.0))
        low, high, center = fader._track_span()
        fader.on_mouse_down(center, low)
        self.assertEqual(fader.value, -60.0)
        fader.on_mouse_move(center, high)
        self.assertEqual(fader.value, 6.0)
        fader.on_mouse_up(center, high)
        self.assertFalse(fader._dragging)

    def test_horizontal_mouse_mapping(self):
        fader = self.add(ui.MixerSlider(0.0, orientation='h'))
        low, high, center = fader._track_span()
        fader.on_mouse_down(low, center)
        self.assertEqual(fader.value, -60.0)
        fader.on_mouse_down(high, center)
        self.assertEqual(fader.value, 6.0)
        fader.on_mouse_up(high, center)

    def test_keyboard(self):
        fader = self.add(ui.MixerSlider(0.0))
        self.app.focus(fader)
        self.app.press_key(ui.VK_UP)
        self.assertGreater(fader.value, 0.0)
        self.app.press_key(ui.VK_DOWN)
        self.assertAlmostEqual(fader.value, 0.0, delta=0.01)
        self.app.press_key(ui.VK_DOWN)
        self.assertLess(fader.value, 0.0)
        self.app.press_key(ui.VK_RIGHT)
        self.assertAlmostEqual(fader.value, 0.0, delta=0.01)

    def test_wheel_is_not_consumed(self):
        self.assertFalse(self.add(ui.MixerSlider()).on_wheel(120))

    def test_paint_states_and_orientations(self):
        fader = self.add(ui.MixerSlider(0.0))
        self.paint(fader, 130, 360)
        fader.focused = True
        fader.hovered = True
        fader._dragging = True
        self.paint(fader, 130, 360)
        fader.set_value(6.0, notify=False)
        self.paint(fader, 130, 360)
        fader.set_value(-60.0, notify=False)
        self.paint(fader, 130, 360)
        horizontal = self.add(ui.MixerSlider(0.0, orientation='h'))
        self.paint(horizontal, 360, 100)
        horizontal.set_value(-30.0, notify=False)
        horizontal.focused = True
        self.paint(horizontal, 360, 100)
