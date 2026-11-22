"""Hand-lay the 32x32 large frond (``restoring_fern_l``).

    python tools/draw_fern_l.py [--out refs/final/restoring_fern_l.png]

Composition: a **bouquet**, not five parallel stalks. All five fronds root inside a
six pixel wide base (x 13-19) and fan outwards as they rise, so the clump is dense
where the stems meet and open at the top - the silhouette a fern actually has.

* two dark fronds behind, three lit ones in front;
* the centre frond is the tallest and the straightest; the outer pair lean the most,
  which is what spreads the fan;
* leaflets are short and uneven (2-4 px, left and right differ), spaced 3 rows apart.
  They are deliberately NOT wide uniform bands: a 6 px ladder of identical blades is
  what made an earlier version's middle frond read as a big empty ribbon.
"""
import argparse
import pathlib

from frond_art import Frond, Grid, counts, draw_frond, finish, rim_light, root

W, H = 32, 32

BACK_TONES = ("g", "D")
FRONT_TONES = ("G", "g")


def build():
    grid = Grid(W, H)

    # ---- back layer: darker and shorter, leaning further out; fills the gaps
    # between the lit fronds so the fan has depth instead of holes
    draw_frond(
        grid,
        Frond(
            x_bottom=14,
            x_top=5,
            tip=7,
            base=27,
            nodes=[(12, 2, 2), (15, 3, 2), (18, 2, 3), (21, 3, 2), (24, 2, 2)],
            tones=BACK_TONES,
            rachis="D",
        ),
    )
    draw_frond(
        grid,
        Frond(
            x_bottom=18,
            x_top=26,
            tip=8,
            base=27,
            nodes=[(13, 2, 2), (16, 2, 3), (19, 3, 2), (22, 2, 3), (25, 2, 2)],
            tones=BACK_TONES,
            rachis="D",
        ),
    )

    # ---- front layer: outer pair leans hardest, centre stands almost straight
    draw_frond(
        grid,
        Frond(
            x_bottom=15,
            x_top=7,
            tip=9,
            base=27,
            nodes=[
                (10, 3, 1),
                (13, 4, 2),
                (16, 5, 3),
                (19, 4, 2),
                (22, 4, 2),
                (25, 3, 1),
            ],
            tones=FRONT_TONES,
        ),
    )
    draw_frond(
        grid,
        Frond(
            x_bottom=17,
            x_top=25,
            tip=10,
            base=27,
            nodes=[
                (11, 1, 3),
                (14, 2, 4),
                (17, 3, 5),
                (20, 2, 4),
                (23, 2, 4),
                (26, 1, 3),
            ],
            tones=FRONT_TONES,
        ),
    )

    # a dark frond sits directly behind the centre one: it fills the gaps between
    # the centre leaflets so the middle of the clump has mass instead of holes
    draw_frond(
        grid,
        Frond(
            x_bottom=16,
            x_top=16,
            tip=6,
            base=27,
            nodes=[(9, 2, 2), (12, 3, 2), (15, 2, 3), (18, 3, 2), (21, 2, 3), (24, 2, 2)],
            tones=BACK_TONES,
            rachis="D",
        ),
    )

    center = Frond(
        x_bottom=16,
        x_top=15,
        tip=3,
        base=27,
        x_profile=[(27, 16), (22, 16), (16, 15), (9, 15), (3, 15)],
        nodes=[
            (5, 2, 3),
            (8, 3, 3),
            (11, 3, 2),
            (14, 4, 3),
            (17, 3, 4),
            (20, 3, 3),
            (23, 3, 2),
            (26, 2, 3),
        ],
        tones=FRONT_TONES,
    )
    draw_frond(grid, center, stagger=1)
    grid.put(15, 3, "G")
    grid.put(14, 4, "G")
    grid.put(16, 4, "g")

    # dark spore dots on the widest centre leaflets


    # rim light on the upper-left tips
    rim_light(grid, (12, 16, 20))

    # pale vein dots up the centre rachis
    for row in (7, 13, 19):
        grid.put(center.x_at(row), row, "B")

    root(grid, 14, 17, (27, 28, 29))
    return grid


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="refs/final/restoring_fern_l.png")
    args = parser.parse_args()

    grid = build()
    finish(grid, pathlib.Path(args.out))
    print("# colors:", counts(grid.rows()))
    for row in grid.rows():
        print(row)


if __name__ == "__main__":
    main()
