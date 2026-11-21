import vesperui as ui
from tests.helpers import WidgetTestCase


class GroupBoxTests(WidgetTestCase):
    def test_add_proxies_to_content(self):
        box = ui.GroupBox('Options')
        label = box.add(ui.Label('inner'))
        self.assertIn(label, box.content.children)
        self.assertIs(label.parent, box.content)

    def test_measure_adds_title_height(self):
        box = ui.GroupBox('Options', layout=ui.VBoxLayout(padding=8, spacing=4))
        box.add(ui.Label('one'))
        box.add(ui.Label('two'))
        cw, ch = box.content.measure(self.app)
        title_h = box._title_height(self.app)
        self.assertGreater(title_h, 0)
        self.assertEqual(box.measure(self.app), (cw, ch + title_h))

    def test_arrange_offsets_content_below_title(self):
        box = ui.GroupBox('Options')
        box.set_bounds(10, 20, 240, 180)
        box.arrange(self.app)
        title_h = box._title_height(self.app)
        self.assertEqual(box.content.x, 10)
        self.assertEqual(box.content.y, 20 + title_h)
        self.assertEqual(box.content.w, 240)
        self.assertEqual(box.content.h, 180 - title_h)

    def test_titleless_box_has_no_offset(self):
        box = ui.GroupBox('')
        self.assertEqual(box._title_height(self.app), 0)
        box.set_bounds(0, 0, 100, 100)
        box.arrange(self.app)
        self.assertEqual((box.content.x, box.content.y), (0, 0))

    def test_draw_with_and_without_background(self):
        for bg in (None, (45, 45, 55)):
            box = ui.GroupBox('Options', bg=bg, border=(90, 90, 110))
            self.add(box, 0, 0, 200, 120)
            self.paint(box, 220, 140)
