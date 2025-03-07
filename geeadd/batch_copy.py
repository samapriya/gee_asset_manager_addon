"""Optimized batch asset copying module for Google Earth Engine."""

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


def camel_case(s):
    """Convert string to camel case (Title Case)."""
    words = s.split()
    return ' '.join(word.title() for word in words)


def create_folder(folder_path):
    """Create a folder if it doesn't exist, handling both cloud and legacy folders."""
    try:
        if ee.data.getAsset(folder_path):
            return True
    except Exception:
        try:
            ee.data.createAsset({"type": ee.data.ASSET_TYPE_FOLDER_CLOUD}, folder_path)
        except Exception:
            try:
                ee.data.createAsset({"type": ee.data.ASSET_TYPE_FOLDER}, folder_path)
            except Exception as e:
                print(f"Error creating folder {folder_path}: {e}")
                return False
    return True


def copy_asset(source, destination, asset_type):
    """Copy a single asset with appropriate error handling and messaging."""
    try:
        # Check if destination already exists
        if ee.data.getAsset(destination):
            print(f"{camel_case(asset_type)} already copied: {destination}")
            return False
    except Exception:
        try:
            print(f"Copying {camel_case(asset_type)} to {destination}")
            ee.data.copyAsset(source, destination)
            return True
        except Exception as e:
            print(f"Error copying {source} to {destination}: {e}")
            return False


def copy_image_collection(source, destination, max_workers=10):
    """Copy an image collection with parallel execution for speed."""
    # Global variable to track if interrupt occurred
    global interrupt_received

    try:
        # Create the collection if it doesn't exist
        try:
            if ee.data.getAsset(destination):
                print(f"Collection exists: {ee.data.getAsset(destination)['id']}")
        except Exception:
            print(f"Collection does not exist: Creating {destination}")
            try:
                ee.data.createAsset({"type": ee.data.ASSET_TYPE_IMAGE_COLL_CLOUD}, destination)
            except Exception:
                ee.data.createAsset({"type": ee.data.ASSET_TYPE_IMAGE_COLL}, destination)

        # Get list of source images
        source_list = ee.data.listAssets({"parent": source})
        source_names = [os.path.basename(asset["name"]) for asset in source_list["assets"]]

        # Get list of destination images
        collection_path = ee.data.getAsset(destination)["name"]
        destination_list = ee.data.listAssets({"parent": collection_path})
        destination_names = [os.path.basename(asset["name"]) for asset in destination_list["assets"]]

        # Find images that need to be copied
        images_to_copy = set(source_names) - set(destination_names)
        total_images = len(images_to_copy)

        if not images_to_copy:
            print("All images already exist in destination collection. Nothing to copy.")
            return

        print(f"Copying {total_images} images in parallel...")

        # Use ThreadPoolExecutor for parallel copying
        results = []
        processed_count = 0
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        futures = {}

        try:
            # Submit all tasks
            for item in images_to_copy:
                if interrupt_received:
                    break
                source_path = f"{source}/{item}"
                dest_path = f"{collection_path}/{item}"
                future = executor.submit(ee.data.copyAsset, source_path, dest_path)
                futures[future] = item

            # Process results with progress bar
            with tqdm(total=total_images, desc="Copying images") as pbar:
                for future in concurrent.futures.as_completed(futures):
                    item = futures[future]

                    # Check if we've received an interrupt
                    if interrupt_received:
                        pbar.write("\nInterrupt received, cancelling remaining copy operations...")
                        # Cancel remaining futures
                        for f in futures:
                            if not f.done():
                                f.cancel()
                        break

                    try:
                        future.result()
                        results.append(True)
                    except Exception as e:
                        pbar.write(f"Error copying {item}: {e}")
                        results.append(False)

                    processed_count += 1
                    pbar.update(1)

        finally:
            # Always shut down the executor
            executor.shutdown(wait=False)

        if interrupt_received:
            print(f"\nOperation interrupted. Copied {processed_count} of {total_images} images.")
        else:
            success_count = sum(results)
            print(f"Successfully copied {success_count} of {total_images} images")

    except Exception as e:
        print(f"Error in collection copy: {e}")


