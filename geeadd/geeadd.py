#! /usr/bin/env python

from .acl_changer import access
from .app2script import jsext
from .batch_copy import copy
from .batch_delete import delete
from .batch_mover import mover
from .ee_del_meta import delprop
from .ee_projects import get_projects
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

import argparse
import concurrent.futures
import importlib.metadata
import json
import os
import subprocess
import sys
import time
import webbrowser
from datetime import datetime

import ee
import requests
from colorama import Fore, Style, init
from packaging import version as pkg_version
from tqdm import tqdm

os.chdir(os.path.dirname(os.path.realpath(__file__)))
lpath = os.path.dirname(os.path.realpath(__file__))
sys.path.append(lpath)

now = datetime.now()

if len(sys.argv) > 1 and sys.argv[1] != "-h":
    ee.Initialize(opt_url='https://earthengine-highvolume.googleapis.com')
# Initialize colorama for cross-platform colored terminal output
init(autoreset=True)


def compare_version(version1, version2):
    """
    Compare two version strings using the packaging.version module.
    Returns: 1 if version1 > version2, -1 if version1 < version2, 0 if equal
    """
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
        print(f"Error fetching version for {package}: {e}")
        return None


def get_installed_version(package):
    """Get the installed version of a package using importlib.metadata."""
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        print(f"Package {package} is not installed")
        return None


def check_package_version(package_name):
    """Check if the installed version of a package is the latest."""
    installed_version = get_installed_version(package_name)
    latest_version = get_latest_version(package_name)

    if not installed_version or not latest_version:
        return

    result = compare_version(latest_version, installed_version)
    border = Style.BRIGHT + "========================================================================="

    if result == 1:
        print(f"\n{border}")
        print(Fore.RED + f"Current version of {package_name} is {installed_version} "
              f"upgrade to latest version: {latest_version}" + Style.RESET_ALL)
        print(f"{border}")
    elif result == -1:
        print(f"\n{border}")
        print(Fore.YELLOW + f"Possibly running staging code {installed_version} "
              f"compared to PyPI release {latest_version}" + Style.RESET_ALL)
        print(f"{border}")
    # Removed the else branch to avoid printing "up to date" message

check_package_version("geeadd")

# Go to the readMe
def readme():
    try:
        a = webbrowser.open(
            "https://samapriya.github.io/gee_asset_manager_addon/", new=2
        )
        if a == False:
            print("Your setup does not have a monitor to display the webpage")
            print(
                " Go to {}".format(
                    "https://samapriya.github.io/gee_asset_manager_addon/"
                )
            )
    except Exception as e:
        print(e)


suffixes = ["B", "KB", "MB", "GB", "TB", "PB"]


def humansize(nbytes):
    i = 0
    while nbytes >= 1024 and i < len(suffixes) - 1:
        nbytes /= 1024.0
        i += 1
    f = ("%.2f" % nbytes).rstrip("0").rstrip(".")
    return "%s %s" % (f, suffixes[i])


