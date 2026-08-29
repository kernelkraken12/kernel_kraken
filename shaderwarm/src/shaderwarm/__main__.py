"""Allow `python3 -m shaderwarm` as well as the `shaderwarm` command."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
