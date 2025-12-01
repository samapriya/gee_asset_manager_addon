"""
Test suite for geeadd CLI tool using the fake ee module.
"""

import sys
from unittest.mock import MagicMock, Mock, patch

import pytest
from click.testing import CliRunner
# Now import geeadd components
from geeadd.geeadd import cli, epoch_convert_time, humansize

# Import fake_ee from conftest (already mocked in sys.modules)
from . import fake_ee


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_ee_initialize():
    """Mock Earth Engine initialization."""
    with patch.object(fake_ee, 'Initialize') as mock:
        yield mock


@pytest.fixture
def mock_session():
    """Mock AuthorizedSession."""
    with patch('geeadd.geeadd.AuthorizedSession') as mock:
        session = MagicMock()
        mock.return_value = session
        yield session


class TestUtilityFunctions:
    """Test utility functions."""

    def test_humansize_bytes(self):
        assert humansize(500) == "500 B"

    def test_humansize_kilobytes(self):
        assert humansize(2048) == "2 KB"

    def test_humansize_megabytes(self):
        assert humansize(5242880) == "5 MB"

    def test_humansize_gigabytes(self):
        assert humansize(3221225472) == "3 GB"

    def test_epoch_convert_time(self):
        # Test epoch timestamp conversion
        timestamp = 1609459200000  # 2021-01-01 00:00:00
        result = epoch_convert_time(timestamp)
        assert "2021-01-01" in result


class TestReadmeCommand:
    """Test the readme command."""

    def test_readme_command(self, runner, mock_ee_initialize):
        """Test opening documentation."""
        with patch('webbrowser.open', return_value=True) as mock_browser:
            result = runner.invoke(cli, ['readme'])
            assert result.exit_code == 0
            mock_browser.assert_called_once_with(
                "https://geeadd.geetools.xyz/", new=2
            )


class TestProjectsCommands:
    """Test project management commands."""

    def test_projects_enabled(self, runner, mock_ee_initialize):
        """Test listing enabled projects."""
        with patch('geeadd.geeadd.get_projects') as mock_get:
            result = runner.invoke(cli, ['projects', 'enabled'])
            assert result.exit_code == 0
            mock_get.assert_called_once()

    def test_projects_dashboard(self, runner, mock_ee_initialize):
        """Test dashboard generation."""
        with patch('geeadd.geeadd.get_projects_with_dashboard') as mock_dash:
            result = runner.invoke(cli, ['projects', 'dashboard'])
            assert result.exit_code == 0
            mock_dash.assert_called_once()

    def test_projects_quota_no_project(self, runner, mock_ee_initialize, mock_session):
        """Test quota display without specific project."""
        # Mock ee.data methods
        with patch.object(fake_ee.data, 'getAssetRoots', return_value=[]):
            with patch.object(fake_ee.data, 'getInfo', return_value=None):
                result = runner.invoke(cli, ['projects', 'quota'])
                assert result.exit_code == 0

    def test_projects_quota_specific(self, runner, mock_ee_initialize):
        """Test quota for specific project."""
        with patch.object(fake_ee.data, 'getInfo') as mock_info:
            mock_info.return_value = {
                'quota': {
                    'sizeBytes': '1000000',
                    'maxSizeBytes': '10000000',
                    'assetCount': '10',
                    'maxAssets': '100'
                }
            }
            result = runner.invoke(
                cli, ['projects', 'quota', '--project', 'projects/test']
            )
            assert result.exit_code == 0


