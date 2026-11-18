"""Checks of the GRKit pack that need no camera, no firmware and no GRKit:

    python3 -m unittest discover -s grkit

The tables are needed for the last class (mfilm_grkit.py --help says how to build them); without them it
is skipped.
"""

import unittest

import numpy as np

import mfilm_grkit as m


def table_of(fn):
    """A made-up table whose every point is fn(red, green, blue index)."""
    i = np.arange(m.GRID)
    b, g, r = np.meshgrid(i, i, i, indexing="ij")
    return np.stack(fn(r, g, b), -1).astype(np.uint8)


class Colour(unittest.TestCase):
    def test_cineon_is_the_darkrooms(self):
        # DEVELOPING.md step 8: v = (685 + 300 log10(0.9892 x + 0.0108)) / 1023
        for x in (0.0, 0.01, 0.18, 1.0, 4.0):
            self.assertAlmostEqual(float(m.cineon(x)), (685 + 300 * np.log10(0.9892 * x + 0.0108)) / 1023, 6)
        self.assertEqual(float(m.cineon(100.0)), 1.0)

    def test_positions_never_leave_the_table(self):
        pos = m.positions(np.array([0.0, 0.5, 1.0]))
        self.assertEqual(int(pos[0]), 0)
        self.assertEqual(int(pos[-1]) >> 8, m.GRID - 2)       # the last cell, never past it

    def test_tetra_gives_the_points(self):
        t = table_of(lambda r, g, b: (r * 7, g * 5, b * 3))
        i = np.arange(m.GRID - 1)
        pos = np.stack([i * 256, (i[::-1]) * 256, i * 256], -1)
        out = m.tetra(t, pos)
        np.testing.assert_array_equal(out[:, 0], i * 7)
        np.testing.assert_array_equal(out[:, 1], i[::-1] * 5)

    def test_tetra_is_exact_on_a_linear_table(self):
        # a table that is linear in each axis is interpolated exactly by every tetrahedron
        t = table_of(lambda r, g, b: (r * 7, g * 7, b * 7))
        rng = np.random.default_rng(1)
        pos = rng.integers(0, (m.GRID - 1) * 256, size=(500, 3))
        out = m.tetra(t, pos).astype(int)
        np.testing.assert_allclose(out, np.round(pos * 7 / 256), atol=1)

    def test_cube_is_red_fastest(self, tmp=None):
        import tempfile
        from pathlib import Path
        rgb = np.zeros((2, 2, 2, 3))
        rgb[0, 0, 1] = (1, 0, 0)            # [blue][green][red]: red = 1 at the second line
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "x.cube"
            m.write_cube(path, rgb, "x")
            lines = [ln for ln in path.read_text().splitlines() if ln[:1].isdigit()]
        self.assertEqual(lines[1], "1.000000 0.000000 0.000000")


class Shelf(unittest.TestCase):
    def test_every_film_has_a_set(self):
        for key in m.FILMS:
            self.assertIn(m.film_set(key), m.SETS)

    def test_names_ids_and_sets_fit_grkit(self):
        rows = [(f"LOOK{i:02}.LUT", key, "look") for i, key in enumerate(m.FILMS)]
        self.assertEqual(m.check(m.plan(rows)), [])

    def test_recipe_values_are_in_grkits_ranges(self):
        for key in m.FILMS:
            g, h, wb = m.grain(key), m.glow(key), m.white_balance(key)
            self.assertIn(g["level"], range(5))
            self.assertIn(g["size"], range(4))
            self.assertIn(h["halation"], range(4))
            self.assertIn(wb["kelvin"], (3200, 5500))

    def test_every_box_has_a_name(self):
        for key in m.FILMS:
            box = m.icon(key)
            self.assertTrue(box["brand"] and box["name"], key)
            self.assertNotEqual(box.get("number"), "", key)

    def test_box_colours_are_rgb(self):
        for key in m.FILMS:
            for rgb in m.icon(key)["colors"].values():
                self.assertEqual(len(rgb), 3)
                self.assertTrue(all(0 <= c <= 255 for c in rgb))

    def test_ink_is_the_palettes(self):
        self.assertEqual(m.ink((m.catalog.AMBER, 185)), [0xF4, 0xA8, 0x1C])   # the hue at its level
        self.assertEqual(m.ink((m.catalog.GRAY, 0)), [4, 3, 3])


@unittest.skipUnless((m.TABLES / "TABLES.txt").exists(), "no tables built")
class Tables(unittest.TestCase):
    def test_grey_prints_as_a_mid_tone(self):
        for file, key, _ in m.shelf():
            if m.FILMS[key]["kind"] == "xpro" or key == "redscale100":
                continue                    # cross-processed and redscale move grey on purpose
            light = np.array([[0.18] * 3]) * m.scale(key)
            grey = m.tetra(m.read_table(m.TABLES / file), m.positions(m.cineon(light)))[0].mean()
            # A stop off in GREY moves grey by about 40. The darkest on the shelf print it about 63
            # (Retro 80S and Infrared 400, as their tables do on the Canon too), the brightest about 159.
            self.assertTrue(55 < grey < 175, f"{key}: 18% grey prints at {grey:.0f}")


if __name__ == "__main__":
    unittest.main()
