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
import ee
import os


# Image copy
def image_copy(initial, replace_string, replaced_string, fpath):
    if replace_string == replaced_string or replace_string == None:
        final = fpath
    else:
        final = initial.replace(replace_string, replaced_string)
    try:
        if ee.data.getAsset(final):
            print("Image already copied: {}".format(final))
    except Exception as e:
        print("Copying image to {}".format(final))
        try:
            ee.data.copyAsset(initial, final)
        except Exception as e:
            print(e)


# Table copy
def table_copy(initial, replace_string, replaced_string, fpath):
    if replace_string == replaced_string or replace_string == None:
        final = fpath
    else:
        final = initial.replace(replace_string, replaced_string)
    try:
        if ee.data.getAsset(final):
            print("Table already copied: {}".format(final))
    except Exception as e:
        print("Copying table to {}".format(final))
        try:
            ee.data.copyAsset(initial, final)
        except Exception as e:
            print(e)


# Collection copy
def collection_copy(initial, replace_string, replaced_string, fpath):
    initial_list = ee.data.listAssets({"parent": initial})
    assets_names = [os.path.basename(asset["name"]) for asset in initial_list["assets"]]
    if replace_string == replaced_string or replace_string == None:
        collection_path = fpath
    else:
        collection_path = initial.replace(replace_string, replaced_string)
    try:
        if ee.data.getAsset(collection_path):
            print(
                "Collection exists: {}".format(ee.data.getAsset(collection_path)["id"])
            )
    except Exception as e:
        print("Collection does not exist: Creating {}".format(collection_path))
        try:
            ee.data.createAsset(
                {"type": ee.data.ASSET_TYPE_IMAGE_COLL_CLOUD}, collection_path
            )
        except Exception:
            ee.data.createAsset(
                {"type": ee.data.ASSET_TYPE_IMAGE_COLL}, collection_path
            )

    collection_path = ee.data.getAsset(collection_path)["name"]
    final_list = ee.data.listAssets({"parent": collection_path})
    final_names = [os.path.basename(asset["name"]) for asset in final_list["assets"]]
    diff = set(assets_names) - set(final_names)
    print("Copying a total of " + str(len(diff)) + " images.....")
    for count, items in enumerate(diff):
        print("Copying " + str(count + 1) + " of " + str(len(diff)), end="\r")
        init = initial + "/" + items
        fin = collection_path + "/" + items
        try:
            ee.data.copyAsset(init, fin)
        except Exception as e:
            print(e)


# Folder create
def fcreate(folder_path, replace_string, replaced_string):
    folder_path = folder_path.replace(replace_string, replaced_string)
    try:
        if ee.data.getAsset(folder_path):
            print("Folder exists: {}".format(ee.data.getAsset(folder_path)["id"]))
    except Exception as e:
        print("Folder does not exist: Creating {}".format(folder_path))
        try:
            ee.data.createAsset({"type": ee.data.ASSET_TYPE_FOLDER_CLOUD}, folder_path)
        except:
            ee.data.createAsset({"type": ee.data.ASSET_TYPE_FOLDER}, folder_path)


# Recursive folder paths
folder_list = []


def get_folder(path):
    parser = ee.data.getAsset(path)
    if parser["type"].lower() == "folder":
        folder_list.append(parser["name"])
        recursive(parser["name"])


def recursive(path):
    path = ee.data.getAsset(path)
    if path["type"].lower() == "folder":
        path = path["name"]
        folder_list.append(path)
        children = ee.data.listAssets({"parent": path})
        for child in children["assets"]:
            if not child["name"] in folder_list:
                get_folder(child["name"])
    return folder_list


