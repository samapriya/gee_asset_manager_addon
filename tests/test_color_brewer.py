"""Tests for color_brewer."""

import builtins
import json
import sys
from typing import Any
from unittest import mock

from geeadd import color_brewer
import pyperclip
import pytest


@pytest.fixture
def palettes() -> dict[str, Any]:
    """Sample palettes for testing."""
    return {
        "Reds": {
            "3": ["fee0d2", "fc9272", "de2d26"],
            "5": ["fee0d2", "fcae91", "fb6a4a", "de2d26", "a50f15"],
            "type": "sequential",
        },
        "Blues": {"3": ["deebf7", "9ecae1", "3182bd"], "type": "sequential"},
        "Greens": {"4": ["edf8e9", "bae4b3", "74c476", "238b45"], "type": "sequential"},
        "RdBu": {"3": ["ef8a62", "f7f7f7", "67a9cf"], "type": "diverging"},
        "Set1": {"3": ["e41a1c", "377eb8", "4daf4a"], "type": "qualitative"},
    }


def test_load_palettes_success():
    """Test load_palettes with valid JSON data."""
    mock_data = {
        "Reds": {"3": ["#fee0d2", "#fc9272", "#de2d26"], "type": "sequential"}
    }
    mock_json = json.dumps(mock_data)
    m = mock.mock_open(read_data=mock_json)
    with mock.patch("builtins.open", m):
        palettes = color_brewer.load_palettes()
        assert palettes == mock_data
        m.assert_called_once()


@mock.patch.object(sys, "exit")
@mock.patch.object(color_brewer.console, "print")
def test_load_palettes_file_not_found(mock_print, mock_exit,):
    """Test load_palettes when palettes.json is not found."""
    mock_exit.side_effect = SystemExit
    with (
        mock.patch.object(builtins, "open", side_effect=FileNotFoundError),
        pytest.raises(SystemExit)
    ):
        color_brewer.load_palettes()
    mock_exit.assert_called_once_with(1)
    mock_print.assert_called_once()


@mock.patch.object(sys, "exit")
@mock.patch.object(color_brewer.console, "print")
def test_load_palettes_json_error(mock_print, mock_exit):
    """Test load_palettes with invalid JSON data."""
    mock_exit.side_effect = SystemExit
    mock_open = mock.mock_open(read_data="invalid json")
    with (
        mock.patch("builtins.open", mock_open),
        pytest.raises(SystemExit)
    ):
        color_brewer.load_palettes()
    mock_exit.assert_called_once_with(1)
    mock_print.assert_called_once()


def test_interpolate_color_black_to_white():
    assert color_brewer.interpolate_color("000000", "ffffff", 0) == "000000"
    assert color_brewer.interpolate_color("000000", "ffffff", 1) == "ffffff"
    assert color_brewer.interpolate_color("000000", "ffffff", 0.5) == "7f7f7f"


def test_interpolate_color_red_to_blue():
    assert color_brewer.interpolate_color("ff0000", "0000ff", 0) == "ff0000"
    assert color_brewer.interpolate_color("ff0000", "0000ff", 1) == "0000ff"
    assert color_brewer.interpolate_color("ff0000", "0000ff", 0.5) == "7f007f"


def test_interpolate_color_white_to_black():
    assert color_brewer.interpolate_color("ffffff", "000000", 0) == "ffffff"
    assert color_brewer.interpolate_color("ffffff", "000000", 1) == "000000"
    assert color_brewer.interpolate_color("ffffff", "000000", 0.5) == "7f7f7f"


def test_interpolate_color_rounding():
    assert color_brewer.interpolate_color("000000", "030000", 0.5) == "010000"