class TestAssetsCommands:
    """Test asset management commands."""

    def test_assets_info(self, runner, mock_ee_initialize):
        """Test asset info display."""
        with patch('geeadd.geeadd.display_asset_info') as mock_display:
            result = runner.invoke(
                cli, ['assets', 'info', 'projects/test/assets/image']
            )
            assert result.exit_code == 0
            mock_display.assert_called_once_with('projects/test/assets/image')

    def test_assets_copy(self, runner, mock_ee_initialize):
        """Test asset copying."""
        with patch('geeadd.geeadd.copy') as mock_copy:
            result = runner.invoke(cli, [
                'assets', 'copy',
                '--initial', 'path/to/source',
                '--final', 'path/to/dest'
            ])
            assert result.exit_code == 0
            mock_copy.assert_called_once_with(
                path='path/to/source',
                fpath='path/to/dest'
            )

    def test_assets_move(self, runner, mock_ee_initialize):
        """Test asset moving."""
        with patch('geeadd.geeadd.mover') as mock_mover:
            result = runner.invoke(cli, [
                'assets', 'move',
                '--initial', 'path/to/source',
                '--final', 'path/to/dest'
            ])
            assert result.exit_code == 0
            mock_mover.assert_called_once()

    def test_assets_access(self, runner, mock_ee_initialize):
        """Test setting asset permissions."""
        with patch('geeadd.geeadd.access') as mock_access:
            result = runner.invoke(cli, [
                'assets', 'access',
                '--id', 'path/to/asset',
                '--user', 'user@example.com',
                '--role', 'reader'
            ])
            assert result.exit_code == 0
            mock_access.assert_called_once()

    def test_assets_delete(self, runner, mock_ee_initialize):
        """Test asset deletion."""
        with patch('geeadd.geeadd.delete') as mock_delete:
            result = runner.invoke(cli, [
                'assets', 'delete',
                '--id', 'path/to/asset'
            ])
            assert result.exit_code == 0
            mock_delete.assert_called_once()

    def test_assets_size_image(self, runner, mock_ee_initialize):
        """Test getting size of an image."""
        mock_asset_info = {'type': 'IMAGE'}

        with patch.object(fake_ee.data, 'getAsset', return_value=mock_asset_info):
            with patch('geeadd.geeadd.ee.ImageCollection') as mock_ic:
                mock_collection = MagicMock()
                mock_collection.aggregate_array.return_value.getInfo.return_value = [1000000]
                mock_ic.fromImages.return_value = mock_collection

                result = runner.invoke(cli, ['assets', 'size', 'path/to/image'])
                assert result.exit_code == 0
                assert 'IMAGE' in result.output or 'Image' in result.output


class TestTasksCommands:
    """Test task management commands."""

    def test_tasks_list_summary(self, runner, mock_ee_initialize):
        """Test listing task summary."""
        with patch.object(fake_ee.data, 'getTaskList') as mock_list:
            mock_list.return_value = [
                {'state': 'RUNNING'},
                {'state': 'READY'},
                {'state': 'COMPLETED'}
            ]
            result = runner.invoke(cli, ['tasks', 'list'])
            assert result.exit_code == 0
            assert 'Running' in result.output or 'RUNNING' in result.output

    def test_tasks_list_by_state(self, runner, mock_ee_initialize):
        """Test filtering tasks by state."""
        with patch.object(fake_ee.data, 'getTaskList') as mock_list:
            mock_list.return_value = [
                {
                    'id': 'task-1',
                    'state': 'COMPLETED',
                    'description': 'Test task',
                    'task_type': 'EXPORT_IMAGE',
                    'attempt': 1,
                    'start_timestamp_ms': 1609459200000,
                    'update_timestamp_ms': 1609462800000
                }
            ]
            result = runner.invoke(cli, ['tasks', 'list', '--state', 'COMPLETED'])
            assert result.exit_code == 0

    def test_tasks_cancel_all(self, runner, mock_ee_initialize):
        """Test cancelling all tasks."""
        with patch.object(fake_ee.data, 'getTaskList') as mock_list:
            with patch.object(fake_ee.data, 'cancelTask') as mock_cancel:
                mock_list.return_value = [
                    {'id': 'task-1', 'state': 'RUNNING'},
                    {'id': 'task-2', 'state': 'READY'}
                ]
                result = runner.invoke(cli, ['tasks', 'cancel', 'all'])
                assert result.exit_code == 0
                assert mock_cancel.call_count == 2

    def test_tasks_cancel_specific(self, runner, mock_ee_initialize):
        """Test cancelling specific task."""
        with patch.object(fake_ee.data, 'getTaskStatus') as mock_status:
            with patch.object(fake_ee.data, 'cancelTask') as mock_cancel:
                mock_status.return_value = [{'state': 'RUNNING'}]
                result = runner.invoke(cli, ['tasks', 'cancel', 'task-123'])
                assert result.exit_code == 0
                mock_cancel.assert_called_once_with('task-123')


