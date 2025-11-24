"""
ColorBrewer palette generator
Inspired by https://colorbrewer2.org/
"""

import json
import sys
from pathlib import Path
from typing import List, Optional
from rich.console import Console
from rich.table import Table

console = Console()

# Try to import pyperclip, but make it optional
try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False


def load_palettes():
    """Load palette data from palettes.json"""
    palette_file = Path(__file__).parent / "palettes.json"
    try:
        with open(palette_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        console.print(f"[red]Error: palettes.json not found in {palette_file.parent}[/red]")
        sys.exit(1)
    except json.JSONDecodeError as e:
        console.print(f"[red]Error: Invalid JSON in palettes.json: {e}[/red]")
        sys.exit(1)


def interpolate_color(c1: str, c2: str, factor: float) -> str:
    """Interpolate between two hex colors (without # prefix)"""
    r1, g1, b1 = int(c1[0:2], 16), int(c1[2:4], 16), int(c1[4:6], 16)
    r2, g2, b2 = int(c2[0:2], 16), int(c2[2:4], 16), int(c2[4:6], 16)
    
    r = int(r1 + (r2 - r1) * factor)
    g = int(g1 + (g2 - g1) * factor)
    b = int(b1 + (b2 - b1) * factor)
    
    return f"{r:02x}{g:02x}{b:02x}"


def interpolate_palette(colors: List[str], target: int) -> List[str]:
    """Interpolate palette to target number of colors"""
    if target <= len(colors):
        return colors[:target]
    
    result = []
    segment = (len(colors) - 1) / (target - 1)
    
    for i in range(target):
        pos = i * segment
        lower = int(pos)
        upper = min(lower + 1, len(colors) - 1)
        factor = pos - lower
        
        if lower == upper:
            result.append(colors[lower])
        else:
            result.append(interpolate_color(colors[lower], colors[upper], factor))
    
    return result


def get_palette(name: str, classes: int, palettes: dict) -> List[str]:
    """Get palette with specified number of classes"""
    if name not in palettes:
        available = sorted(palettes.keys())
        console.print(f"[red]Error: Palette '{name}' not found[/red]")
        console.print(f"[yellow]Available palettes: {', '.join(available)}[/yellow]")
        sys.exit(1)
    
    palette = palettes[name]
    available_sizes = sorted([int(k) for k in palette.keys() if k.isdigit()])
    
    if classes < 3:
        console.print(f"[red]Error: Minimum 3 classes required[/red]")
        sys.exit(1)
    
    # Exact match
    if classes in available_sizes:
        return palette[str(classes)]
    
    # Too small - return minimum
    if classes < min(available_sizes):
        return palette[str(min(available_sizes))][:classes]
    
    # Too large - interpolate from maximum
    if classes > max(available_sizes):
        return interpolate_palette(palette[str(max(available_sizes))], classes)
    
    # Between sizes - interpolate
    lower = max([s for s in available_sizes if s < classes])
    return interpolate_palette(palette[str(lower)], classes)


def list_palettes(palettes: dict, palette_type: Optional[str] = None):
    """List all available palettes using rich tables"""
    sequential = []
    diverging = []
    qualitative = []
    
    for name, data in sorted(palettes.items()):
        ptype = data.get("type", "unknown")
        sizes = sorted([int(k) for k in data.keys() if k.isdigit()])
        
        if ptype == "sequential":
            sequential.append((name, min(sizes), max(sizes)))
        elif ptype == "diverging":
            diverging.append((name, min(sizes), max(sizes)))
        elif ptype == "qualitative":
            qualitative.append((name, min(sizes), max(sizes)))
    
    if palette_type is None or palette_type == "sequential":
        table = Table(title="[bold cyan]Sequential Palettes[/bold cyan]", show_header=True)
        table.add_column("Palette", style="cyan", width=15)
        table.add_column("Colors", style="green", justify="right")
        
        for name, min_size, max_size in sequential:
            table.add_row(name, f"{min_size}-{max_size}")
        
        console.print(table)
        console.print()
    
    if palette_type is None or palette_type == "diverging":
        table = Table(title="[bold magenta]Diverging Palettes[/bold magenta]", show_header=True)
        table.add_column("Palette", style="magenta", width=15)
        table.add_column("Colors", style="green", justify="right")
        
        for name, min_size, max_size in diverging:
            table.add_row(name, f"{min_size}-{max_size}")
        
        console.print(table)
        console.print()
    
    if palette_type is None or palette_type == "qualitative":
        table = Table(title="[bold yellow]Qualitative Palettes[/bold yellow]", show_header=True)
        table.add_column("Palette", style="yellow", width=15)
        table.add_column("Colors", style="green", justify="right")
        
        for name, min_size, max_size in qualitative:
            table.add_row(name, f"{min_size}-{max_size}")
        
        console.print(table)


def copy_to_clipboard(text: str) -> bool:
    """Copy text to clipboard if pyperclip is available"""
    if not PYPERCLIP_AVAILABLE:
        return False
    
    try:
        pyperclip.copy(text)
        return True
    except Exception:
        return False


def generate_palette(name: str, classes: int, output_format: str = 'json', auto_copy: bool = False):
    """Generate a color palette"""
    palettes = load_palettes()
    colors = get_palette(name, classes, palettes)
    
    output_text = ""
    
    if output_format == 'json':
        output_text = json.dumps(colors)
        console.print_json(data=colors)
    elif output_format == 'hex':
        hex_colors = [f"#{c}" for c in colors]
        output_text = "\n".join(hex_colors)
        for color in hex_colors:
            console.print(color)
    elif output_format == 'list':
        hex_colors = [f"#{c}" for c in colors]
        output_text = ", ".join(hex_colors)
        console.print(output_text)
    elif output_format == 'css':
        css_output = f"/* {name} palette - {classes} colors */\n"
        css_output += ":root {\n"
        for i, color in enumerate(colors, 1):
            css_output += f"  --color-{name.lower()}-{i}: #{color};\n"
        css_output += "}"
        output_text = css_output
        console.print(css_output)
    elif output_format == 'python':
        python_output = f"# {name} palette - {classes} colors\n"
        python_output += f"{name.upper()}_PALETTE = [\n"
        for color in colors:
            python_output += f"    '#{color}',\n"
        python_output += "]"
        output_text = python_output
        console.print(python_output)
    elif output_format == 'js':
        js_output = f"// {name} palette - {classes} colors\n"
        js_output += f"const {name.lower()}Palette = [\n"
        for color in colors:
            js_output += f"  '#{color}',\n"
        js_output += "];"
        output_text = js_output
        console.print(js_output)
    
    # Auto-copy to clipboard if enabled and available
    if auto_copy:
        if copy_to_clipboard(output_text):
            console.print("\n[green]✓ Copied to clipboard![/green]")
        else:
            if not PYPERCLIP_AVAILABLE:
                console.print("\n[yellow]⚠ Clipboard copy not available. Install pyperclip: pip install pyperclip[/yellow]")
            else:
                console.print("\n[yellow]⚠ Could not copy to clipboard[/yellow]")
    
    return colors
