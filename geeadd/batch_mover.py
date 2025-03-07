"""Optimized batch asset moving module for Google Earth Engine."""

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

import concurrent.futures
import os
import signal
import sys

import ee
from tqdm import tqdm

# Global flag to track interrupt status
interrupt_received = False

# Global list to track folders
folder_list = []


# Signal handler for keyboard interrupts
def handle_interrupt(sig, frame):
    """Handle interrupt signals gracefully."""
    global interrupt_received
    if not interrupt_received:
        print(
            "\nInterrupt received! Gracefully shutting down... (This may take a moment)"
        )
        print(
            "Press Ctrl+C again to force immediate exit (may leave tasks in an inconsistent state)"
        )
        interrupt_received = True
    else:
        print("\nForced exit requested. Exiting immediately.")
        sys.exit(1)


def camel_case(s):
    """Convert string to camel case (Title Case)."""
    words = s.split()
    return " ".join(word.title() for word in words)


def create_folder(folder_path, replace_string, replaced_string):
    """Create a folder if it doesn't exist, handling both cloud and legacy folders."""
    folder_path = folder_path.replace(replace_string, replaced_string)
    try:
        if ee.data.getAsset(folder_path):
            print(f"Folder exists: {ee.data.getAsset(folder_path)['id']}")
    except Exception:
        print(f"Folder does not exist: Creating {folder_path}")
        try:
            ee.data.createAsset({"type": ee.data.ASSET_TYPE_FOLDER_CLOUD}, folder_path)
        except Exception:
            try:
                ee.data.createAsset({"type": ee.data.ASSET_TYPE_FOLDER}, folder_path)
            except Exception as e:
                print(f"Error creating folder {folder_path}: {e}")


def move_asset(source, replace_string, replaced_string, fpath, ftype="asset"):
    """Move a single asset with appropriate error handling and messaging."""
    if replace_string == replaced_string or replace_string is None:
        final = fpath
    else:
        final = source.replace(replace_string, replaced_string)

    try:
        # Check if destination already exists
        if ee.data.getAsset(final):
            print(f"{camel_case(ftype)} already moved: {final}")
            return False
    except Exception:
        try:
            print(f"Moving {camel_case(ftype)} to {final}")
            ee.data.renameAsset(source, final)
            return True
        except Exception as e:
            print(f"Error moving {source} to {final}: {e}")
            return False


def move_image_collection(
    source, replace_string, replaced_string, fpath, max_workers=10
):
    """Move an image collection with parallel execution for speed."""
    # Global variable to track if interrupt occurred
    global interrupt_received

    if replace_string == replaced_string or replace_string is None:
        collection_path = fpath
    else:
        collection_path = source.replace(replace_string, replaced_string)

    try:
        # Create the collection if it doesn't exist
        try:
            if ee.data.getAsset(collection_path):
                print(f"Collection exists: {ee.data.getAsset(collection_path)['id']}")
        except Exception:
            print(f"Collection does not exist: Creating {collection_path}")
            try:
                ee.data.createAsset(
                    {"type": ee.data.ASSET_TYPE_IMAGE_COLL_CLOUD}, collection_path
                )
            except Exception:
                ee.data.createAsset(
                    {"type": ee.data.ASSET_TYPE_IMAGE_COLL}, collection_path
                )

        # Get list of source images
        source_list = ee.data.listAssets({"parent": source})
        source_names = [
            os.path.basename(asset["name"]) for asset in source_list["assets"]
        ]

        # Get list of destination images
        collection_path = ee.data.getAsset(collection_path)["name"]
        final_list = ee.data.listAssets({"parent": collection_path})
        final_names = [
            os.path.basename(asset["name"]) for asset in final_list["assets"]
        ]

        # Find images that need to be moved
        diff = set(source_names) - set(final_names)
        total_images = len(diff)

        if not diff:
            print(
                "All images already exist in destination collection. Nothing to move."
            )
            return

        print(f"Moving a total of {total_images} images...")

        # Use ThreadPoolExecutor for parallel moving
        results = []
        processed_count = 0
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        futures = {}

        try:
            # Submit all tasks
            for item in diff:
                if interrupt_received:
                    break
                source_path = f"{source}/{item}"
                dest_path = f"{collection_path}/{item}"
                future = executor.submit(ee.data.renameAsset, source_path, dest_path)
                futures[future] = item

            # Process results with progress bar
            with tqdm(total=total_images, desc="Moving images") as pbar:
                for future in concurrent.futures.as_completed(futures):
                    item = futures[future]

                    # Check if we've received an interrupt
                    if interrupt_received:
                        pbar.write(
                            "\nInterrupt received, cancelling remaining move operations..."
                        )
                        # Cancel remaining futures
                        for f in futures:
                            if not f.done():
                                f.cancel()
                        break

                    try:
                        future.result()
                        results.append(True)
                    except Exception as e:
                        pbar.write(f"Error moving {item}: {e}")
                        results.append(False)

                    processed_count += 1
                    pbar.update(1)

        finally:
            # Always shut down the executor
            executor.shutdown(wait=False)

        if interrupt_received:
            print(
                f"\nOperation interrupted. Moved {processed_count} of {total_images} images."
            )
        else:
            success_count = sum(results)
            print(f"Successfully moved {success_count} of {total_images} images")

    except Exception as e:
        print(f"Error in collection move: {e}")


