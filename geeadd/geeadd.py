#! /usr/bin/env python

from .acl_changer import access
from .app2script import jsext
from .batch_copy import copy
from .batch_mover import mover
from .ee_del_meta import delprop
from .ee_report import ee_report

__copyright__ = """

    Copyright 2021 Samapriya Roy

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
import csv
import json
import os
import shutil
import subprocess
import sys
import urllib.request
import webbrowser
import zipfile
from datetime import datetime
from shutil import copyfile

import ee
import pkg_resources
import requests
from bs4 import BeautifulSoup

os.chdir(os.path.dirname(os.path.realpath(__file__)))
lpath = os.path.dirname(os.path.realpath(__file__))
sys.path.append(lpath)

now = datetime.now()


class Solution:
    def compareVersion(self, version1, version2):
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

# Get package version


def geeadd_version():
    url = "https://pypi.org/project/geeadd/"
    source = requests.get(url)
    html_content = source.text
    soup = BeautifulSoup(html_content, "html.parser")
    company = soup.find("h1")
    vcheck = ob1.compareVersion(
        company.string.strip().split(" ")[-1],
        pkg_resources.get_distribution("geeadd").version,
    )
    if vcheck == 1:
        print(
            "\n"
            + "========================================================================="
        )
        print(
            "Current version of geeadd is {} upgrade to lastest version: {}".format(
                pkg_resources.get_distribution("geeadd").version,
                company.string.strip().split(" ")[-1],
            )
        )
        print(
            "========================================================================="
        )
    elif vcheck == -1:
        print(
            "\n"
            + "========================================================================="
        )
        print(
            "Possibly running staging code {} compared to pypi release {}".format(
                pkg_resources.get_distribution("geeadd").version,
                company.string.strip().split(" ")[-1],
            )
        )
        print(
            "========================================================================="
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


def read_from_parser(args):
    readme()


suffixes = ["B", "KB", "MB", "GB", "TB", "PB"]


def humansize(nbytes):
    i = 0
    while nbytes >= 1024 and i < len(suffixes) - 1:
        nbytes /= 1024.0
        i += 1
    f = ("%.2f" % nbytes).rstrip("0").rstrip(".")
    return "%s %s" % (f, suffixes[i])


def cancel_tasks(tasks):
    ee.Initialize()
    if tasks == "all":
        try:
            print("Attempting to cancel all tasks")
            all_tasks = [
                task
                for task in ee.data.listOperations()
                if task["metadata"]["state"] == "RUNNING"
                or task["metadata"]["state"] == "PENDING"
            ]
            if len(all_tasks) > 0:
                for task in all_tasks:
                    ee.data.cancelOperation(task["name"])
                print(
                    "Request completed task ID or task type {} cancelled".format(
                        tasks)
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
                    "Request completed task ID or task type: {} cancelled".format(
                        tasks)
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
                if task["metadata"]["state"] == "PENDING"
            ]
            if len(ready_tasks) > 0:
                for task in ready_tasks:
                    ee.data.cancelOperation(task["name"])
                print(
                    "Request completed task ID or task type: {} cancelled".format(
                        tasks)
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
                or get_status["metadata"]["state"] == "PENDING"
            ):
                ee.data.cancelTask(task["id"])
                print(
                    "Request completed task ID or task type: {} cancelled".format(
                        tasks)
                )
            else:
                print("Task in status {}".format(
                    get_status["metadata"]["state"]))
        except Exception as e:
            print("No task found with given task ID {}".format(tasks))


def cancel_tasks_from_parser(args):
    cancel_tasks(tasks=args.tasks)


def delete(ids):
    try:
        print("Recursively deleting path: {}".format(ids))
        subprocess.call(
            "earthengine rm -r {}".format(ids), shell=True, stdout=subprocess.PIPE
        )
    except Exception as e:
        print(e)


def delete_collection_from_parser(args):
    delete(ids=args.id)


def quota(project):
    ee.Initialize()
    if project is not None:
        try:
            if not project.endswith('/'):
                project = project+'/'
            else:
                project = project
            project_detail = ee.data.getAsset(project)
            print("")
            if 'sizeBytes' in project_detail['quota']:
                print('Used {} of {}'.format(humansize(int(project_detail['quota']['sizeBytes'])), (humansize(
                    int(project_detail['quota']['maxSizeBytes'])))))
            else:
                print('Used 0 of {}'.format(
                    humansize(int(project_detail['quota']['maxSizeBytes']))))
            if 'assetCount' in project_detail['quota']:
                print('Used {:,} assets of {:,} total'.format(int(
                    project_detail['quota']['assetCount']), int(project_detail['quota']['maxAssetCount'])))
            else:
                print('Used 0 assets of {:,} total'.format(
                    int(project_detail['quota']['maxAssetCount'])))
        except Exception as e:
            print(e)
    else:
        for roots in ee.data.getAssetRoots():
            quota = ee.data.getAssetRootQuota(roots["id"])
            print("")
            print(
                "Root assets path: {}".format(
                    roots["id"].replace(
                        "projects/earthengine-legacy/assets/", "")
                )
            )
            print(
                "Used {} of {}".format(
                    humansize(quota["asset_size"]["usage"]),
                    humansize(quota["asset_size"]["limit"]),
                )
            )
            print(
                "Used {:,} assets of {:,} total".format(
                    quota["asset_count"]["usage"], quota["asset_count"]["limit"]
                )
            )


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


def tasks(state):
    ee.Initialize()
    if state is not None:
        task_bundle = []
        operations = [status
                      for status in ee.data.listOperations() if status["metadata"]["state"] == state.upper()]
        for operation in operations:
            task_id = operation['name'].split('/')[-1]
            description = operation['metadata']['description'].split(
                ':')[-1].strip().replace('"', '')
            op_type = operation['metadata']['type']
            attempt_count = str(operation['metadata']['attempt'])
            start = datetime.strptime(
                operation['metadata']["startTime"], "%Y-%m-%dT%H:%M:%S.%fZ")
            end = datetime.strptime(
                operation['metadata']["updateTime"], "%Y-%m-%dT%H:%M:%S.%fZ")
            time_difference = end-start
            item = {
                "task_id": task_id,
                "operation_type": op_type,
                "description/path": description,
                "run_time": str(time_difference),
                "attempt": attempt_count
            }
            task_bundle.append(item)
        print(json.dumps(task_bundle, indent=2))
    else:
        statuses = ee.data.listOperations()
        st = []
        for status in statuses:
            st.append(status["metadata"]["state"])
        print(f"Tasks Running: {st.count('RUNNING')}")
        print(f"Tasks Pending: {st.count('PENDING')}")
        print(f"Tasks Completed: {st.count('SUCCEEDED')}")
        print(f"Tasks Failed: {st.count('FAILED')}")
        print(
            f"Tasks Cancelled: {st.count('CANCELLED') + st.count('CANCELLING')}")


def tasks_from_parser(args):
    tasks(state=args.state)


def assetsize(asset):
    ee.Initialize()
    header = ee.data.getAsset(asset)["type"]
    if header == "IMAGE_COLLECTION":
        collc = ee.ImageCollection(asset)
        size = collc.aggregate_array("system:asset_size")
        print("")
        print(str(asset) + " ===> " + str(humansize(sum(size.getInfo()))))
        print("Total number of items in collection: {}".format(
            collc.size().getInfo()))
    elif header == "IMAGE":
        collc = ee.Image(asset)
        print("")
        print(
            str(asset)
            + " ===> "
            + str(humansize(collc.get("system:asset_size").getInfo()))
        )
    elif header == "TABLE":
        collc = ee.FeatureCollection(asset)
        print("")
        print(
            str(asset)
            + " ===> "
            + str(humansize(collc.get("system:asset_size").getInfo()))
        )
    elif header == "FOLDER":
        b = subprocess.Popen(
            "earthengine du {} -s".format(asset), shell=True, stdout=subprocess.PIPE
        )
        out, err = b.communicate()
        val = [item for item in out.decode(
            "ascii").split(" ") if item.isdigit()]
        size = humansize(float(val[0]))
        num = subprocess.Popen("earthengine ls {}".format(asset), shell=True, stdout=subprocess.PIPE
                               )
        out, err = num.communicate()
        out = out.decode("ascii")
        num = [i for i in out.split("\n") if i if len(
            i) > 1 if not i.startswith("Running")]
        print("")
        # print(num.split("\n"))
        print(str(asset) + " ===> " + str(size))
        print("Total number of items in folder: {}".format(len(num)))


def assetsize_from_parser(args):
    assetsize(asset=args.asset)


def search(mname, source):
    gee_bundle = []
    if source is not None and source == 'community':
        r = requests.get(
            'https://raw.githubusercontent.com/samapriya/awesome-gee-community-datasets/master/community_datasets.json')
        community_list = r.json()
        print('Looking within {} community datasets'.format(len(community_list)))
        i = 1
        for rows in community_list:
            if mname.lower() in str(rows["title"]).lower():
                try:
                    if rows["type"] == "image_collection":
                        rows["id"] = "ee.ImageCollection('{}')".format(
                            rows["id"])
                    elif rows["type"] == "image":
                        rows["id"] = "ee.Image('{}')".format(rows["id"])
                    elif rows["type"] == "table":
                        rows["id"] = "ee.FeatureCollection('{}')".format(
                            rows["id"])
                    item = {
                        "index": i,
                        "title": rows["title"],
                        "ee_id_snippet": rows["id"],
                        "provider": rows["provider"],
                        "sample_code": rows["sample_code"],
                    }

                    gee_bundle.append(item)
                    i = i + 1
                except Exception as e:
                    print(e)
            elif mname.lower() in str(rows["id"]).lower():
                try:
                    if rows["type"] == "image_collection":
                        rows["id"] = "ee.ImageCollection('{}')".format(
                            rows["id"])
                    elif rows["type"] == "image":
                        rows["id"] = "ee.Image('{}')".format(rows["id"])
                    elif rows["type"] == "table":
                        rows["id"] = "ee.FeatureCollection('{}')".format(
                            rows["id"])
                    item = {
                        "index": i,
                        "title": rows["title"],
                        "ee_id_snippet": rows["id"],
                        "provider": rows["provider"],
                        "sample_code": rows["sample_code"],
                    }
                    gee_bundle.append(item)
                    i = i + 1
                except Exception as e:
                    print(e)
            elif mname.lower() in str(rows["provider"]).lower():
                try:
                    if rows["type"] == "image_collection":
                        rows["id"] = "ee.ImageCollection('{}')".format(
                            rows["id"])
                    elif rows["type"] == "image":
                        rows["id"] = "ee.Image('{}')".format(rows["id"])
                    elif rows["type"] == "table":
                        rows["id"] = "ee.FeatureCollection('{}')".format(
                            rows["id"])
                    item = {
                        "index": i,
                        "title": rows["title"],
                        "ee_id_snippet": rows["id"],
                        "provider": rows["provider"],
                        "sample_code": rows["sample_code"],
                    }
                    gee_bundle.append(item)
                    i = i + 1
                except Exception as e:
                    print(e)
            elif mname.lower() in str(rows["tags"]).lower():
                try:
                    if rows["type"] == "image_collection":
                        rows["id"] = "ee.ImageCollection('{}')".format(
                            rows["id"])
                    elif rows["type"] == "image":
                        rows["id"] = "ee.Image('{}')".format(rows["id"])
                    elif rows["type"] == "table":
                        rows["id"] = "ee.FeatureCollection('{}')".format(
                            rows["id"])
                    item = {
                        "index": i,
                        "title": rows["title"],
                        "ee_id_snippet": rows["id"],
                        "provider": rows["provider"],
                        "sample_code": rows["sample_code"],
                    }
                    gee_bundle.append(item)
                    i = i + 1
                except Exception as e:
                    print(e)
    elif source is None:
        r = requests.get(
            'https://raw.githubusercontent.com/samapriya/Earth-Engine-Datasets-List/master/gee_catalog.json')
        catalog_list = r.json()
        print('Looking within {} gee catalog datasets'.format(len(catalog_list)))
        i = 1
        for rows in catalog_list:
            if mname.lower() in str(rows["title"]).lower():
                try:
                    if rows["type"] == "image_collection":
                        rows["id"] = "ee.ImageCollection('{}')".format(
                            rows["id"])
                    elif rows["type"] == "image":
                        rows["id"] = "ee.Image('{}')".format(rows["id"])
                    elif rows["type"] == "table":
                        rows["id"] = "ee.FeatureCollection('{}')".format(
                            rows["id"])
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
                        rows["id"] = "ee.ImageCollection('{}')".format(
                            rows["id"])
                    elif rows["type"] == "image":
                        rows["id"] = "ee.Image('{}')".format(rows["id"])
                    elif rows["type"] == "table":
                        rows["id"] = "ee.FeatureCollection('{}')".format(
                            rows["id"])
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
                        rows["id"] = "ee.ImageCollection('{}')".format(
                            rows["id"])
                    elif rows["type"] == "image":
                        rows["id"] = "ee.Image('{}')".format(rows["id"])
                    elif rows["type"] == "table":
                        rows["id"] = "ee.FeatureCollection('{}')".format(
                            rows["id"])
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
                        rows["id"] = "ee.ImageCollection('{}')".format(
                            rows["id"])
                    elif rows["type"] == "image":
                        rows["id"] = "ee.Image('{}')".format(rows["id"])
                    elif rows["type"] == "table":
                        rows["id"] = "ee.FeatureCollection('{}')".format(
                            rows["id"])
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

    parser_quota = subparsers.add_parser(
        "quota", help="Print Earth Engine total quota and used quota"
    )
    optional_named = parser_quota.add_argument_group(
        "Optional named arguments")
    optional_named.add_argument(
        "--project",
        help="Project Name usually in format projects/project-name/assets/",
        default=None,
    )
    parser_quota.set_defaults(func=quota_from_parser)

    parser_app2script = subparsers.add_parser(
        "app2script", help="Get underlying script for public Google earthengine app"
    )
    required_named = parser_app2script.add_argument_group(
        "Required named arguments.")
    required_named.add_argument(
        "--url", help="Earthengine app url", required=True)
    optional_named = parser_app2script.add_argument_group(
        "Optional named arguments")
    optional_named.add_argument(
        "--outfile",
        help="Write the script out to a .js file: Open in any text editor",
        default=None,
    )
    parser_app2script.set_defaults(func=app2script_from_parser)

    parser_search = subparsers.add_parser(
        "search", help="Search public GEE catalog using keywords"
    )
    required_named = parser_search.add_argument_group(
        "Required named arguments.")
    required_named.add_argument(
        "--keywords",
        help="Keywords to search for can be id, provider, tag and so on",
        required=True,
    )
    optional_named = parser_search.add_argument_group(
        "Optional named arguments")
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
    required_named = parser_ee_report.add_argument_group(
        "Required named arguments.")
    required_named.add_argument(
        "--outfile", help="This it the location of your report csv file ", required=True
    )
    optional_named = parser_ee_report.add_argument_group(
        "Optional named arguments")
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
    required_named = parser_assetsize.add_argument_group(
        "Required named arguments.")
    required_named.add_argument(
        "--asset",
        help="Earth Engine Asset for which to get size properties",
        required=True,
    )
    parser_assetsize.set_defaults(func=assetsize_from_parser)

    parser_tasks = subparsers.add_parser(
        "tasks",
        help="Queries current task status [completed,running,pending,failed,cancelled]",
    )
    optional_named = parser_tasks.add_argument_group(
        "Optional named arguments")
    optional_named.add_argument(
        "--state",
        help="Query by state type SUCCEEDED|PENDING|RUNNING|FAILED",
    )
    parser_tasks.set_defaults(func=tasks_from_parser)

    parser_cancel = subparsers.add_parser(
        "cancel", help="Cancel all, running or ready tasks or task ID"
    )
    required_named = parser_cancel.add_argument_group(
        "Required named arguments.")
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
    required_named = parser_copy.add_argument_group(
        "Required named arguments.")
    required_named.add_argument("--initial", help="Existing path of assets")
    required_named.add_argument("--final", help="New path for assets")
    parser_copy.set_defaults(func=copy_from_parser)

    parser_move = subparsers.add_parser(
        "move", help="Moves entire folders, collections, images or tables"
    )
    required_named = parser_move.add_argument_group(
        "Required named arguments.")
    required_named.add_argument("--initial", help="Existing path of assets")
    required_named.add_argument("--final", help="New path for assets")
    parser_move.set_defaults(func=move_from_parser)

    parser_access = subparsers.add_parser(
        "access",
        help="Sets Permissions for entire folders, collections, images or tables",
    )
    required_named = parser_access.add_argument_group(
        "Required named arguments.")
    required_named.add_argument(
        "--asset",
        help="This is the path to the earth engine asset whose permission you are changing folder/collection/image",
        required=True,
    )
    required_named.add_argument(
        "--user",
        help='"user:person@example.com" or "group:team@example.com" or "serviceAccount:account@gserviceaccount.com", try using "allUsers" to make it public',
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
    required_named = parser_delete.add_argument_group(
        "Required named arguments.")
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
