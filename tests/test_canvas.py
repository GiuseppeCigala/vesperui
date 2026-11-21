import pywinui as ui
from tests.helpers import WidgetTestCase


class CanvasTests(WidgetTestCase):
    def test_primitives_are_recorded(self):
        canvas = self.add(ui.Canvas())
        canvas.line(0, 0, 10, 10)
        canvas.rect(1, 2, 30, 40, fill=(1, 2, 3))
        canvas.ellipse(5, 5, 20, 10)
        canvas.circle(50, 50, 10)
        canvas.text(4, 6, 'hello')

        kinds = [item[0] for item in canvas.items]
        self.assertEqual(kinds, ['line', 'rect', 'ellipse', 'ellipse', 'text'])
        # circle() is sugar for a square ellipse.
        self.assertEqual(canvas.items[3][1:5], (40, 40, 20, 20))

    def test_clear_removes_primitives(self):
        canvas = self.add(ui.Canvas())
        canvas.line(0, 0, 1, 1)
        canvas.rect(0, 0, 1, 1)
        canvas.clear()
        self.assertEqual(canvas.items, [])

    def test_measure_defaults(self):
        canvas = ui.Canvas()
        self.assertEqual(canvas.measure(self.app), (300, 200))

    def test_draw_all_primitives(self):
        canvas = ui.Canvas(bg=(20, 20, 20))
        canvas.line(0, 0, 50, 50, color=(255, 0, 0), width=2)
        canvas.rect(5, 5, 40, 30, color=(0, 255, 0), width=2)
        canvas.rect(60, 5, 40, 30, fill=(0, 0, 255))
        canvas.ellipse(10, 80, 30, 20, color=(255, 255, 0), fill=(50, 50, 50))
        canvas.circle(150, 90, 15, color=(255, 255, 255))
        canvas.text(5, 5, 'label', size=16, bold=True)
        self.add(canvas, 0, 0, 300, 200)
        self.paint(canvas, 300, 200)
