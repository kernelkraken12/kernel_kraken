"""Tux ASCII art + the banner. The canonical community-recognized Tux."""

# The canonical Tux (v2 — the accurate Linux mascot the family picked)
TUX_V2 = r"""
      .--.
     |o_o |
     |:_/ |
    //   \ \
   (|     | )
  /'\_   _/`\
  \___)=(___/
"""

# The colorized variant (ANSI) — orange beak, yellow feet, white belly
TUX_V2_COLOR = (
    "\x1b[37m      .--.\x1b[0m\n"
    "\x1b[37m     |\x1b[0m\x1b[33mo_o\x1b[0m\x1b[37m |\x1b[0m\n"
    "\x1b[37m     |:\x1b[0m\x1b[33m_\x1b[0m\x1b[37m/ |\x1b[0m\n"
    "\x1b[37m    //   \\ \\\x1b[0m\n"
    "\x1b[37m   (|\x1b[0m\x1b[37m     | )\x1b[0m\n"
    "\x1b[37m  /'\\_\x1b[0m\x1b[37m   _/`\\\x1b[0m\n"
    "\x1b[37m  \\___\x1b[0m\x1b[33m)=(\x1b[0m\x1b[37m___/\x1b[0m\n"
)

TAGLINE = "TUX APPROVES: WILL IT RUN ON LINUX?"


def tux_banner(color: bool = True) -> str:
    """Return the Tux banner (colorized if the terminal supports it)."""
    art = TUX_V2_COLOR if color else TUX_V2
    return art + "  " + TAGLINE + "\n"
