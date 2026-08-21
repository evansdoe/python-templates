"""Pytest configuration for template tests."""


def pytest_addoption(parser):
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="Run slow integration tests (uv sync inside generated projects)",
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: marks tests that run uv sync (deselect with '-m \"not slow\"')")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-slow"):
        skip_slow = __import__("pytest").mark.skip(reason="need --run-slow option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)
