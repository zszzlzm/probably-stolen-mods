"""Hand-lay the 48x64 hydroponic growth portrait (``restoring_fern_p``).

    python scripts/draw_fern_p.py [--out refs/final/restoring_fern_p.png]

This is not an inventory icon: the sprite is drawn behind/on the hydroponic module, so
it has to match the vanilla growth sprites. Both vanilla ``_p`` sprites keep their
content inside rows 11-46 and columns 1-46 - the same box is used here.

The first attempt at this sprite was rejected for looking like a grid: vertical rachises
with horizontal leaflet bands, all at the same angle. This version fixes that at the
source of the pattern:

* every rachis is an **arc**, not a straight line - it bows outward between the base
  and the tip (``x_profile`` with a bulge waypoint);
* every leaflet is **angled** (``rise=2``): it climbs one row every two pixels, so the
  blades point up-and-out instead of lying flat;
* node spacing and leaflet length vary per frond, and the clump is round rather than a
  fan of straight spokes.

There is no tray: the module owns the tray, and neither vanilla growth sprite draws one.
"""
import argparse
import pathlib

from frond_art import Frond, Grid, counts, draw_frond, finish, rim_light

W, H = 48, 64

BACK_TONES = ("g", "D")
FRONT_TONES = ("G", "g")

BASE = 41      # stems meet the root mass here


def arc(x_base, x_tip, tip_row, bulge):
    """Rachis waypoints for a frond that bows out between base and tip."""
    mid_row = (BASE + tip_row) // 2
    mid_x = round((x_base + x_tip) / 2 + bulge)
    return [(BASE, x_base), (mid_row, mid_x), (tip_row, x_tip)]


def nodes(tip, step, cycle):
    """Leaflet pairs from just below the tip down to the base.

    ``cycle`` repeats down the frond so blade lengths vary instead of marching.
    """
    rows = []
    i = 0
    for row in range(tip + 2, BASE, step):
        rows.append((row, cycle[i % len(cycle)], cycle[(i + 1) % len(cycle)]))
        i += 1
    return rows


def draw_roots(grid):
    """Tapering root mass plus uneven strands, as in the vanilla growth sprites."""
    for x in range(17, 32):
        grid.put(x, 40, "g")
    for x in range(18, 31):
        grid.put(x, 41, "D")
    for x in range(20, 29):
        grid.put(x, 42, "D")
    for x in (19, 23, 27, 30):
        grid.put(x, 42, "g")

    for x, bottom, drift in ((19, 46, -1), (23, 45, 0), (26, 46, 1), (30, 44, 0)):
        for y in range(42, bottom + 1):
            grid.put(x + (drift if y > 44 else 0), y, "T")
        grid.put(x + (drift if bottom > 44 else 0), bottom, "B")


def build():
    grid = Grid(W, H)

    # ---- dark outer fronds first: their arcs set the round silhouette
    for x_base, x_tip, tip_row, bulge, cycle in (
        (21, 5, 26, -3, (3, 3, 2)),
        (27, 43, 27, 3, (3, 3, 2)),
    ):
        draw_frond(
            grid,
            Frond(
                x_bottom=x_base,
                x_top=x_tip,
                tip=tip_row,
                base=BASE,
                x_profile=arc(x_base, x_tip, tip_row, bulge),
                nodes=nodes(tip_row, 4, cycle),
                tones=BACK_TONES,
                rachis="g",
            ),
            rise=1,
        )

    # ---- lit fronds: two leaning pairs
    for x_base, x_tip, tip_row, bulge, cycle in (
        (22, 12, 16, -2, (3, 3, 2)),
        (26, 36, 17, 2, (3, 3, 2)),
    ):
        draw_frond(
            grid,
            Frond(
                x_bottom=x_base,
                x_top=x_tip,
                tip=tip_row,
                base=BASE,
                x_profile=arc(x_base, x_tip, tip_row, bulge),
                nodes=nodes(tip_row, 4, cycle),
                tones=FRONT_TONES,
            ),
            rise=1,
        )

    # ---- centre frond: tallest, nearly upright with a small bow
    center = Frond(
        x_bottom=24,
        x_top=24,
        tip=11,
        base=BASE,
        x_profile=[(BASE, 24), (30, 25), (20, 24), (11, 24)],
        nodes=nodes(11, 4, (3, 3, 2, 3)),
        tones=FRONT_TONES,
    )
    draw_frond(grid, center, stagger=1, rise=1)
    grid.put(24, 11, "G")
    grid.put(23, 12, "G")
    grid.put(25, 12, "g")

    # rim light on the upper-left tips, vein dots up the centre rachis
    rim_light(grid, (13, 18, 23, 28))
    for row in (15, 21, 27, 33):
        grid.put(center.x_at(row), row, "B")

    draw_roots(grid)
    return grid


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="refs/final/restoring_fern_p.png")
    args = parser.parse_args()

    grid = build()
    finish(grid, pathlib.Path(args.out))
    print("# colors:", counts(grid.rows()))
    for row in grid.rows():
        print(row)


if __name__ == "__main__":
    main()
