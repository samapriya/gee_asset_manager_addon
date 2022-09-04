from __future__ import print_function

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
import csv
import random
import subprocess
import sys

import ee
from logzero import logger

# Empty Lists
folder_paths = []
image_list = []
collection_list = []
table_list = []

suffixes = ["B", "KB", "MB", "GB", "TB", "PB"]


def humansize(nbytes):
    i = 0
    while nbytes >= 1024 and i < len(suffixes) - 1:
        nbytes /= 1024.0
        i += 1
    f = ("%.2f" % nbytes).rstrip("0").rstrip(".")
    return "%s %s" % (f, suffixes[i])


def recprocess(gee_type, location):
    try:
        if gee_type == "collection":
            own = ee.data.getAssetAcl(location)
            o = ",".join(own["owners"])
            r = ",".join(own["readers"])
            w = ",".join(own["writers"])
            return [o, r, w]
        elif gee_type == "image":
            own = ee.data.getAssetAcl(location)
            o = ",".join(own["owners"])
            r = ",".join(own["readers"])
            w = ",".join(own["writers"])
            return [o, r, w]
        elif gee_type == "table":
            own = ee.data.getAssetAcl(location)
            o = ",".join(own["owners"])
            r = ",".join(own["readers"])
            w = ",".join(own["writers"])
            return [o, r, w]
        elif gee_type == "folder":
            own = ee.data.getAssetAcl(location)
            o = ",".join(own["owners"])
            r = ",".join(own["readers"])
            w = ",".join(own["writers"])
            # print(o,r,w)
            return [o, r, w]
    except Exception as e:
        print(e)


# Recursive folder paths
def recursive(path):
    if ee.data.getAsset(path)["type"].lower() == "folder":
        children = ee.data.listAssets({"parent": path})
    folder_paths.append(path)
    val = [child["type"].lower() == "folder" for child in children["assets"]]
    while len(val) > 0 and True in val:
        for child in children["assets"]:
            if child["type"].lower() == "folder":
                folder_paths.append(child["name"])
                children = ee.data.listAssets({"parent": child["name"]})
        val = [child["type"].lower() == "folder" for child in children["assets"]]
    return folder_paths


def assetsize(asset):
    ee.Initialize()
    header = ee.data.getAsset(asset)["type"]
    if header == "IMAGE_COLLECTION":
        collc = ee.ImageCollection(asset)
        size = collc.aggregate_array("system:asset_size")
        return [str(humansize(sum(size.getInfo()))), str(collc.size().getInfo())]
    elif header == "IMAGE":
        collc = ee.Image(asset)
        return [str(humansize(collc.get("system:asset_size").getInfo())), 1]
    elif header == "TABLE":
        collc = ee.FeatureCollection(asset)
        return [str(humansize(collc.get("system:asset_size").getInfo())), 1]
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
        return [str(size), str(len(num))]

# folder parse


def fparse(path):
    ee.Initialize()
    if ee.data.getAsset(path)["type"].lower() == "folder":
        gee_folder_path = recursive(path)
        for folders in gee_folder_path:
            children = ee.data.listAssets({"parent": folders})
            for child in children["assets"]:
                if child["type"].lower() == "image_collection":
                    collection_list.append(child["id"])
                elif child["type"].lower() == "image":
                    image_list.append(child["id"])
                elif child["type"].lower() == "table":
                    table_list.append(child["id"])
    elif ee.data.getAsset(path)["type"].lower() == "image":
        image_list.append(path)
    elif ee.data.getAsset(path)["type"].lower() == "image_collection":
        collection_list.append(path)
    elif ee.data.getAsset(path)["type"].lower() == "table":
        table_list.append(path)
    else:
        print(ee.data.getAsset(path)["type"].lower())
    return [collection_list, table_list, image_list, folder_paths]


# request type of asset, asset path and user to give permission
def ee_report(output, path):
    choicelist = [
        "Go grab some tea.....",
        "Go Stretch.....",
        "Go take a walk.....",
        "Go grab some coffee.....",
    ]  # adding something fun
    path_list = []
    logger.debug("This might take sometime. {}".format(
        random.choice(choicelist)))
    ee.Initialize()
    with open(output, "w") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=[
                "type",
                "path",
                "No of Assets",
                "size",
                "owner",
                "readers",
                "writers",
            ],
            delimiter=",",
            lineterminator="\n",
        )
        writer.writeheader()
    if path is not None:
        if not path.endswith('/') and path.endswith('assets'):
            path = path+'/'
        parser = ee.data.getAsset(path)
        if parser["type"].lower() == "folder" and path.startswith('user'):
            path = parser["name"]
        path_list.append(path)
        logger.debug(f"Processing your folder: {path}")
        collection_list, table_list, image_list, folder_paths = fparse(
            path)
    else:
        collection_path = ee.data.getAssetRoots()
        for roots in collection_path:
            path_list.append(roots['id'])
            logger.debug("Processing your root folder: {}".format(roots["id"]))
            collection_list, table_list, image_list, folder_paths = fparse(
                roots["id"])
    logger.debug(
        "Processing a total of: {} folders {} collections {} images {} tables".format(
            len(folder_paths), len(collection_list), len(
                image_list), len(table_list),
        )
        + "\n"
    )
    if folder_paths:
        for folder in folder_paths:
            if not folder in path_list:
                gee_id = ee.data.getAsset(folder)['name']
                gee_type = "folder"
                logger.info("Processing Folder {}".format(gee_id))
                total_size, total_count = assetsize(gee_id)
                o, r, w = recprocess(gee_type, gee_id)
                try:
                    with open(output, "a") as csvfile:
                        writer = csv.writer(
                            csvfile, delimiter=",", lineterminator="\n")
                        writer.writerow(
                            [gee_type, gee_id, total_count, total_size, o, r, w]
                        )
                    csvfile.close()
                except Exception as e:
                    print(e)
    if collection_list:
        for collection in collection_list:
            gee_id = ee.data.getAsset(collection)['name']
            gee_type = "collection"
            logger.info("Processing Collection {}".format(gee_id))
            total_size, total_count = assetsize(gee_id)
            o, r, w = recprocess(gee_type, gee_id)
            # print(gee_id,gee_type,total_size,total_count,o,r,w)
            with open(output, "a") as csvfile:
                writer = csv.writer(csvfile, delimiter=",",
                                    lineterminator="\n")
                writer.writerow(
                    [gee_type, gee_id, total_count, total_size, o, r, w])
            csvfile.close()
    if table_list:
        for table in table_list:
            gee_id = ee.data.getAsset(table)['name']
            gee_type = "table"
            logger.info("Processing table {}".format(gee_id))
            total_size, total_count = assetsize(gee_id)
            o, r, w = recprocess(gee_type, gee_id)
            # print(gee_id,gee_type,total_size,total_count,o,r,w)
            with open(output, "a") as csvfile:
                writer = csv.writer(csvfile, delimiter=",",
                                    lineterminator="\n")
                writer.writerow(
                    [gee_type, gee_id, total_count, total_size, o, r, w])
            csvfile.close()
    if image_list:
        for image in image_list:
            gee_id = ee.data.getAsset(image)['name']
            gee_type = "image"
            logger.info("Processing image {}".format(gee_id))
            total_size, total_count = assetsize(gee_id)
            o, r, w = recprocess(gee_type, gee_id)
            # print(gee_id,gee_type,total_size,total_count,o,r,w)
            with open(output, "a") as csvfile:
                writer = csv.writer(csvfile, delimiter=",",
                                    lineterminator="\n")
                writer.writerow(
                    [gee_type, gee_id, total_count, total_size, o, r, w])
            csvfile.close()