def get_folder_structure(path):
    """Recursively gather all folders under a path."""
    folder_list = []

    def recursive_get_folders(current_path):
        try:
            asset_info = ee.data.getAsset(current_path)
            if asset_info["type"].lower() == "folder":
                folder_list.append(asset_info["name"])
                children = ee.data.listAssets({"parent": current_path})
                for child in children["assets"]:
                    if child["type"].lower() == "folder":
                        recursive_get_folders(child["name"])
        except Exception as e:
            print(f"Error accessing {current_path}: {e}")

    recursive_get_folders(path)
    return sorted(list(set(folder_list)))


# Global flag to track interrupt status
interrupt_received = False

# Signal handler for keyboard interrupts
def handle_interrupt(sig, frame):
    """Handle interrupt signals gracefully."""
    global interrupt_received
    if not interrupt_received:
        print("\nInterrupt received! Gracefully shutting down... (This may take a moment)")
        print("Press Ctrl+C again to force immediate exit (may leave tasks in an inconsistent state)")
        interrupt_received = True
    else:
        print("\nForced exit requested. Exiting immediately.")
        sys.exit(1)

def copy(path, fpath, max_workers=10):
    """Copy Earth Engine assets from path to fpath.

    Args:
        path: Source asset path
        fpath: Destination asset path
        max_workers: Maximum number of parallel workers for collection copying
    """
    global interrupt_received
    interrupt_received = False

    # Set up signal handler for graceful interrupts
    original_sigint_handler = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, handle_interrupt)

    try:
        ee.Initialize()

        asset_info = ee.data.getAsset(path)
        if not asset_info:
            print(f"Source asset not found: {path}")
            return

        asset_type = asset_info["type"].lower()

        if asset_type == "folder":
            # Copy folder structure
            folders = get_folder_structure(path)
            print(f"Found {len(folders)} folders to copy")

            # Get path prefixes for replacement
            initial_path_suffix = path.split("/")[-1]
            replace_string = "/".join(ee.data.getAsset(path)["name"].split("/")[:-1]) + "/" + initial_path_suffix

            final_path_suffix = fpath.split("/")[-1]
            replaced_string = ee.data.getAsset("/".join(fpath.split("/")[:-1]) + "/")["name"] + "/" + final_path_suffix

            # Create folder structure
            for folder in folders:
                if interrupt_received:
                    print("Operation interrupted. Stopping folder creation.")
                    break

                new_folder = folder.replace(replace_string, replaced_string)
                create_folder(new_folder)

                # Process assets in this folder
                try:
                    children = ee.data.listAssets({"parent": folder})
                    for child in children["assets"]:
                        if interrupt_received:
                            print("Operation interrupted. Stopping asset processing.")
                            break

                        child_type = child["type"].lower()
                        child_path = child["name"]
                        child_dest = child_path.replace(replace_string, replaced_string)

                        if child_type == "image_collection":
                            copy_image_collection(child_path, child_dest, max_workers)
                        elif child_type == "image":
                            copy_asset(child_path, child_dest, "image")
                        elif child_type == "table":
                            copy_asset(child_path, child_dest, "table")
                        elif child_type == "feature_view":
                            copy_asset(child_path, child_dest, "feature view")

                        # Check interrupt again after each asset
                        if interrupt_received:
                            break
                except Exception as e:
                    print(f"Error processing assets in folder {folder}: {e}")

        elif asset_type == "image":
            # Copy individual image
            destination = fpath
            copy_asset(path, destination, "image")

        elif asset_type == "image_collection":
            # Copy collection
            copy_image_collection(path, fpath, max_workers)

        elif asset_type in ("table", "feature_view"):
            # Copy table or feature view
            copy_asset(path, fpath, asset_type)

        else:
            print(f"Unsupported asset type: {asset_type}")

    except Exception as e:
        if not interrupt_received:
            print(f"Error copying assets: {e}")
    finally:
        # Restore original signal handler
        signal.signal(signal.SIGINT, original_sigint_handler)

        if interrupt_received:
            print("\nCopy operation was interrupted and has been stopped.")
            print("Some assets may have been copied while others were not.")
        else:
            print("Copy operation completed.")
