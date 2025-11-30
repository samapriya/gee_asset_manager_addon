"""
pytest configuration and shared fixtures
"""

import pytest
import os


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle CI environment"""
    # Skip tests requiring EE if not in CI and no credentials
    skip_ee = pytest.mark.skip(reason="Earth Engine credentials not available")
    
    for item in items:
        # Check if test needs EE initialization
        if "ee_initialized" in item.fixturenames:
            # In CI, we have credentials via CLOUD_SA
            if not os.environ.get('GITHUB_ACTIONS'):
                # Local testing - skip if EE not initialized
                try:
                    import ee
                    ee.Initialize(opt_url='https://earthengine-highvolume.googleapis.com')
                except:
                    item.add_marker(skip_ee)


def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="run slow tests"
    )