# Copy function
def copy(path, fpath):
    ee.Initialize()
    try:
        if not ee.data.getAsset(path) == None:
            if ee.data.getAsset(path)["type"].lower() == "folder":
                gee_folder_path = recursive(path)
                gee_folder_path = sorted(list(set(gee_folder_path)))
                print("Total folders: {}".format(len(set(folder_list))))
                # Get the initial path
                initial_path_suffix = path.split("/")[-1]
                replace_string = (
                    "/".join(ee.data.getAsset(path + "/")["name"].split("/")[:-1])
                    + "/"
                    + initial_path_suffix
                )
                # Get the final path
                final_path_suffix = fpath.split("/")[-1]
                replaced_string = (
                    ee.data.getAsset(("/".join(fpath.split("/")[:-1]) + "/"))["name"]
                    + "/"
                    + final_path_suffix
                )
                for folders in gee_folder_path:
                    fcreate(folders, replace_string, replaced_string)
                    children = ee.data.listAssets({"parent": folders})
                    for child in children["assets"]:
                        if child["type"].lower() == "image_collection":
                            collection_copy(
                                child["name"], replace_string, replaced_string, fpath
                            )
                        elif child["type"].lower() == "image":
                            image_copy(
                                child["name"], replace_string, replaced_string, fpath
                            )
                        elif child["type"].lower() == "table":
                            table_copy(
                                child["name"], replace_string, replaced_string, fpath
                            )
                    print("")
            elif ee.data.getAsset(path)["type"].lower() == "image":
                path = ee.data.getAsset(path)["name"]
                initial_path_suffix = path.split("/")[-1]
                replace_string = (
                    "/".join(ee.data.getAsset(path)["name"].split("/")[:-1])
                    + "/"
                    + initial_path_suffix
                )
                final_path_suffix = fpath.split("/")[-1]
                replaced_string = (
                    ee.data.getAsset("/".join(fpath.split("/")[:-1]))["name"]
                    + "/"
                    + final_path_suffix
                )
                image_copy(path, replace_string, replaced_string, fpath)
            elif ee.data.getAsset(path)["type"].lower() == "image_collection":
                path = ee.data.getAsset(path)["name"]
                initial_list = ee.data.listAssets({"parent": path})
                assets_names = [
                    os.path.basename(asset["name"]) for asset in initial_list["assets"]
                ]
                collection_path = fpath
                try:
                    if ee.data.getAsset(collection_path):
                        print(
                            "Collection exists: {}".format(
                                ee.data.getAsset(collection_path)["id"]
                            )
                        )
                except Exception as e:
                    print(
                        "Collection does not exist: Creating {}".format(collection_path)
                    )
                    try:
                        ee.data.createAsset(
                            {"type": ee.data.ASSET_TYPE_IMAGE_COLL_CLOUD},
                            collection_path,
                        )
                    except Exception:
                        ee.data.createAsset(
                            {"type": ee.data.ASSET_TYPE_IMAGE_COLL}, collection_path
                        )

                collection_path = ee.data.getAsset(collection_path)["name"]
                final_list = ee.data.listAssets({"parent": collection_path})
                final_names = [
                    os.path.basename(asset["name"]) for asset in final_list["assets"]
                ]
                diff = set(assets_names) - set(final_names)
                print("Copying a total of " + str(len(diff)) + " images.....")
                for count, items in enumerate(diff):
                    print(
                        "Copying " + str(count + 1) + " of " + str(len(diff)), end="\r"
                    )
                    init = path + "/" + items
                    fin = collection_path + "/" + items
                    try:
                        ee.data.copyAsset(init, fin)
                    except Exception as e:
                        print(e)
                # collection_copy(path, replace_string, replaced_string, fpath)
            elif ee.data.getAsset(path)["type"].lower() == "table":
                path = ee.data.getAsset(path)["name"]
                replace_string = None
                replaced_string = ee.data.getAsset(
                    "/".join(fpath.split("/")[:-1]) + "/"
                )["name"]
                table_copy(path, replace_string, replaced_string, fpath)
    except Exception as e:
        print(e)


# copy(path='projects/earthengine-legacy/assets/users/samapriya/ppop/Dar-Es-Salaam-AOI',fpath='projects/earthengine-legacy/assets/users/samapriya/Dar-Es-Salaam-AOI')
