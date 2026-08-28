"""Allow `python3 -m protondbcli` to work as well as the `proton` command."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
