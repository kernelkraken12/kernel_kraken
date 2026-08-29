#!/usr/bin/env bash
# install.sh — the EASY, distro-agnostic installer for shaderwarm.
#
# Works on EVERY Linux distro with Python 3.10+. No sudo, no package
# manager, no hard-coded root paths (ground rules #1/#2). Installs the
# `shaderwarm` command into ~/.local/bin and the library into
# ~/.local/lib/shaderwarm/.

set -euo pipefail

PREFIX="${1:-$HOME/.local}"
BIN_DIR="$PREFIX/bin"
LIB_DIR="$PREFIX/lib/shaderwarm"

echo "🐧 Installing shaderwarm (the kernel kraken's shader cache keeper)..."

# --- 1. python check (the only real requirement) ---
if command -v python3 >/dev/null 2>&1; then
  PY=python3
else
  echo "✗ Python 3 is required but was not found." >&2
  exit 1
fi
PY_MAJOR=$("$PY" -c 'import sys; print(sys.version_info.major)')
PY_MINOR=$("$PY" -c 'import sys; print(sys.version_info.minor)')
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
  echo "✗ Python 3.10+ is required (found $("$PY" --version 2>&1))." >&2
  exit 1
fi

# --- 2. copy the package (no root needed) ---
mkdir -p "$BIN_DIR" "$LIB_DIR"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/src/shaderwarm"
if [ ! -d "$SRC_DIR" ]; then
  echo "✗ package source not found at $SRC_DIR — run install.sh from the project root." >&2
  exit 1
fi
cp -r "$SRC_DIR"/* "$LIB_DIR/"

# --- 3. the launcher (PYTHONPATH = the PARENT of the package dir!) ---
cat > "$BIN_DIR/shaderwarm" <<EOF
#!/usr/bin/env bash
PYTHONPATH="$(dirname "$LIB_DIR")" exec "$PY" -m shaderwarm "\$@"
EOF
chmod +x "$BIN_DIR/shaderwarm"

# --- 4. the backups dir (XDG) ---
DATA_BASE="${XDG_DATA_HOME:-$HOME/.local/share}"
mkdir -p "$DATA_BASE/shaderwarm/backups"

# --- 5. the PATH hint ---
if ! echo ":$PATH:" | grep -q ":$BIN_DIR:"; then
  echo ""
  echo "ℹ️  $BIN_DIR is not on your PATH yet. Add it with one of:"
  echo "    echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc && source ~/.bashrc"
  echo "    (or the equivalent for your shell: ~/.zshrc / ~/.profile / fish)"
fi

echo ""
echo "✅ shaderwarm installed!"
echo "   Try it:  shaderwarm scan"
echo "   Help:    shaderwarm --help"
echo "   Warm:    shaderwarm warm <game> --watch"