def cancel_tasks(tasks):
    """
    Cancels Earth Engine tasks based on specified criteria.

    Args:
        tasks: Can be "all", "running", "pending", or a specific task ID
    """
    try:
        if tasks == "all":
            # Use the task list approach from TaskCancelCommand
            print("Attempting to cancel all tasks")
            statuses = ee.data.getTaskList()
            cancelled_count = 0

            with tqdm(total=len(statuses), desc="Cancelling tasks") as pbar:
                for status in statuses:
                    state = status['state']
                    task_id = status['id']

                    if state == 'READY' or state == 'RUNNING':
                        try:
                            ee.data.cancelTask(task_id)
                            cancelled_count += 1
                        except ee.EEException as e:
                            print(f"Error cancelling task {task_id}: {e}")
                    pbar.update(1)

            if cancelled_count > 0:
                print(f"Successfully cancelled {cancelled_count} tasks")
            else:
                print("No running or pending tasks found to cancel")

        elif tasks == "running":
            print("Attempting to cancel running tasks")
            statuses = ee.data.getTaskList()
            running_tasks = [status for status in statuses if status['state'] == 'RUNNING']

            if running_tasks:
                with tqdm(total=len(running_tasks), desc="Cancelling running tasks") as pbar:
                    cancelled_count = 0
                    for status in running_tasks:
                        try:
                            ee.data.cancelTask(status['id'])
                            cancelled_count += 1
                        except ee.EEException as e:
                            print(f"Error cancelling task {status['id']}: {e}")
                        pbar.update(1)
                print(f"Successfully cancelled {cancelled_count} running tasks")
            else:
                print("No running tasks found")

        elif tasks == "pending":
            print("Attempting to cancel pending tasks")
            statuses = ee.data.getTaskList()
            pending_tasks = [status for status in statuses if status['state'] == 'READY']

            if pending_tasks:
                with tqdm(total=len(pending_tasks), desc="Cancelling pending tasks") as pbar:
                    cancelled_count = 0
                    for status in pending_tasks:
                        try:
                            ee.data.cancelTask(status['id'])
                            cancelled_count += 1
                        except ee.EEException as e:
                            print(f"Error cancelling task {status['id']}: {e}")
                        pbar.update(1)
                print(f"Successfully cancelled {cancelled_count} pending tasks")
            else:
                print("No pending tasks found")

        elif tasks is not None:
            # Check if it's a valid task ID
            print(f"Attempting to cancel task with ID: {tasks}")

            try:
                statuses = ee.data.getTaskStatus([tasks])
                if not statuses:
                    print(f"Task {tasks} not found")
                    return

                status = statuses[0]
                state = status['state']

                if state == 'UNKNOWN':
                    print(f"Unknown task ID: {tasks}")
                elif state in ['READY', 'RUNNING']:
                    ee.data.cancelTask(tasks)
                    print(f"Successfully cancelled task {tasks}")
                else:
                    print(f"Task {tasks} is already in state '{state}' and cannot be cancelled")
            except ee.EEException as e:
                print(f"Error accessing task {tasks}: {e}")
        else:
            print("Please specify 'all', 'running', 'pending', or a specific task ID")

    except Exception as e:
        print(f"Error in cancel_tasks: {e}")

