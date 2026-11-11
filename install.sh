#!/usr/bin/env bash
set -euo pipefail

DEST_DIR="${HOME}/.local/bin"
mkdir -p "${DEST_DIR}"
install -Dm755 "$(dirname "$0")/niri-window-label" "${DEST_DIR}/niri-window-label"

echo "✓ Instalado en ${DEST_DIR}/niri-window-label"
echo "Para iniciar o reiniciar el servicio en niri ejecuta:"
echo "  niri-window-label restart"
