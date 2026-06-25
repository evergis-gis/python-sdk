# -*- coding: utf-8 -*-
"""CLI: ``python -m evergis_tutorial_setup themes <names> [--force]``"""

from __future__ import annotations

import argparse
import sys

from ._runner import setup


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m evergis_tutorial_setup",
        description="Provision tutorial demo data in an EverGIS instance.",
    )
    sub = parser.add_subparsers(dest="step", required=True)

    p_themes = sub.add_parser("themes", help="Set up one or more themes.")
    p_themes.add_argument(
        "names", nargs="+",
        help="Theme names (e.g. 'shared features layers') or 'all'.",
    )
    p_themes.add_argument(
        "--force", action="store_true",
        help="Re-create seed layers and overwrite existing mirrored files.",
    )

    args = parser.parse_args(argv)
    if args.step == "themes":
        setup(themes=args.names, force=args.force)
    return 0


if __name__ == "__main__":
    sys.exit(main())
