"""Command line entry point for {{ cookiecutter.project_name }}."""

from __future__ import annotations

import argparse

from . import __version__


def main(argv: list[str] | None = None) -> int:
    """Run the command line interface."""
    parser = argparse.ArgumentParser(prog="{{ cookiecutter.__project_slug }}")
    parser.add_argument("--version", action="version", version=__version__)
    parser.parse_args(argv)
    print("Hello from {{ cookiecutter.project_name }}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
