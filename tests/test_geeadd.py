"""
Comprehensive tests for geeadd CLI commands
Tests actual Earth Engine functionality using service account authentication
"""

import pytest
import json
import os
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
import ee

# Import the CLI app
from geeadd import cli


@pytest.fixture(scope="session")
def ee_initialized():
    """Initialize Earth Engine once for all tests"""
    # Check if running in CI with service account
    if os.environ.get('GITHUB_ACTIONS'):
        sa_json = os.environ.get('CLOUD_SA')
        if sa_json:
            # Parse the service account JSON
            sa_dict = json.loads(sa_json)
            service_account_email = sa_dict['client_email']
            
            # Create credentials from service account info
            credentials = ee.ServiceAccountCredentials(
                service_account_email, 
                key_data=sa_json
            )
            ee.Initialize(credentials, opt_url='https://earthengine-highvolume.googleapis.com')
        else:
            pytest.skip("No service account credentials available")
    else:
        # For local testing, try to use default credentials
        try:
            ee.Initialize(opt_url='https://earthengine-highvolume.googleapis.com')
        except Exception as e:
            pytest.skip(f"Earth Engine initialization failed: {e}")
    
    return True


@pytest.fixture
def runner():
    """Click CLI test runner"""
    return CliRunner()


class TestCLIBasics:
    """Test basic CLI functionality"""
    
    def test_version(self, runner):
        """Test version command"""
        result = runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert 'geeadd' in result.output.lower()
    
    def test_help(self, runner):
        """Test help command"""
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'Google Earth Engine' in result.output
        assert 'projects' in result.output
        assert 'assets' in result.output
        assert 'tasks' in result.output
        assert 'utils' in result.output
    
    def test_readme_command(self, runner):
        """Test readme command"""
        with patch('webbrowser.open') as mock_open:
            mock_open.return_value = True
            result = runner.invoke(cli, ['readme'])
            assert result.exit_code == 0


class TestProjectsGroup:
    """Test projects group commands"""
    
    def test_projects_help(self, runner):
        """Test projects help"""
        result = runner.invoke(cli, ['projects', '--help'])
        assert result.exit_code == 0
        assert 'enabled' in result.output
        assert 'dashboard' in result.output
        assert 'quota' in result.output
    
    def test_projects_enabled(self, runner, ee_initialized):
        """Test listing enabled projects"""
        result = runner.invoke(cli, ['projects', 'enabled'])
        # Should complete without error
        assert result.exit_code == 0
    
    def test_projects_quota_no_args(self, runner, ee_initialized):
        """Test quota without specific project"""
        result = runner.invoke(cli, ['projects', 'quota'])
        # Should complete without error
        assert result.exit_code == 0
    
    def test_projects_dashboard(self, runner, ee_initialized, tmp_path):
        """Test dashboard generation"""
        outdir = tmp_path / "dashboard.html"
        result = runner.invoke(cli, ['projects', 'dashboard', '--outdir', str(outdir)])
        # Should complete without error
        assert result.exit_code == 0


class TestAssetsGroup:
    """Test assets group commands"""
    
    def test_assets_help(self, runner):
        """Test assets help"""
        result = runner.invoke(cli, ['assets', '--help'])
        assert result.exit_code == 0
        assert 'copy' in result.output
        assert 'move' in result.output
        assert 'delete' in result.output
        assert 'access' in result.output
        assert 'size' in result.output
    
    def test_assets_info_public_asset(self, runner, ee_initialized):
        """Test asset info on a public dataset"""
        result = runner.invoke(cli, [
            'assets', 'info', 
            'LANDSAT/LC08/C02/T1_L2/LC08_044034_20140318'
        ])
        # Should complete without error
        assert result.exit_code == 0
    
    def test_assets_size_public_collection(self, runner, ee_initialized):
        """Test size calculation on a small public collection"""
        # Use a small collection to avoid timeout
        result = runner.invoke(cli, [
            'assets', 'size',
            'LANDSAT/LC08/C02/T1_L2/LC08_044034_20140318'
        ])
        # Should complete without error (or handle gracefully)
        assert result.exit_code in [0, 1]  # May fail if no access, but shouldn't crash


class TestTasksGroup:
    """Test tasks group commands"""
    
    def test_tasks_help(self, runner):
        """Test tasks help"""
        result = runner.invoke(cli, ['tasks', '--help'])
        assert result.exit_code == 0
        assert 'list' in result.output
        assert 'cancel' in result.output
    
    def test_tasks_list_summary(self, runner, ee_initialized):
        """Test task list summary"""
        result = runner.invoke(cli, ['tasks', 'list'])
        # Should complete without error
        assert result.exit_code == 0
    
    def test_tasks_list_by_state(self, runner, ee_initialized):
        """Test task list filtered by state"""
        result = runner.invoke(cli, ['tasks', 'list', '--state', 'COMPLETED'])
        # Should complete without error
        assert result.exit_code == 0


