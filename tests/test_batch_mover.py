"""Tests for batch_mover module.

SPDX-License-Identifier: Apache-2.0
"""

import io
import signal
import sys
import time
from unittest import mock

import pytest

import ee
from geeadd import batch_mover


def test_retry_success_first_try():
    """Test that the decorator doesn't retry if the function succeeds."""
    mock_func = mock.Mock(return_value="success")

    @batch_mover.retry_on_ee_error(max_retries=3, backoff_factor=0.01)
    def func_to_decorate():
        return mock_func()

    result = func_to_decorate()

    assert result == "success"
    mock_func.assert_called_once()


@mock.patch.object(time, "sleep")
def test_retry_rate_limit_success_after_retry(mock_sleep):
    """Test retry on rate limit EEException, succeeding on retry."""
    mock_func = mock.Mock()
    mock_func.side_effect = [
        ee.EEException("Rate limit exceeded"),
        "success",
    ]

    @batch_mover.retry_on_ee_error(max_retries=3, backoff_factor=0.01)
    def func_to_decorate():
        return mock_func()

    result = func_to_decorate()

    assert result == "success"
    assert mock_func.call_count == 2
    mock_sleep.assert_called_once()


@mock.patch.object(time, "sleep")
def test_retry_quota_error_success_after_retry(mock_sleep):
    """Test retry on quota EEException, succeeding on retry."""
    mock_func = mock.Mock()
    mock_func.side_effect = [
        ee.EEException("Quota exceeded for project"),
        "success",
    ]

    @batch_mover.retry_on_ee_error(max_retries=3, backoff_factor=0.01)
    def func_to_decorate():
        return mock_func()

    result = func_to_decorate()

    assert result == "success"
    assert mock_func.call_count == 2
    mock_sleep.assert_called_once()


@mock.patch.object(time, "sleep")
def test_retry_failure_after_max_retries(mock_sleep):
    """Test that EEException is raised after max_retries."""
    mock_func = mock.Mock(side_effect=ee.EEException("Rate limit exceeded"))

    @batch_mover.retry_on_ee_error(max_retries=3, backoff_factor=0.01)
    def func_to_decorate():
        return mock_func()

    with pytest.raises(ee.EEException, match="Rate limit exceeded"):
        func_to_decorate()

    assert mock_func.call_count == 3
    assert mock_sleep.call_count == 2


@mock.patch.object(time, "sleep")
def test_retry_non_rate_limit_ee_exception(mock_sleep):
    """Test no retry on non-rate-limit EEException."""
    mock_func = mock.Mock(side_effect=ee.EEException("Asset not found"))

    @batch_mover.retry_on_ee_error(max_retries=3, backoff_factor=0.01)
    def func_to_decorate():
        return mock_func()

    with pytest.raises(ee.EEException, match="Asset not found"):
        func_to_decorate()

    mock_func.assert_called_once()
    mock_sleep.assert_not_called()


@mock.patch.object(time, "sleep")
def test_retry_other_exception(mock_sleep):
    """Test no retry on non-EEException."""
    mock_func = mock.Mock(side_effect=ValueError("Some other error"))

    @batch_mover.retry_on_ee_error(max_retries=3, backoff_factor=0.01)
    def func_to_decorate():
        return mock_func()

    with pytest.raises(ValueError, match="Some other error"):
        func_to_decorate()

    mock_func.assert_called_once()
    mock_sleep.assert_not_called()

def test_handle_interrupt_first_call():
  """Test handle_interrupt on first call."""
  batch_mover.interrupt_received = False
  batch_mover.handle_interrupt(signal.SIGINT, None)
  assert batch_mover.interrupt_received


def test_handle_interrupt_second_call():
  """Test handle_interrupt on second call."""
  batch_mover.interrupt_received = True
  with mock.patch.object(sys, "exit") as mock_exit:
    batch_mover.handle_interrupt(signal.SIGINT, None)
    mock_exit.assert_called_once_with(1)


@pytest.mark.parametrize(
    "input_str, expected_output",
    [
        ("image", "Image"),
        ("image collection", "Image Collection"),
        ("feature view", "Feature View"),
        ("table", "Table"),
        ("", ""),
        ("ALREADY TITLE CASE", "Already Title Case"),
        ("asset", "Asset"),
    ],
)
def test_camel_case(input_str, expected_output):
  assert batch_mover.camel_case(input_str) == expected_output


@mock.patch.object(ee.data, "getAsset")
def test_get_asset_safe_success(mock_get_asset):
    """Test get_asset_safe successfully returns asset."""
    mock_get_asset.return_value = {"id": "test/asset", "type": "IMAGE"}
    asset = batch_mover.get_asset_safe("test/asset")
    assert asset == {"id": "test/asset", "type": "IMAGE"}
    mock_get_asset.assert_called_once_with("test/asset")

@mock.patch.object(ee.data, "getAsset")
def test_get_asset_safe_not_found(mock_get_asset):
    """Test get_asset_safe returns None when asset not found."""
    mock_get_asset.side_effect = ee.EEException("Asset test/asset not found.")
    asset = batch_mover.get_asset_safe("test/asset")
    assert asset is None
    mock_get_asset.assert_called_once_with("test/asset")

@mock.patch.object(ee.data, "getAsset")
def test_get_asset_safe_does_not_exist(mock_get_asset):
    """Test get_asset_safe returns None when asset does not exist."""
    mock_get_asset.side_effect = ee.EEException(
        "Asset projects/proj/assets/asset does not exist"
    )
    asset = batch_mover.get_asset_safe("projects/proj/assets/asset")
    assert asset is None
    mock_get_asset.assert_called_once_with("projects/proj/assets/asset")

@mock.patch.object(ee.data, "getAsset")
def test_get_asset_safe_ee_exception_propagates(mock_get_asset):
    """Test get_asset_safe raises other EEExceptions."""
    mock_get_asset.side_effect = ee.EEException("Some other EE error")
    with pytest.raises(ee.EEException, match="Some other EE error"):
        batch_mover.get_asset_safe("test/asset")
    mock_get_asset.assert_called_once_with("test/asset")

@mock.patch.object(ee.data, "getAsset")
def test_get_asset_safe_other_exception(mock_get_asset):
    """Test get_asset_safe returns None on other exceptions."""
    mock_get_asset.side_effect = ValueError("Some other error")
    asset = batch_mover.get_asset_safe("test/asset")
    assert asset is None
    mock_get_asset.assert_called_once_with("test/asset")