def test_interpolate_palette():
    """Test interpolate_palette."""
    colors = ["000000", "ffffff"]
    # Target < len(colors)
    assert color_brewer.interpolate_palette(colors, 1) == ["000000"]
    # Target == len(colors)
    assert color_brewer.interpolate_palette(colors, 2) == ["000000", "ffffff"]
    # Target > len(colors)
    assert color_brewer.interpolate_palette(colors, 3) == ["000000", "7f7f7f", "ffffff"]
    assert color_brewer.interpolate_palette(colors, 5) == [
        "000000",
        "3f3f3f",
        "7f7f7f",
        "bfbfbf",
        "ffffff",
    ]


@mock.patch.object(sys, "exit")
@mock.patch.object(color_brewer.console, "print")
# pylint: disable-next=redefined-outer-name
def test_get_palette_not_found(mock_print, mock_exit, palettes):
    """Test get_palette with a palette name that does not exist."""
    mock_exit.side_effect = SystemExit
    with pytest.raises(SystemExit):
        color_brewer.get_palette("Purples", 3, palettes)
    mock_exit.assert_called_once_with(1)
    # Check that *some* print call happened.
    # The second call is the list of palettes.
    assert mock_print.call_count == 2


@mock.patch.object(sys, "exit")
@mock.patch.object(color_brewer.console, "print")
# pylint: disable-next=redefined-outer-name
def test_get_palette_too_few_classes(mock_print, mock_exit, palettes):
    """Test get_palette with fewer than 3 classes."""
    mock_exit.side_effect = SystemExit
    with pytest.raises(SystemExit):
        color_brewer.get_palette("Reds", 2, palettes)
    mock_exit.assert_called_once_with(1)
    mock_print.assert_called_with("[red]Error: Minimum 3 classes required[/red]")


# pylint: disable-next=redefined-outer-name
def test_get_palette_exact_match(palettes):
    """Test get_palette with an exact match for classes."""
    assert color_brewer.get_palette("Reds", 3, palettes) == [
        "fee0d2",
        "fc9272",
        "de2d26",
    ]
    assert color_brewer.get_palette("Reds", 5, palettes) == [
        "fee0d2",
        "fcae91",
        "fb6a4a",
        "de2d26",
        "a50f15",
    ]


# pylint: disable-next=redefined-outer-name
def test_get_palette_too_small(palettes):
    """Test get_palette with classes smaller than min available."""
    assert color_brewer.get_palette("Greens", 3, palettes) == [
        "edf8e9",
        "bae4b3",
        "74c476",
    ]


# pylint: disable-next=redefined-outer-name
def test_get_palette_too_large_interpolate(palettes):
    """Test get_palette with classes > max available size."""
    assert color_brewer.get_palette("Blues", 4, palettes) == [
        "deebf7",
        "b3d5e8",
        "79b2d5",
        "3182bd",
    ]


# pylint: disable-next=redefined-outer-name
def test_get_palette_between_interpolate(palettes):
    """Test get_palette with classes between available sizes."""
    assert color_brewer.get_palette("Reds", 4, palettes) == [
        "fee0d2",
        "fcac92",
        "f27058",
        "de2d26",
    ]


# pylint: disable-next=redefined-outer-name
def test_list_palettes_all(palettes):
    """Test list_palettes with no type filter."""
    with mock.patch.object(color_brewer.console, "print") as mock_print:
        color_brewer.list_palettes(palettes)
        assert mock_print.call_count == 5
        args0, _ = mock_print.call_args_list[0]
        assert "Sequential Palettes" in args0[0].title
        assert args0[0].row_count == 3
        args2, _ = mock_print.call_args_list[2]
        assert "Diverging Palettes" in args2[0].title
        assert args2[0].row_count == 1
        args4, _ = mock_print.call_args_list[4]
        assert "Qualitative Palettes" in args4[0].title
        assert args4[0].row_count == 1


