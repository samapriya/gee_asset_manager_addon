"""
Pytest configuration for geeadd tests.
"""

import pytest
import sys
import os
from unittest.mock import Mock, MagicMock, patch

# Import fake_ee from the same directory
from . import fake_ee

# Mock ee module before geeadd imports
sys.modules['ee'] = fake_ee

# Mock other dependencies that might not be installed
mock_box = MagicMock()
mock_box.Box = dict
sys.modules['box'] = mock_box


@pytest.fixture(scope='session', autouse=True)
def setup_environment():
    """Set up test environment."""
    # Ensure ee is mocked
    if 'ee' not in sys.modules:
        sys.modules['ee'] = fake_ee
    
    yield
    
    # Cleanup
    pass


@pytest.fixture
def runner():
    """Create a Click CLI test runner."""
    from click.testing import CliRunner
    return CliRunner()


@pytest.fixture
def mock_ee_initialize():
    """Mock Earth Engine initialization."""
    with patch.object(fake_ee, 'Initialize') as mock:
        yield mock


@pytest.fixture
def mock_session():
    """Mock AuthorizedSession."""
    session = MagicMock()
    session.get.return_value.json.return_value = {
        'assets': [],
        'quota': {
            'sizeBytes': '5000000000',
            'maxSizeBytes': '10000000000',
            'assetCount': '50',
            'maxAssets': '1000'
        }
    }
    return session


@pytest.fixture
def sample_task_list():
    """Sample task list for testing."""
    return [
        {
            'id': 'TASK001',
            'state': 'RUNNING',
            'description': 'Export Image Task',
            'task_type': 'EXPORT_IMAGE',
            'attempt': 1,
            'start_timestamp_ms': 1609459200000,
            'update_timestamp_ms': 1609462800000,
            'destination_uris': ['https://code.earthengine.google.com/?asset=projects/test/image'],
            'batch_eecu_usage_seconds': 120.5
        },
        {
            'id': 'TASK002',
            'state': 'READY',
            'description': 'Export Table Task',
            'task_type': 'EXPORT_TABLE',
            'attempt': 1,
            'start_timestamp_ms': 1609459200000,
            'update_timestamp_ms': 1609459300000,
        },
    ]
