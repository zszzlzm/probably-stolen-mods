"""Tiny pixel-art toolkit shared by the hand-laid sprites.

A sprite is a ``Grid`` of palette letters (``"."`` = transparent). The helpers here
cover the two things every sprite in this mod needs and that are easy to get wrong:

* ``fill_seams`` closes pinholes that are enclosed on all four sides - vanilla items
  never show a transparent hole inside their silhouette;
* ``outline`` paints the 1 px plum border on the *exterior* of the silhouette only.
  It first collects the boundary pixels and paints them afterwards: painting while
  scanning makes freshly painted pixels look like content and floods the canvas.
"""
from collections import deque

TRANSPARENT = "."


class Grid:
    def __init__(self, width, height, fill=TRANSPARENT):
        self.width = width
        self.height = height
        self.cells = [[fill] * width for _ in range(height)]

    def put(self, x, y, color):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.cells[y][x] = color

    def at(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.cells[y][x]
        return TRANSPARENT

    def rows(self):
        return ["".join(row) for row in self.cells]

    def is_empty(self, x, y):
        return self.at(x, y) == TRANSPARENT


def fill_seams(grid, color):
    """Give fully enclosed transparent pixels a solid colour (no pinholes)."""
    for y in range(grid.height):
        for x in range(grid.width):
            if grid.at(x, y) != TRANSPARENT:
                continue
            if all(
                grid.at(x + dx, y + dy) != TRANSPARENT
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
            ):
                grid.put(x, y, color)


def _outside_mask(grid):
    """Flood fill the background from the canvas border (4-connectivity)."""
    outside = [[False] * grid.width for _ in range(grid.height)]
    queue = deque()
    for x in range(grid.width):
        for y in (0, grid.height - 1):
            if grid.is_empty(x, y):
                outside[y][x] = True
                queue.append((x, y))
    for y in range(grid.height):
        for x in (0, grid.width - 1):
            if grid.is_empty(x, y) and not outside[y][x]:
                outside[y][x] = True
                queue.append((x, y))
    while queue:
        x, y = queue.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if (
                0 <= nx < grid.width
                and 0 <= ny < grid.height
                and not outside[ny][nx]
                and grid.is_empty(nx, ny)
            ):
                outside[ny][nx] = True
                queue.append((nx, ny))
    return outside


def outline(grid, color):
    """Paint the 1 px exterior border of the silhouette, leaving inner seams alone."""
    outside = _outside_mask(grid)
    edge = []
    for y in range(grid.height):
        for x in range(grid.width):
            if not outside[y][x] or not grid.is_empty(x, y):
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if grid.at(x + dx, y + dy) != TRANSPARENT:
                    edge.append((x, y))
                    break
    for x, y in edge:
        grid.put(x, y, color)
    return grid
