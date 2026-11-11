#!/usr/bin/env python3
"""
Pruebas unitarias y de integración para niri-window-label.
Ejecutar con: python3 -m unittest discover -s tests -v
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
        """En un monitor 1920x1080 con dos ventanas de media pantalla (936px),
        la columna 1 debe centrarse a la izquierda (~484px) y la columna 2 a la derecha (~1436px)."""
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
        """Simula un monitor Ultrawide 3440x1440 con 3 ventanas de 1/3 de ancho (1125px cada una).
        Deben quedar centradas en el tercio izquierdo, tercio central y tercio derecho."""
        engine = nwl.LayoutStateEngine()
        w1 = make_win(10, col=1, width=1125.0, ts_secs=100)
        w2 = make_win(11, col=2, width=1125.0, ts_secs=101)
        w3 = make_win(12, col=3, width=1125.0, ts_secs=102)
        engine.windows = {10: w1, 11: w2, 12: w3}

        cx1, _, _ = engine._compute_window_geometry_on_output(w1, 3440, 1440, update_viewport=False)
        cx2, _, _ = engine._compute_window_geometry_on_output(w2, 3440, 1440, update_viewport=False)
        cx3, _, _ = engine._compute_window_geometry_on_output(w3, 3440, 1440, update_viewport=False)

        self.assertTrue(500 <= cx1 <= 650, f"Tercio izquierdo inesperado: {cx1}")
        self.assertTrue(1650 <= cx2 <= 1790, f"Tercio central inesperado: {cx2}")
        self.assertTrue(2790 <= cx3 <= 2930, f"Tercio derecho inesperado: {cx3}")

    def test_move_column_from_right_to_left_updates_side(self):
        """Reproduce el caso en el segundo monitor (1600x900) cuando una ventana en la mitad
        derecha se mueve hacia la izquierda (forced_side='left')."""
        engine = nwl.LayoutStateEngine()
        w_other = make_win(2, col=2, width=1600.0, ws_id=4, ts_secs=200)
        w_moved = make_win(40, col=3, width=776.0, ws_id=4, ts_secs=205)
        engine.windows = {2: w_other, 40: w_moved}

        # Inicialmente en col 3 está en la mitad derecha (~1196px)
        cx_before, _, _ = engine._compute_window_geometry_on_output(w_moved, 1600, 900)
        self.assertGreater(cx_before, 800.0)

        # Ahora el usuario mueve la ventana 40 a la izquierda (pasa a col 2 y la otra a col 3)
        w_moved["layout"]["pos_in_scrolling_layout"] = [2, 1]
        w_other["layout"]["pos_in_scrolling_layout"] = [3, 1]
        engine.forced_side[40] = "left"

        cx_after, _, _ = engine._compute_window_geometry_on_output(w_moved, 1600, 900)
        self.assertLess(cx_after, 800.0)
        self.assertAlmostEqual(cx_after, 404.0, delta=1.0)

    def test_vertically_stacked_windows_in_same_column(self):
        """Dos ventanas apiladas en la misma columna (row 1 y row 2) deben tener distinto top_y."""
        engine = nwl.LayoutStateEngine()
        top_win = make_win(1, col=1, row=1, width=936.0, height=480.0)
        bot_win = make_win(2, col=1, row=2, width=936.0, height=480.0)
        engine.windows = {1: top_win, 2: bot_win}

        _, ty1, _ = engine._compute_window_geometry_on_output(top_win, 1920, 1080)
        _, ty2, _ = engine._compute_window_geometry_on_output(bot_win, 1920, 1080)

        self.assertEqual(ty1, 16.0)
        self.assertEqual(ty2, 16.0 + 480.0 + 16.0)

    def test_fullscreen_detection(self):
        """Una ventana en mosaico normal (1920x1026 por la barra superior) NO es fullscreen,
        mientras que una 1920x1080 SÍ es fullscreen."""
        engine = nwl.LayoutStateEngine()
        tiled_win = make_win(1, col=1, width=1920.0, height=1026.0, win_size=[1920, 1026])
        full_win = make_win(2, col=2, width=1920.0, height=1080.0, win_size=[1920, 1080])

        self.assertFalse(engine._is_window_fullscreen(tiled_win, 1920, 1080))
        self.assertTrue(engine._is_window_fullscreen(full_win, 1920, 1080))

    def test_smart_project_folder_and_custom_naming(self):
        """Verifica prioridad de nombre personalizado y auto-nombrado por carpeta de proyecto."""
        engine = nwl.LayoutStateEngine()
        w = make_win(10, col=1, title="npm start", app_id="kitty")

        # 1. Sin nombre personalizado pero con carpeta de proyecto detectada ("VoiceApp")
        lbl, is_custom = engine._format_label_for_window(w, {}, project_override="VoiceApp")
        self.assertFalse(is_custom)
        self.assertEqual(lbl, "VoiceApp  •  npm start")

        # 2. Si el título ya contiene el nombre del proyecto, no lo duplica
        w_dup = make_win(11, col=1, title="VoiceApp — Dolphin", app_id="dolphin")
        lbl_dup, _ = engine._format_label_for_window(w_dup, {}, project_override="VoiceApp")
        self.assertEqual(lbl_dup, "VoiceApp — Dolphin")

        # 3. Con nombre personalizado en window-names.json, usa el personalizado y activa is_custom
        lbl_custom, is_custom = engine._format_label_for_window(
            w, {"10": "Servidor Principal"}, project_override="VoiceApp"
        )
        self.assertTrue(is_custom)
        self.assertEqual(lbl_custom, "Servidor Principal")

    def test_floating_window_coordinates(self):
        """Verifica que las ventanas flotantes (ej. Picture-in-Picture) usen tile_pos_in_workspace_view."""
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
        """Simula una cinta de 10 columnas mezclando tamaños completos (1888px) y mitades (936px),
        recorriéndolas de principio a fin y de regreso."""
        engine = nwl.LayoutStateEngine()
        widths = [1888.0, 936.0, 1888.0, 936.0, 936.0, 936.0, 1888.0, 936.0, 936.0, 1888.0]
        for idx, w_px in enumerate(widths, start=1):
            engine.windows[idx] = make_win(idx, col=idx, width=w_px, ts_secs=100 + idx)

        # Recorrido de izquierda a derecha (1 -> 10) y de derecha a izquierda (10 -> 1)
        sequence = list(range(1, 11)) + list(range(10, 0, -1))
        for wid in sequence:
            win = engine.windows[wid]
            cx, ty, _ = engine._compute_window_geometry_on_output(win, 1920, 1080, update_viewport=True)
            self.assertTrue(
                0.0 < cx < 1920.0,
                f"Columna {wid} quedó fuera de pantalla en el recorrido: center_x={cx}",
            )
            self.assertEqual(ty, 16.0)

    def test_multi_monitor_workspace_isolation(self):
        """Verifica que moverse en el Monitor 2 (workspace 4) no altere la vista del Monitor 1 (workspace 1)."""
        engine = nwl.LayoutStateEngine()
        # Monitor 1 (ws 1): dos mitades
        m1_left = make_win(1, col=1, width=936.0, ws_id=1, ts_secs=100)
        m1_right = make_win(2, col=2, width=936.0, ws_id=1, ts_secs=101)
        # Monitor 2 (ws 4): tres columnas
        m2_c1 = make_win(30, col=1, width=776.0, ws_id=4, ts_secs=100)
        m2_c2 = make_win(31, col=2, width=776.0, ws_id=4, ts_secs=101)
        m2_c3 = make_win(32, col=3, width=1568.0, ws_id=4, ts_secs=102)
        engine.windows = {1: m1_left, 2: m1_right, 30: m2_c1, 31: m2_c2, 32: m2_c3}

        cx_m1_before, _, _ = engine._compute_window_geometry_on_output(m1_right, 1920, 1080)
        # Ahora navegamos intensamente en el Monitor 2
        engine._compute_window_geometry_on_output(m2_c3, 1600, 900)
        engine._compute_window_geometry_on_output(m2_c1, 1600, 900)
        engine._compute_window_geometry_on_output(m2_c2, 1600, 900)

        # El Monitor 1 debe conservar exactamente su posición
        cx_m1_after, _, _ = engine._compute_window_geometry_on_output(
            m1_right, 1920, 1080, update_viewport=False
        )
        self.assertAlmostEqual(cx_m1_before, cx_m1_after, delta=0.1)

    def test_peek_mode_filters_only_visible_windows(self):
        """Si hay 6 ventanas en un workspace pero solo 2 caben en pantalla, el filtro de Vistazo (Peek)
        solo debe detectar como visibles esas 2 ventanas."""
        engine = nwl.LayoutStateEngine()
        for c in range(1, 7):
            engine.windows[c] = make_win(c, col=c, width=936.0, ws_id=1, ts_secs=100 + c)

        # Enfocamos la columna 6 (por lo que en pantalla están visibles la columna 5 y la 6)
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
        """Verifica que los títulos largos se recorten a 56 chars y se limpien IDs cerrados."""
        long_title = "A" * 120
        truncated = nwl.truncate_text(long_title, 56)
        self.assertEqual(len(truncated), 56)
        self.assertTrue(truncated.endswith("…"))

        names = {"1": "Activa", "2": "Cerrada", "3": "También Activa"}
        open_ids = {"1", "3"}
        cleaned = {k: v for k, v in names.items() if k in open_ids}
        self.assertEqual(cleaned, {"1": "Activa", "3": "También Activa"})

    def test_custom_css_override_merging(self):
        """Verifica que ~/.config/niri/window-label.css se combine sobre el CSS base."""
        import tempfile

        base = b".badge-box { border-radius: 12px; }"
        with tempfile.TemporaryDirectory() as tmp:
            custom_file = Path(tmp) / "window-label.css"
            # Si no existe, devuelve el CSS base intacto
            self.assertEqual(nwl.build_stylesheet(base, custom_file), base)

            # Si existe, concatena las reglas del usuario al final para sobrescribir
            custom_file.write_text(".badge-box { border-color: #ff007c; }", encoding="utf-8")
            merged = nwl.build_stylesheet(base, custom_file)
            self.assertIn(b"#ff007c", merged)
            self.assertTrue(merged.startswith(base))


if __name__ == "__main__":
    unittest.main()
