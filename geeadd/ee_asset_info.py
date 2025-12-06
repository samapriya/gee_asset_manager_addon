"""Earth Engine Asset Information Display for Google Earth Engine.

SPDX-License-Identifier: Apache-2.0
"""

import datetime

import ee
import rich.box
import rich.console
import rich.panel
import rich.syntax
import rich.table
import rich.tree

console = rich.console.Console()


def format_bytes(bytes_val: float) -> str:
    """Convert bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} PB"


def format_timestamp(timestamp_str: str | None) -> str:
    """Format ISO timestamp to readable date."""
    if not timestamp_str:
        return "N/A"
    try:
        dt = datetime.datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
    except Exception:
        return timestamp_str


def display_asset_info(asset_id: str) -> dict | None:
    """Display Earth Engine asset information beautifully.

    Args:
        asset_id: The full path to the Earth Engine asset

    Returns:
        Dictionary containing asset information, or None if an error occurred

    Example:
        >>> display_asset_info("TIGER/2020/TABBLOCK20")
    """
    try:
        asset_info = ee.data.getAsset(asset_id)

        # Type-specific color
        type_config = {
            'IMAGE': 'cyan',
            'IMAGE_COLLECTION': 'magenta',
            'TABLE': 'green',
            'FOLDER': 'yellow'
        }

        asset_type = asset_info.get('type', 'UNKNOWN')
        color = type_config.get(asset_type, 'white')

        # Main header
        console.print()
        console.print(rich.panel.Panel(
            f"[bold {color}]{asset_type}[/bold {color}]\n[dim]{asset_info.get('id', 'N/A')}[/dim]",
            title="[bold]Earth Engine Asset Info[/bold]",
            border_style=color,
            box=rich.box.DOUBLE
        ))

        # Basic Information Table
        basic_table = rich.table.Table(show_header=False, box=rich.box.SIMPLE, padding=(0, 2))
        basic_table.add_column("Property", style="bold cyan", width=20)
        basic_table.add_column("Value", style="white")

        basic_table.add_row("Name", asset_info.get('name', 'N/A'))
        basic_table.add_row("Type", f"[{color}]{asset_type}[/{color}]")

        if 'updateTime' in asset_info:
            basic_table.add_row("Last Updated", format_timestamp(asset_info['updateTime']))

        if 'sizeBytes' in asset_info:
            size_bytes = int(asset_info['sizeBytes'])
            basic_table.add_row("Size", f"{format_bytes(size_bytes)} ({size_bytes:,} bytes)")

        console.print(basic_table)
        console.print()

        # Temporal Information (for IMAGES)
        if asset_type == 'IMAGE' and ('startTime' in asset_info or 'endTime' in asset_info):
            temporal_table = rich.table.Table(title="Temporal Coverage", box=rich.box.ROUNDED, border_style="blue")
            temporal_table.add_column("Period", style="bold")
            temporal_table.add_column("Date", style="cyan")

            if 'startTime' in asset_info:
                temporal_table.add_row("Start", format_timestamp(asset_info['startTime']))
            if 'endTime' in asset_info:
                temporal_table.add_row("End", format_timestamp(asset_info['endTime']))

            console.print(temporal_table)
            console.print()

        # Properties (for IMAGES)
        if 'properties' in asset_info and asset_info['properties']:
            props_table = rich.table.Table(title="Properties", box=rich.box.ROUNDED, border_style="green")
            props_table.add_column("Key", style="bold green")
            props_table.add_column("Value", style="white")

            for key, value in asset_info['properties'].items():
                props_table.add_row(key, str(value))

            console.print(props_table)
            console.print()

        # Bands Information (for IMAGES)
        if 'bands' in asset_info and asset_info['bands']:
            console.print(rich.panel.Panel("[bold cyan]Band Information[/bold cyan]", box=rich.box.ROUNDED))

            for idx, band in enumerate(asset_info['bands'], 1):
                tree = rich.tree.Tree(f"[bold yellow]Band {idx}: {band.get('id', 'Unknown')}[/bold yellow]")

                # Data Type
                if 'dataType' in band:
                    dt = band['dataType']
                    dt_node = tree.add("[cyan]Data Type[/cyan]")
                    dt_node.add(f"Precision: {dt.get('precision', 'N/A')}")
                    if 'range' in dt:
                        dt_node.add(f"Range: {dt['range']}")

                # Grid Information
                if 'grid' in band:
                    grid = band['grid']
                    grid_node = tree.add("[magenta]Grid[/magenta]")
                    grid_node.add(f"CRS: {grid.get('crsCode', 'N/A')}")

                    if 'dimensions' in grid:
                        dims = grid['dimensions']
                        grid_node.add(f"Dimensions: {dims.get('width')} × {dims.get('height')}")

                    if 'affineTransform' in grid:
                        transform = grid['affineTransform']
                        res_x = abs(transform.get('scaleX', 0))
                        res_y = abs(transform.get('scaleY', 0))
                        grid_node.add(f"Resolution: {res_x}° × {res_y}°")

                # Pyramiding Policy
                if 'pyramidingPolicy' in band:
                    tree.add(f"[green]Pyramiding:[/green] {band['pyramidingPolicy']}")

                console.print(tree)
                console.print()

        # Geometry (for IMAGES)
        if 'geometry' in asset_info:
            geom = asset_info['geometry']

            # Check if geometry is unbounded
            is_unbounded = False
            if asset_type == 'IMAGE':
                try:
                    image = ee.Image(asset_id)
                    is_unbounded = image.geometry().isUnbounded().getInfo()
                except Exception:
                    # Fallback: check for infinity in coordinates
                    coords_str = str(geom.get('coordinates', []))
                    is_unbounded = 'Infinity' in coords_str or '-Infinity' in coords_str

            if is_unbounded:
                console.print(rich.panel.Panel(
                    "[bold]Unbounded[/bold]",
                    title="Geometry",
                    border_style="blue",
                    box=rich.box.ROUNDED
                ))
                console.print()
            else:
                geom_content = f"[bold]Type:[/bold] {geom.get('type', 'N/A')}\n"
                coords = geom.get('coordinates', [])
                if coords:
                    geom_content += f"[dim]Coordinates available ({len(str(coords))} chars)[/dim]"

                console.print(rich.panel.Panel(
                    geom_content,
                    title="Geometry",
                    border_style="blue",
                    box=rich.box.ROUNDED
                ))
                console.print()

        return asset_info

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        return None
