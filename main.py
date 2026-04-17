from __future__ import annotations

import argparse

from snake_game.app import main as gui_main
from snake_game.terminal_app import main as terminal_main


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Python snake game.")
    parser.add_argument(
        "--mode",
        choices=("terminal", "gui"),
        default="terminal",
        help="Choose the runtime mode. Default is terminal for maximum compatibility.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.mode == "gui":
        gui_main()
    else:
        terminal_main()


if __name__ == "__main__":
    main()
