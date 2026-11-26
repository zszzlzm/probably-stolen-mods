"""Hand-lay the 16x32 standard frond (``restoring_fern``).

    python scripts/draw_fern.py [--out refs/final/restoring_fern.png]

The large tier is a five frond bouquet; 16 px of width cannot hold that, so the
standard tier is the same plant at the size where it reads: **one** frond crown with a
dark frond tucked right behind it. Everything else follows the current drawing rules:

* the rachis bends (``x_profile``) instead of standing dead straight;
* leaflets are short and uneven (2-4 px, left and right differ), 3 rows apart, and the
  two longest get a one pixel notch so they read as two pinnules;
* the right leaflet of each pair drops one row (``stagger=1``);
* a dark frond behind the front one fills the gaps - without it the background shows
  through between leaflets and the sprite looks perforated;
* rim light and vein dots are picked from the finished sprite, root is 4x2 dark teal.
"""
import argparse
import pathlib

from frond_art import Frond, Grid, counts, draw_frond, finish, rim_light, root

W, H = 16, 32

BACK_TONES = ("g", "g")
FRONT_TONES = ("G", "g")


def build():
    grid = Grid(W, H)

    # dark frond right behind the front one: closes the gaps between leaflets
    draw_frond(
        grid,
        Frond(
            x_bottom=9,
            x_top=9,
            tip=6,
            base=26,
            nodes=[(9, 1, 2), (12, 2, 1), (15, 1, 2), (18, 2, 1), (21, 1, 2), (24, 1, 1)],
            tones=BACK_TONES,
            rachis="g",
        ),
    )

    # short side frond at the lower left: makes the plant read as a clump, and it is
    # drawn in the dark tones so it stays behind the main frond
    draw_frond(
        grid,
        Frond(
            x_bottom=6,
            x_top=4,
            tip=13,
            base=26,
            nodes=[(16, 2, 1), (19, 2, 1), (22, 2, 1), (25, 1, 1)],
            tones=BACK_TONES,
            rachis="g",
        ),
    )

    # front frond: bent rachis, uneven leaflets, notched where they are long enough
    front = Frond(
        x_bottom=8,
        x_top=7,
        tip=3,
        base=26,
        x_profile=[(26, 8), (18, 8), (10, 7), (3, 7)],
        nodes=[
            (5, 2, 2),
            (8, 3, 2),
            (11, 4, 3),
            (14, 4, 4),
            (17, 5, 4),
            (20, 4, 5),
            (23, 3, 3),
            (26, 2, 2),
        ],
        tones=FRONT_TONES,
    )
    draw_frond(grid, front, stagger=1)

    # pointed top
    grid.put(front.x_at(3), 3, "G")
    grid.put(front.x_at(4) - 1, 4, "G")
    grid.put(front.x_at(4) + 1, 4, "g")

    # rim light on the upper-left tips; pale vein dots up the rachis
    rim_light(grid, (8, 12, 16))
    for row in (9, 15, 21):
        grid.put(front.x_at(row), row, "B")

    # dark teal root
    root(grid, 7, 9, (27, 28))
    return grid


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="refs/final/restoring_fern.png")
    args = parser.parse_args()

    grid = build()
    finish(grid, pathlib.Path(args.out))
    print("# colors:", counts(grid.rows()))
    for row in grid.rows():
        print(row)


if __name__ == "__main__":
    main()
