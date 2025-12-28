"""Tests for batch_delete."""

import concurrent.futures
import io
import json
import logging
import signal
import sys
import time
from unittest import mock

from geeadd import batch_delete
import pytest

import ee


def test_handle_interrupt_first_call():
  """Test handle_interrupt on first call."""
  batch_delete.interrupt_received = False
  with mock.patch.object(
      sys, "stdout", new_callable=io.StringIO
  ) as mock_stdout:
    batch_delete.handle_interrupt(signal.SIGINT, None)
  assert batch_delete.interrupt_received
  assert "Interrupt received!" in mock_stdout.getvalue()
  assert "Press Ctrl+C again" in mock_stdout.getvalue()


def test_handle_interrupt_second_call():
  """Test handle_interrupt on second call."""
  batch_delete.interrupt_received = True
  with mock.patch.object(
      sys, "stdout", new_callable=io.StringIO
  ) as mock_stdout:
    with mock.patch.object(sys, "exit") as mock_exit:
      batch_delete.handle_interrupt(signal.SIGINT, None)
      mock_exit.assert_called_once_with(1)
  assert "Forced exit requested." in mock_stdout.getvalue()


@mock.patch.object(ee.data, "getAsset")
def test_get_asset_success(mock_get_asset):
  """Test get_asset on success."""
  batch_delete.asset_list = []
  mock_get_asset.return_value = {"type": "Image", "name": "test/asset"}
  name, asset_type = batch_delete.get_asset("test/asset")
  assert name == "test/asset"
  assert asset_type == "image"
  assert batch_delete.asset_list == [{"path": "test/asset", "type": "image"}]
  mock_get_asset.assert_called_once_with("test/asset")


@mock.patch.object(ee.data, "getAsset")
def test_get_asset_failure(mock_get_asset):
  """Test get_asset on failure."""
  batch_delete.asset_list = []
  mock_get_asset.side_effect = Exception("Asset not found.")
  name, asset_type = batch_delete.get_asset("test/asset")
  assert name is None
  assert asset_type is None
  assert not batch_delete.asset_list
  mock_get_asset.assert_called_once_with("test/asset")


ASSET_INFO = {
    "test/folder1": {"type": "FOLDER", "name": "test/folder1"},
    "test/folder1/image1": {"type": "IMAGE", "name": "test/folder1/image1"},
    "test/folder1/subfolder1": {
        "type": "FOLDER",
        "name": "test/folder1/subfolder1",
    },
    "test/folder1/subfolder1/image2": {
        "type": "IMAGE",
        "name": "test/folder1/subfolder1/image2",
    },
    "test/folder1/collection1": {
        "type": "IMAGE_COLLECTION",
        "name": "test/folder1/collection1",
    },
    "test/folder1/collection1/image3": {
        "type": "IMAGE",
        "name": "test/folder1/collection1/image3",
    },
    "test/image_only": {"type": "IMAGE", "name": "test/image_only"},
}

LIST_ASSETS_RESULTS = {
    "test/folder1": {
        "assets": [
            {"name": "test/folder1/image1", "type": "IMAGE"},
            {"name": "test/folder1/subfolder1", "type": "FOLDER"},
            {"name": "test/folder1/collection1", "type": "IMAGE_COLLECTION"},
        ]
    },
    "test/folder1/subfolder1": {
        "assets": [{"name": "test/folder1/subfolder1/image2", "type": "IMAGE"}]
    },
    "test/folder1/collection1": {
        "assets": [{"name": "test/folder1/collection1/image3", "type": "IMAGE"}]
    },
}


def mock_get_asset_se(path):
  if path in ASSET_INFO:
    return ASSET_INFO[path]
  raise ee.EEException(f"Asset not found: {path}")


def mock_list_assets_se(params):
  parent = params["parent"]
  if parent in LIST_ASSETS_RESULTS:
    return LIST_ASSETS_RESULTS[parent]
  return {"assets": []}


MOCKED_FAILED_ASSETS = ({
    "asset_id": "test/asset",
    "status": "failed",
},)


@mock.patch.object(batch_delete, "logger")
def test_save_failed_assets_empty(mock_logger):
  """Test save_failed_assets with no failed assets."""
  batch_delete.save_failed_assets([])
  mock_logger.info.assert_called_once_with("No failed assets to save")


