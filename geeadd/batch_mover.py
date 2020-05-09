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
import ee
import os
import json


# Image copy
def image_move(initial, replace_string, replaced_string, fpath):
    ee.Initialize()
    if replace_string == replaced_string or replace_string == None:
        final = fpath
    else:
        final = initial.replace(replace_string, replaced_string)
    if ee.data.getInfo(final):
        print("Image already move: {}".format(final))
    else:
        print("Moving image to {}".format(final))
        try:
            ee.data.renameAsset(initial, final)
        except Exception as e:
            print(e)


# Table copy
def table_move(initial, replace_string, replaced_string, fpath):
    ee.Initialize()
    if replace_string == replaced_string or replace_string == None:
        final = fpath
    else:
        final = initial.replace(replace_string, replaced_string)
    if ee.data.getInfo(final):
        print("Table already moved: {}".format(final))
    else:
        print("Moving table to {}".format(final))
        try:
            ee.data.renameAsset(initial, final)
        except Exception as e:
            print(e)


# Collection copy
def collection_move(initial, replace_string, replaced_string, fpath):
    ee.Initialize()
    initial_list = ee.data.getList(params={"id": initial})
    assets_names = [os.path.basename(asset["id"]) for asset in initial_list]
    if replace_string == replaced_string or replace_string == None:
        collection_path = fpath
    else:
        collection_path = initial.replace(replace_string, replaced_string)
    if ee.data.getInfo(collection_path):
        print("Collection exists: {}".format(ee.data.getInfo(collection_path)["id"]))
    else:
        print("Collection does not exist: Creating {}".format(collection_path))
        ee.data.createAsset({"type": ee.data.ASSET_TYPE_IMAGE_COLL}, collection_path)
    final_list = ee.data.getList(params={"id": collection_path})
    final_names = [os.path.basename(asset["id"]) for asset in final_list]
    diff = set(assets_names) - set(final_names)
    print("Moving a total of " + str(len(diff)) + " images.....")
    for count, items in enumerate(diff):
        print("Moving " + str(count + 1) + " of " + str(len(diff)), end="\r")
        init = initial + "/" + items
        fin = collection_path + "/" + items
        try:
            ee.data.renameAsset(init, fin)
        except Exception as e:
            print(e)


# Folder create
def fcreate(folder_path, replace_string, replaced_string):
    ee.Initialize()
    folder_path = folder_path.replace(replace_string, replaced_string)
    if ee.data.getInfo(folder_path):
        print("Folder exists: {}".format(ee.data.getInfo(folder_path)["id"]))
    else:
        print("Folder does not exist: Creating {}".format(folder_path))
        ee.data.createAsset({"type": ee.data.ASSET_TYPE_FOLDER}, folder_path)


# Recursive folder paths
folder_paths = []


def recursive(path):
    ee.Initialize()
    if ee.data.getInfo(path)["type"].lower() == "folder":
        children = ee.data.getList({"id": path})
    folder_paths.append(path)
    val = [child["type"].lower() == "folder" for child in children]
    while len(val) > 0 and True in val:
        for child in children:
            if child["type"].lower() == "folder":
                folder_paths.append(child["id"])
                children = ee.data.getList({"id": child["id"]})
        val = [child["type"].lower() == "folder" for child in children]
    print("Total folders: {}".format(len(folder_paths)))
    return folder_paths


# Copy function
def mover(path, fpath):
    ee.Initialize()
    if not ee.data.getInfo(path)==None:
        if ee.data.getInfo(path)["type"].lower() == "folder":
            replace_string=path
            replaced_string=fpath
            gee_folder_path = recursive(path)
            for folders in gee_folder_path:
                fcreate(folders, replace_string, replaced_string)
                children = ee.data.getList({"id": folders})
                for child in children:
                    if child["type"].lower() == "imagecollection":
                        collection_move(child["id"], replace_string, replaced_string, fpath)
                    elif child["type"].lower() == "image":
                        image_move(child["id"], replace_string, replaced_string, fpath)
                    elif child["type"].lower() == "table":
                        table_move(child["id"], replace_string, replaced_string, fpath)
                print("")
        elif ee.data.getInfo(path)["type"].lower() == "image":
            replace_string = None
            replaced_string = "/".join(fpath.split("/")[:-1])
            image_move(path, replace_string, replaced_string, fpath)
        elif ee.data.getInfo(path)["type"].lower() == "image_collection":
            replace_string = None
            replaced_string = "/".join(fpath.split("/")[:-1])
            collection_move(path, replace_string, replaced_string, fpath)
        elif ee.data.getInfo(path)["type"].lower() == "table":
            replace_string = None
            replaced_string = "/".join(fpath.split("/")[:-1])
            table_move(path, replace_string, replaced_string, fpath)
    else:
        print('Initial path {} not found'.format(path))
