#!/usr/bin/env python3
"""
Unit and integration tests for niri-window-label.
Run with: python3 -m unittest discover -s tests -v
"""

import importlib.machinery
import importlib.util
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "niri-window-label"
loader = importlib.machinery.SourceFileLoader("niri_window_label", str(SCRIPT_PATH))
spec = importlib.util.spec_from_loader(loader.name, loader)
nwl = importlib.util.module_from_spec(spec)
loader.exec_module(nwl)


def make_win(
    wid: int,
    col: int,
    row: int = 1,
    width: float = 936.0,
    height: float = 994.0,
    ws_id: int = 1,
    ts_secs: int = 100,
    title: str = "nvim",
    app_id: str = "kitty",
    win_size: list[int] | None = None,
) -> dict:
    return {
        "id": wid,
        "title": title,
        "app_id": app_id,
        "pid": None,
        "workspace_id": ws_id,
        "is_focused": False,
        "is_floating": False,
        "layout": {
            "pos_in_scrolling_layout": [col, row],
            "tile_size": [width, height],
            "window_size": win_size or [int(width), int(height)],
            "tile_pos_in_workspace_view": None,
        },
        "focus_timestamp": {"secs": ts_secs, "nanos": 0},
    }


class TestWindowLabelGeometryAndNaming(unittest.TestCase):
    def test_two_half_screen_windows_left_and_right(self):
        """On a 1920x1080 monitor with two half-screen windows (936px),
        column 1 must center on the left (~484px) and column 2 on the right (~1436px)."""
        engine = nwl.LayoutStateEngine()
        w1 = make_win(1, col=1, width=936.0, ts_secs=100)
        w2 = make_win(2, col=2, width=936.0, ts_secs=101)
        engine.windows = {1: w1, 2: w2}

        cx1, ty1, _ = engine._compute_window_geometry_on_output(w1, 1920, 1080)
        cx2, ty2, _ = engine._compute_window_geometry_on_output(w2, 1920, 1080)

        self.assertAlmostEqual(cx1, 16.0 + 936.0 / 2.0, delta=1.0)
        self.assertAlmostEqual(cx2, 16.0 + 936.0 + 16.0 + 936.0 / 2.0, delta=1.0)
        self.assertEqual(ty1, 16.0)
        self.assertEqual(ty2, 16.0)

    def test_three_columns_on_ultrawide_monitor(self):
        """Simulate a 3440x1440 ultrawide monitor with 3 one-third width windows (1125px each).
        They must center in the left third, middle third, and right third."""
        engine = nwl.LayoutStateEngine()
        w1 = make_win(10, col=1, width=1125.0, ts_secs=100)
        w2 = make_win(11, col=2, width=1125.0, ts_secs=101)
        w3 = make_win(12, col=3, width=1125.0, ts_secs=102)
        engine.windows = {10: w1, 11: w2, 12: w3}

        cx1, _, _ = engine._compute_window_geometry_on_output(w1, 3440, 1440, update_viewport=False)
        cx2, _, _ = engine._compute_window_geometry_on_output(w2, 3440, 1440, update_viewport=False)
        cx3, _, _ = engine._compute_window_geometry_on_output(w3, 3440, 1440, update_viewport=False)

        self.assertTrue(500 <= cx1 <= 650, f"Unexpected left third: {cx1}")
        self.assertTrue(1650 <= cx2 <= 1790, f"Unexpected middle third: {cx2}")
        self.assertTrue(2790 <= cx3 <= 2930, f"Unexpected right third: {cx3}")

    def test_move_column_from_right_to_left_updates_side(self):
        """Reproduce moving a right-half window to the left half on a secondary monitor (1600x900)
        via forced_side='left'."""
        engine = nwl.LayoutStateEngine()
        w_other = make_win(2, col=2, width=1600.0, ws_id=4, ts_secs=200)
        w_moved = make_win(40, col=3, width=776.0, ws_id=4, ts_secs=205)
        engine.windows = {2: w_other, 40: w_moved}

        # Initially at col 3 on the right half (~1196px)
        cx_before, _, _ = engine._compute_window_geometry_on_output(w_moved, 1600, 900)
        self.assertGreater(cx_before, 800.0)

        # Now the user moves window 40 to the left (becomes col 2 while the other becomes col 3)
        w_moved["layout"]["pos_in_scrolling_layout"] = [2, 1]
        w_other["layout"]["pos_in_scrolling_layout"] = [3, 1]
        engine.forced_side[40] = "left"

        cx_after, _, _ = engine._compute_window_geometry_on_output(w_moved, 1600, 900)
        self.assertLess(cx_after, 800.0)
        self.assertAlmostEqual(cx_after, 404.0, delta=1.0)

    def test_vertically_stacked_windows_in_same_column(self):
        """Two windows stacked in the same column (row 1 and row 2) must have distinct top_y values."""
        engine = nwl.LayoutStateEngine()
        top_win = make_win(1, col=1, row=1, width=936.0, height=480.0)
        bot_win = make_win(2, col=1, row=2, width=936.0, height=480.0)
        engine.windows = {1: top_win, 2: bot_win}

        _, ty1, _ = engine._compute_window_geometry_on_output(top_win, 1920, 1080)
        _, ty2, _ = engine._compute_window_geometry_on_output(bot_win, 1920, 1080)

        self.assertEqual(ty1, 16.0)
        self.assertEqual(ty2, 16.0 + 480.0 + 16.0)

    def test_fullscreen_detection(self):
        """A normal tiled window (1920x1026 due to top bar) is NOT fullscreen,
        whereas a 1920x1080 window IS fullscreen."""
        engine = nwl.LayoutStateEngine()
        tiled_win = make_win(1, col=1, width=1920.0, height=1026.0, win_size=[1920, 1026])
        full_win = make_win(2, col=2, width=1920.0, height=1080.0, win_size=[1920, 1080])

        self.assertFalse(engine._is_window_fullscreen(tiled_win, 1920, 1080))
        self.assertTrue(engine._is_window_fullscreen(full_win, 1920, 1080))

    def test_smart_project_folder_and_custom_naming(self):
        """Verify custom name priority and automatic project folder naming."""
        engine = nwl.LayoutStateEngine()
        w = make_win(10, col=1, title="npm start", app_id="kitty")

        # 1. Without a custom name, use the detected project directory ("VoiceApp")
        lbl, is_custom = engine._format_label_for_window(w, {}, project_override="VoiceApp")
        self.assertFalse(is_custom)
        self.assertEqual(lbl, "VoiceApp  •  npm start")

        # 2. If the window title already contains the project name, do not duplicate it
        w_dup = make_win(11, col=1, title="VoiceApp — Dolphin", app_id="dolphin")
        lbl_dup, _ = engine._format_label_for_window(w_dup, {}, project_override="VoiceApp")
        self.assertEqual(lbl_dup, "VoiceApp — Dolphin")

        # 3. With a custom name in window-names.json, prefer the custom name and set is_custom=True
        lbl_custom, is_custom = engine._format_label_for_window(
            w, {"10": "Main Server"}, project_override="VoiceApp"
        )
        self.assertTrue(is_custom)
        self.assertEqual(lbl_custom, "Main Server")

    def test_floating_window_coordinates(self):
        """Verify that floating windows (e.g. Picture-in-Picture) use tile_pos_in_workspace_view."""
        engine = nwl.LayoutStateEngine()
        float_win = make_win(99, col=1, width=480.0, height=270.0)
        float_win["is_floating"] = True
        float_win["layout"]["pos_in_scrolling_layout"] = None
        float_win["layout"]["tile_pos_in_workspace_view"] = [1200.0, 650.0]
        engine.windows = {99: float_win}

        cx, ty, cw = engine._compute_window_geometry_on_output(float_win, 1920, 1080)
        self.assertAlmostEqual(cx, 1200.0 + 240.0, delta=0.5)
        self.assertAlmostEqual(ty, 650.0, delta=0.5)
        self.assertEqual(cw, 480.0)

    def test_long_strip_10_mixed_columns_never_exceeds_monitor_bounds(self):
        """Simulate a strip of 10 columns mixing full-width (1888px) and half-width (936px) windows,
        traversing from start to end and back."""
        engine = nwl.LayoutStateEngine()
        widths = [1888.0, 936.0, 1888.0, 936.0, 936.0, 936.0, 1888.0, 936.0, 936.0, 1888.0]
        for idx, w_px in enumerate(widths, start=1):
            engine.windows[idx] = make_win(idx, col=idx, width=w_px, ts_secs=100 + idx)

        # Traverse left-to-right (1 -> 10) and right-to-left (10 -> 1)
        sequence = list(range(1, 11)) + list(range(10, 0, -1))
        for wid in sequence:
            win = engine.windows[wid]
            cx, ty, _ = engine._compute_window_geometry_on_output(win, 1920, 1080, update_viewport=True)
            self.assertTrue(
                0.0 < cx < 1920.0,
                f"Column {wid} went off-screen during traversal: center_x={cx}",
            )
            self.assertEqual(ty, 16.0)

    def test_multi_monitor_workspace_isolation(self):
        """Verify that scrolling on Monitor 2 (workspace 4) does not alter Monitor 1 (workspace 1)."""
        engine = nwl.LayoutStateEngine()
        # Monitor 1 (ws 1): two half-width windows
        m1_left = make_win(1, col=1, width=936.0, ws_id=1, ts_secs=100)
        m1_right = make_win(2, col=2, width=936.0, ws_id=1, ts_secs=101)
        # Monitor 2 (ws 4): three columns
        m2_c1 = make_win(30, col=1, width=776.0, ws_id=4, ts_secs=100)
        m2_c2 = make_win(31, col=2, width=776.0, ws_id=4, ts_secs=101)
        m2_c3 = make_win(32, col=3, width=1568.0, ws_id=4, ts_secs=102)
        engine.windows = {1: m1_left, 2: m1_right, 30: m2_c1, 31: m2_c2, 32: m2_c3}

        cx_m1_before, _, _ = engine._compute_window_geometry_on_output(m1_right, 1920, 1080)
        # Navigate extensively on Monitor 2
        engine._compute_window_geometry_on_output(m2_c3, 1600, 900)
        engine._compute_window_geometry_on_output(m2_c1, 1600, 900)
        engine._compute_window_geometry_on_output(m2_c2, 1600, 900)

        # Monitor 1 must preserve its exact viewport position
        cx_m1_after, _, _ = engine._compute_window_geometry_on_output(
            m1_right, 1920, 1080, update_viewport=False
        )
        self.assertAlmostEqual(cx_m1_before, cx_m1_after, delta=0.1)

    def test_peek_mode_filters_only_visible_windows(self):
        """If 6 windows exist in a workspace but only 2 fit on screen, Peek mode filtering
        must only classify those 2 windows as visible."""
        engine = nwl.LayoutStateEngine()
        for c in range(1, 7):
            engine.windows[c] = make_win(c, col=c, width=936.0, ws_id=1, ts_secs=100 + c)

        # Focus column 6 (so columns 5 and 6 are visible on screen)
        engine._compute_window_geometry_on_output(engine.windows[6], 1920, 1080, update_viewport=True)

        visible_ids = []
        for wid, win in sorted(engine.windows.items()):
            cx, _, _ = engine._compute_window_geometry_on_output(
                win, 1920, 1080, update_viewport=False
            )
            if 20.0 <= cx <= (1920.0 - 20.0):
                visible_ids.append(wid)

        self.assertEqual(visible_ids, [5, 6])

    def test_closed_windows_garbage_collection_and_truncation(self):
        """Verify that long titles are truncated to 56 chars and closed window IDs are pruned."""
        long_title = "A" * 120
        truncated = nwl.truncate_text(long_title, 56)
        self.assertEqual(len(truncated), 56)
        self.assertTrue(truncated.endswith("…"))

        names = {"1": "Active", "2": "Closed", "3": "Also Active"}
        open_ids = {"1", "3"}
        cleaned = {k: v for k, v in names.items() if k in open_ids}
        self.assertEqual(cleaned, {"1": "Active", "3": "Also Active"})

    def test_custom_css_override_merging(self):
        """Verify that ~/.config/niri/window-label.css is appended on top of the base stylesheet."""
        import tempfile

        base = b".badge-box { border-radius: 12px; }"
        with tempfile.TemporaryDirectory() as tmp:
            custom_file = Path(tmp) / "window-label.css"
            # When custom file does not exist, return the base CSS unchanged
            no_theme = Path(tmp) / "missing.theme.css"
            self.assertEqual(nwl.build_stylesheet(base, custom_file, no_theme), base)

            # When custom file exists, append user rules at the end so they override defaults
            custom_file.write_text(".badge-box { border-color: #ff007c; }", encoding="utf-8")
            merged = nwl.build_stylesheet(base, custom_file, no_theme)
            self.assertIn(b"#ff007c", merged)
            self.assertTrue(merged.startswith(base))

            # Theme file goes between the defaults and the user's file
            theme_file = Path(tmp) / "window-label.theme.css"
            theme_file.write_text("@define-color nwl_accent #123456;", encoding="utf-8")
            layered = nwl.build_stylesheet(base, custom_file, theme_file)
            self.assertLess(layered.index(b"#123456"), layered.index(b"#ff007c"))

    def test_i18n_language_detection_and_translation(self):
        """Verify automatic language detection from locale env vars and English fallback."""
        self.assertEqual(nwl.detect_language({"LANG": "es_MX.UTF-8"}), "es")
        self.assertEqual(nwl.detect_language({"LANG": "en_US.UTF-8"}), "en")
        self.assertEqual(nwl.detect_language({"LANG": "fr_FR.UTF-8"}), "en")
        self.assertEqual(
            nwl.detect_language({"LANG": "en_US.UTF-8", "NIRI_LABEL_LANG": "es"}), "es"
        )

        self.assertEqual(
            nwl.tr("rename_header", lang="en", app_id="kitty"), "🏷️  Rename window [kitty]"
        )
        self.assertEqual(
            nwl.tr("rename_header", lang="es", app_id="kitty"), "🏷️  Renombrar ventana [kitty]"
        )
        self.assertEqual(nwl.tr("untitled", lang="en"), "Untitled")
        self.assertEqual(nwl.tr("untitled", lang="es"), "Sin título")

    def test_minimap_companion_plugin_connection(self):
        """Verify that niri-window-label can connect to niri-minimap when installed."""
        minimap_script = Path("/home/alfus985/projects/niri-minimap/niri-minimap")
        if minimap_script.exists():
            plugin = nwl.load_minimap_engine(minimap_script)
            self.assertIsNotNone(plugin)
            w1 = make_win(1, col=1, width=936.0, ts_secs=100)
            w2 = make_win(2, col=2, width=936.0, ts_secs=101)
            plugin.windows = {1: w1, 2: w2}
            cols = plugin.compute_strip_state(w2, 1920, 1080, custom_names={"1": "API"})
            plain = plugin.format_strip_plain(cols)
            self.assertEqual(plain, "◇  ▣   2/2")