class TestUtilsGroup:
    """Test utils group commands"""
    
    def test_utils_help(self, runner):
        """Test utils help"""
        result = runner.invoke(cli, ['utils', '--help'])
        assert result.exit_code == 0
        assert 'search' in result.output
        assert 'app2script' in result.output
        assert 'report' in result.output
        assert 'palette' in result.output
    
    def test_utils_search(self, runner, ee_initialized):
        """Test catalog search"""
        result = runner.invoke(cli, [
            'utils', 'search',
            '--keywords', 'Landsat',
            '--max-results', '3'
        ])
        # Should complete without error
        assert result.exit_code == 0
        # Should return JSON results
        assert '[' in result.output or 'No results' in result.output
    
    def test_utils_palette_list(self, runner):
        """Test palette list"""
        result = runner.invoke(cli, ['utils', 'palette', '--list'])
        assert result.exit_code == 0
        assert 'Blues' in result.output or 'Sequential' in result.output
    
    def test_utils_palette_generate(self, runner):
        """Test palette generation"""
        result = runner.invoke(cli, [
            'utils', 'palette',
            '--name', 'Blues',
            '--classes', '5',
            '--format', 'json'
        ])
        assert result.exit_code == 0
        # Should contain hex color codes
        assert '#' in result.output
    
    def test_utils_report(self, runner, ee_initialized, tmp_path):
        """Test report generation"""
        outfile = tmp_path / "report.csv"
        result = runner.invoke(cli, [
            'utils', 'report',
            '--outfile', str(outfile),
            '--format', 'csv'
        ])
        # Should complete (may fail if no projects, but shouldn't crash)
        assert result.exit_code in [0, 1]


class TestDeprecatedCommands:
    """Test that deprecated commands show warnings but still work"""
    
    def test_deprecated_quota(self, runner, ee_initialized):
        """Test deprecated quota command"""
        result = runner.invoke(cli, ['quota'])
        assert result.exit_code == 0
        assert 'deprecated' in result.output.lower()
    
    def test_deprecated_assetsize(self, runner, ee_initialized):
        """Test deprecated assetsize command"""
        result = runner.invoke(cli, [
            'assetsize',
            'LANDSAT/LC08/C02/T1_L2/LC08_044034_20140318'
        ])
        assert result.exit_code in [0, 1]
        assert 'deprecated' in result.output.lower()


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_invalid_asset_info(self, runner, ee_initialized):
        """Test asset info with invalid asset"""
        result = runner.invoke(cli, [
            'assets', 'info',
            'invalid/asset/path/that/does/not/exist'
        ])
        # Should fail gracefully
        assert result.exit_code == 1
    
    def test_search_no_keywords(self, runner):
        """Test search without keywords"""
        result = runner.invoke(cli, ['utils', 'search'])
        # Should show error about missing keywords
        assert result.exit_code == 2  # Click's exit code for missing required option
    
    def test_palette_invalid_name(self, runner):
        """Test palette with invalid name"""
        result = runner.invoke(cli, [
            'utils', 'palette',
            '--name', 'InvalidPaletteName',
            '--classes', '5'
        ])
        # Should show error
        assert result.exit_code == 1


class TestUtilityFunctions:
    """Test utility functions used throughout the CLI"""
    
    def test_humansize_conversion(self):
        """Test humansize function"""
        from geeadd import humansize
        
        assert humansize(0) == "0 B"
        assert humansize(1024) == "1 KB"
        assert humansize(1024 * 1024) == "1 MB"
        assert humansize(1024 * 1024 * 1024) == "1 GB"
        assert humansize(1536) == "1.5 KB"
    
    def test_version_comparison(self):
        """Test version comparison function"""
        from geeadd import compare_version
        
        assert compare_version("2.0.0", "1.0.0") == 1
        assert compare_version("1.0.0", "2.0.0") == -1
        assert compare_version("1.0.0", "1.0.0") == 0
        assert compare_version("1.0.1", "1.0.0") == 1


# Integration test that requires actual EE access
class TestIntegration:
    """Integration tests requiring actual Earth Engine access"""
    
    @pytest.mark.slow
    def test_full_workflow(self, runner, ee_initialized):
        """Test a complete workflow"""
        # 1. Check projects
        result = runner.invoke(cli, ['projects', 'enabled'])
        assert result.exit_code == 0
        
        # 2. Check quota
        result = runner.invoke(cli, ['projects', 'quota'])
        assert result.exit_code == 0
        
        # 3. List tasks
        result = runner.invoke(cli, ['tasks', 'list'])
        assert result.exit_code == 0
        
        # 4. Search catalog
        result = runner.invoke(cli, [
            'utils', 'search',
            '--keywords', 'elevation',
            '--max-results', '2'
        ])
        assert result.exit_code == 0
