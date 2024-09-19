#! /usr/bin/env python

from .acl_changer import access
from .app2script import jsext
from .batch_copy import copy
from .batch_mover import mover
from .ee_del_meta import delprop
from .ee_projects import get_projects
from .ee_report import ee_report

__copyright__ = """

    Copyright 2024 Samapriya Roy

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
import json
import os
import subprocess
import sys
import webbrowser
from datetime import datetime
from importlib.metadata import version

import ee
import requests
from bs4 import BeautifulSoup

os.chdir(os.path.dirname(os.path.realpath(__file__)))
lpath = os.path.dirname(os.path.realpath(__file__))
sys.path.append(lpath)

now = datetime.now()

if len(sys.argv) > 1 and sys.argv[1] != "-h":
    ee.Initialize()


class Solution:
    """
    A class for comparing version strings.
    """

    def compareVersion(self, version1, version2):
        """
        Compare two version strings.

        Args:
            version1 (str): The first version string.
            version2 (str): The second version string.

        Returns:
            int: 1 if version1 > version2, -1 if version1 < version2, 0 if equal.
        """
        versions1 = [int(v) for v in version1.split(".")]
        versions2 = [int(v) for v in version2.split(".")]
        for i in range(max(len(versions1), len(versions2))):
            v1 = versions1[i] if i < len(versions1) else 0
            v2 = versions2[i] if i < len(versions2) else 0
            if v1 > v2:
                return 1
            elif v1 < v2:
                return -1
        return 0


ob1 = Solution()


def geeadd_version():
    """
    Check and notify about the latest version of the 'geeadd' package.
    """
    url = "https://pypi.org/project/geeadd/"
    source = requests.get(url)
    html_content = source.text
    soup = BeautifulSoup(html_content, "html.parser")
    company = soup.find("h1")
    installed_version = version("geeadd")
    vcheck = ob1.compareVersion(
        company.string.strip().split(" ")[-1],
        installed_version,
    )
    if vcheck == 1:
        print(
            f"Current version of geeadd is {installed_version} upgrade to latest version: {company.string.strip().split(' ')[-1]}"
        )
    elif vcheck == -1:
        print(
            f"Possibly running staging code {installed_version} compared to pypi release {company.string.strip().split(' ')[-1]}"
        )


geeadd_version()


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
    if tasks == "all":
        try:
            print("Attempting to cancel all tasks")
            all_tasks = [
                task
                for task in ee.data.listOperations()
                if task["metadata"]["state"] == "RUNNING"
                or task["metadata"]["state"] == "READY"
            ]
            if len(all_tasks) > 0:
                for task in all_tasks:
                    ee.data.cancelOperation(task["name"])
                print(
                    "Request completed task ID or task type {} cancelled".format(tasks)
                )
            elif len(all_tasks) == 0:
                print("No Running or Pending tasks found")
        except Exception as e:
            print(e)
    elif tasks == "running":
        try:
            print("Attempting to cancel running tasks")
            running_tasks = [
                task
                for task in ee.data.listOperations()
                if task["metadata"]["state"] == "RUNNING"
            ]
            if len(running_tasks) > 0:
                for task in running_tasks:
                    ee.data.cancelOperation(task["name"])
                print(
                    "Request completed task ID or task type: {} cancelled".format(tasks)
                )
            elif len(running_tasks) == 0:
                print("No Running tasks found")
        except Exception as e:
            print(e)
    elif tasks == "pending":
        try:
            print("Attempting to cancel queued tasks or pending tasks")
            ready_tasks = [
                task
                for task in ee.data.listOperations()
                if task["metadata"]["state"] == "READY"
            ]
            if len(ready_tasks) > 0:
                for task in ready_tasks:
                    ee.data.cancelOperation(task["name"])
                print(
                    "Request completed task ID or task type: {} cancelled".format(tasks)
                )
            elif len(ready_tasks) == 0:
                print("No Pending tasks found")
        except Exception as e:
            print(e)
    elif tasks is not None:
        try:
            print("Attempting to cancel task with given task ID {}".format(tasks))
            get_status = ee.data.getOperation(
                "projects/earthengine-legacy/operations/{}".format(tasks)
            )
            if (
                get_status["metadata"]["state"] == "RUNNING"
                or get_status["metadata"]["state"] == "READY"
            ):
                ee.data.cancelTask(task["id"])
                print(
                    "Request completed task ID or task type: {} cancelled".format(tasks)
                )
            else:
                print("Task in status {}".format(get_status["metadata"]["state"]))
        except Exception as e:
            print("No task found with given task ID {}".format(tasks))


def delete(ids):
    try:
        print("Recursively deleting path: {}".format(ids))
        process_output = subprocess.run(["earthengine", "rm", "-r", "{}".format(ids)], capture_output=True, text=True)
        print("output from commandline: {}".format(process_output.stdout))
    except Exception as e:
        print(e)

def project_quota(project):
        try:
            if not project.endswith("/"):
                project = project + "/"
            else:
                project = project
            project_detail = ee.data.getAsset(project)
            print("")
            print(f"Cloud project path: {project}")
            if "sizeBytes" in project_detail["quota"]:
                print(
                    f'Used {humansize(int(project_detail["quota"]["sizeBytes"]))} of {humansize(int(project_detail["quota"]["maxSizeBytes"]))}'
                )
            else:
                print(
                    f'Used 0 of {humansize(int(project_detail["quota"]["maxSizeBytes"]))}'
                )
            if "assetCount" in project_detail["quota"]:
                print(
                    f'Used {int(project_detail["quota"]["assetCount"]):,} assets of {int(project_detail["quota"]["maxAssets"]):,} total'
                )
            else:
                print(
                    f'Used 0 assets of {int(project_detail["quota"]["maxAssets"]):,} total'
                )
        except Exception as error:
            print(error)

def quota(project):
    if project is not None:
        project_quota(project)
    else:
        vcheck = ob1.compareVersion(
                "0.1.379",
                version('earthengine-api'),
            )
        if vcheck == 0 or vcheck == 1:
            for roots in ee.data.getAssetRoots():
                quota = ee.data.getAssetRootQuota(roots["id"])
                print("")
                print(
                    f"Root assets path: {roots['id'].replace('projects/earthengine-legacy/assets/', '')}"
                )
                print(
                    f"Used {humansize(quota['asset_size']['usage'])} of {humansize(quota['asset_size']['limit'])}"
                )
                print(
                    f"Used {quota['asset_count']['usage']:,} assets of {quota['asset_count']['limit']:,} total"
                )
        elif vcheck ==-1:
            asset_list = ee.data.getAssetRoots()[0]
            project = f"{asset_list.get('id').split('/assets/')[0]}/assets/"
            project_quota(project)

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


def search(mname, source):
    gee_bundle = []
    if source is not None and source == "community":
        r = requests.get(
            "https://raw.githubusercontent.com/samapriya/awesome-gee-community-datasets/master/community_datasets.json"
        )
        community_list = r.json()
        print("Looking within {} community datasets".format(len(community_list)))
        i = 1
        for rows in community_list:
            if mname.lower() in str(rows["title"]).lower():
                try:
                    if rows["type"] == "image_collection":
                        rows["id"] = "ee.ImageCollection('{}')".format(rows["id"])
                    elif rows["type"] == "image":
                        rows["id"] = "ee.Image('{}')".format(rows["id"])
                    elif rows["type"] == "table":
                        rows["id"] = "ee.FeatureCollection('{}')".format(rows["id"])
                    item = {
                        "index": i,
                        "title": rows["title"],
                        "ee_id_snippet": rows["id"],
                        "provider": rows["provider"],
                        "tags": rows["tags"],
                        "license": rows["license"],
                        "sample_code": rows["sample_code"],
                    }

                    gee_bundle.append(item)
                    i = i + 1
                except Exception as e:
                    print(e)
            elif mname.lower() in str(rows["id"]).lower():
                try:
                    if rows["type"] == "image_collection":
                        rows["id"] = "ee.ImageCollection('{}')".format(rows["id"])
                    elif rows["type"] == "image":
                        rows["id"] = "ee.Image('{}')".format(rows["id"])
                    elif rows["type"] == "table":
                        rows["id"] = "ee.FeatureCollection('{}')".format(rows["id"])
                    item = {
                        "index": i,
                        "title": rows["title"],
                        "ee_id_snippet": rows["id"],
                        "provider": rows["provider"],
                        "tags": rows["tags"],
                        "license": rows["license"],
                        "sample_code": rows["sample_code"],
                    }
                    gee_bundle.append(item)
                    i = i + 1
                except Exception as e:
                    print(e)
            elif mname.lower() in str(rows["provider"]).lower():
                try:
                    if rows["type"] == "image_collection":
                        rows["id"] = "ee.ImageCollection('{}')".format(rows["id"])
                    elif rows["type"] == "image":
                        rows["id"] = "ee.Image('{}')".format(rows["id"])
                    elif rows["type"] == "table":
                        rows["id"] = "ee.FeatureCollection('{}')".format(rows["id"])
                    item = {
                        "index": i,
                        "title": rows["title"],
                        "ee_id_snippet": rows["id"],
                        "provider": rows["provider"],
                        "tags": rows["tags"],
                        "license": rows["license"],
                        "sample_code": rows["sample_code"],
                    }
                    gee_bundle.append(item)
                    i = i + 1
                except Exception as e:
                    print(e)
            elif mname.lower() in str(rows["tags"]).lower():
                try:
                    if rows["type"] == "image_collection":
                        rows["id"] = "ee.ImageCollection('{}')".format(rows["id"])
                    elif rows["type"] == "image":
                        rows["id"] = "ee.Image('{}')".format(rows["id"])
                    elif rows["type"] == "table":
                        rows["id"] = "ee.FeatureCollection('{}')".format(rows["id"])
                    item = {
                        "index": i,
                        "title": rows["title"],
                        "ee_id_snippet": rows["id"],
                        "provider": rows["provider"],
                        "tags": rows["tags"],
                        "license": rows["license"],
                        "sample_code": rows["sample_code"],
                    }
                    gee_bundle.append(item)
                    i = i + 1
                except Exception as e:
                    print(e)
    elif source is None:
        r = requests.get(
            "https://raw.githubusercontent.com/samapriya/Earth-Engine-Datasets-List/master/gee_catalog.json"
        )
        catalog_list = r.json()
        print("Looking within {} gee catalog datasets".format(len(catalog_list)))
        i = 1
        for rows in catalog_list:
            if mname.lower() in str(rows["title"]).lower():
                try:
                    if rows["type"] == "image_collection":
                        rows["id"] = "ee.ImageCollection('{}')".format(rows["id"])
                    elif rows["type"] == "image":
                        rows["id"] = "ee.Image('{}')".format(rows["id"])
                    elif rows["type"] == "table":
                        rows["id"] = "ee.FeatureCollection('{}')".format(rows["id"])
                    item = {
                        "index": i,
                        "title": rows["title"],
                        "ee_id_snippet": rows["id"],
                        "start_date": rows["start_date"],
                        "end_date": rows["end_date"],
                        "asset_url": rows["asset_url"],
                        "thumbnail_url": rows["thumbnail_url"],
                    }
                    gee_bundle.append(item)
                    i = i + 1
                except Exception as e:
                    print(e)
            elif mname.lower() in str(rows["id"]).lower():
                try:
                    if rows["type"] == "image_collection":
                        rows["id"] = "ee.ImageCollection('{}')".format(rows["id"])
                    elif rows["type"] == "image":
                        rows["id"] = "ee.Image('{}')".format(rows["id"])
                    elif rows["type"] == "table":
                        rows["id"] = "ee.FeatureCollection('{}')".format(rows["id"])
                    item = {
                        "index": i,
                        "title": rows["title"],
                        "ee_id_snippet": rows["id"],
                        "start_date": rows["start_date"],
                        "end_date": rows["end_date"],
                        "asset_url": rows["asset_url"],
                        "thumbnail_url": rows["thumbnail_url"],
                    }
                    gee_bundle.append(item)
                    i = i + 1
                except Exception as e:
                    print(e)
            elif mname.lower() in str(rows["provider"]).lower():
                try:
                    if rows["type"] == "image_collection":
                        rows["id"] = "ee.ImageCollection('{}')".format(rows["id"])
                    elif rows["type"] == "image":
                        rows["id"] = "ee.Image('{}')".format(rows["id"])
                    elif rows["type"] == "table":
                        rows["id"] = "ee.FeatureCollection('{}')".format(rows["id"])
                    item = {
                        "index": i,
                        "title": rows["title"],
                        "ee_id_snippet": rows["id"],
                        "start_date": rows["start_date"],
                        "end_date": rows["end_date"],
                        "asset_url": rows["asset_url"],
                        "thumbnail_url": rows["thumbnail_url"],
                    }
                    gee_bundle.append(item)
                    i = i + 1
                except Exception as e:
                    print(e)
            elif mname.lower() in str(rows["tags"]).lower():
                try:
                    if rows["type"] == "image_collection":
                        rows["id"] = "ee.ImageCollection('{}')".format(rows["id"])
                    elif rows["type"] == "image":
                        rows["id"] = "ee.Image('{}')".format(rows["id"])
                    elif rows["type"] == "table":
                        rows["id"] = "ee.FeatureCollection('{}')".format(rows["id"])
                    item = {
                        "index": i,
                        "title": rows["title"],
                        "ee_id_snippet": rows["id"],
                        "start_date": rows["start_date"],
                        "end_date": rows["end_date"],
                        "asset_url": rows["asset_url"],
                        "thumbnail_url": rows["thumbnail_url"],
                    }
                    gee_bundle.append(item)
                    i = i + 1
                except Exception as e:
                    print(e)
    print("")
    print(json.dumps(gee_bundle, indent=4, sort_keys=False))


def quota_from_parser(args):
    quota(project=args.project)


def ee_report_from_parser(args):
    ee_report(output=args.outfile, path=args.path)


def move_from_parser(args):
    mover(path=args.initial, fpath=args.final)


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
    delete(ids=args.id)


def tasks_from_parser(args):
    tasks(state=args.state,id=args.id)


def assetsize_from_parser(args):
    assetsize(asset=args.asset)


def search_from_parser(args):
    search(mname=args.keywords, source=args.source)


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
        "search", help="Search public GEE catalog using keywords"
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
        help="Type community to search within the Community Dataset Catalog",
        default=None,
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
    required_named.add_argument("--initial", help="Existing path of assets")
    required_named.add_argument("--final", help="New path for assets")
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
