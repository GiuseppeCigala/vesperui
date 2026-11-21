import vesperui as ui
from tests.helpers import WidgetTestCase


class PanelTests(WidgetTestCase):
    def test_measure_uses_layout(self):
        panel = ui.Panel(layout=ui.VBoxLayout(padding=6, spacing=4))
        first = panel.add(ui.Label('first'))
        second = panel.add(ui.Label('second'))

        fw, fh = first.measure(self.app)
        sw, sh = second.measure(self.app)
        self.assertEqual(panel.measure(self.app),
                         (max(fw, sw) + 12, fh + sh + 4 + 12))

    def test_arrange_positions_children(self):
        panel = ui.Panel(layout=ui.VBoxLayout(padding=6, spacing=4))
        first = panel.add(ui.Label('first'))
        second = panel.add(ui.Label('second'))
        panel.set_bounds(20, 30, 300, 200)
        panel.arrange(self.app)

        self.assertEqual((first.x, first.y), (26, 36))
        self.assertEqual(first.w, 288)
        self.assertEqual(second.x, 26)
        self.assertEqual(second.w, 288)
        self.assertEqual(second.y, first.y + first.h + 4)

    def test_arrange_propagates_to_nested_containers(self):
        inner = ui.Panel(layout=ui.VBoxLayout(padding=2, spacing=2))
        label = inner.add(ui.Label('nested'))
        outer = ui.Panel(layout=ui.VBoxLayout(padding=4, spacing=4))
        outer.add(inner)
        outer.set_bounds(0, 0, 200, 120)
        outer.arrange(self.app)
        self.assertEqual(inner.x, 4)
        self.assertEqual(inner.y, 4)
        self.assertEqual(label.x, inner.x + 2)
        self.assertEqual(label.y, inner.y + 2)

    def test_draw_square_background(self):
        panel = ui.Panel(bg=(40, 40, 40))
        self.add(panel, 0, 0, 100, 60)
        self.paint(panel, 120, 80)

    def test_draw_rounded_shadow_gradient_border(self):
        panel = ui.Panel(bg=(30, 30, 40), radius=14, shadow=True,
                         gradient=((60, 60, 80), (20, 20, 30)),
                         border=(120, 120, 150))
        self.add(panel, 20, 20, 160, 90)
        self.paint(panel, 240, 160)