class TestAltTabTitles(unittest.TestCase):
    def test_strip_removes_leftover_strip(self):
        self.assertEqual(nwl.strip_minimap_from_title("🏷️ API   ⟪◇  ▣   2/2⟫"), "API")
        self.assertEqual(nwl.strip_minimap_from_title("~ ⟪□ ▣ 2/2⟫"), "~")

    def test_plain_title_untouched(self):
        self.assertEqual(nwl.strip_minimap_from_title("vim ⟪x"), "vim ⟪x")

    def test_only_terminals_are_retitled(self):
        self.assertTrue(nwl.is_terminal_window({"app_id": "kitty"}))
        self.assertTrue(nwl.is_terminal_window({"app_id": "Alacritty"}))
        self.assertFalse(nwl.is_terminal_window({"app_id": "firefox"}))
        self.assertFalse(nwl.is_terminal_window({}))


class TestAltTabOrder(unittest.TestCase):
    def test_mru_focused_first_then_newest(self):
        wins = {
            1: {"id": 1, "focus_timestamp": {"secs": 10, "nanos": 0}},
            2: {"id": 2, "focus_timestamp": {"secs": 30, "nanos": 0}},
            3: {"id": 3, "focus_timestamp": {"secs": 20, "nanos": 5}},
            4: {"id": 4},
        }
        self.assertEqual(nwl.mru_window_ids(wins, 1), [1, 2, 3, 4])
        self.assertEqual(nwl.mru_window_ids(wins, None), [2, 3, 1, 4])

    def test_monotonic_timestamp_shape(self):
        ts = nwl.monotonic_timestamp()
        self.assertLess(ts["nanos"], 1_000_000_000)
        self.assertGreaterEqual(ts["secs"], 0)


