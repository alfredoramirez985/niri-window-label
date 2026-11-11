# niri-window-label 🏷️

Minimalist floating window label & custom window renamer for the **[niri](https://github.com/YaLTeR/niri)** Wayland compositor.

When working with many columns in niri's scrollable strip (especially multiple terminals), it is easy to lose track of which window is which. **`niri-window-label`** solves this without modifying or recompiling niri:

- **Minimalist Hover / Focus Badge:** Shows a sleek, click-through Wayland Layer-Shell pill centered at the top of the active window (even on half-screen or stacked windows) when you hover over it or focus it.
- **Smart Auto-Naming by Project Folder:** If a terminal doesn't have a custom name yet, automatically prefixes its title with the current project directory name (e.g., `VoiceApp  •  npm start` instead of just `npm start`).
- **Peek All Visible Windows (`Super + Alt + N`):** Displays the minimalist badge simultaneously over **all currently visible windows across all monitors** at once for a quick overview.
- **Multi-Monitor Ready:** Automatically appears on the exact monitor (`LVDS`, `VGA`, `HDMI`, `DP`, `eDP`) where the focused window lives.
- **Custom Window Names (`Super + N`):** Rename any open window on the fly via a native GTK Layer-Shell input popup. Custom-named windows are highlighted in gold.
- **Native `Alt + Tab` Title Sync:** Automatically updates the Wayland title (`OSC 2`) of terminal windows (`kitty`, `Alacritty`, `foot`, `wezterm`, etc.) so your custom name also appears directly underneath the window preview in niri's built-in `Alt + Tab` switcher.
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

3. Add keybindings inside your `binds` block:
```kdl
binds {
    Mod+N hotkey-overlay-title="Rename Focused Window" { spawn "~/.local/bin/niri-window-label" "rename"; }
    Mod+Shift+N hotkey-overlay-title="Find Window by Custom Name" { spawn "~/.local/bin/niri-window-label" "switcher"; }
    Mod+Alt+N hotkey-overlay-title="Peek All Visible Windows" { spawn "~/.local/bin/niri-window-label" "peek"; }
}
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
```

---

## 🇪🇸 Español

Identificador minimalista de ventanas y renombrador para el compositor Wayland **niri**.

- **Cartel minimalista al pasar el mouse:** Muestra únicamente el nombre personalizado (en dorado) o el título por defecto de la ventana, centrado sobre la ventana activa y con soporte completo para múltiples monitores y ventanas de media pantalla.
- **Renombrado rápido (`Super + N`):** Abre un cuadro nativo para asignar un nuevo nombre a la ventana actual (dejar vacío y presionar Enter restaura el nombre original).
- **Sincronización con `Alt + Tab`:** Actualiza automáticamente el título de tus terminales para que al presionar `Alt + Tab` aparezca tu nombre personalizado debajo de la ventana.

## 📄 License

GPL-3.0
