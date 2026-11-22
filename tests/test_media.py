import vesperui as ui
from tests.helpers import WidgetTestCase


class MediaButtonTests(WidgetTestCase):
    def test_measure_and_defaults(self):
        button = ui.MediaButton('play')
        self.assertEqual(button.icon, 'play')
        self.assertEqual(button.measure(self.app), (40, 40))
        self.assertFalse(button.active)
        self.assertEqual(ui.MediaButton('unknown').icon, 'play')
        self.assertEqual(ui.MediaButton('stop', size=28).measure(self.app),
                         (28, 28))

    def test_click_callback_and_focus(self):
        calls = []
        button = self.add(ui.MediaButton('play',
                                         on_click=lambda: calls.append(1)))
        self.app.click_widget(button)
        self.assertEqual(calls, [1])
        self.assertIs(self.app.focused, button)

    def test_keyboard_activation(self):
        calls = []
        button = self.add(ui.MediaButton('stop',
                                         on_click=lambda: calls.append(1)))
        self.app.focus(button)
        self.app.press_key(ui.VK_RETURN)
        self.app.press_key(ui.VK_SPACE)
        self.assertEqual(calls, [1, 1])

    def test_release_outside_cancels(self):
        calls = []
        button = self.add(ui.MediaButton('ff',
                                         on_click=lambda: calls.append(1)))
        button.on_mouse_down(button.x + 2, button.y + 2)
        self.assertTrue(button.pressed)
        button.on_mouse_up(button.x + button.w + 20, button.y + 2)
        self.assertFalse(button.pressed)
        self.assertEqual(calls, [])

    def test_paint_all_icons_and_states(self):
        for icon in ui.MediaButton.ICONS:
            button = self.add(ui.MediaButton(icon))
            self.paint(button, 60, 60)
            button.hovered = True
            self.paint(button, 60, 60)
            button.focused = True
            button.pressed = True
            self.paint(button, 60, 60)
            button.active = True
            self.paint(button, 60, 60)


class TransportBarTests(WidgetTestCase):
    def test_construction_and_measure(self):
        bar = ui.TransportBar()
        self.assertEqual(tuple(bar.buttons), ui.TransportBar.ORDER)
        self.assertEqual(bar.buttons['rew'].icon, 'rew')
        self.assertEqual(bar.buttons['ff'].icon, 'ff')
        self.assertEqual(bar.measure(self.app), (232, 40))

    def test_command_callbacks(self):
        commands = []
        bar = self.add(ui.TransportBar(on_command=commands.append))
        bar.arrange(self.app)
        for name in ui.TransportBar.ORDER:
            self.app.click_widget(bar.buttons[name])
        self.assertEqual(commands, list(ui.TransportBar.ORDER))

    def test_specific_callbacks(self):
        events = []
        bar = self.add(ui.TransportBar(
            on_command=events.append,
            on_rew=lambda: events.append('rew-cb'),
            on_play=lambda: events.append('play-cb'),
            on_pause=lambda: events.append('pause-cb'),
            on_stop=lambda: events.append('stop-cb'),
            on_ff=lambda: events.append('ff-cb')))
        bar.arrange(self.app)
        self.app.click_widget(bar.buttons['play'])
        self.app.click_widget(bar.buttons['stop'])
        self.assertEqual(events, ['play-cb', 'play', 'stop-cb', 'stop'])

    def test_set_active(self):
        bar = self.add(ui.TransportBar())
        bar.set_active('play')
        self.assertTrue(bar.buttons['play'].active)
        self.assertFalse(bar.buttons['stop'].active)
        bar.set_active('pause')
        self.assertFalse(bar.buttons['play'].active)
        self.assertTrue(bar.buttons['pause'].active)
        bar.set_active(None)
        self.assertFalse(any(button.active for button in bar.buttons.values()))

    def test_paint(self):
        bar = self.add(ui.TransportBar())
        bar.arrange(self.app)
        bar.set_active('play')
        self.paint(bar, 260, 60)
        bar.buttons['rew'].hovered = True
        bar.buttons['ff'].focused = True
        bar.buttons['stop'].pressed = True
        self.paint(bar, 260, 60)
