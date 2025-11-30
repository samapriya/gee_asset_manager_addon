"""
pytest configuration and shared fixtures for geeadd CLI tests
"""

import pytest
import os
import subprocess


# -----------------------------------------------------------
#  Register custom markers
# -----------------------------------------------------------
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with -m 'not slow')"
    )


# -----------------------------------------------------------
#  Slow test command-line option
# -----------------------------------------------------------
def pytest_addoption(parser):
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="run slow tests",
    )


def pytest_collection_modifyitems(config, items):
    """Automatically skip slow tests unless --run-slow is used."""
    if not config.getoption("--run-slow"):
        skip_slow = pytest.mark.skip(reason="need --run-slow to execute slow tests")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)


# -----------------------------------------------------------
#  Fixture: ee_initialized
#  Matches logic used in test_geead.py
# -----------------------------------------------------------
@pytest.fixture(scope="session")
def ee_initialized():
    """
    Initialize Earth Engine once per test session.

    Behavior defined to match test_geead.py:
    - On CI (GITHUB_ACTIONS), require CLOUD_SA to exist.
    - Locally, run `geeadd projects quota` to check authentication.
    - If authentication unavailable, skip the test.
    """
    # Running in CI (GitHub Actions)
    if os.environ.get("GITHUB_ACTIONS"):
        sa_json = os.environ.get("CLOUD_SA")
        if not sa_json:
            pytest.skip("No service account (CLOUD_SA) available in CI environment")
        return True

    # Local testing: check if EE auth works by running geeadd
    result = subprocess.run(
        ["geeadd", "projects", "quota"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        pytest.skip("Earth Engine not authenticated locally")

    return True
