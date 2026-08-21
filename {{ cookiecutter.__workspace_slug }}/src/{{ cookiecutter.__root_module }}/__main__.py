"""Entry point for {{ cookiecutter.workspace_name }}.

Compose the workspace members here. A member becomes importable once it is
listed in the root `dependencies` *and* in `[tool.uv.sources]`:

    dependencies = ["geo-core"]

    [tool.uv.sources]
    geo-core = { workspace = true }
"""

from __future__ import annotations

import argparse

from . import __version__


def main(argv: list[str] | None = None) -> int:
    """Run the command line interface."""
    parser = argparse.ArgumentParser(prog="{{ cookiecutter.__workspace_slug }}")
    parser.add_argument("--version", action="version", version=__version__)
    parser.parse_args(argv)
    print("Hello from {{ cookiecutter.workspace_name }}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
