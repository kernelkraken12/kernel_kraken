#!/usr/bin/env bash
# install.sh — the EASY, distro-agnostic installer for protondbcli.
#
# Works on EVERY Linux distro: Fedora, Ubuntu/Debian, Arch, CachyOS,
# openSUSE, NixOS (non-Nix path), Alpine... — anything with Python 3.9+.
# No sudo, no package manager, no hard-coded root paths (ground rules #1/#2).
#
# Installs the `proton` command into ~/.local/bin (already on most PATHs)
# and the library into ~/.local/lib/protondbcli/.
#
# Usage:
#   curl -fsSL <URL> | bash
#   bash install.sh
#   bash install.sh --prefix ~/custom/bin

set -euo pipefail

# --- the config (XDG-compliant) ---
PREFIX="${1:-$HOME/.local}"
BIN_DIR="$PREFIX/bin"
LIB_DIR="$PREFIX/lib/protondbcli"

echo "🐧 Installing protondbcli (the kernel kraken's game checker)..."

# --- 1. python check (the only real requirement) ---
if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1 && python --version 2>&1 | grep -q "3\."; then
  PY=python
else
  echo "✗ Python 3 is required but was not found." >&2
  echo "  Install Python 3 first (any distro: 'dnf install python3', 'apt install python3', 'pacman -S python', ...)." >&2
  exit 1
fi

# python version check (3.10+ — the code uses the modern X | None syntax)
PY_MAJOR=$("$PY" -c 'import sys; print(sys.version_info.major)')
PY_MINOR=$("$PY" -c 'import sys; print(sys.version_info.minor)')
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
  echo "✗ Python 3.10+ is required (found $("$PY" --version 2>&1))." >&2
  exit 1
fi

# --- 2. copy the package (no root needed) ---
mkdir -p "$BIN_DIR" "$LIB_DIR"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/src/protondbcli"
if [ ! -d "$SRC_DIR" ]; then
  echo "✗ package source not found at $SRC_DIR — run install.sh from the project root." >&2
  exit 1
fi
cp -r "$SRC_DIR"/* "$LIB_DIR/"

# --- 3. the launcher script ---
cat > "$BIN_DIR/proton" <<EOF
#!/usr/bin/env bash
# protondbcli launcher — runs the installed package with the system python.
# PYTHONPATH must be the PARENT of the package dir (import protondbcli).
PYTHONPATH="$(dirname "$LIB_DIR")" exec "$PY" -m protondbcli "\$@"
EOF
chmod +x "$BIN_DIR/proton"

# --- 4. the cache dir (XDG) ---
CACHE_BASE="${XDG_CACHE_HOME:-$HOME/.cache}"
mkdir -p "$CACHE_BASE/protondbcli"

# --- 5. the PATH hint ---
if ! echo ":$PATH:" | grep -q ":$BIN_DIR:"; then
  echo ""
  echo "ℹ️  $BIN_DIR is not on your PATH yet. Add it with one of:"
  echo "    echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc && source ~/.bashrc"
  echo "    (or the equivalent for your shell: ~/.zshrc / ~/.profile / fish)"
fi

echo ""
echo "✅ protondbcli installed!"
echo "   Try it:  proton cairn"
echo "   Help:    proton --help"
echo "   Fresh:   proton cairn --fresh"