def quota(project_path=None):
    """
    Display quota information for Earth Engine assets with a visual progress bar.

    Args:
        project_path: Optional. Specific project path to check.
                      If None, attempts to get all available projects.

                      Examples:
                      - "users/username"
                      - "projects/earthengine-legacy/assets/users/username"
                      - "projects/my-project-id"
                      - "my-project-id" (will try to detect the correct format)
    """
    try:
        def draw_bar(percent, width=30):
            """Draw a simple progress bar"""
            filled = int(width * percent / 100)
            bar = "█" * filled + "░" * (width - filled)
            return f"[{bar}] {percent:.1f}%"

        def display_quota_info(project_name, info, project_type="Project"):
            """Display quota info uniformly"""
            if "quota" in info:
                quota_info = info["quota"]
                print(f"\n{project_type}: {project_name}")

                # Size quota
                used_size = int(quota_info.get("sizeBytes", 0))
                max_size = int(quota_info.get("maxSizeBytes", 1))
                percent = (used_size / max_size * 100) if max_size > 0 else 0
                print(f"Storage: {humansize(used_size)} of {humansize(max_size)}")
                print(f"  {draw_bar(percent)}")

                # Asset count quota
                used_assets = int(quota_info.get("assetCount", 0))
                max_assets = int(quota_info.get("maxAssets", 1))
                percent = (used_assets / max_assets * 100) if max_assets > 0 else 0
                print(f"Assets: {used_assets:,} of {max_assets:,}")
                print(f"  {draw_bar(percent)}")
                return True
            elif "asset_size" in info:
                # Legacy format
                print(f"\n{project_type}: {project_name}")

                size_usage = info["asset_size"]["usage"]
                size_limit = info["asset_size"]["limit"]
                size_percent = (size_usage / size_limit * 100) if size_limit > 0 else 0

                count_usage = info["asset_count"]["usage"]
                count_limit = info["asset_count"]["limit"]
                count_percent = (
                    (count_usage / count_limit * 100) if count_limit > 0 else 0
                )

                print(f"Storage: {humansize(size_usage)} of {humansize(size_limit)}")
                print(f"  {draw_bar(size_percent)}")
                print(f"Assets: {count_usage:,} of {count_limit:,}")
                print(f"  {draw_bar(count_percent)}")
                return True
            else:
                print(f"No quota information available for {project_name}")
                return False

        # If no path provided, try to get all projects
        if project_path is None:
            try:
                roots = ee.data.getAssetRoots()
                if not roots:
                    print("No accessible projects found.")
                    return

                # Group projects by parent to avoid showing the same quota multiple times
                processed_projects = set()

                for root in roots:
                    root_path = root["id"]

                    # Skip if we've already processed this project
                    parent_project = (
                        root_path.split("/assets/")[0]
                        if "/assets/" in root_path
                        else root_path
                    )
                    if parent_project in processed_projects:
                        continue

                    processed_projects.add(parent_project)

                    # First try the direct getInfo approach
                    try:
                        asset_info = ee.data.getInfo(parent_project)
                        if asset_info and "quota" in asset_info:
                            # This is a project with quota info
                            project_type = (
                                "Legacy project"
                                if "earthengine-legacy" in str(asset_info)
                                else "Cloud project"
                            )
                            display_quota_info(parent_project, asset_info, project_type)
                            continue
                    except:
                        pass

                    # Try legacy approach
                    if root_path.startswith("users/"):
                        try:
                            quota_info = ee.data.getAssetRootQuota(root_path)
                            display_quota_info(root_path, quota_info, "Legacy project")
                            continue
                        except:
                            pass

                    # Try cloud approach with multiple formats
                    if root_path.startswith("projects/"):
                        cloud_formats = [
                            # Try with /assets/
                            f"{parent_project}/assets/",
                            # Try with just /assets
                            f"{parent_project}/assets",
                            # Try original
                            parent_project,
                        ]

                        success = False
                        for path_format in cloud_formats:
                            try:
                                project_detail = ee.data.getAsset(path_format)
                                if "quota" in project_detail:
                                    display_quota_info(
                                        parent_project, project_detail, "Cloud project"
                                    )
                                    success = True
                                    break
                            except:
                                # Silently try next format
                                continue

                        if success:
                            continue

                    # As a last resort, try getInfo on the original path
                    try:
                        info = ee.data.getInfo(root_path)
                        if info and ("quota" in info or "asset_size" in info):
                            project_type = (
                                "Legacy project"
                                if root_path.startswith("users/")
                                else "Cloud project"
                            )
                            display_quota_info(root_path, info, project_type)
                    except:
                        pass

                return
            except Exception as e:
                print(f"Could not list projects: {str(e)}")
                print("Falling back to current user quota.")
                try:
                    # Try to get default user quota
                    quota_info = ee.data.getAssetRootQuota("users/")
                    print("Current user quota:")
                    display_quota_info("users/", quota_info, "User quota")
                    return
                except Exception as e2:
                    print(f"Could not get user quota: {str(e2)}")
                    return

        # Handle the case where user provided just a name without prefix
        if not project_path.startswith("projects/") and not project_path.startswith(
            "users/"
        ):
            # Try to detect if it's a project ID
            try:
                # First try as a cloud project
                cloud_path = f"projects/{project_path}"
                asset_info = ee.data.getInfo(cloud_path)
                if asset_info:
                    print(f"Detected project ID format, using: {cloud_path}")
                    project_path = cloud_path
            except:
                # If that fails, try as a legacy user
                try:
                    legacy_path = f"users/{project_path}"
                    quota_info = ee.data.getAssetRootQuota(legacy_path)
                    if quota_info:
                        print(f"Detected legacy user format, using: {legacy_path}")
                        project_path = legacy_path
                except:
                    # Keep original if both fail
                    pass

        # Try direct getInfo approach first (works for projects/sat-io style paths)
        try:
            asset_info = ee.data.getInfo(project_path)
            if asset_info and "quota" in asset_info:
                project_type = (
                    "Legacy project"
                    if "earthengine-legacy" in str(asset_info)
                    else "Cloud project"
                )
                return display_quota_info(project_path, asset_info, project_type)
        except:
            pass

        # Try with /assets suffix for cloud projects
        if (
            project_path.startswith("projects/")
            and not project_path.endswith("/assets")
            and "/assets" not in project_path
        ):
            try:
                asset_info = ee.data.getInfo(f"{project_path}/assets")
                if asset_info and "quota" in asset_info:
                    return display_quota_info(project_path, asset_info, "Cloud project")
            except:
                pass

        # Try legacy approach
        try:
            quota_info = ee.data.getAssetRootQuota(project_path)
            return display_quota_info(project_path, quota_info, "Legacy project")
        except:
            pass

        # Try cloud approach with multiple formats
        cloud_formats = [
            f"{project_path}/assets/"
            if not project_path.endswith("/assets/") and "/assets/" not in project_path
            else project_path,
            f"{project_path}/assets"
            if not project_path.endswith("/assets") and "/assets" not in project_path
            else project_path,
            project_path,
        ]

        for path_format in cloud_formats:
            try:
                project_detail = ee.data.getAsset(path_format)
                if "quota" in project_detail:
                    parent_path = (
                        path_format.split("/assets")[0]
                        if "/assets" in path_format
                        else path_format
                    )
                    return display_quota_info(
                        parent_path, project_detail, "Cloud project"
                    )
            except:
                continue

        print(f"Could not retrieve quota information for {project_path}")
        return False

    except Exception as e:
        # print(f"Error retrieving quota: {str(e)}")
        return False