@mock.patch.object(color_brewer.console, "print")
# pylint: disable-next=redefined-outer-name
def test_list_palettes_sequential(mock_print, palettes):
    """Test list_palettes with sequential type filter."""
    color_brewer.list_palettes(palettes, palette_type="sequential")
    assert mock_print.call_count == 2
    args, _ = mock_print.call_args_list[0]
    table = args[0]
    assert "Sequential Palettes" in table.title
    assert table.row_count == 3


@mock.patch.object(color_brewer.console, "print")
# pylint: disable-next=redefined-outer-name
def test_list_palettes_diverging(mock_print, palettes):
    """Test list_palettes with diverging type filter."""
    color_brewer.list_palettes(palettes, palette_type="diverging")
    assert mock_print.call_count == 2
    args, _ = mock_print.call_args_list[0]
    table = args[0]
    assert "Diverging Palettes" in table.title
    assert table.row_count == 1


@mock.patch.object(color_brewer.console, "print")
# pylint: disable-next=redefined-outer-name
def test_list_palettes_qualitative(mock_print, palettes):
    """Test list_palettes with qualitative type filter."""
    color_brewer.list_palettes(palettes, palette_type="qualitative")
    assert mock_print.call_count == 1
    args, _ = mock_print.call_args_list[0]
    table = args[0]
    assert "Qualitative Palettes" in table.title
    assert table.row_count == 1


@mock.patch.object(color_brewer, "PYPERCLIP_AVAILABLE", False)
def test_copy_to_clipboard_unavailable():
    """Test copy_to_clipboard when pyperclip is not available."""
    assert not color_brewer.copy_to_clipboard("test")


@mock.patch.object(color_brewer, "PYPERCLIP_AVAILABLE", True)
@mock.patch.object(pyperclip, "copy")
def test_copy_to_clipboard_success(mock_copy):
    """Test copy_to_clipboard when pyperclip is available and copy succeeds."""
    assert color_brewer.copy_to_clipboard("test")
    mock_copy.assert_called_once_with("test")


@mock.patch.object(color_brewer, "PYPERCLIP_AVAILABLE", True)
@mock.patch.object(pyperclip, "copy", side_effect=Exception("Copy failed"))
def test_copy_to_clipboard_failure(mock_copy):
    """Test copy_to_clipboard when pyperclip is available and copy fails."""
    assert not color_brewer.copy_to_clipboard("test")
    mock_copy.assert_called_once_with("test")


@pytest.mark.parametrize(
    "name, classes, output_format, expected_text_or_data, colors",
    [
        (
            "Reds",
            3,
            "json",
            ["fee0d2", "fc9272", "de2d26"],
            ["fee0d2", "fc9272", "de2d26"],
        ),
        (
            "Reds",
            3,
            "hex",
            ["#fee0d2", "#fc9272", "#de2d26"],
            ["fee0d2", "fc9272", "de2d26"],
        ),
        (
            "Reds",
            3,
            "list",
            ["#fee0d2, #fc9272, #de2d26"],
            ["fee0d2", "fc9272", "de2d26"],
        ),
        (
            "Reds",
            3,
            "css",
            [
                "/* Reds palette - 3 colors */\n:root {\n  --color-reds-1: #fee0d2;\n  --color-reds-2: #fc9272;\n  --color-reds-3: #de2d26;\n}"
            ],
            ["fee0d2", "fc9272", "de2d26"],
        ),
        (
            "Reds",
            3,
            "python",
            [
                "# Reds palette - 3 colors\nREDS_PALETTE = [\n    '#fee0d2',\n    '#fc9272',\n    '#de2d26',\n]"
            ],
            ["fee0d2", "fc9272", "de2d26"],
        ),
        (
            "Reds",
            3,
            "js",
            [
                "// Reds palette - 3 colors\nconst redsPalette = [\n  '#fee0d2',\n  '#fc9272',\n  '#de2d26',\n];"
            ],
            ["fee0d2", "fc9272", "de2d26"],
        ),
    ],
)
@mock.patch.object(color_brewer, "load_palettes")
@mock.patch.object(color_brewer, "get_palette")
@mock.patch.object(color_brewer, "console")
def test_generate_palette_formats(
    mock_console,
    mock_get_palette,
    mock_load_palettes,
    palettes,  # pylint: disable=redefined-outer-name
    name,
    classes,
    output_format,
    expected_text_or_data,
    colors,
):
    """Test generate_palette with different output formats."""
    mock_load_palettes.return_value = palettes
    mock_get_palette.return_value = colors

    with mock.patch("geeadd.color_brewer.copy_to_clipboard") as mock_copy:
        color_brewer.generate_palette(name, classes, output_format=output_format)
        mock_copy.assert_not_called()

    mock_get_palette.assert_called_once_with(name, classes, palettes)

    if output_format == "json":
        mock_console.print_json.assert_called_once_with(data=expected_text_or_data)
    elif output_format == "hex":
        calls = [mock.call(c) for c in expected_text_or_data]
        mock_console.print.assert_has_calls(calls)
    else:
        mock_console.print.assert_called_once_with(expected_text_or_data[0])