class TestUtilsCommands:
    """Test utility commands."""

    def test_utils_app2script(self, runner, mock_ee_initialize):
        """Test extracting script from app."""
        with patch('geeadd.geeadd.jsext') as mock_jsext:
            result = runner.invoke(cli, [
                'utils', 'app2script',
                '--url', 'https://example.earthengine.app/view/test'
            ])
            assert result.exit_code == 0
            mock_jsext.assert_called_once()

    def test_utils_search(self, runner, mock_ee_initialize):
        """Test GEE catalog search."""
        with patch('geeadd.geeadd.EnhancedGEESearch') as mock_search_class:
            mock_search = MagicMock()
            mock_search.search.return_value = []
            mock_search_class.return_value = mock_search

            result = runner.invoke(cli, [
                'utils', 'search',
                '--keywords', 'landsat'
            ])
            assert result.exit_code == 0

    def test_utils_report(self, runner, mock_ee_initialize):
        """Test generating asset report."""
        with patch('geeadd.geeadd.ee_report') as mock_report:
            result = runner.invoke(cli, [
                'utils', 'report',
                '--outfile', 'report.csv'
            ])
            assert result.exit_code == 0
            mock_report.assert_called_once()

    def test_utils_palette_list(self, runner, mock_ee_initialize):
        """Test listing color palettes."""
        with patch('geeadd.geeadd.load_palettes', return_value={}):
            with patch('geeadd.geeadd.list_color_palettes') as mock_list:
                result = runner.invoke(cli, ['utils', 'palette', '--list'])
                assert result.exit_code == 0
                mock_list.assert_called_once()

    def test_utils_palette_generate(self, runner, mock_ee_initialize):
        """Test generating a palette."""
        with patch('geeadd.geeadd.generate_palette') as mock_gen:
            result = runner.invoke(cli, [
                'utils', 'palette',
                '--name', 'Blues',
                '--classes', '5'
            ])
            assert result.exit_code == 0
            mock_gen.assert_called_once()


class TestDeprecatedCommands:
    """Test deprecated command redirects."""

    def test_deprecated_quota(self, runner, mock_ee_initialize):
        """Test deprecated quota command."""
        with patch.object(fake_ee.data, 'getAssetRoots', return_value=[]):
            result = runner.invoke(cli, ['quota'])
            assert result.exit_code == 0
            assert 'deprecated' in result.output.lower()

    def test_deprecated_copy(self, runner, mock_ee_initialize):
        """Test deprecated copy command."""
        with patch('geeadd.geeadd.copy') as mock_copy:
            result = runner.invoke(cli, [
                'copy',
                '--initial', 'source',
                '--final', 'dest'
            ])
            assert result.exit_code == 0
            assert 'deprecated' in result.output.lower()
            mock_copy.assert_called_once()

    def test_deprecated_delete(self, runner, mock_ee_initialize):
        """Test deprecated delete command."""
        with patch('geeadd.geeadd.delete') as mock_delete:
            result = runner.invoke(cli, [
                'delete',
                '--id', 'asset-path'
            ])
            assert result.exit_code == 0
            assert 'deprecated' in result.output.lower()


class TestIntegration:
    """Integration tests using fake ee module."""

    def test_full_workflow_with_fake_ee(self, runner, mock_ee_initialize):
        """Test a complete workflow using the fake ee module."""
        # Test that Image operations work
        img = fake_ee.Image.constant(0)
        bands = img.bandNames()
        assert bands.getInfo() == ["B1", "B2"]

        # Test Geometry operations
        geom = fake_ee.Geometry.Point([0, 0])
        assert geom.type().value == "Point"

        # Test FeatureCollection
        fc = fake_ee.FeatureCollection([])
        img_from_fc = fc.style()
        assert isinstance(img_from_fc, fake_ee.Image)

    def test_error_handling(self, runner, mock_ee_initialize):
        """Test error handling in commands."""
        # Test missing required options
        result = runner.invoke(cli, ['assets', 'copy'])
        assert result.exit_code != 0

        # Test invalid choices
        result = runner.invoke(cli, [
            'assets', 'access',
            '--asset', 'test',
            '--user', 'user@test.com',
            '--role', 'invalid'
        ])
        assert result.exit_code != 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