class TestMonitorMap(unittest.TestCase):
    OUTPUTS = {
        "VGA-1": {"make": "HP Inc.", "model": "HP P204", "logical": {"x": 1920, "y": 0, "width": 1600, "height": 900}},
        "LVDS-1": {"make": "Seiko Epson Corporation", "model": "0x314C", "logical": {"x": 0, "y": 0, "width": 1920, "height": 1080}},
    }

    def test_numbered_left_to_right(self):
        self.assertEqual(nwl.ordered_output_names(self.OUTPUTS), ["LVDS-1", "VGA-1"])

    def test_friendly_names(self):
        self.assertEqual(nwl.monitor_display_name("LVDS-1", self.OUTPUTS["LVDS-1"]), nwl.tr("alttab_laptop"))
        self.assertEqual(nwl.monitor_display_name("VGA-1", self.OUTPUTS["VGA-1"]), "HP P204")
        self.assertEqual(nwl.monitor_display_name("VGA-1", self.OUTPUTS["VGA-1"], {"VGA-1": "Lateral"}), "Lateral")
        self.assertEqual(nwl.monitor_display_name("DP-2", {"make": "Dell", "model": "0xA0B1"}), "Dell")

    def test_badges(self):
        self.assertEqual(nwl.monitor_badge(0), "①")
        self.assertEqual(nwl.monitor_badge(1), "②")
        self.assertEqual(nwl.monitor_badge(12), "13")


class TestStylesheet(unittest.TestCase):
    def setUp(self):
        try:
            import gi
            gi.require_version("Gtk", "3.0")
            from gi.repository import Gtk
        except (ImportError, ValueError):
            self.skipTest("GTK3 not available")
        self.Gtk = Gtk

    def _color_of(self, css: bytes, css_class: str) -> str:
        Gtk = self.Gtk
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        label = Gtk.Label()  # keep a reference: a freed widget's context loses its styles
        ctx = label.get_style_context()
        ctx.add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        ctx.add_class(css_class)
        return ctx.get_color(Gtk.StateFlags.NORMAL).to_string()

    def test_default_css_parses(self):
        self.assertEqual(self._color_of(nwl.DEFAULT_CSS, "alttab-counter"), "rgb(125,207,255)")

    def test_user_palette_override_wins(self):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".css", delete=False) as f:
            f.write("@define-color nwl_focus #ff0000;\n")
        css = nwl.build_stylesheet(nwl.DEFAULT_CSS, Path(f.name), Path("/nonexistent/theme.css"))
        Path(f.name).unlink()
        self.assertEqual(self._color_of(css, "alttab-counter"), "rgb(255,0,0)")


if __name__ == "__main__":
    unittest.main()
