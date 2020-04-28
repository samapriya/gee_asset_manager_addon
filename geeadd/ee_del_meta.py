from __future__ import print_function

__copyright__ = """

    Copyright 2019 Samapriya Roy

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


def delprop(collection_path, property):
    ee.Initialize()
    lst = []
    header = ee.data.getInfo(collection_path)["type"]
    if header == "IMAGE":
        lst.append(collection_path)
        assets_names = lst
    if header == "IMAGE_COLLECTION":
        assets_list = ee.data.getList(params={"id": collection_path})
        assets_names = [os.path.basename(asset["id"]) for asset in assets_list]
    print("Deleting metadata for total of " + str(len(assets_names)) + " assets.....")
    for count, items in enumerate(assets_names):
        if header == "IMAGE_COLLECTION":
            nullgrid = {property: None}
            init = collection_path + "/" + items
            try:
                print(
                    "Processing " + str(count + 1) + " of " + str(len(assets_names)),
                    end="\r",
                )
                ee.data.setAssetProperties(init, nullgrid)
            except Exception as e:
                print(
                    "Could not run " + str(count + 1) + " of " + str(len(assets_names))
                )
                print(e)
        if header == "IMAGE":
            nullgrid = {property: None}
            init = collection_path + "/" + items
            try:
                print(
                    "Processing " + str(count + 1) + " of " + str(len(assets_names)),
                    end="\r",
                )
                ee.data.setAssetProperties(init, nullgrid)
            except Exception as e:
                print(
                    "Could not run " + str(count + 1) + " of " + str(len(assets_names))
                )
                print(e)


# delprop(collection_path='users/samapriya/LA_ASSET_EXP/LS_UNMX_OTSU_MEDOID',property='gridded')
# ee.data.setAssetProperties(args.asset_id, properties)