def epoch_convert_time(epoch_timestamp):
    dt_object = datetime.fromtimestamp(epoch_timestamp/1000)
    formatted_date_time = dt_object.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    return formatted_date_time

def tasks(state,id):
    if state is not None:
        task_bundle = []
        operations = [
            status
            for status in ee.data.getTaskList()
            if status["state"] == state.upper()
        ]
        for operation in operations:
            task_id = operation["id"]
            description = operation["description"].split(":")[0]
            op_type = operation["task_type"]
            attempt_count = operation["attempt"]
            date_format = "%Y-%m-%dT%H:%M:%S.%fZ"
            start = datetime.strptime(epoch_convert_time(operation["start_timestamp_ms"]),date_format)
            end = datetime.strptime(epoch_convert_time(operation["update_timestamp_ms"]),date_format)
            time_difference = end - start
            item = {
                "task_id": task_id,
                "operation_type": op_type,
                "description": description,
                "run_time": str(time_difference),
                "attempt": attempt_count,
            }
            if 'destination_uris' in operation:
                item['item_path']=operation['destination_uris'][0].replace('https://code.earthengine.google.com/?asset=','')
            if 'batch_eecu_usage_seconds' in operation:
                item['eecu_usage'] = operation['batch_eecu_usage_seconds']
            task_bundle.append(item)
        print(json.dumps(task_bundle, indent=2))
    elif id is not None:
        operations = [
            status
            for status in ee.data.getTaskList()
            if status["id"] == id
        ]
        for operation in operations:
            task_id = operation["id"]
            description = operation["description"].split(":")[0]
            op_type = operation["task_type"]
            attempt_count = operation["attempt"]
            date_format = "%Y-%m-%dT%H:%M:%S.%fZ"
            start = datetime.strptime(epoch_convert_time(operation["start_timestamp_ms"]),date_format)
            end = datetime.strptime(epoch_convert_time(operation["update_timestamp_ms"]),date_format)
            time_difference = end - start
            item = {
                "task_id": task_id,
                "operation_type": op_type,
                "description": description,
                "run_time": str(time_difference),
                "attempt": attempt_count,
            }
            if 'destination_uris' in operation:
                item['item_path']=operation['destination_uris'][0].replace('https://code.earthengine.google.com/?asset=','')
            if 'batch_eecu_usage_seconds' in operation:
                item['eecu_usage'] = operation['batch_eecu_usage_seconds']
            print(json.dumps(item, indent=2))
    else:
        statuses = ee.data.getTaskList()
        st = []
        for status in statuses:
            st.append(status["state"])
        print(f"Tasks Running: {st.count('RUNNING')}")
        print(f"Tasks Pending: {st.count('READY')}")
        print(f"Tasks Completed: {st.count('COMPLETED')+st.count('SUCCEEDED')}")
        print(f"Tasks Failed: {st.count('FAILED')}")
        print(f"Tasks Cancelled: {st.count('CANCELLED') + st.count('CANCELLING')}")

