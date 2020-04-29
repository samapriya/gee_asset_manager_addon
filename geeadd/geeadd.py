#! /usr/bin/env python

__copyright__ = """

    Copyright 2020 Samapriya Roy

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
import os
import csv
import sys
import json
import ee
import webbrowser
import subprocess
import zipfile
import shutil
import pkg_resources
import urllib.request
from datetime import datetime
from shutil import copyfile

os.chdir(os.path.dirname(os.path.realpath(__file__)))
lpath = os.path.dirname(os.path.realpath(__file__))
sys.path.append(lpath)
from .batch_copy import copy
from .batch_mover import mover
from .acl_changer import access
from .ee_report import ee_report
from .ee_del_meta import delprop
from .app2script import jsext

now = datetime.now()

# Get package version
def geeadd_version():
    print(pkg_resources.get_distribution("geeadd").version)


def version_from_parser(args):
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
                for task in ee.data.getTaskList()
                if task["state"] == "RUNNING" or task["state"] == "READY"
            ]
            if len(all_tasks) > 0:
                for task in all_tasks:
                    ee.data.cancelTask(task["id"])
                print(
                    "Request completed task ID or task type {} cancelled".format(tasks)
                )
            elif len(all_tasks) == 0:
                print("No Running or Ready tasks found")
        except Exception as e:
            print(e)
    elif tasks == "running":
        try:
            print("Attempting to cancel running tasks")
            running_tasks = [
                task for task in ee.data.getTaskList() if task["state"] == "RUNNING"
            ]
            if len(running_tasks) > 0:
                for task in running_tasks:
                    ee.data.cancelTask(task["id"])
                print(
                    "Request completed task ID or task type {} cancelled".format(tasks)
                )
            elif len(running_tasks) == 0:
                print("No Running tasks found")
        except Exception as e:
            print(e)
    elif tasks == "ready":
        try:
            print("Attempting to cancel queued tasks or ready tasks")
            ready_tasks = [
                task for task in ee.data.getTaskList() if task["state"] == "READY"
            ]
            if len(ready_tasks) > 0:
                for task in ready_tasks:
                    ee.data.cancelTask(task["id"])
                print(
                    "Request completed task ID or task type {} cancelled".format(tasks)
                )
            elif len(ready_tasks) == 0:
                print("No Ready tasks found")
        except Exception as e:
            print(e)
    elif tasks is not None:
        try:
            print("Attempting to cancel task with given task ID {}".format(tasks))
            get_status = ee.data.getTaskStatus(tasks)[0]
            if get_status["state"] == "RUNNING" or get_status["state"] == "READY":
                ee.data.cancelTask(task["id"])
                print(
                    "Request completed task ID or task type {} cancelled".format(tasks)
                )
            elif get_status["state"] == "UNKNOWN":
                print("No task found with given task ID {}".format(tasks))
        except Exception as e:
            print(e)


def cancel_tasks_from_parser(args):
    cancel_tasks(tasks=args.tasks)


def delete(ids):
    try:
        print("Recursively deleting path: {}".format(ids))
        subprocess.call("earthengine --no-use_cloud_api rm -r " + ids,shell=True)
    except Exception as e:
        print(e)


def delete_collection_from_parser(args):
    delete(ids=args.id)


def quota():
    ee.Initialize()
    for roots in ee.data.getAssetRoots():
        quota = ee.data.getAssetRootQuota(roots["id"])
        print("")
        print(
            "Root assets path: {}".format(
                roots["id"].replace("projects/earthengine-legacy/assets/", "")
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
    quota()


def ee_report_from_parser(args):
    ee_report(output=args.outfile)


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


def tasks():
    ee.Initialize()
    statuses = ee.data.getTaskList()
    st = []
    for status in statuses:
        st.append(status["state"])
    print("Tasks Running: " + str(st.count("RUNNING")))
    print("Tasks Ready: " + str(st.count("READY")))
    print("Tasks Completed: " + str(st.count("COMPLETED")))
    print("Tasks Failed: " + str(st.count("FAILED")))
    print("Tasks Cancelled: " + str(st.count("CANCELLED")))


def tasks_from_parser(args):
    tasks()


def assetsize(asset):
    ee.Initialize()
    header = ee.data.getInfo(asset)["type"]
    if header == "IMAGE_COLLECTION":
        collc = ee.ImageCollection(asset)
        size = collc.aggregate_array("system:asset_size")
        print("")
        print(str(asset) + " ===> " + str(humansize(sum(size.getInfo()))))
        print("Total number of items in collection: {}".format(collc.size().getInfo()))
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
        b = subprocess.check_output(
            "earthengine --no-use_cloud_api du " + asset + " -s", shell=True
        ).decode("ascii")
        num = subprocess.check_output(
            "earthengine --no-use_cloud_api ls " + asset, shell=True
        ).decode("ascii")
        size = humansize(float(b.strip().split(" ")[0]))
        print("")
        print(str(asset) + " ===> " + str(size))
        print("Total number of items in folder: {}".format(len(num.split("\n")) - 1))


def assetsize_from_parser(args):
    assetsize(asset=args.asset)


def search(mname):
    out_file_path = os.path.join(lpath, "eed.zip")
    for f in os.listdir(lpath):
        if f.endswith(".csv"):
            try:
                os.unlink(os.path.join(lpath, f))
            except WindowsError:
                with open(os.path.join(lpath, f), mode="w") as outfile:
                    outfile.close()

    # get os type
    name = os.name

    # set base folder names and paths
    folder_name = "Earth-Engine-Datasets-List-master"
    pth = os.path.join(lpath, folder_name)

    if os.path.exists(pth):
        if name == "nt":
            os.system("rmdir " + '"' + pth + '" /s /q')
        elif name == "posix":
            try:
                shutil.rmtree(pth)
            except:
                print("Try using sudo privileges")

    try:
        urllib.request.urlretrieve(
            "https://github.com/samapriya/Earth-Engine-Datasets-List/archive/master.zip",
            out_file_path,
        )
    except:
        print("The URL is invalid. Please double check the URL.")

    # Unzip the zip file
    zip_ref = zipfile.ZipFile(out_file_path)
    for file in zip_ref.namelist():
        if zip_ref.getinfo(file).filename.endswith(".csv"):
            zip_ref.extract(file, lpath)

    for items in os.listdir(os.path.join(lpath, folder_name)):
        if items.endswith(".csv"):
            copyfile(os.path.join(pth, items), os.path.join(lpath, items))
            print(
                "Using Earth Engine Catalog with date: {}".format(
                    items.split("_")[1].split(".")[0]
                )
                + "\n"
            )
    gee_bundle = []
    for items in os.listdir(lpath):
        if items.endswith(".csv"):
            i = 1
            input_file = csv.DictReader(open(os.path.join(lpath, items)))
            for rows in input_file:
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


def search_from_parser(args):
    search(mname=args.keywords)


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Google Earth Engine Batch Asset Manager with Addons"
    )
    subparsers = parser.add_subparsers()

    parser_version = subparsers.add_parser(
        "version", help="Prints porder version and exists"
    )
    parser_version.set_defaults(func=version_from_parser)

    parser_read = subparsers.add_parser(
        "readme", help="Go the web based porder readme page"
    )
    parser_read.set_defaults(func=read_from_parser)

    parser_quota = subparsers.add_parser(
        "quota", help="Print Earth Engine total quota and used quota"
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
    parser_search.set_defaults(func=search_from_parser)

    parser_ee_report = subparsers.add_parser(
        "ee_report",
        help="Prints a detailed report of all Earth Engine Assets includes Asset Type, Path,Number of Assets,size(MB),unit,owner,readers,writers",
    )
    required_named = parser_ee_report.add_argument_group("Required named arguments.")
    required_named.add_argument(
        "--outfile", help="This it the location of your report csv file ", required=True
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
    parser_tasks.set_defaults(func=tasks_from_parser)

    parser_cancel = subparsers.add_parser("cancel", help="Cancel all running tasks")
    required_named = parser_cancel.add_argument_group("Required named arguments.")
    required_named.add_argument(
        "--tasks",
        help="You can provide tasks as running or ready or all or even a single task id",
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

    args.func(args)


if __name__ == "__main__":
    main()
