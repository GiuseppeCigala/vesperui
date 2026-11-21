"""Box layout managers (vertical and horizontal)."""


# ============================================================================
# LAYOUTS
# ============================================================================
class VBoxLayout:
    def __init__(self, padding=8, spacing=8):
        self.padding = padding; self.spacing = spacing
    def measure(self, p, app):
        if not p.children: return (100, 100)
        sizes = [c.measure(app) for c in p.children]
        tw = max(w for w, _ in sizes)
        th = sum(h for _, h in sizes) + self.spacing * (len(p.children) - 1)
        return (tw + 2 * self.padding, th + 2 * self.padding)
    def arrange(self, p, app):
        if not p.children: return
        ix, iy = p.x + self.padding, p.y + self.padding
        iw = max(0, p.w - 2 * self.padding)
        ih = max(0, p.h - 2 * self.padding)
        infos = [(c, c.measure(app), c.stretch) for c in p.children]
        fixed = sum(h for _, (_, h), s in infos if s == 0)
        st_total = sum(s for _, _, s in infos if s > 0)
        avail = max(0, ih - fixed - self.spacing * (len(infos) - 1))
        bottom = iy + ih
        y = iy
        for c, (pw, ph), s in infos:
            h = (avail * s / st_total) if s > 0 and st_total else ph
            h = max(0, min(int(h), bottom - y))
            c.set_bounds(ix, y, iw, h)
            y += h + self.spacing

class HBoxLayout:
    def __init__(self, padding=8, spacing=8):
        self.padding = padding; self.spacing = spacing
    def measure(self, p, app):
        if not p.children: return (100, 100)
        sizes = [c.measure(app) for c in p.children]
        tw = sum(w for w, _ in sizes) + self.spacing * (len(p.children) - 1)
        th = max(h for _, h in sizes)
        return (tw + 2 * self.padding, th + 2 * self.padding)
    def arrange(self, p, app):
        if not p.children: return
        ix, iy = p.x + self.padding, p.y + self.padding
        iw = max(0, p.w - 2 * self.padding)
        ih = max(0, p.h - 2 * self.padding)
        infos = [(c, c.measure(app), c.stretch) for c in p.children]
        fixed = sum(w for _, (w, _), s in infos if s == 0)
        st_total = sum(s for _, _, s in infos if s > 0)
        avail = max(0, iw - fixed - self.spacing * (len(infos) - 1))
        right = ix + iw
        x = ix
        for c, (pw, ph), s in infos:
            w = (avail * s / st_total) if s > 0 and st_total else pw
            w = max(0, min(int(w), right - x))
            c.set_bounds(x, iy, w, ih)
            x += w + self.spacing

