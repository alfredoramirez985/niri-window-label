# niri-window-label 🏷️

Minimalist floating window label & custom window renamer for the **[niri](https://github.com/YaLTeR/niri)** Wayland compositor.

When working with many columns in niri's scrollable strip (especially multiple terminals), it is easy to lose track of which window is which. **`niri-window-label`** solves this without modifying or recompiling niri:

- **Minimalist Hover / Focus Badge:** Shows a sleek, click-through Wayland Layer-Shell pill centered at the top of the active window (even on half-screen or stacked windows) when you hover over it or focus it.
- **Smart Auto-Naming by Project Folder:** If a terminal doesn't have a custom name yet, automatically prefixes its title with the current project directory name (e.g., `VoiceApp  •  npm start` instead of just `npm start`).
- **Peek All Visible Windows (`Super + Alt + N`):** Displays the minimalist badge simultaneously over **all currently visible windows across all monitors** at once for a quick overview.
- **Multi-Monitor Ready:** Automatically appears on the exact monitor (`LVDS`, `VGA`, `HDMI`, `DP`, `eDP`) where the focused window lives.
- **Custom Window Names (`Super + N`):** Rename any open window on the fly via a native GTK Layer-Shell input popup. Custom-named windows are highlighted in gold.
- **`Alt + Tab` with a Master Strip:** A replacement for niri's switcher with the column strip of the selected window's workspace on top (it follows your selection, even across monitors), a to-scale mini-map of your monitors numbered left to right, and a most-recently-used window list. Fully themable via CSS.
- **Terminal Title Sync:** Automatically updates the Wayland title (`OSC 2`) of terminal windows (`kitty`, `Alacritty`, `foot`, `wezterm`, etc.) to your custom name, so it shows up in any window list.
- **Quick Window Switcher (`Super + Shift + N`):** Jump to any window by its custom name using `rofi`.

---

## 📦 Dependencies

- `niri`
- `python3` + `python-gobject` (`PyGObject`) + `python-cairo`
- `gtk3` + `gtk-layer-shell`
- *(Optional)* `rofi` (for `niri-window-label switcher`)

On **Arch Linux / CachyOS**:
```bash
sudo pacman -S python python-gobject python-cairo gtk3 gtk-layer-shell
```

---

## 🚀 Installation

```bash
git clone https://github.com/alfredoramirez985/niri-window-label.git
cd niri-window-label
./install.sh
```

Or copy `niri-window-label` directly to `~/.local/bin/`:
```bash
install -Dm755 niri-window-label ~/.local/bin/niri-window-label
```

---

## ⚙️ Niri Configuration (`~/.config/niri/config.kdl`)

1. Enable `focus-follows-mouse` inside your `input` block so hovering over any visible window triggers the label without scrolling the strip:
```kdl
input {
    focus-follows-mouse max-scroll-amount="0%"
}
```

2. Start the daemon automatically with niri:
```kdl
spawn-sh-at-startup "~/.local/bin/niri-window-label daemon"
```

3. *(Optional)* Replace niri's `Alt + Tab` with the master-strip switcher. Turn off the built-in one and bind the keys (inside `binds`):
```kdl
recent-windows {
    off
}

binds {
    Alt+Tab repeat=false { spawn "~/.local/bin/niri-window-label" "alt-tab"; }
    Alt+Shift+Tab repeat=false { spawn "~/.local/bin/niri-window-label" "alt-tab" "--reverse"; }
}
```
Hold `Alt` and press `Tab` to move, release `Alt` (or press `Enter` / click a row) to switch, `Esc` to cancel.

4. Add keybindings inside your `binds` block:
```kdl
binds {
    Mod+N hotkey-overlay-title="Rename Focused Window" { spawn "~/.local/bin/niri-window-label" "rename"; }
    Mod+Shift+N hotkey-overlay-title="Find Window by Custom Name" { spawn "~/.local/bin/niri-window-label" "switcher"; }
    Mod+Alt+N hotkey-overlay-title="Peek All Visible Windows" { spawn "~/.local/bin/niri-window-label" "peek"; }
}
```

---

## 🎨 Custom Styling (`~/.config/niri/window-label.css`)

Your `~/.config/niri/window-label.css` is loaded **after** the built-in stylesheet, so it only needs the rules you want to change. Start from [`window-label.example.css`](window-label.example.css), which documents every class:

```bash
cp window-label.example.css ~/.config/niri/window-label.css
niri-window-label css        # print the full built-in stylesheet for reference
```

**Matching your theme:** all colors come from a small palette of named colors, so usually you only need to redefine a few of them:

```css
@define-color nwl_accent #cba6f7;
@define-color nwl_focus  #89dceb;
@define-color nwl_bg     rgba(30, 30, 46, 0.96);
```

| Color | Used for |
|---|---|
| `nwl_bg`, `nwl_border` | Panel background and border |
| `nwl_accent` | Header, active monitor, selected row |
| `nwl_focus` | Selected column in the strip, counter |
| `nwl_text`, `nwl_text_dim`, `nwl_text_bright` | Main text, unselected rows, selected row |
| `nwl_muted` | Off-screen columns, meta text, hints |
| `nwl_custom`, `nwl_custom_focus` | Windows renamed with `Super + N` |
| `nwl_selected_bg`, `nwl_monitor_bg`, `nwl_monitor_on` | Derived backgrounds (follow `nwl_accent` / `nwl_muted`) |

The `Alt + Tab` switcher re-reads the file every time it opens, so a theme-switch script can rewrite it and the next `Alt + Tab` already uses the new colors. Badges pick up changes after `niri-window-label restart`.

**HyDE integration (automatic theme colors):** if you use [HyDE](https://github.com/HyDE-Project/HyDE), install the wallbash template and every theme / wallpaper change regenerates `~/.config/niri/window-label.theme.css` with the theme's colors:

```bash
cp hyde/niri-window-label.dcol ~/.config/hyde/wallbash/always/
~/.local/lib/hyde/color.set.sh --single ~/.config/hyde/wallbash/always/niri-window-label.dcol  # first time only
```

Load order is: built-in defaults → `window-label.theme.css` (generated) → `window-label.css` (yours, always wins). The generated file is picked up live, no restart needed.

**Monitor names:** the switcher shows the built-in panel as "Laptop" and other monitors by model. To use your own names, create `~/.config/niri/monitor-names.json`:

```json
{ "LVDS-1": "Main", "VGA-1": "Side" }
```

---

## 🛠️ CLI Usage

```bash
niri-window-label daemon     # Run the overlay listener daemon
niri-window-label restart    # Restart the background daemon in niri
niri-window-label rename     # Open the GTK Layer-Shell popup to rename the focused window
niri-window-label switcher   # Open the rofi window switcher sorted by custom names
niri-window-label peek       # Show badges over ALL currently visible windows across all monitors
niri-window-label show       # Show the badge for the currently focused window on demand
niri-window-label alt-tab    # Open / advance the Alt+Tab switcher (--reverse to go back)
niri-window-label css        # Print the built-in stylesheet
```

---

## 🇪🇸 Español

Identificador minimalista de ventanas y renombrador para el compositor Wayland **niri**.

- **Cartel minimalista al pasar el mouse:** Muestra únicamente el nombre personalizado (en dorado) o el título por defecto de la ventana, centrado sobre la ventana activa y con soporte completo para múltiples monitores y ventanas de media pantalla.
- **Renombrado rápido (`Super + N`):** Abre un cuadro nativo para asignar un nuevo nombre a la ventana actual (dejar vacío y presionar Enter restaura el nombre original).
- **`Alt + Tab` con cinta maestra:** Reemplaza el selector de niri: arriba la cinta de columnas del escritorio de la ventana seleccionada (se mueve con tu selección, incluso entre monitores), un mini-mapa a escala de tus monitores numerados de izquierda a derecha y la lista de ventanas por uso reciente. Ver la configuración en el paso 3.
- **Personalizable con tu tema:** Copia `window-label.example.css` a `~/.config/niri/window-label.css` y redefine los colores de la paleta (`@define-color nwl_accent …`). El `Alt + Tab` toma los cambios la siguiente vez que lo abres, sin reiniciar. `niri-window-label css` muestra todos los estilos por defecto.
- **Integración con HyDE:** copia `hyde/niri-window-label.dcol` a `~/.config/hyde/wallbash/always/` y cada cambio de tema o fondo genera `~/.config/niri/window-label.theme.css` con los colores del tema. Tu `window-label.css` se carga después y siempre gana.
- **Nombres de monitores:** Opcional, en `~/.config/niri/monitor-names.json` (por ejemplo `{ "LVDS-1": "Principal", "VGA-1": "Lateral" }`).
- **Sincronización de títulos de terminales:** Actualiza automáticamente el título de tus terminales con tu nombre personalizado.

## 📄 License

GPL-3.0
