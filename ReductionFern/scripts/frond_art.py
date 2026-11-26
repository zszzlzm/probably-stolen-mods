"""Drawing helpers for the hand-laid fern sprites.

The two fern icons (``draw_fern.py`` 16x32, ``draw_fern_l.py`` 32x32) share the
palette, the ``Frond`` record, the leaflet wedge, the rim light and the renderer
here; the scripts only describe geometry.

A frond is drawn as:

* a rachis from ``tip`` to ``base``. It can lean (``x_bottom`` -> ``x_top``) or follow
  a few ``x_profile`` waypoints, because a perfectly straight rachis is what makes a
  frond look generated rather than grown;
* one leaflet pair every few rows. The lit row is full length; the shadow row is
  inset by one pixel at the outer end, which gives each leaflet a pointed tip and
  opens the dark V notch against the rachis;
* long leaflets can be split by a one pixel notch (``notch_min``): a fern leaflet is
  a compound pinnule, and without that break the wide bands read as empty ribbons -
  this is the detail fix for the large tier's centre frond.
"""
from dataclasses import dataclass, field

from PIL import Image

from pixel_art import TRANSPARENT, Grid, fill_seams, outline

COLORS = {
    "K": (0x29, 0x22, 0x34),  # outline / deepest shadow
    "D": (0x27, 0x56, 0x54),  # dark teal: seams, shadow fronds, root, notch
    "T": (0x2F, 0x75, 0x6F),  # teal rachis
    "B": (0x45, 0x91, 0x8B),  # pale vein
    "L": (0x8A, 0xBF, 0xBB),  # rim light
    "G": (0x3D, 0x82, 0x3F),  # leaf green
    "g": (0x41, 0x60, 0x3F),  # dark leaf green
}
BACKGROUND_ALPHA = 3


@dataclass
class Frond:
    """One upright frond.

    ``nodes`` is a list of ``(row, left_length, right_length)``: the leaflet's lit
    row and how far it reaches out on each side. Unequal lengths keep the plant from
    looking machine-made. ``x_profile`` (list of ``(row, x)``) overrides the simple
    lean with a bent rachis when supplied.
    """

    x_bottom: int
    x_top: int
    tip: int
    base: int
    nodes: list = field(default_factory=list)
    tones: tuple = ("G", "g")          # (lit, shadow)
    rachis: str = "T"
    x_profile: list = field(default_factory=list)

    def x_at(self, row):
        """Rachis column at ``row``: profile waypoints, else a linear lean."""
        if self.x_profile:
            points = sorted(self.x_profile)
            if row <= points[0][0]:
                return points[0][1]
            if row >= points[-1][0]:
                return points[-1][1]
            for (y0, x0), (y1, x1) in zip(points, points[1:]):
                if y0 <= row <= y1:
                    t = (row - y0) / (y1 - y0)
                    return round(x0 + (x1 - x0) * t)
        if self.tip == self.base:
            return self.x_bottom
        t = (row - self.base) / (self.tip - self.base)
        return round(self.x_bottom + (self.x_top - self.x_bottom) * t)


def draw_rachis(grid, frond):
    for row in range(frond.tip, frond.base + 1):
        grid.put(frond.x_at(row), row, frond.rachis)


def draw_leaflet(grid, x, row, length, side, tones, notch=None, rise=0):
    """One leaflet.

    ``rise=0`` draws a horizontal blade (lit row + shadow row) - fine for the small
    icons, but at 48x64 a field of horizontal blades on vertical stems reads as a
    grid. ``rise=2`` lifts the blade one row every two pixels instead, which is what
    makes a fern leaflet look like a leaflet rather than a rung.
    """
    lit, shade = tones
    for k in range(1, length + 1):
        y = row - ((k - 1) // rise if rise else 0)
        if k == notch:
            grid.put(x + side * k, y, "D")
            continue
        grid.put(x + side * k, y, lit)
        if k >= 2:
            grid.put(x + side * k, y + 1, shade)


def draw_frond(grid, frond, stagger=0, notch_min=None, rise=0):
    """Draw rachis + leaflet pairs.

    ``stagger`` drops the right leaflet of each pair by that many rows, breaking the
    mirror symmetry. ``notch_min`` splits every leaflet at least that long.
    """
    draw_rachis(grid, frond)
    for row, left, right in frond.nodes:
        x = frond.x_at(row)
        for side, length, dy in ((-1, left, 0), (+1, right, stagger)):
            notch = None
            if notch_min is not None and length >= notch_min:
                notch = length // 2
            draw_leaflet(grid, x, row + dy, length, side, frond.tones, notch, rise)


def rim_light(grid, rows, lit=("G",), color="L"):
    """Catch the light on the leftmost lit pixel of the given rows.

    Picking the pixel from the sprite instead of hard-coding coordinates keeps the
    highlight on the silhouette when the geometry changes.
    """
    for row in rows:
        for x in range(grid.width):
            if grid.at(x, row) in lit:
                grid.put(x, row, color)
                break


def sori(grid, spots, color="D"):
    """Dark spore dots on the leaf surface (fern undersides carry them in rows)."""
    for x, y in spots:
        if grid.at(x, y) == "G":
            grid.put(x, y, color)


def root(grid, x0, x1, rows, color="D"):
    for y in rows:
        for x in range(x0, x1 + 1):
            grid.put(x, y, color)


def finish(grid, path, seam="D", border="K", previews=((1, "_x1"), (12, "_x12"))):
    """Close pinholes, outline the silhouette, and write the PNG plus previews."""
    fill_seams(grid, seam)
    outline(grid, border)

    image = Image.new("RGBA", (grid.width, grid.height), (0, 0, 0, BACKGROUND_ALPHA))
    for y in range(grid.height):
        for x in range(grid.width):
            color = grid.at(x, y)
            if color != TRANSPARENT:
                image.putpixel((x, y), COLORS[color] + (255,))
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)

    for scale, suffix in previews:
        big = image.resize((grid.width * scale, grid.height * scale), Image.NEAREST)
        canvas = Image.new("RGBA", big.size, (26, 28, 32, 255))
        canvas.alpha_composite(big)
        canvas.save(path.with_name(path.stem + suffix + ".png"))
    return image


def counts(rows):
    tally = {}
    for row in rows:
        for color in row:
            if color != TRANSPARENT:
                tally[color] = tally.get(color, 0) + 1
    return sorted(tally.items())


__all__ = [
    "COLORS",
    "Frond",
    "Grid",
    "counts",
    "draw_frond",
    "finish",
    "rim_light",
    "root",
    "sori",
]