@mock.patch.object(color_brewer, "load_palettes")
@mock.patch.object(color_brewer, "get_palette")
@mock.patch.object(color_brewer, "console")
@mock.patch.object(color_brewer, "copy_to_clipboard", return_value=True)
def test_generate_palette_copy_success(
    # pylint: disable-next=redefined-outer-name
    mock_copy, mock_console, mock_get_palette, mock_load_palettes, palettes
):
    """Test generate_palette with auto_copy=True and successful copy."""
    mock_load_palettes.return_value = palettes
    mock_get_palette.return_value = ["f00", "0f0"]
    color_brewer.generate_palette("foo", 2, "list", auto_copy=True)
    mock_copy.assert_called_once_with("#f00, #0f0")
    mock_console.print.assert_called_with("\n[green]✓ Copied to clipboard![/green]")


@mock.patch.object(color_brewer, "load_palettes")
@mock.patch("geeadd.color_brewer.get_palette")
@mock.patch("geeadd.color_brewer.console")
@mock.patch("geeadd.color_brewer.copy_to_clipboard", return_value=False)
@mock.patch("geeadd.color_brewer.PYPERCLIP_AVAILABLE", False)
def test_generate_palette_copy_unavailable(
    # pylint: disable-next=redefined-outer-name
    mock_copy, mock_console, mock_get_palette, mock_load_palettes, palettes
):
    """Test generate_palette with auto_copy=True and pyperclip unavailable."""
    mock_load_palettes.return_value = palettes
    mock_get_palette.return_value = ["f00", "0f0"]
    color_brewer.generate_palette("foo", 2, "list", auto_copy=True)
    mock_copy.assert_called_once_with("#f00, #0f0")
    mock_console.print.assert_called_with(
        "\n[yellow]⚠ Clipboard copy not available. Install pyperclip: pip install pyperclip[/yellow]"
    )


@mock.patch.object(color_brewer, "load_palettes")
@mock.patch.object(color_brewer, "get_palette")
@mock.patch.object(color_brewer, "console")
@mock.patch.object(color_brewer, "copy_to_clipboard", return_value=False)
@mock.patch.object(color_brewer, "PYPERCLIP_AVAILABLE", True)
def test_generate_palette_copy_failed(
    # pylint: disable-next=redefined-outer-name
    mock_copy, mock_console, mock_get_palette, mock_load_palettes, palettes
):
    """Test generate_palette with auto_copy=True and copy failing."""
    mock_load_palettes.return_value = palettes
    mock_get_palette.return_value = ["f00", "0f0"]
    color_brewer.generate_palette("foo", 2, "list", auto_copy=True)
    mock_copy.assert_called_once_with("#f00, #0f0")
    mock_console.print.assert_called_with("\n[yellow]⚠ Could not copy to clipboard[/yellow]")
