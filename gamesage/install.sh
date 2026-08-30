#!/bin/bash
# gamesage installer — no sudo, works on every distro with Python 3.10+.
# Installs to ~/.local (XDG) and adds the PATH hint if needed.
set -e

LIB="$HOME/.local/lib/gamesage"
BIN="$HOME/.local/bin"
SRC="$(cd "$(dirname "$0")" && pwd)"

echo "🐧 Installing gamesage to $LIB"

mkdir -p "$LIB" "$BIN"
cp -r "$SRC/gamesage" "$LIB/"

cat > "$BIN/gamesage" << 'LAUNCHER'
#!/bin/sh
export PYTHONPATH="$HOME/.local/lib"
exec python3 -m gamesage "$@"
LAUNCHER
chmod +x "$BIN/gamesage"

case ":$PATH:" in
  *":$BIN:"*) : ;;
  *) echo "  ℹ Add to your PATH:  export PATH=\"\$HOME/.local/bin:\$PATH\"" ;;
esac

echo "✅ gamesage installed! Try:"
echo "   gamesage start \"Cairn\"   # before you play"
echo "   gamesage end              # after you finish — the report saves itself!"