def assetsize(asset):
    """
    Print the size and item count of an Earth Engine asset.

    Args:
        asset (str): The Earth Engine asset path.

    """

    asset_info = ee.data.getAsset(asset)

    header = asset_info["type"]

    if header in ["IMAGE_COLLECTION", "IMAGE", "TABLE","FEATURE_VIEW"]:
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
        print(f"\n{asset} ===> {humansize(size)}")
        print(f"Total number of items in {header.title()}: {item_count}")

    elif header == "FOLDER":
        out = subprocess.check_output(f"earthengine du {asset} -s", shell=True).decode(
            "ascii"
        )
        size = humansize(float(out.split()[0]))
        num = subprocess.check_output(f"earthengine ls -r {asset}", shell=True).decode(
            "ascii"
        )
        num = [
            i
            for i in num.split("\n")
            if i and len(i) > 1 and not i.startswith("Running")
        ]

        print(f"\n{asset} ===> {size}")
        print(f"Total number of items including all folders: {len(num)}")


def search(mname, source, max_results=10, include_docs=False, allow_subsets=False):
    """
    Search GEE catalog using enhanced search engine with relevance ranking

    Args:
        mname: Search keywords
        source: 'main', 'community', or None (searches both)
        max_results: Maximum number of results to return
        include_docs: Whether to search documentation URLs
        allow_subsets: Whether to show all regional/temporal variants
    """
    search_engine = EnhancedGEESearch()

    # Determine which catalog to search
    if source is not None and source == "community":
        search_source = 'community'
    elif source is not None and source == "main":
        search_source = 'main'
    else:
        search_source = 'both'

    # Load the appropriate datasets
    search_engine.load_datasets(source=search_source)

    # Perform the search
    results = search_engine.search(
        query=mname,
        max_results=max_results,
        include_docs=include_docs,
        allow_subsets=allow_subsets,
        source=search_source
    )

    print("")
    print(json.dumps(results, indent=2, sort_keys=False))

def quota_from_parser(args):
    quota(project_path=args.project)


def ee_report_from_parser(args):
    ee_report(output=args.outfile, path=args.path)


def move_from_parser(args):
    mover(path=args.initial, fpath=args.final, cleanup=args.cleanup)


def copy_from_parser(args):
    copy(path=args.initial, fpath=args.final)


def access_from_parser(args):
    access(collection_path=args.asset, user=args.user, role=args.role)


def delete_metadata_from_parser(args):
    delprop(collection_path=args.asset, property=args.property)


def app2script_from_parser(args):
    jsext(url=args.url, outfile=args.outfile)


def read_from_parser(args):
    readme()

def projects_from_parser(args):
    get_projects()

def cancel_tasks_from_parser(args):
    cancel_tasks(tasks=args.tasks)


def delete_collection_from_parser(args):
    delete(
        ids=args.id,
        max_workers=args.workers,
        max_retries=args.retries,
        verbose=args.verbose
    )

def tasks_from_parser(args):
    tasks(state=args.state,id=args.id)


def assetsize_from_parser(args):
    assetsize(asset=args.asset)


