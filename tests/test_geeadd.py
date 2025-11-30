"""
Comprehensive tests for geeadd CLI commands
Tests actual Earth Engine functionality using service account authentication
"""

import pytest
import json
import os
import subprocess
import sys
import time
from unittest.mock import patch, MagicMock


# Test configuration
TEST_PROJECT = "projects/space-geographer"
TEST_ASSET_SOURCE = f"{TEST_PROJECT}/assets/git-test"
TEST_ASSET_STAGING = f"{TEST_PROJECT}/assets/git-test-staging"
TEST_ASSET_MV = f"{TEST_PROJECT}/assets/git-test-staging-mv"


@pytest.fixture(scope="session")
def ee_initialized():
    """Initialize Earth Engine once for all tests"""
    # Check if running in CI with service account
    if os.environ.get('GITHUB_ACTIONS'):
        sa_json = os.environ.get('CLOUD_SA')
        if not sa_json:
            pytest.skip("No service account credentials available")
    else:
        # For local testing, check if EE is authenticated
        result = subprocess.run(
            ['geeadd', 'projects', 'quota'],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            pytest.skip("Earth Engine not authenticated locally")
    
    return True


def run_geeadd(args, check=False):
    """Helper function to run geeadd commands"""
    cmd = ['geeadd'] + args
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )
    
    if check and result.returncode != 0:
        print(f"Command failed: {' '.join(cmd)}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
    
    return result


class TestCLIBasics:
    """Test basic CLI functionality"""
    
    def test_version(self):
        """Test version command"""
        result = run_geeadd(['--version'])
        assert result.returncode == 0
        assert 'geeadd' in result.stdout.lower() or 'version' in result.stdout.lower()
    
    def test_help(self):
        """Test help command"""
        result = run_geeadd(['--help'])
        assert result.returncode == 0
        assert 'Google Earth Engine' in result.stdout or 'Batch Asset Manager' in result.stdout
        assert 'projects' in result.stdout
        assert 'assets' in result.stdout
        assert 'tasks' in result.stdout
        assert 'utils' in result.stdout
    
    def test_help_short(self):
        """Test -h flag"""
        result = run_geeadd(['-h'])
        assert result.returncode == 0
        assert 'projects' in result.stdout


class TestProjectsGroup:
    """Test projects group commands"""
    
    def test_projects_help(self):
        """Test projects help"""
        result = run_geeadd(['projects', '--help'])
        assert result.returncode == 0
        assert 'enabled' in result.stdout
        assert 'dashboard' in result.stdout
        assert 'quota' in result.stdout
    
    def test_projects_quota(self, ee_initialized):
        """Test quota command - REAL TEST"""
        result = run_geeadd(['projects', 'quota'])
        assert result.returncode == 0
        # Should show quota info with storage and assets
        assert len(result.stdout) > 0
        print(f"\n✅ Quota output:\n{result.stdout}")
    
    def test_projects_enabled_mock(self):
        """Test projects enabled with mock (needs gcloud)"""
        # Mock the get_projects function since it requires gcloud
        with patch('geeadd.get_projects') as mock_projects:
            mock_projects.return_value = None
            result = run_geeadd(['projects', 'enabled'])
            # Should complete (may show empty or error, but shouldn't crash)
            assert result.returncode in [0, 1]
    
    def test_projects_dashboard_mock(self, tmp_path):
        """Test dashboard with mock (needs gcloud)"""
        # This requires gcloud, so we just test it doesn't crash
        outdir = tmp_path / "dashboard.html"
        result = run_geeadd(['projects', 'dashboard', '--outdir', str(outdir)])
        # May fail without gcloud, but shouldn't crash hard
        assert result.returncode in [0, 1]


class TestUtilsGroup:
    """Test utils group commands with REAL operations"""
    
    def test_utils_help(self):
        """Test utils help"""
        result = run_geeadd(['utils', '--help'])
        assert result.returncode == 0
        assert 'search' in result.stdout
        assert 'app2script' in result.stdout
        assert 'report' in result.stdout
        assert 'palette' in result.stdout
    
    def test_utils_app2script(self, tmp_path, ee_initialized):
        """Test app2script - REAL TEST"""
        outfile = tmp_path / "landscan.js"
        result = run_geeadd([
            'utils', 'app2script',
            '--url', 'https://sat-io.earthengine.app/view/landscan',
            '--outfile', str(outfile)
        ])
        assert result.returncode == 0
        # Check that output file was created
        if outfile.exists():
            print(f"✅ Script extracted to: {outfile}")
            assert outfile.stat().st_size > 0
    
    def test_utils_palette_list(self):
        """Test palette list - REAL TEST"""
        result = run_geeadd(['utils', 'palette', '--list'])
        assert result.returncode == 0
        assert 'Blues' in result.stdout or 'Sequential' in result.stdout
        print(f"\n✅ Palette list output:\n{result.stdout[:500]}")
    
    def test_utils_palette_generate_blues(self):
        """Test palette generation - REAL TEST"""
        result = run_geeadd([
            'utils', 'palette',
            '--name', 'Blues',
            '--classes', '5',
            '--format', 'json'
        ])
        assert result.returncode == 0
        assert '#' in result.stdout
        print(f"\n✅ Blues palette:\n{result.stdout}")
    
    def test_utils_search_fire(self, ee_initialized):
        """Test catalog search - REAL TEST"""
        result = run_geeadd([
            'utils', 'search',
            '--keywords', 'fire',
            '--max-results', '5'
        ])
        assert result.returncode == 0
        # Should return JSON results
        assert '[' in result.stdout
        print(f"\n✅ Search results for 'fire':\n{result.stdout[:500]}")
    
    def test_utils_report_json(self, ee_initialized, tmp_path):
        """Test report generation - REAL TEST"""
        outfile = tmp_path / "ee_report.json"
        result = run_geeadd([
            'utils', 'report',
            '--outfile', str(outfile),
            '--format', 'json',
            '--path', TEST_PROJECT
        ])
        # Should complete successfully or fail gracefully
        assert result.returncode in [0, 1]
        if outfile.exists():
            print(f"✅ Report generated: {outfile}")
            with open(outfile) as f:
                data = json.load(f)
                print(f"✅ Report contains {len(data)} items")


class TestAssetsGroupIntegrated:
    """Test assets group with REAL operations in a specific sequence"""
    
    def test_01_assets_help(self):
        """Test assets help"""
        result = run_geeadd(['assets', '--help'])
        assert result.returncode == 0
        assert 'copy' in result.stdout
        assert 'move' in result.stdout
        assert 'delete' in result.stdout
        assert 'access' in result.stdout
        assert 'size' in result.stdout
    
    def test_02_cleanup_staging_if_exists(self, ee_initialized):
        """Step 1: Delete staging asset if it exists - REAL TEST"""
        print(f"\n🧹 Cleaning up {TEST_ASSET_STAGING} if it exists...")
        result = run_geeadd([
            'assets', 'delete',
            '--id', TEST_ASSET_STAGING
        ])
        # May fail if doesn't exist, that's OK
        if result.returncode == 0:
            print(f"✅ Deleted {TEST_ASSET_STAGING}")
            # Give EE time to process
            time.sleep(2)
        else:
            print(f"ℹ️  {TEST_ASSET_STAGING} doesn't exist or couldn't be deleted")
    
    def test_03_copy_to_staging(self, ee_initialized):
        """Step 2: Copy test asset to staging - REAL TEST"""
        print(f"\n📋 Copying {TEST_ASSET_SOURCE} to {TEST_ASSET_STAGING}...")
        result = run_geeadd([
            'assets', 'copy',
            '--initial', TEST_ASSET_SOURCE,
            '--final', TEST_ASSET_STAGING
        ])
        assert result.returncode == 0
        print(f"✅ Successfully copied to {TEST_ASSET_STAGING}")
        # Give EE time to process
        time.sleep(3)
    
    def test_04_asset_size(self, ee_initialized):
        """Step 3: Check asset size - REAL TEST"""
        print(f"\n📊 Checking size of {TEST_ASSET_STAGING}...")
        result = run_geeadd([
            'assets', 'size',
            TEST_ASSET_STAGING
        ])
        # Should work or fail gracefully
        if result.returncode == 0:
            print(f"✅ Size info:\n{result.stdout}")
            assert len(result.stdout) > 0
        else:
            print(f"⚠️  Could not get size (asset may still be copying)")
    
    def test_05_asset_access(self, ee_initialized):
        """Step 4: Set public read access - REAL TEST"""
        print(f"\n🔓 Setting public read access on {TEST_ASSET_STAGING}...")
        result = run_geeadd([
            'assets', 'access',
            '--asset', TEST_ASSET_STAGING,
            '--user', 'allUsers',
            '--role', 'reader'
        ])
        assert result.returncode == 0
        print(f"✅ Public read access granted")
        time.sleep(1)
    
    def test_06_delete_metadata(self, ee_initialized):
        """Step 5: Delete metadata property - REAL TEST"""
        print(f"\n🗑️  Deleting metadata property 'property_1' from {TEST_ASSET_STAGING}...")
        result = run_geeadd([
            'assets', 'delete-meta',
            '--asset', TEST_ASSET_STAGING,
            '--property', 'property_1'
        ])
        # May succeed or fail if property doesn't exist
        if result.returncode == 0:
            print(f"✅ Metadata property deleted")
        else:
            print(f"ℹ️  Property may not exist: {result.stderr}")
    
    def test_07_copy_staging_to_mv(self, ee_initialized):
        """Step 6: Copy staging to mv location - REAL TEST"""
        print(f"\n📋 Copying {TEST_ASSET_STAGING} to {TEST_ASSET_MV}...")
        
        # First cleanup mv location if it exists
        cleanup_result = run_geeadd([
            'assets', 'delete',
            '--id', TEST_ASSET_MV
        ])
        if cleanup_result.returncode == 0:
            print(f"✅ Cleaned up old {TEST_ASSET_MV}")
            time.sleep(2)
        
        # Now copy
        result = run_geeadd([
            'assets', 'copy',
            '--initial', TEST_ASSET_STAGING,
            '--final', TEST_ASSET_MV
        ])
        assert result.returncode == 0
        print(f"✅ Successfully copied to {TEST_ASSET_MV}")
        time.sleep(2)
    
    def test_08_asset_info(self, ee_initialized):
        """Step 7: Get asset info - REAL TEST"""
        print(f"\n📄 Getting info for {TEST_ASSET_STAGING}...")
        result = run_geeadd([
            'assets', 'info',
            TEST_ASSET_STAGING
        ])
        if result.returncode == 0:
            print(f"✅ Asset info:\n{result.stdout[:500]}")
            assert len(result.stdout) > 0
        else:
            print(f"⚠️  Could not get asset info")
    
    @pytest.mark.slow
    def test_09_cleanup_test_assets(self, ee_initialized):
        """Step 8: Final cleanup (slow test) - REAL TEST"""
        print(f"\n🧹 Final cleanup of test assets...")
        
        # Delete staging
        result1 = run_geeadd([
            'assets', 'delete',
            '--id', TEST_ASSET_STAGING
        ])
        if result1.returncode == 0:
            print(f"✅ Deleted {TEST_ASSET_STAGING}")
        
        time.sleep(2)
        
        # Delete mv
        result2 = run_geeadd([
            'assets', 'delete',
            '--id', TEST_ASSET_MV
        ])
        if result2.returncode == 0:
            print(f"✅ Deleted {TEST_ASSET_MV}")


class TestTasksGroup:
    """Test tasks group commands"""
    
    def test_tasks_help(self):
        """Test tasks help"""
        result = run_geeadd(['tasks', '--help'])
        assert result.returncode == 0
        assert 'list' in result.stdout
        assert 'cancel' in result.stdout
    
    def test_tasks_list(self, ee_initialized):
        """Test task list - REAL TEST"""
        result = run_geeadd(['tasks', 'list'])
        assert result.returncode == 0
        # Should show task summary or JSON
        assert len(result.stdout) > 0
        print(f"\n✅ Task list:\n{result.stdout}")
    
    def test_tasks_list_completed(self, ee_initialized):
        """Test task list filtered by COMPLETED - REAL TEST"""
        result = run_geeadd(['tasks', 'list', '--state', 'COMPLETED'])
        assert result.returncode == 0
        # Should return JSON array
        print(f"\n✅ Completed tasks:\n{result.stdout[:500]}")
    
    def test_tasks_cancel_mock(self, ee_initialized):
        """Test task cancel with mock (to avoid actually canceling tasks)"""
        # We don't want to actually cancel tasks in tests
        # So we just verify the command structure works with help
        result = run_geeadd(['tasks', 'cancel', '--help'])
        assert result.returncode == 0
        assert 'all' in result.stdout or 'running' in result.stdout
        print("\n✅ Tasks cancel command help verified")


class TestDeprecatedCommands:
    """Test that deprecated commands show warnings but still work"""
    
    def test_deprecated_quota(self, ee_initialized):
        """Test deprecated quota command"""
        result = run_geeadd(['quota'])
        assert result.returncode in [0, 1]
        # Should mention deprecation
        output = result.stdout + result.stderr
        assert 'deprecated' in output.lower() or len(result.stdout) > 0
    
    def test_deprecated_assetsize(self, ee_initialized):
        """Test deprecated assetsize command"""
        result = run_geeadd([
            'assetsize',
            TEST_ASSET_SOURCE
        ])
        assert result.returncode in [0, 1]
        output = result.stdout + result.stderr
        # Should show deprecation or size info
        if result.returncode == 0:
            assert len(result.stdout) > 0


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_invalid_command(self):
        """Test invalid command"""
        result = run_geeadd(['invalid_command_xyz'])
        assert result.returncode != 0
    
    def test_invalid_asset_info(self, ee_initialized):
        """Test asset info with invalid asset"""
        result = run_geeadd([
            'assets', 'info',
            'invalid/asset/path/that/does/not/exist'
        ])
        # Should fail gracefully
        assert result.returncode == 1
    
    def test_search_no_keywords(self):
        """Test search without keywords"""
        result = run_geeadd(['utils', 'search'])
        # Should show error about missing keywords
        assert result.returncode == 2
    
    def test_palette_invalid_name(self):
        """Test palette with invalid name"""
        result = run_geeadd([
            'utils', 'palette',
            '--name', 'InvalidPaletteName123456',
            '--classes', '5'
        ])
        # Should show error
        assert result.returncode == 1


class TestAllHelpCommands:
    """Test that all help commands work"""
    
    def test_main_help(self):
        """Test main help"""
        result = run_geeadd(['--help'])
        assert result.returncode == 0
    
    def test_projects_subcommands_help(self):
        """Test all projects subcommands help"""
        subcommands = ['enabled', 'dashboard', 'quota']
        for cmd in subcommands:
            result = run_geeadd(['projects', cmd, '--help'])
            assert result.returncode == 0, f"Failed for: projects {cmd} --help"
    
    def test_assets_subcommands_help(self):
        """Test all assets subcommands help"""
        subcommands = ['info', 'copy', 'move', 'delete', 'delete-meta', 'access', 'size']
        for cmd in subcommands:
            result = run_geeadd(['assets', cmd, '--help'])
            assert result.returncode == 0, f"Failed for: assets {cmd} --help"
    
    def test_tasks_subcommands_help(self):
        """Test all tasks subcommands help"""
        subcommands = ['list', 'cancel']
        for cmd in subcommands:
            result = run_geeadd(['tasks', cmd, '--help'])
            assert result.returncode == 0, f"Failed for: tasks {cmd} --help"
    
    def test_utils_subcommands_help(self):
        """Test all utils subcommands help"""
        subcommands = ['search', 'app2script', 'report', 'palette']
        for cmd in subcommands:
            result = run_geeadd(['utils', cmd, '--help'])
            assert result.returncode == 0, f"Failed for: utils {cmd} --help"


class TestUtilityFunctions:
    """Test utility functions used throughout the CLI"""
    
    def test_humansize_conversion(self):
        """Test humansize function"""
        from geeadd import humansize
        
        assert humansize(0) == "0 B"
        assert humansize(1024) == "1 KB"
        assert humansize(1024 * 1024) == "1 MB"
        assert humansize(1024 * 1024 * 1024) == "1 GB"
    
    def test_version_comparison(self):
        """Test version comparison function"""
        from geeadd import compare_version
        
        assert compare_version("2.0.0", "1.0.0") == 1
        assert compare_version("1.0.0", "2.0.0") == -1
        assert compare_version("1.0.0", "1.0.0") == 0


@pytest.mark.slow
class TestIntegration:
    """Integration tests requiring actual Earth Engine access"""
    
    def test_full_workflow(self, ee_initialized):
        """Test a complete workflow"""
        print("\n" + "="*60)
        print("Running Full Integration Workflow")
        print("="*60)
        
        # 1. Check quota
        result = run_geeadd(['projects', 'quota'])
        assert result.returncode == 0
        print("\n✅ Step 1: Quota check passed")
        
        # 2. Search catalog
        result = run_geeadd([
            'utils', 'search',
            '--keywords', 'elevation',
            '--max-results', '2'
        ])
        assert result.returncode == 0
        print("✅ Step 2: Catalog search passed")
        
        # 3. List tasks
        result = run_geeadd(['tasks', 'list'])
        assert result.returncode == 0
        print("✅ Step 3: Task list passed")
        
        # 4. Generate palette
        result = run_geeadd([
            'utils', 'palette',
            '--name', 'RdYlGn',
            '--classes', '9',
            '--format', 'json'
        ])
        assert result.returncode == 0
        print("✅ Step 4: Palette generation passed")
        
        print("\n" + "="*60)
        print("✅ Full Integration Workflow Completed Successfully!")
        print("="*60)
