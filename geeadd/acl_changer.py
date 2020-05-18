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
import json
import itertools

# Empty Lists
folder_paths = []
image_list = []
collection_list = []
table_list = []

# Recursive folder paths
def recursive(path):
    if ee.data.getAsset(path)["type"].lower() == "folder":
        children = ee.data.listAssets({"parent": "projects/earthengine-legacy/assets/{}".format(path)})
    folder_paths.append(path.replace('projects/earthengine-legacy/assets/',''))
    val = [child["type"].lower() == "folder" for child in children['assets']]
    while len(val) > 0 and True in val:
        for child in children['assets']:
            if child["type"].lower() == "folder":
                folder_paths.append(child["id"])
                children = ee.data.listAssets({"parent": "projects/earthengine-legacy/assets/{}".format(child["id"])})
        val = [child["type"].lower() == "folder" for child in children['assets']]
    print("Total folders: {}".format(len(folder_paths)))
    return folder_paths


# folder parse
def fparse(path):
    ee.Initialize()
    if ee.data.getAsset(path)["type"].lower() == "folder":
        gee_folder_path = recursive(path)
        for folders in gee_folder_path:
            children = ee.data.listAssets({"parent": "projects/earthengine-legacy/assets/{}".format(folders)})
            for child in children['assets']:
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


##request type of asset, asset path and user to give permission
def access(collection_path, user, role):
    ee.Initialize()
    asset_list = fparse(collection_path)
    asset_names = list(itertools.chain(*asset_list))
    print("Changing permission for total of " + str(len(asset_names)) + " items.....")
    for count, init in enumerate(asset_names):
        print("Working on ===> {}".format(init))
        acl = ee.data.getAssetAcl(init)
        if role == "reader":
            if not user in acl["readers"]:
                baselist = acl["readers"]
                baselist.append(user)
                acl["readers"] = baselist
                acl["owners"] = []
                try:
                    ee.data.setAssetAcl(init, json.dumps(acl))
                except Exception as e:
                    print(e)
            else:
                print("user already has read access to this asset:SKIPPING")
        if role == "writer":
            if not user in acl["writers"]:
                baselist = acl["writers"]
                baselist.append(user)
                acl["readers"] = baselist
                acl["owners"] = []
                try:
                    ee.data.setAssetAcl(init, json.dumps(acl))
                except Exception as e:
                    print(e)
            else:
                print("user already has write access to this asset:SKIPPING")
        if role == "delete":
            if not user in acl["readers"]:
                print("user does not have permission:SKIPPING")
            else:
                baselist = acl["readers"]
                baselist.remove(user)
                acl["readers"] = baselist
                acl["owners"] = []
                try:
                    ee.data.setAssetAcl(init, json.dumps(acl))
                except Exception as e:
                    print(e)