def search_from_parser(args):
    search(
        mname=args.keywords,
        source=args.source,
        max_results=args.max_results if hasattr(args, 'max_results') else 5,
        include_docs=args.include_docs if hasattr(args, 'include_docs') else False,
        allow_subsets=args.allow_subsets if hasattr(args, 'allow_subsets') else False
    )

def main(args=None):
    parser = argparse.ArgumentParser(
        description="Google Earth Engine Batch Asset Manager with Addons"
    )
    subparsers = parser.add_subparsers()

    parser_read = subparsers.add_parser(
        "readme", help="Go the web based geeadd readme page"
    )
    parser_read.set_defaults(func=read_from_parser)

    parser_projects = subparsers.add_parser(
        "projects", help="Prints a list of Google Cloud Projects you own with Earth Engine API enabled"
    )
    parser_projects.set_defaults(func=projects_from_parser)

    parser_quota = subparsers.add_parser(
        "quota", help="Print Earth Engine total quota and used quota"
    )
    optional_named = parser_quota.add_argument_group("Optional named arguments")
    optional_named.add_argument(
        "--project",
        help="Project Name usually in format projects/project-name/assets/",
        default=None,
    )
    parser_quota.set_defaults(func=quota_from_parser)

    parser_app2script = subparsers.add_parser(
        "app2script", help="Get underlying script for public Google earthengine app"
    )
    required_named = parser_app2script.add_argument_group("Required named arguments.")
    required_named.add_argument("--url", help="Earthengine app url", required=True)
    optional_named = parser_app2script.add_argument_group("Optional named arguments")
    optional_named.add_argument(
        "--outfile",
        help="Write the script out to a .js file: Open in any text editor",
        default=None,
    )
    parser_app2script.set_defaults(func=app2script_from_parser)

    parser_search = subparsers.add_parser(
        "search", help="Search public GEE catalog using keywords with relevance ranking"
    )
    required_named = parser_search.add_argument_group("Required named arguments.")
    required_named.add_argument(
        "--keywords",
        help="Keywords to search for can be id, provider, tag and so on",
        required=True,
    )
    optional_named = parser_search.add_argument_group("Optional named arguments")
    optional_named.add_argument(
        "--source",
        help="Catalog to search: 'main' (official catalog), 'community' (community datasets), or leave blank for both",
        default=None,
    )
    optional_named.add_argument(
        "--max_results",
        help="Maximum number of results to return (default: 10)",
        type=int,
        default=5,
    )
    optional_named.add_argument(
        "--include_docs",
        help="Search documentation URLs for keywords (slower but more thorough)",
        action="store_true",
        default=False,
    )
    optional_named.add_argument(
        "--allow_subsets",
        help="Show all regional/temporal variants instead of grouping them",
        action="store_true",
        default=False,
    )
    parser_search.set_defaults(func=search_from_parser)

    parser_ee_report = subparsers.add_parser(
        "ee_report",
        help="Prints a detailed report of all Earth Engine Assets includes Asset Type, Path,Number of Assets,size(MB),unit,owner,readers,writers",
    )
    required_named = parser_ee_report.add_argument_group("Required named arguments.")
    required_named.add_argument(
        "--outfile", help="This it the location of your report csv file ", required=True
    )
    optional_named = parser_ee_report.add_argument_group("Optional named arguments")
    optional_named.add_argument(
        "--path",
        help="Path to any folder including project folders",
        default=None,
    )
    parser_ee_report.set_defaults(func=ee_report_from_parser)

    parser_assetsize = subparsers.add_parser(
        "assetsize",
        help="Prints any asset size (folders,collections,images or tables) in Human Readable form & Number of assets included",
    )
    required_named = parser_assetsize.add_argument_group("Required named arguments.")
    required_named.add_argument(
        "--asset",
        help="Earth Engine Asset for which to get size properties",
        required=True,
    )
    parser_assetsize.set_defaults(func=assetsize_from_parser)

    parser_tasks = subparsers.add_parser(
        "tasks",
        help="Queries current task status [completed,running,ready,failed,cancelled]",
    )
    optional_named = parser_tasks.add_argument_group("Optional named arguments")
    optional_named.add_argument(
        "--state",
        help="Query by state type COMPLETED|READY|RUNNING|FAILED",
    )
    optional_named.add_argument(
        "--id",
        help="Query by task id",
    )
    parser_tasks.set_defaults(func=tasks_from_parser)

    parser_cancel = subparsers.add_parser(
        "cancel", help="Cancel all, running or ready tasks or task ID"
    )
    required_named = parser_cancel.add_argument_group("Required named arguments.")
    required_named.add_argument(
        "--tasks",
        help="You can provide tasks as running or pending or all or even a single task id",
        required=True,
        default=None,
    )
    parser_cancel.set_defaults(func=cancel_tasks_from_parser)

    parser_copy = subparsers.add_parser(
        "copy", help="Copies entire folders, collections, images or tables"
    )
    required_named = parser_copy.add_argument_group("Required named arguments.")
    required_named.add_argument("--initial", help="Existing path of assets")
    required_named.add_argument("--final", help="New path for assets")
    parser_copy.set_defaults(func=copy_from_parser)

    parser_move = subparsers.add_parser(
        "move", help="Moves entire folders, collections, images or tables"
    )
    required_named = parser_move.add_argument_group("Required named arguments.")
    required_named.add_argument("--initial", help="Existing path of assets", required=True)
    required_named.add_argument("--final", help="New path for assets", required=True)
    optional_named = parser_move.add_argument_group("Optional named arguments")
    optional_named.add_argument(
        "--no-cleanup",
        dest="cleanup",
        action="store_false",
        default=True,
        help="Keep empty source folders after moving (default: cleanup enabled)"
    )
    parser_move.set_defaults(func=move_from_parser)

    parser_access = subparsers.add_parser(
        "access",
        help="Sets Permissions for entire folders, collections, images or tables",
    )
    required_named = parser_access.add_argument_group("Required named arguments.")
    required_named.add_argument(
        "--asset",
        help="This is the path to the earth engine asset whose permission you are changing folder/collection/image",
        required=True,
    )
    required_named.add_argument(
        "--user",
        help='Can be user email or serviceAccount like account@gserviceaccount.com or groups like group@googlegroups.com or try using "allUsers" to make it public',
        required=True,
        default=False,
    )
    required_named.add_argument(
        "--role", help="Choose between reader, writer or delete", required=True
    )
    parser_access.set_defaults(func=access_from_parser)

    parser_delete = subparsers.add_parser(
        "delete", help="Deletes folders or collections recursively"
    )
    required_named = parser_delete.add_argument_group("Required named arguments.")
    required_named.add_argument(
        "--id",
        help="Full path to asset for deletion. Recursively removes all folders, collections and images.",
        required=True,
    )
    optional_named = parser_delete.add_argument_group("Optional named arguments")
    optional_named.add_argument('--workers', type=int, default=5,
                        help='Number of concurrent workers (default: 5)')
    optional_named.add_argument('--retries', type=int, default=5,
                        help='Maximum retry attempts per asset (default: 5)')
    optional_named.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose debug logging')
    parser_delete.set_defaults(func=delete_collection_from_parser)

    parser_delete_metadata = subparsers.add_parser(
        "delete_metadata",
        help="Use with caution: delete any metadata from collection or image",
    )
    required_named = parser_delete_metadata.add_argument_group(
        "Required named arguments."
    )
    required_named.add_argument(
        "--asset",
        help="This is the path to the earth engine asset whose permission you are changing collection/image",
        required=True,
    )
    required_named.add_argument(
        "--property",
        help="Metadata name that you want to delete",
        required=True,
        default=False,
    )
    parser_delete_metadata.set_defaults(func=delete_metadata_from_parser)

    args = parser.parse_args()

    try:
        func = args.func
    except AttributeError:
        parser.error("too few arguments")
    func(args)


if __name__ == "__main__":
    main()
