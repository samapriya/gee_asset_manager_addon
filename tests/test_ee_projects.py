"""Tests for geeadd.ee_projects."""

import subprocess
from unittest import mock

from geeadd import ee_projects


def test_is_gcloud_installed_true():
    """Test is_gcloud_installed when gcloud is installed."""
    with mock.patch.object(subprocess, 'run') as mock_run:
        mock_run.return_value.returncode = 0
        assert ee_projects.is_gcloud_installed()


def test_is_gcloud_installed_false_filenotfound():
    """Test is_gcloud_installed when gcloud is not found."""
    with mock.patch.object(subprocess, 'run', side_effect=FileNotFoundError):
        assert not ee_projects.is_gcloud_installed()


def test_is_gcloud_installed_false_returncode_error():
    """Test is_gcloud_installed when gcloud returns a non-zero exit code."""
    with mock.patch.object(subprocess, 'run') as mock_run:
        mock_run.return_value.returncode = 1
        assert not ee_projects.is_gcloud_installed()


def test_is_gcloud_authenticated_true():
    """Test is_gcloud_authenticated when gcloud is authenticated."""
    with mock.patch.object(subprocess, 'run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = (
            '[{"account": "user@google.com", "status": "ACTIVE"}]'
        )
        assert ee_projects.is_gcloud_authenticated()


def test_is_gcloud_authenticated_false_no_active_account():
    """Test is_gcloud_authenticated when no account is active."""
    with mock.patch.object(subprocess, 'run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = (
            '[{"account": "user@google.com", "status": ""}]'
        )
        assert not ee_projects.is_gcloud_authenticated()


def test_is_gcloud_authenticated_false_empty_list():
    """Test is_gcloud_authenticated when gcloud returns an empty list."""
    with mock.patch.object(subprocess, 'run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = '[]'
        assert not ee_projects.is_gcloud_authenticated()


def test_is_gcloud_authenticated_false_returncode_error():
    """Test is_gcloud_authenticated when gcloud returns a non-zero exit code."""
    with mock.patch.object(subprocess, 'run') as mock_run:
        mock_run.return_value.returncode = 1
        assert not ee_projects.is_gcloud_authenticated()


def test_is_gcloud_authenticated_false_filenotfound():
    """Test is_gcloud_authenticated when gcloud is not found."""
    with mock.patch.object(subprocess, 'run', side_effect=FileNotFoundError):
        assert not ee_projects.is_gcloud_authenticated()


def test_is_gcloud_authenticated_false_timeout():
    """Test is_gcloud_authenticated when gcloud command times out."""
    with mock.patch.object(
        subprocess,
        'run',
        side_effect=subprocess.TimeoutExpired(cmd='', timeout=1)
    ):
        assert not ee_projects.is_gcloud_authenticated()


def test_is_gcloud_authenticated_false_json_error():
    """Test is_gcloud_authenticated when gcloud returns invalid json."""
    with mock.patch.object(subprocess, 'run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = 'invalid json'
        assert not ee_projects.is_gcloud_authenticated()


def test_check_gcloud_true():
    """Test check_gcloud when gcloud is installed and authenticated."""
    with (
        mock.patch.object(ee_projects, 'is_gcloud_installed', return_value=True),
        mock.patch.object(ee_projects, 'is_gcloud_authenticated', return_value=True)
    ):
        assert ee_projects.check_gcloud()


def test_check_gcloud_false_not_installed():
    """Test check_gcloud when gcloud is not installed."""
    with (
        mock.patch.object(ee_projects, 'is_gcloud_installed', return_value=False),
        mock.patch.object(ee_projects, 'is_gcloud_authenticated', return_value=True)
    ):
        assert not ee_projects.check_gcloud()


def test_check_gcloud_false_not_authenticated():
    """Test check_gcloud when gcloud is not authenticated."""
    with (
        mock.patch.object(ee_projects, 'is_gcloud_installed', return_value=True),
        mock.patch.object(ee_projects, 'is_gcloud_authenticated', return_value=False)
    ):
        assert not ee_projects.check_gcloud()


def test_check_gcloud_false_not_installed_or_authenticated():
    """Test check_gcloud when gcloud is not installed or authenticated."""
    with (
        mock.patch.object(ee_projects, 'is_gcloud_installed', return_value=False),
        mock.patch.object(ee_projects, 'is_gcloud_authenticated', return_value=False)
    ):
        assert not ee_projects.check_gcloud()


def test_list_enabled_services_success():
    """Test list_enabled_services successful execution."""
    with mock.patch.object(subprocess, 'run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = (
            '[{"name": "service1"}, {"name": "service2"}]'
        )
        result = ee_projects.list_enabled_services('project-name')
        assert result == [{'name': 'service1'}, {'name': 'service2'}]


def test_list_enabled_services_error_returncode():
    """Test list_enabled_services with non-zero return code."""
    with mock.patch.object(subprocess, 'run') as mock_run:
        mock_run.return_value.returncode = 1
        result = ee_projects.list_enabled_services('project-name')
        assert result is None


def test_list_enabled_services_timeout():
    """Test list_enabled_services with timeout."""
    with mock.patch.object(subprocess, 'run', side_effect=subprocess.TimeoutExpired(cmd='', timeout=1)):
        result = ee_projects.list_enabled_services('project-name')
        assert result is None


def test_list_enabled_services_json_error():
    """Test list_enabled_services with invalid json output."""
    with mock.patch.object(subprocess, 'run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = 'invalid json'
        result = ee_projects.list_enabled_services('project-name')
        assert result is None


def test_project_permissions_earthengine_enabled():
    """Test project_permissions when earthengine is enabled."""
    value = [{
        'name': 'projects/42/services/earthengine.googleapis.com',
        'parent': 'projects/42',
    }]
    with mock.patch.object(ee_projects, 'list_enabled_services', return_value=value):
        assert ee_projects.project_permissions('project-name') == (
            'project-name',
            '42',
            True,
        )


def test_project_permissions_earthengine_enabled_complex():
    """Test project_permissions when earthengine is enabled."""
    value = [{
        'config': {},
        'name': 'projects/987654321/services/earthengine.googleapis.com',
        'parent': 'projects/987654321',
        'state': 'ENABLED',
    }]
    with mock.patch.object(ee_projects, 'list_enabled_services', return_value=value):
        assert ee_projects.project_permissions('project-name') == (
            'project-name',
            '987654321',
            True,
        )


def test_project_permissions_earthengine_disabled():
    """Test project_permissions when earthengine is not enabled."""
    value = [{'name': 'service1'}]
    with mock.patch.object(ee_projects, 'list_enabled_services', return_value=value):
        assert ee_projects.project_permissions('project-name') is None


def test_project_permissions_no_services():
    """Test project_permissions when no services are enabled."""
    with mock.patch.object(ee_projects, 'list_enabled_services', return_value=[]):
        assert ee_projects.project_permissions('project-name') is None


def test_project_permissions_list_services_fails():
    """Test project_permissions when list_enabled_services returns None."""
    with mock.patch.object(ee_projects, 'list_enabled_services', return_value=None):
        assert ee_projects.project_permissions('project-name') is None
