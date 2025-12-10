from unittest import mock

import pytest

import ee
from geeadd import batch_copy


@pytest.mark.parametrize(
    "input_str, expected",
    [
        ("hello world", "Hello World"),
        ("image", "Image"),
        ("image collection", "Image Collection"),
        ("feature view", "Feature View"),
        ("", ""),
        ("ALREADY TITLE", "Already Title"),
        ("another_string", "Another_String"),
    ],
)
def test_camel_case(input_str, expected):
    """Test camel_case function."""
    assert batch_copy.camel_case(input_str) == expected


@mock.patch.object(ee.data, "getAsset")
def test_get_asset_safe_found(mock_get_asset):
    """Test get_asset_safe when asset is found."""
    mock_get_asset.return_value = {"type": "Image", "id": "test/asset"}
    asset = batch_copy.get_asset_safe("test/asset")
    assert asset == {"type": "Image", "id": "test/asset"}
    mock_get_asset.assert_called_once_with("test/asset")


@mock.patch.object(ee.data, "getAsset")
def test_get_asset_safe_not_found(mock_get_asset):
    """Test get_asset_safe when asset is not found."""
    mock_get_asset.side_effect = batch_copy.ee.EEException("Asset not found.")
    asset = batch_copy.get_asset_safe("test/asset")
    assert asset is None
    mock_get_asset.assert_called_once_with("test/asset")


@mock.patch.object(ee.data, "getAsset")
def test_get_asset_safe_does_not_exist(mock_get_asset):
    """Test get_asset_safe when asset does not exist."""
    mock_get_asset.side_effect = batch_copy.ee.EEException(
        "Asset does not exist."
    )
    asset = batch_copy.get_asset_safe("test/asset")
    assert asset is None
    mock_get_asset.assert_called_once_with("test/asset")


@mock.patch.object(ee.data, "getAsset")
def test_get_asset_safe_other_ee_exception(mock_get_asset):
    """Test get_asset_safe with other EEException."""
    mock_get_asset.side_effect = batch_copy.ee.EEException("Some other error.")
    with pytest.raises(batch_copy.ee.EEException):
        batch_copy.get_asset_safe("test/asset")
    mock_get_asset.assert_called_once_with("test/asset")


@mock.patch.object(ee.data, "getAsset")
def test_get_asset_safe_generic_exception(mock_get_asset):
    """Test get_asset_safe with a generic exception."""
    mock_get_asset.side_effect = Exception("Generic error.")
    asset = batch_copy.get_asset_safe("test/asset")
    assert asset is None
    mock_get_asset.assert_called_once_with("test/asset")
