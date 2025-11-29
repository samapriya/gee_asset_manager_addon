"""
Google Earth Engine Batch Asset Manager with Addons
"""

from .acl_changer import access
from .app2script import jsext
from .batch_copy import copy
from .batch_delete import delete
from .batch_mover import mover
from .color_brewer import PYPERCLIP_AVAILABLE, generate_palette
from .color_brewer import list_palettes as list_color_palettes
from .color_brewer import load_palettes
from .ee_asset_info import display_asset_info
from .ee_del_meta import delprop
from .ee_projects import get_projects
from .ee_projects_dash import get_projects_with_dashboard
from .ee_report import ee_report
from .search_fast import EnhancedGEESearch

__copyright__ = """
    Copyright 2025 Samapriya Roy
    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at
       http://www.apache.org/licenses/LICENSE-2.0
    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""
__license__ = "Apache 2.0"

import importlib.metadata
import json
import os
import subprocess
import sys
import time
import webbrowser
from datetime import datetime

import click
import ee
import requests
from click import Group
from google.auth.transport.requests import AuthorizedSession
from packaging import version as pkg_version
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.tree import Tree
from tqdm import tqdm


class OrderedGroup(Group):
    def list_commands(self, ctx):
        return list(self.commands)

console = Console()

# Deprecated command mapping
DEPRECATED_COMMANDS = {
    'quota': 'projects quota',
    'projects': 'projects enabled',
    'projects_dash': 'projects dashboard',
    'tasks': 'tasks list',
    'cancel': 'tasks cancel',
    'copy': 'assets copy',
    'move': 'assets move',
    'access': 'assets access',
    'delete': 'assets delete',
    'delete_metadata': 'assets delete-meta',
    'app2script': 'utils app2script',
    'search': 'utils search',
    'ee_report': 'utils report',
    'assetsize': 'assets size',
}

os.chdir(os.path.dirname(os.path.realpath(__file__)))
lpath = os.path.dirname(os.path.realpath(__file__))
sys.path.append(lpath)

now = datetime.now()

# Initialize Earth Engine for all commands except help
if len(sys.argv) > 1 and sys.argv[1] not in ['-h', '--help', '--version']:
    # Handle deprecated 'projects' command by checking if it's being used without subcommands
    if sys.argv[1] == 'projects' and len(sys.argv) == 2:
        console.print(Panel(
            "[yellow]Command[/yellow] [bold red]'geeadd projects'[/bold red] [yellow]is deprecated![/yellow]\n\n"
            "[green]Use instead:[/green] [bold cyan]geeadd projects enabled[/bold cyan]\n\n"
            "[dim]Showing 'projects' group help instead...[/dim]",
            title="[bold red]Deprecated Usage[/bold red]",
            border_style="red"
        ))
    ee.Initialize(opt_url='https://earthengine-highvolume.googleapis.com')


def compare_version(version1, version2):
    """Compare two version strings using the packaging.version module."""
    v1 = pkg_version.parse(version1)
    v2 = pkg_version.parse(version2)
    if v1 > v2:
        return 1
    elif v1 < v2:
        return -1
    else:
        return 0


def get_latest_version(package):
    """Get the latest version of a package from PyPI."""
    try:
        response = requests.get(f"https://pypi.org/pypi/{package}/json", timeout=5)
        response.raise_for_status()
        return response.json()["info"]["version"]
    except (requests.RequestException, KeyError) as e:
        return None


def get_installed_version(package):
    """Get the installed version of a package using importlib.metadata."""
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return None


def check_package_version(package_name):
    """Check if the installed version of a package is the latest."""
    installed_version = get_installed_version(package_name)
    latest_version = get_latest_version(package_name)

    if not installed_version or not latest_version:
        return

    result = compare_version(latest_version, installed_version)

    if result == 1:
        console.print(Panel(
            f"[yellow]Current version:[/yellow] {installed_version}\n"
            f"[green]Latest version:[/green] {latest_version}\n\n"
            f"[cyan]Upgrade with:[/cyan] pip install --upgrade {package_name}",
            title=f"[bold red]Update Available for {package_name}[/bold red]",
            border_style="red"
        ))
    elif result == -1:
        console.print(Panel(
            f"[yellow]Running staging version {installed_version}[/yellow]\n"
            f"PyPI release: {latest_version}",
            title="[bold yellow]Development Version[/bold yellow]",
            border_style="yellow"
        ))


check_package_version("geeadd")

suffixes = ["B", "KB", "MB", "GB", "TB", "PB"]


def humansize(nbytes):
    """Convert bytes to human readable format."""
    i = 0
    while nbytes >= 1024 and i < len(suffixes) - 1:
        nbytes /= 1024.0
        i += 1
    f = ("%.2f" % nbytes).rstrip("0").rstrip(".")
    return f"{f} {suffixes[i]}"


def epoch_convert_time(epoch_timestamp):
    """Convert epoch timestamp to formatted datetime string."""
    dt_object = datetime.fromtimestamp(epoch_timestamp/1000)
    formatted_date_time = dt_object.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    return formatted_date_time


# Main CLI group
@click.group(
    cls=OrderedGroup,
    help="Google Earth Engine Batch Asset Manager with Addons\n\n"
         "A modern CLI tool for managing GEE assets, tasks, and projects.",
    context_settings=dict(help_option_names=['-h', '--help'])
)
@click.version_option(version=get_installed_version("geeadd"), prog_name="geeadd")
def cli():
    """Main entry point for geeadd CLI."""
    pass


# 1. README command (first)
@cli.command('readme', help="Open the geeadd documentation webpage")
def readme():
    """Open documentation in browser."""
    try:
        opened = webbrowser.open("https://geeadd.geetools.xyz/", new=2)
        if not opened:
            console.print("[yellow]Your setup does not have a monitor to display the webpage[/yellow]")
            console.print("[cyan]Go to: https://geeadd.geetools.xyz/[/cyan]")
        else:
            console.print("[green]Opening documentation in browser...[/green]")
    except Exception as e:
        console.print(f"[red]Error opening browser: {e}[/red]")
        console.print("[cyan]Visit: https://geeadd.geetools.xyz/[/cyan]")


# 2. Projects group (second)
@cli.group(help="Manage Earth Engine projects", context_settings=dict(help_option_names=['-h', '--help']))
def projects():
    """Project management commands."""
    pass


@projects.command('enabled', help="List Google Cloud Projects with Earth Engine API enabled")
def projects_enabled():
    """List all projects with EE enabled."""
    get_projects()


@projects.command('dashboard', help="Create interactive HTML dashboard of EE projects")
@click.option('--outdir', default=None, help='Output directory for dashboard files')
def projects_dashboard(outdir):
    """Generate projects dashboard."""
    get_projects_with_dashboard(output_dir=outdir)


@projects.command('quota', help="Display Earth Engine quota information")
@click.option('--project', default=None, help='Specific project path (e.g., projects/my-project or users/username)')
def projects_quota(project):
    """Display quota information."""
    session = AuthorizedSession(ee.data.get_persistent_credentials())

    def draw_bar(percent, width=30):
        """Draw a simple progress bar"""
        filled = int(width * percent / 100)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}] {percent:.1f}%"

    def display_quota_info(project_name, info, project_type="Project"):
        """Display quota info uniformly"""
        if "quota" in info:
            quota_info = info["quota"]

            table = Table(title=f"[bold cyan]{project_type}: {project_name}[/bold cyan]",
                         show_header=False, box=None)

            # Size quota
            used_size = int(quota_info.get("sizeBytes", 0))
            max_size = int(quota_info.get("maxSizeBytes", 1))
            percent = (used_size / max_size * 100) if max_size > 0 else 0

            table.add_row("[cyan]Storage:[/cyan]", f"{humansize(used_size)} of {humansize(max_size)}")
            table.add_row("", draw_bar(percent))

            # Asset count quota
            used_assets = int(quota_info.get("assetCount", 0))
            max_assets = int(quota_info.get("maxAssets", 1))
            percent = (used_assets / max_assets * 100) if max_assets > 0 else 0

            table.add_row("[cyan]Assets:[/cyan]", f"{used_assets:,} of {max_assets:,}")
            table.add_row("", draw_bar(percent))

            console.print(table)
            console.print()
            return True
        elif "asset_size" in info:
            # Legacy format
            table = Table(title=f"[bold cyan]{project_type}: {project_name}[/bold cyan]",
                         show_header=False, box=None)

            size_usage = info["asset_size"]["usage"]
            size_limit = info["asset_size"]["limit"]
            size_percent = (size_usage / size_limit * 100) if size_limit > 0 else 0

            count_usage = info["asset_count"]["usage"]
            count_limit = info["asset_count"]["limit"]
            count_percent = (count_usage / count_limit * 100) if count_limit > 0 else 0

            table.add_row("[cyan]Storage:[/cyan]", f"{humansize(size_usage)} of {humansize(size_limit)}")
            table.add_row("", draw_bar(size_percent))
            table.add_row("[cyan]Assets:[/cyan]", f"{count_usage:,} of {count_limit:,}")
            table.add_row("", draw_bar(count_percent))

            console.print(table)
            console.print()
            return True
        else:
            return False

    def get_legacy_roots():
        """Get all legacy root assets"""
        legacy_roots = []
        try:
            url = 'https://earthengine.googleapis.com/v1/projects/earthengine-legacy:listAssets'
            response = session.get(url=url)
            for asset in response.json().get('assets', []):
                legacy_roots.append(asset['id'])
        except Exception as e:
            console.print(f"[yellow]Warning: Could not retrieve legacy roots: {str(e)}[/yellow]")
        return legacy_roots

    def try_get_quota(path, is_legacy=False):
        """Try multiple methods to get quota for a given path"""
        try:
            asset_info = ee.data.getInfo(path)
            if asset_info and "quota" in asset_info:
                return asset_info
        except:
            pass

        if is_legacy:
            try:
                quota_info = ee.data.getAssetRootQuota(path)
                if quota_info:
                    return quota_info
            except:
                pass

        if path.startswith("projects/") and "/assets" not in path:
            for suffix in ["/assets", "/assets/"]:
                try:
                    asset_info = ee.data.getAsset(path + suffix)
                    if asset_info and "quota" in asset_info:
                        return asset_info
                except:
                    pass

        return None

    # If no path provided, display all projects
    if project is None:
        console.print("[bold cyan]Earth Engine Quota Summary[/bold cyan]\n")

        displayed_projects = set()
        found_any = False

        with console.status("[bold cyan]Fetching quota information...", spinner="dots"):
            try:
                roots = ee.data.getAssetRoots()

                for root in roots:
                    root_path = root["id"]
                    parent_project = root_path.split("/assets/")[0] if "/assets/" in root_path else root_path

                    if parent_project in displayed_projects:
                        continue

                    is_legacy = parent_project.startswith("users/")
                    quota_info = try_get_quota(parent_project, is_legacy=is_legacy)

                    if quota_info:
                        project_type = "Legacy Project" if is_legacy else "Cloud Project"
                        display_quota_info(parent_project, quota_info, project_type)
                        displayed_projects.add(parent_project)
                        found_any = True

            except Exception as e:
                console.print(f"[yellow]Warning: Could not list asset roots: {str(e)}[/yellow]")

            legacy_roots = get_legacy_roots()

            for legacy_path in legacy_roots:
                if legacy_path in displayed_projects:
                    continue

                quota_info = try_get_quota(legacy_path, is_legacy=True)

                if quota_info:
                    display_quota_info(legacy_path, quota_info, "Legacy Root")
                    displayed_projects.add(legacy_path)
                    found_any = True

        if not found_any:
            console.print("[yellow]No quota information available for any projects.[/yellow]")

        return

    # Handle specific project path
    if not project.startswith("projects/") and not project.startswith("users/"):
        try:
            cloud_path = f"projects/{project}"
            test_info = ee.data.getInfo(cloud_path)
            if test_info:
                project = cloud_path
        except:
            try:
                legacy_path = f"users/{project}"
                test_info = ee.data.getAssetRootQuota(legacy_path)
                if test_info:
                    project = legacy_path
            except:
                pass

    is_legacy = project.startswith("users/")
    quota_info = try_get_quota(project, is_legacy=is_legacy)

    if quota_info:
        project_type = "Legacy Project" if is_legacy else "Cloud Project"
        display_quota_info(project, quota_info, project_type)
    else:
        console.print(f"[red]Could not retrieve quota information for {project}[/red]")


# 3. Assets group (third)
@cli.group(help="Manage Earth Engine assets", context_settings=dict(help_option_names=['-h', '--help']))
def assets():
    """Asset management commands."""
    pass


@assets.command('info', help="Display detailed information about an Earth Engine asset")
@click.argument('asset_id', required=True)
def assets_info(asset_id):
    """Display detailed asset information with beautiful formatting."""
    display_asset_info(asset_id)


@assets.command('copy', help="Copy folders, collections, images or tables")
@click.option('--initial', required=True, help='Existing path of assets')
@click.option('--final', required=True, help='New path for assets')
def assets_copy(initial, final):
    """Copy assets."""
    copy(path=initial, fpath=final)


@assets.command('move', help="Move folders, collections, images or tables")
@click.option('--initial', required=True, help='Existing path of assets')
@click.option('--final', required=True, help='New path for assets')
@click.option('--no-cleanup', 'cleanup', is_flag=True, default=True,
              help='Keep empty source folders after moving')
def assets_move(initial, final, cleanup):
    """Move assets."""
    mover(path=initial, fpath=final, cleanup=cleanup)


@assets.command('access', help="Set permissions for assets")
@click.option('--asset', required=True, help='Path to the Earth Engine asset')
@click.option('--user', required=True, help='User email, service account, group, or "allUsers"')
@click.option('--role', required=True, type=click.Choice(['reader', 'writer', 'delete']),
              help='Permission role')
def assets_access(asset, user, role):
    """Set asset permissions."""
    access(collection_path=asset, user=user, role=role)


@assets.command('delete', help="Delete folders or collections recursively")
@click.option('--id', 'asset_id', required=True, help='Full path to asset for deletion')
@click.option('--workers', default=5, help='Number of concurrent workers')
@click.option('--retries', default=5, help='Maximum retry attempts per asset')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose debug logging')
def assets_delete(asset_id, workers, retries, verbose):
    """Delete assets recursively."""
    delete(ids=asset_id, max_workers=workers, max_retries=retries, verbose=verbose)


@assets.command('delete-meta', help="Delete metadata from collection or image")
@click.option('--asset', required=True, help='Path to the Earth Engine asset')
@click.option('--property', required=True, help='Metadata property name to delete')
def assets_delete_meta(asset, property):
    """Delete asset metadata."""
    delprop(collection_path=asset, property=property)


@assets.command('size', help="Display asset size and item count")
@click.argument('asset', required=True)
def assets_size(asset):
    """Print asset size information."""
    asset_info = ee.data.getAsset(asset)
    header = asset_info["type"]

    if header in ["IMAGE_COLLECTION", "IMAGE", "TABLE", "FEATURE_VIEW"]:
        with console.status(f"[bold cyan]Calculating size for {header}...", spinner="dots"):
            if header == "IMAGE_COLLECTION":
                collc = ee.ImageCollection(asset)
                size = sum(collc.aggregate_array("system:asset_size").getInfo())
                item_count = collc.size().getInfo()
            elif header == "IMAGE":
                collc = ee.ImageCollection.fromImages([ee.Image(asset)])
                size = sum(collc.aggregate_array("system:asset_size").getInfo())
                item_count = 1
            elif header == "TABLE":
                collc = ee.FeatureCollection(asset)
                size = float(collc.get("system:asset_size").getInfo())
                item_count = collc.size().getInfo()
            elif header == "FEATURE_VIEW":
                collc = ee.data.getAsset(asset)
                size = float(collc['sizeBytes'])
                item_count = collc['featureCount']

        table = Table(show_header=False, box=None)
        table.add_row("[cyan]Asset:[/cyan]", asset)
        table.add_row("[cyan]Type:[/cyan]", header.title())
        table.add_row("[cyan]Size:[/cyan]", humansize(size))
        table.add_row("[cyan]Items:[/cyan]", str(item_count))
        console.print(table)

    elif header == "FOLDER":
        with console.status("[bold cyan]Calculating folder size...", spinner="dots"):
            out = subprocess.check_output(f"earthengine du {asset} -s", shell=True).decode("ascii")
            size = humansize(float(out.split()[0]))
            num = subprocess.check_output(f"earthengine ls -r {asset}", shell=True).decode("ascii")
            num = [i for i in num.split("\n") if i and len(i) > 1 and not i.startswith("Running")]

        table = Table(show_header=False, box=None)
        table.add_row("[cyan]Folder:[/cyan]", asset)
        table.add_row("[cyan]Size:[/cyan]", size)
        table.add_row("[cyan]Total items:[/cyan]", str(len(num)))
        console.print(table)


# 4. Tasks group (fourth)
@cli.group(help="Manage Earth Engine tasks", context_settings=dict(help_option_names=['-h', '--help']))
def tasks():
    """Task management commands."""
    pass


@tasks.command('list', help="List tasks by state or get details of a specific task")
@click.option('--state', type=click.Choice(['COMPLETED', 'READY', 'RUNNING', 'FAILED', 'CANCELLED'], case_sensitive=False),
              help='Filter tasks by state')
@click.option('--id', 'task_id', help='Get details of a specific task ID')
def tasks_list(state, task_id):
    """Query current task status."""
    if state is not None:
        task_bundle = []
        operations = [
            status
            for status in ee.data.getTaskList()
            if status["state"] == state.upper()
        ]

        with console.status(f"[bold cyan]Fetching {state.upper()} tasks...", spinner="dots"):
            for operation in operations:
                task_id_val = operation["id"]
                description = operation["description"].split(":")[0]
                op_type = operation["task_type"]
                attempt_count = operation["attempt"]
                date_format = "%Y-%m-%dT%H:%M:%S.%fZ"
                start = datetime.strptime(epoch_convert_time(operation["start_timestamp_ms"]), date_format)
                end = datetime.strptime(epoch_convert_time(operation["update_timestamp_ms"]), date_format)
                time_difference = end - start
                item = {
                    "task_id": task_id_val,
                    "operation_type": op_type,
                    "description": description,
                    "run_time": str(time_difference),
                    "attempt": attempt_count,
                }
                if 'destination_uris' in operation:
                    item['item_path'] = operation['destination_uris'][0].replace('https://code.earthengine.google.com/?asset=', '')
                if 'batch_eecu_usage_seconds' in operation:
                    item['eecu_usage'] = operation['batch_eecu_usage_seconds']
                task_bundle.append(item)

        console.print_json(data=task_bundle)

    elif task_id is not None:
        operations = [
            status
            for status in ee.data.getTaskList()
            if status["id"] == task_id
        ]
        for operation in operations:
            task_id_val = operation["id"]
            description = operation["description"].split(":")[0]
            op_type = operation["task_type"]
            attempt_count = operation["attempt"]
            date_format = "%Y-%m-%dT%H:%M:%S.%fZ"
            start = datetime.strptime(epoch_convert_time(operation["start_timestamp_ms"]), date_format)
            end = datetime.strptime(epoch_convert_time(operation["update_timestamp_ms"]), date_format)
            time_difference = end - start
            item = {
                "task_id": task_id_val,
                "operation_type": op_type,
                "description": description,
                "run_time": str(time_difference),
                "attempt": attempt_count,
            }
            if 'destination_uris' in operation:
                item['item_path'] = operation['destination_uris'][0].replace('https://code.earthengine.google.com/?asset=', '')
            if 'batch_eecu_usage_seconds' in operation:
                item['eecu_usage'] = operation['batch_eecu_usage_seconds']
            console.print_json(data=item)
    else:
        statuses = ee.data.getTaskList()
        st = []
        for status in statuses:
            st.append(status["state"])

        table = Table(title="[bold cyan]Task Summary[/bold cyan]", show_header=True, header_style="bold magenta")
        table.add_column("Status", style="cyan", width=20)
        table.add_column("Count", justify="right", style="green")

        table.add_row("Running", str(st.count('RUNNING')))
        table.add_row("Pending", str(st.count('READY')))
        table.add_row("Completed", str(st.count('COMPLETED') + st.count('SUCCEEDED')))
        table.add_row("Failed", str(st.count('FAILED')))
        table.add_row("Cancelled", str(st.count('CANCELLED') + st.count('CANCELLING')))

        console.print(table)


@tasks.command('cancel', help="Cancel tasks (all, running, pending, or specific task ID)")
@click.argument('target', type=str, required=True)
def tasks_cancel(target):
    """Cancel Earth Engine tasks."""
    try:
        if target == "all":
            console.print("[bold yellow]Attempting to cancel all tasks...[/bold yellow]")
            statuses = ee.data.getTaskList()
            cancelled_count = 0

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console
            ) as progress:
                task = progress.add_task("[cyan]Cancelling tasks...", total=len(statuses))

                for status in statuses:
                    state = status['state']
                    task_id = status['id']

                    if state == 'READY' or state == 'RUNNING':
                        try:
                            ee.data.cancelTask(task_id)
                            cancelled_count += 1
                        except ee.EEException as e:
                            console.print(f"[red]Error cancelling task {task_id}: {e}[/red]")
                    progress.update(task, advance=1)

            if cancelled_count > 0:
                console.print(f"[green]Successfully cancelled {cancelled_count} tasks[/green]")
            else:
                console.print("[yellow]No running or pending tasks found to cancel[/yellow]")

        elif target == "running":
            console.print("[bold yellow]Attempting to cancel running tasks...[/bold yellow]")
            statuses = ee.data.getTaskList()
            running_tasks = [status for status in statuses if status['state'] == 'RUNNING']

            if running_tasks:
                with Progress(console=console) as progress:
                    task = progress.add_task("[cyan]Cancelling running tasks...", total=len(running_tasks))
                    cancelled_count = 0
                    for status in running_tasks:
                        try:
                            ee.data.cancelTask(status['id'])
                            cancelled_count += 1
                        except ee.EEException as e:
                            console.print(f"[red]Error cancelling task {status['id']}: {e}[/red]")
                        progress.update(task, advance=1)
                console.print(f"[green]Successfully cancelled {cancelled_count} running tasks[/green]")
            else:
                console.print("[yellow]No running tasks found[/yellow]")

        elif target == "pending":
            console.print("[bold yellow]Attempting to cancel pending tasks...[/bold yellow]")
            statuses = ee.data.getTaskList()
            pending_tasks = [status for status in statuses if status['state'] == 'READY']

            if pending_tasks:
                with Progress(console=console) as progress:
                    task = progress.add_task("[cyan]Cancelling pending tasks...", total=len(pending_tasks))
                    cancelled_count = 0
                    for status in pending_tasks:
                        try:
                            ee.data.cancelTask(status['id'])
                            cancelled_count += 1
                        except ee.EEException as e:
                            console.print(f"[red]Error cancelling task {status['id']}: {e}[/red]")
                        progress.update(task, advance=1)
                console.print(f"[green]Successfully cancelled {cancelled_count} pending tasks[/green]")
            else:
                console.print("[yellow]No pending tasks found[/yellow]")

        else:
            # Assume it's a task ID
            console.print(f"[bold yellow]Attempting to cancel task: {target}[/bold yellow]")

            try:
                statuses = ee.data.getTaskStatus([target])
                if not statuses:
                    console.print(f"[red]Task {target} not found[/red]")
                    return

                status = statuses[0]
                state = status['state']

                if state == 'UNKNOWN':
                    console.print(f"[red]Unknown task ID: {target}[/red]")
                elif state in ['READY', 'RUNNING']:
                    ee.data.cancelTask(target)
                    console.print(f"[green]Successfully cancelled task {target}[/green]")
                else:
                    console.print(f"[yellow]Task {target} is already in state '{state}' and cannot be cancelled[/yellow]")
            except ee.EEException as e:
                console.print(f"[red]Error accessing task {target}: {e}[/red]")

    except Exception as e:
        console.print(f"[red]Error in cancel_tasks: {e}[/red]")


# 5. Utils group (fifth)
@cli.group(help="Utility commands", context_settings=dict(help_option_names=['-h', '--help']))
def utils():
    """Utility commands."""
    pass


@utils.command('app2script', help="Extract script from public Earth Engine app")
@click.option('--url', required=True, help='Earth Engine app URL')
@click.option('--outfile', default=None, help='Output .js file path')
def utils_app2script(url, outfile):
    """Get underlying script from EE app."""
    jsext(url=url, outfile=outfile)


@utils.command('search', help="Search GEE catalog with relevance ranking")
@click.option('--keywords', required=True, help='Search keywords')
@click.option('--source', type=click.Choice(['main', 'community']), default=None,
              help='Catalog to search (main, community, or both)')
@click.option('--max-results', default=5, help='Maximum number of results')
@click.option('--include-docs', is_flag=True, help='Search documentation URLs')
@click.option('--allow-subsets', is_flag=True, help='Show all regional/temporal variants')
def utils_search(keywords, source, max_results, include_docs, allow_subsets):
    """Search GEE catalog."""
    search_engine = EnhancedGEESearch()

    if source is not None and source == "community":
        search_source = 'community'
    elif source is not None and source == "main":
        search_source = 'main'
    else:
        search_source = 'both'

    search_engine.load_datasets(source=search_source)

    results = search_engine.search(
        query=keywords,
        max_results=max_results,
        include_docs=include_docs,
        allow_subsets=allow_subsets,
        source=search_source
    )

    console.print_json(data=results)


@utils.command('report', help="Generate detailed asset report")
@click.option('--outfile', required=True, help='Output file path for report')
@click.option('--path', default=None, help='Path to folder or project')
@click.option('--format', 'output_format', default='csv',
              type=click.Choice(['csv', 'json']), help='Output format')
def utils_report(outfile, path, output_format):
    """Generate Earth Engine asset report."""
    ee_report(output_path=outfile, asset_path=path, output_format=output_format)


@utils.command('palette', help="Generate ColorBrewer color palettes for data visualization")
@click.option('--name', help='Palette name (e.g., Blues, RdYlGn, Set1)')
@click.option('--classes', type=int, help='Number of colors to generate (minimum 3)')
@click.option('--list', 'show_list', is_flag=True, help='List all available palettes')
@click.option('--type', 'palette_type',
              type=click.Choice(['sequential', 'diverging', 'qualitative']),
              help='Filter palette list by type')
@click.option('--format', 'output_format',
              type=click.Choice(['json', 'hex', 'list', 'css', 'python', 'js']),
              default='json',
              help='Output format')
@click.option('--copy', 'auto_copy', is_flag=True,
              help='Automatically copy output to clipboard')
def utils_palette(name, classes, show_list, palette_type, output_format, auto_copy):
    """
    Generate ColorBrewer color palettes for data visualization.

    Inspired by https://colorbrewer2.org/

    \b
    Output Formats:
      json   - JSON array (default)
      hex    - Hex codes, one per line
      list   - Comma-separated hex codes
      css    - CSS custom properties
      python - Python list variable
      js     - JavaScript array constant

    \b
    Examples:

    \b
      # List all available palettes
      geeadd utils palette --list

    \b
      # List only sequential palettes
      geeadd utils palette --list --type sequential

    \b
      # Generate 5 colors from Blues palette
      geeadd utils palette --name Blues --classes 5

    \b
      # Generate colors in hex format and copy to clipboard
      geeadd utils palette --name RdYlGn --classes 9 --format hex --copy

    \b
      # Generate CSS custom properties
      geeadd utils palette --name Set1 --classes 8 --format css

    \b
      # Generate Python list
      geeadd utils palette --name Spectral --classes 11 --format python --copy

    \b
      # Generate JavaScript array
      geeadd utils palette --name Blues --classes 7 --format js --copy
    """
    if show_list:
        palettes = load_palettes()
        list_color_palettes(palettes, palette_type)

        # Show clipboard availability info
        if not PYPERCLIP_AVAILABLE:
            console.print("\n[dim]💡 Tip: Install pyperclip for clipboard support: pip install pyperclip[/dim]")

    elif name and classes:
        generate_palette(name, classes, output_format, auto_copy)
    else:
        console.print("[red]Error: Either use --list or provide both --name and --classes[/red]")
        console.print("\n[yellow]Examples:[/yellow]")
        console.print("  geeadd utils palette --list")
        console.print("  geeadd utils palette --name Blues --classes 5")
        console.print("  geeadd utils palette --name RdYlGn --classes 9 --format hex --copy")
        sys.exit(1)


# ============================================================================
# DEPRECATED COMMAND HANDLERS - Show migration messages
# ============================================================================

@cli.command('quota', hidden=True)
@click.option('--project', default=None)
@click.pass_context
def deprecated_quota(ctx, project):
    """Deprecated: Use 'geeadd projects quota' instead."""
    console.print(Panel(
        "[yellow]Command[/yellow] [bold red]'geeadd quota'[/bold red] [yellow]is deprecated![/yellow]\n\n"
        "[green]Use instead:[/green] [bold cyan]geeadd projects quota[/bold cyan]\n\n"
        "[dim]Redirecting you to the new command...[/dim]",
        title="[bold red]Deprecated Command[/bold red]",
        border_style="red"
    ))
    ctx.invoke(projects_quota, project=project)


@cli.command('deprecated-projects', hidden=True)
@click.pass_context
def deprecated_projects_old(ctx):
    """Deprecated: Use 'geeadd projects enabled' instead."""
    console.print(Panel(
        "[yellow]Command[/yellow] [bold red]'geeadd projects'[/bold red] [yellow]is deprecated![/yellow]\n\n"
        "[green]Use instead:[/green] [bold cyan]geeadd projects enabled[/bold cyan]\n\n"
        "[dim]Redirecting you to the new command...[/dim]",
        title="[bold red]Deprecated Command[/bold red]",
        border_style="red"
    ))
    ctx.invoke(projects_enabled)


@cli.command('projects_dash', hidden=True)
@click.option('--outdir', default=None)
@click.pass_context
def deprecated_projects_dash(ctx, outdir):
    """Deprecated: Use 'geeadd projects dashboard' instead."""
    console.print(Panel(
        "[yellow]Command[/yellow] [bold red]'geeadd projects_dash'[/bold red] [yellow]is deprecated![/yellow]\n\n"
        "[green]Use instead:[/green] [bold cyan]geeadd projects dashboard[/bold cyan]\n\n"
        "[dim]Redirecting you to the new command...[/dim]",
        title="[bold red]Deprecated Command[/bold red]",
        border_style="red"
    ))
    ctx.invoke(projects_dashboard, outdir=outdir)


@cli.command('cancel', hidden=True)
@click.argument('tasks_arg', required=True)
@click.pass_context
def deprecated_cancel(ctx, tasks_arg):
    """Deprecated: Use 'geeadd tasks cancel' instead."""
    console.print(Panel(
        "[yellow]Command[/yellow] [bold red]'geeadd cancel'[/bold red] [yellow]is deprecated![/yellow]\n\n"
        "[green]Use instead:[/green] [bold cyan]geeadd tasks cancel[/bold cyan]\n\n"
        "[dim]Redirecting you to the new command...[/dim]",
        title="[bold red]Deprecated Command[/bold red]",
        border_style="red"
    ))
    ctx.invoke(tasks_cancel, target=tasks_arg)


@cli.command('copy', hidden=True)
@click.option('--initial', required=True)
@click.option('--final', required=True)
@click.pass_context
def deprecated_copy(ctx, initial, final):
    """Deprecated: Use 'geeadd assets copy' instead."""
    console.print(Panel(
        "[yellow]Command[/yellow] [bold red]'geeadd copy'[/bold red] [yellow]is deprecated![/yellow]\n\n"
        "[green]Use instead:[/green] [bold cyan]geeadd assets copy[/bold cyan]\n\n"
        "[dim]Redirecting you to the new command...[/dim]",
        title="[bold red]Deprecated Command[/bold red]",
        border_style="red"
    ))
    ctx.invoke(assets_copy, initial=initial, final=final)


@cli.command('move', hidden=True)
@click.option('--initial', required=True)
@click.option('--final', required=True)
@click.option('--no-cleanup', 'cleanup', is_flag=True, default=True)
@click.pass_context
def deprecated_move(ctx, initial, final, cleanup):
    """Deprecated: Use 'geeadd assets move' instead."""
    console.print(Panel(
        "[yellow]Command[/yellow] [bold red]'geeadd move'[/bold red] [yellow]is deprecated![/yellow]\n\n"
        "[green]Use instead:[/green] [bold cyan]geeadd assets move[/bold cyan]\n\n"
        "[dim]Redirecting you to the new command...[/dim]",
        title="[bold red]Deprecated Command[/bold red]",
        border_style="red"
    ))
    ctx.invoke(assets_move, initial=initial, final=final, cleanup=cleanup)


@cli.command('access', hidden=True)
@click.option('--asset', required=True)
@click.option('--user', required=True)
@click.option('--role', required=True)
@click.pass_context
def deprecated_access(ctx, asset, user, role):
    """Deprecated: Use 'geeadd assets access' instead."""
    console.print(Panel(
        "[yellow]Command[/yellow] [bold red]'geeadd access'[/bold red] [yellow]is deprecated![/yellow]\n\n"
        "[green]Use instead:[/green] [bold cyan]geeadd assets access[/bold cyan]\n\n"
        "[dim]Redirecting you to the new command...[/dim]",
        title="[bold red]Deprecated Command[/bold red]",
        border_style="red"
    ))
    ctx.invoke(assets_access, asset=asset, user=user, role=role)


@cli.command('delete', hidden=True)
@click.option('--id', 'asset_id', required=True)
@click.option('--workers', default=5)
@click.option('--retries', default=5)
@click.option('--verbose', '-v', is_flag=True)
@click.pass_context
def deprecated_delete(ctx, asset_id, workers, retries, verbose):
    """Deprecated: Use 'geeadd assets delete' instead."""
    console.print(Panel(
        "[yellow]Command[/yellow] [bold red]'geeadd delete'[/bold red] [yellow]is deprecated![/yellow]\n\n"
        "[green]Use instead:[/green] [bold cyan]geeadd assets delete[/bold cyan]\n\n"
        "[dim]Redirecting you to the new command...[/dim]",
        title="[bold red]Deprecated Command[/bold red]",
        border_style="red"
    ))
    ctx.invoke(assets_delete, asset_id=asset_id, workers=workers, retries=retries, verbose=verbose)


@cli.command('delete_metadata', hidden=True)
@click.option('--asset', required=True)
@click.option('--property', required=True)
@click.pass_context
def deprecated_delete_metadata(ctx, asset, property):
    """Deprecated: Use 'geeadd assets delete-meta' instead."""
    console.print(Panel(
        "[yellow]Command[/yellow] [bold red]'geeadd delete_metadata'[/bold red] [yellow]is deprecated![/yellow]\n\n"
        "[green]Use instead:[/green] [bold cyan]geeadd assets delete-meta[/bold cyan]\n\n"
        "[dim]Redirecting you to the new command...[/dim]",
        title="[bold red]Deprecated Command[/bold red]",
        border_style="red"
    ))
    ctx.invoke(assets_delete_meta, asset=asset, property=property)


@cli.command('app2script', hidden=True)
@click.option('--url', required=True)
@click.option('--outfile', default=None)
@click.pass_context
def deprecated_app2script(ctx, url, outfile):
    """Deprecated: Use 'geeadd utils app2script' instead."""
    console.print(Panel(
        "[yellow]Command[/yellow] [bold red]'geeadd app2script'[/bold red] [yellow]is deprecated![/yellow]\n\n"
        "[green]Use instead:[/green] [bold cyan]geeadd utils app2script[/bold cyan]\n\n"
        "[dim]Redirecting you to the new command...[/dim]",
        title="[bold red]Deprecated Command[/bold red]",
        border_style="red"
    ))
    ctx.invoke(utils_app2script, url=url, outfile=outfile)


@cli.command('search', hidden=True)
@click.option('--keywords', required=True)
@click.option('--source', default=None)
@click.option('--max-results', default=5)
@click.option('--include-docs', is_flag=True)
@click.option('--allow-subsets', is_flag=True)
@click.pass_context
def deprecated_search(ctx, keywords, source, max_results, include_docs, allow_subsets):
    """Deprecated: Use 'geeadd utils search' instead."""
    console.print(Panel(
        "[yellow]Command[/yellow] [bold red]'geeadd search'[/bold red] [yellow]is deprecated![/yellow]\n\n"
        "[green]Use instead:[/green] [bold cyan]geeadd utils search[/bold cyan]\n\n"
        "[dim]Redirecting you to the new command...[/dim]",
        title="[bold red]Deprecated Command[/bold red]",
        border_style="red"
    ))
    ctx.invoke(utils_search, keywords=keywords, source=source, max_results=max_results,
               include_docs=include_docs, allow_subsets=allow_subsets)


@cli.command('ee_report', hidden=True)
@click.option('--outfile', required=True)
@click.option('--path', default=None)
@click.option('--format', 'output_format', default='csv')
@click.pass_context
def deprecated_ee_report(ctx, outfile, path, output_format):
    """Deprecated: Use 'geeadd utils report' instead."""
    console.print(Panel(
        "[yellow]Command[/yellow] [bold red]'geeadd ee_report'[/bold red] [yellow]is deprecated![/yellow]\n\n"
        "[green]Use instead:[/green] [bold cyan]geeadd utils report[/bold cyan]\n\n"
        "[dim]Redirecting you to the new command...[/dim]",
        title="[bold red]Deprecated Command[/bold red]",
        border_style="red"
    ))
    ctx.invoke(utils_report, outfile=outfile, path=path, output_format=output_format)


@cli.command('assetsize', hidden=True)
@click.argument('asset', required=True)
@click.pass_context
def deprecated_assetsize(ctx, asset):
    """Deprecated: Use 'geeadd assets size' instead."""
    console.print(Panel(
        "[yellow]Command[/yellow] [bold red]'geeadd assetsize'[/bold red] [yellow]is deprecated![/yellow]\n\n"
        "[green]Use instead:[/green] [bold cyan]geeadd assets size[/bold cyan]\n\n"
        "[dim]Redirecting you to the new command...[/dim]",
        title="[bold red]Deprecated Command[/bold red]",
        border_style="red"
    ))
    ctx.invoke(assets_size, asset=asset)


def main():
    """Main entry point."""
    cli()