@mock.patch.object(batch_delete, "print")
@mock.patch.object(batch_delete, "logger")
@mock.patch.object(json, "dump")
def test_save_failed_assets_with_filename(
    mock_json_dump, mock_logger, mock_print
):
  """Test save_failed_assets with a filename."""
  m = mock.mock_open()
  with mock.patch.object(batch_delete, "open", m):
    batch_delete.save_failed_assets(
        MOCKED_FAILED_ASSETS, filename="output.json"
    )
  m.assert_called_once_with("output.json", "w")
  mock_json_dump.assert_called_once_with(MOCKED_FAILED_ASSETS, m(), indent=2)
  mock_logger.info.assert_called_once_with(
      "Failed assets saved to: output.json"
  )
  mock_print.assert_called_once_with("Failed assets saved to: output.json")


@mock.patch.object(batch_delete, "datetime")
@mock.patch.object(batch_delete, "print")
@mock.patch.object(batch_delete, "logger")
@mock.patch.object(json, "dump")
def test_save_failed_assets_no_filename(
    mock_json_dump, mock_logger, mock_print, mock_datetime
):
  """Test save_failed_assets without a filename."""
  mock_datetime.datetime.now().strftime.return_value = "20251222_074500"
  m = mock.mock_open()
  with mock.patch.object(batch_delete, "open", m):
    batch_delete.save_failed_assets(MOCKED_FAILED_ASSETS)
  expected_filename = "failed_deletions_20251222_074500.json"
  m.assert_called_once_with(expected_filename, "w")
  mock_json_dump.assert_called_once_with(MOCKED_FAILED_ASSETS, m(), indent=2)
  mock_logger.info.assert_called_once_with(
      f"Failed assets saved to: {expected_filename}"
  )
  mock_print.assert_called_once_with(
      f"Failed assets saved to: {expected_filename}"
  )


@mock.patch.object(batch_delete, "logger")
@mock.patch.object(json, "dump")
def test_save_failed_assets_exception(mock_json_dump, mock_logger):
  """Test save_failed_assets with an exception during file write."""
  with mock.patch.object(batch_delete, "open", mock.mock_open()) as m:
    m.side_effect = IOError("Cannot write")
    batch_delete.save_failed_assets(
        MOCKED_FAILED_ASSETS, filename="output.json"
    )
  m.assert_called_once_with("output.json", "w")
  mock_json_dump.assert_not_called()
  mock_logger.error.assert_called_once_with(
      "Failed to save failed assets: Cannot write"
  )


@mock.patch.object(batch_delete.tqdm_module, "tqdm", new=mock.MagicMock())
@mock.patch.object(signal, "signal")
@mock.patch.object(signal, "getsignal")
@mock.patch.object(logging, "basicConfig")
@mock.patch.object(batch_delete, "save_failed_assets")
@mock.patch.object(batch_delete, "delete_with_retry")
@mock.patch.object(batch_delete, "recursive_parallel")
@mock.patch.object(ee.data, "getAsset")
def test_delete_get_asset_exception(
    mock_get_asset,
    mock_recursive_parallel,
    mock_delete_with_retry,
    mock_save_failed_assets,
    mock_log_config,
    mock_getsignal,
    mock_signal,
):
  """Test delete when getAsset fails."""
  del mock_delete_with_retry, mock_save_failed_assets, mock_log_config, mock_getsignal, mock_signal  # Unused.

  mock_get_asset.side_effect = Exception("GEE error")
  result = batch_delete.delete("test/asset")
  assert result is None
  mock_get_asset.assert_called_once_with("test/asset")
  mock_recursive_parallel.assert_not_called()


@mock.patch.object(batch_delete.tqdm_module, "tqdm", new=mock.MagicMock())
@mock.patch.object(signal, "signal")
@mock.patch.object(signal, "getsignal")
@mock.patch.object(logging, "basicConfig")
@mock.patch.object(batch_delete, "save_failed_assets")
@mock.patch.object(batch_delete, "delete_with_retry")
@mock.patch.object(batch_delete, "recursive_parallel")
@mock.patch.object(ee.data, "getAsset")
def test_delete_no_assets(
    mock_get_asset,
    mock_recursive_parallel,
    mock_delete_with_retry,
    mock_save_failed_assets,
    mock_log_config,
    mock_getsignal,
    mock_signal,
):
  """Test delete with no assets found."""
  del mock_save_failed_assets, mock_log_config, mock_getsignal, mock_signal  # Unused.

  mock_get_asset.return_value = {"type": "Image", "name": "test/asset"}
  mock_recursive_parallel.return_value = []
  result = batch_delete.delete("test/asset")
  assert result is None
  mock_get_asset.assert_called_once_with("test/asset")
  mock_recursive_parallel.assert_called_once_with("test/asset", 10)
  mock_delete_with_retry.assert_not_called()