def get_folder(path):
    """Get folder information and add to folder_list."""
    parser = ee.data.getAsset(path)
    if parser["type"].lower() == "folder":
        folder_list.append(parser["name"])
        recursive(parser["name"])


def recursive(path):
    """Recursively gather all folders under a path."""
    path_info = ee.data.getAsset(path)
    if path_info["type"].lower() == "folder":
        path = path_info["name"]
        folder_list.append(path)
        children = ee.data.listAssets({"parent": path})
        for child in children["assets"]:
            if not child["name"] in folder_list:
                get_folder(child["name"])
    return folder_list


def mover(path, fpath, max_workers=10):
    """Move Earth Engine assets from path to fpath.

    Args:
        path: Source asset path
        fpath: Destination asset path
        max_workers: Maximum number of parallel workers for collection moving
    """
    global interrupt_received
    global folder_list

    interrupt_received = False
    folder_list = []

    # Set up signal handler for graceful interrupts
    original_sigint_handler = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, handle_interrupt)

    try:
        ee.Initialize()

        try:
            if not ee.data.getAsset(path):
                print(f"Initial path {path} not found")
                return

            asset_info = ee.data.getAsset(path)
            asset_type = asset_info["type"].lower()

            if asset_type == "folder":
                # Move folder structure
                gee_folder_path = recursive(path)
                gee_folder_path = sorted(list(set(folder_list)))
                print(f"Total folders: {len(set(folder_list))}")

                # Get path prefixes for replacement
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

                # Create folder structure
                for folder in gee_folder_path:
                    if interrupt_received:
                        print("Operation interrupted. Stopping folder creation.")
                        break

                    create_folder(folder, replace_string, replaced_string)

                    # Process assets in this folder
                    try:
                        children = ee.data.listAssets({"parent": folder})
                        for child in children["assets"]:
                            if interrupt_received:
                                print(
                                    "Operation interrupted. Stopping asset processing."
                                )
                                break

                            child_type = child["type"].lower()
                            child_path = child["name"]

                            if child_type == "image_collection":
                                move_image_collection(
                                    child_path,
                                    replace_string,
                                    replaced_string,
                                    fpath,
                                    max_workers,
                                )
                            elif child_type == "image":
                                move_asset(
                                    child_path,
                                    replace_string,
                                    replaced_string,
                                    fpath,
                                    "image",
                                )
                            elif child_type == "table":
                                move_asset(
                                    child_path,
                                    replace_string,
                                    replaced_string,
                                    fpath,
                                    "table",
                                )
                            elif child_type == "feature_view":
                                move_asset(
                                    child_path,
                                    replace_string,
                                    replaced_string,
                                    fpath,
                                    "feature view",
                                )

                            # Check interrupt again after each asset
                            if interrupt_received:
                                break
                    except Exception as e:
                        print(f"Error processing assets in folder {folder}: {e}")
                    print("")

            elif asset_type == "image":
                # Move individual image
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

                move_asset(path, replace_string, replaced_string, fpath, "image")

            elif asset_type == "image_collection":
                # Move collection
                path = ee.data.getAsset(path)["name"]
                initial_list = ee.data.listAssets({"parent": path})
                assets_names = [
                    os.path.basename(asset["name"]) for asset in initial_list["assets"]
                ]

                initial_path_suffix = path.split("/")[-1]
                replace_string = (
                    "/".join(path.split("/")[:-1]) + "/" + initial_path_suffix
                )

                move_image_collection(path, replace_string, None, fpath, max_workers)

            elif asset_type == "table":
                # Move table
                path = ee.data.getAsset(path)["name"]
                replace_string = None
                replaced_string = ee.data.getAsset(
                    "/".join(fpath.split("/")[:-1]) + "/"
                )["name"]
                move_asset(path, replace_string, replaced_string, fpath, "table")

            elif asset_type == "feature_view":
                # Move feature view
                path = ee.data.getAsset(path)["name"]
                replace_string = None
                replaced_string = ee.data.getAsset(
                    "/".join(fpath.split("/")[:-1]) + "/"
                )["name"]
                move_asset(path, replace_string, replaced_string, fpath, "feature view")

            else:
                print(f"Unsupported asset type: {asset_type}")

        except Exception as e:
            print(e)
            print(f"Initial path {path} not found")

    except Exception as e:
        if not interrupt_received:
            print(f"Error moving assets: {e}")
    finally:
        # Restore original signal handler
        signal.signal(signal.SIGINT, original_sigint_handler)

        if interrupt_received:
            print("\nMove operation was interrupted and has been stopped.")
            print("Some assets may have been moved while others were not.")
