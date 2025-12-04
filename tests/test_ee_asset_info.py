"""Tests for geeadd.ee_projects."""

from unittest import mock

from geeadd import ee_asset_info
import rich.console


def test_format_bytes():
    """Test format_bytes."""
    assert ee_asset_info.format_bytes(0) == '0.00 B'
    assert ee_asset_info.format_bytes(1023) == '1023.00 B'
    assert ee_asset_info.format_bytes(1024) == '1.00 KB'
    assert ee_asset_info.format_bytes(1024**2) == '1.00 MB'
    assert ee_asset_info.format_bytes(1024**3) == '1.00 GB'
    assert ee_asset_info.format_bytes(1024**4) == '1.00 TB'
    assert ee_asset_info.format_bytes(1024**5) == '1.00 PB'


def test_format_timestamp():
    """Test format_timestamp."""
    assert ee_asset_info.format_timestamp(None) == 'N/A'
    assert ee_asset_info.format_timestamp('2024-01-01T12:30:00Z') == (
        '2024-01-01 12:30:00 UTC'
    )
    assert (
        ee_asset_info.format_timestamp('2023-11-20T08:15:45.123456+00:00') ==
        '2023-11-20 08:15:45 UTC'
    )
    assert ee_asset_info.format_timestamp('invalid-timestamp') == (
        'invalid-timestamp'
    )


def test_display_asset_info_image():
    """Test display_asset_info for an IMAGE asset."""
    asset_info = {
        'type': 'IMAGE',
        'id': 'test/image',
        'name': 'test/image',
        'updateTime': '2024-01-01T00:00:00Z',
        'sizeBytes': '1024',
        'startTime': '2023-01-01T00:00:00Z',
        'endTime': '2023-12-31T23:59:59Z',
        'properties': {'foo': 'bar'},
        'bands': [{
            'id': 'B1',
            'dataType': {'precision': 'INT', 'range': [0, 255]},
            'grid': {
                'crsCode': 'EPSG:4326',
                'dimensions': {'width': 100, 'height': 100},
                'affineTransform': {'scaleX': 1, 'scaleY': -1},
            },
            'pyramidingPolicy': 'MEAN',
        }],
        'geometry': {'type': 'Polygon', 'coordinates': [...]},
    }
    with (
        mock.patch.object(ee_asset_info, 'ee') as mock_ee,
        mock.patch.object(rich.console.Console, 'print') as mock_print
    ):
        mock_ee.data.getAsset.return_value = asset_info
        result = ee_asset_info.display_asset_info('test/image')
        assert result == asset_info
        mock_print.assert_called()


def test_display_asset_info_table():
    """Test display_asset_info for a TABLE asset."""
    asset_info = {'type': 'TABLE', 'id': 'test/table'}
    with (
        mock.patch.object(ee_asset_info, 'ee') as mock_ee,
        mock.patch.object(rich.console.Console, 'print') as mock_print
    ):
        mock_ee.data.getAsset.return_value = asset_info
        result = ee_asset_info.display_asset_info('test/table')
        assert result == asset_info
        mock_print.assert_called()


def test_display_asset_info_exception():
    """Test display_asset_info with an exception."""
    with (
        mock.patch.object(ee_asset_info, 'ee') as mock_ee,
        mock.patch.object(rich.console.Console, 'print') as mock_print
    ):
        mock_ee.data.getAsset.side_effect = Exception('Asset not found')
        result = ee_asset_info.display_asset_info('bad/asset')
        assert result is None
        mock_print.assert_called_with(
            '[bold red]Error:[/bold red] Asset not found')


def test_display_asset_info_unbounded_geometry():
    """Test display_asset_info with unbounded geometry."""
    asset_info = {
        'type': 'IMAGE',
        'id': 'test/image_unbounded',
        'geometry': {'type': 'Polygon', 'coordinates': [[-180, -90, 180, 90]]},
    }
    with (
        mock.patch.object(ee_asset_info, 'ee') as mock_ee,
        mock.patch.object(rich.console.Console, 'print') as mock_print
    ):
        mock_ee.data.getAsset.return_value = asset_info
        mock_geom = mock.Mock()
        mock_geom.isUnbounded.return_value.getInfo.return_value = True
        mock_img_instance = mock_ee.Image.return_value
        mock_img_instance.geometry.return_value = mock_geom

        result = ee_asset_info.display_asset_info('test/image_unbounded')
        assert result == asset_info
        mock_print.assert_called()
