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
import logging
import os
import signal
import sys
import time
from functools import wraps
from typing import Any

import ee
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def retry_on_ee_error(max_retries: int = 3, backoff_factor: float = 2):
    """Decorator for retrying EE operations with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except ee.EEException as e:
                    if attempt == max_retries - 1:
                        raise
                    if "rate limit" in str(e).lower() or "quota" in str(e).lower():
                        wait_time = backoff_factor ** attempt
                        logger.warning(f"Rate limit hit, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                    else:
                        raise
            return None
        return wrapper
    return decorator


def camel_case(s: str) -> str:
    """Convert string to camel case (Title Case)."""
    words = s.split()
    return ' '.join(word.title() for word in words)


def get_asset_safe(asset_path: str) -> dict[str, Any] | None:
    """Safely get asset with proper error handling."""
    try:
        return ee.data.getAsset(asset_path)
    except ee.EEException as e:
        if 'not found' in str(e).lower():
            return None
        raise
    except Exception:
        return None


def create_folder(folder_path: str) -> bool:
    """Create a folder if it doesn't exist, handling both cloud and legacy folders."""
    try:
        if get_asset_safe(folder_path):
            logger.debug(f"Folder already exists: {folder_path}")
            return True
    except Exception:
        pass

    # Try creating with modern string literals
    try:
        logger.info(f"Creating folder: {folder_path}")
        ee.data.createAsset({"type": "FOLDER"}, folder_path)
        return True
    except Exception:
        # Fallback to legacy approach if needed
        try:
            ee.data.createAsset({"type": "Folder"}, folder_path)
            return True
        except Exception as e:
            logger.error(f"Error creating folder {folder_path}: {e}")
            return False


@retry_on_ee_error(max_retries=3)
def copy_asset(source: str, destination: str, asset_type: str) -> bool:
    """Copy a single asset with appropriate error handling and messaging."""
    try:
        # Check if destination already exists
        if get_asset_safe(destination):
            logger.info(f"{camel_case(asset_type)} already copied: {destination}")
            return False
    except Exception:
        pass

    try:
        logger.info(f"Copying {camel_case(asset_type)} to {destination}")
        ee.data.copyAsset(source, destination)
        return True
    except Exception as e:
        logger.error(f"Error copying {source} to {destination}: {e}")
        return False


def copy_image_collection(source: str, destination: str, max_workers: int = 10) -> None:
    """Copy an image collection with parallel execution for speed."""
    global interrupt_received

    try:
        # Create the collection if it doesn't exist
        dest_asset = get_asset_safe(destination)
        if dest_asset:
            logger.info(f"Collection exists: {dest_asset['id']}")
        else:
            logger.info(f"Collection does not exist: Creating {destination}")
            try:
                # Try modern approach first
                ee.data.createAsset({"type": "IMAGE_COLLECTION"}, destination)
            except Exception:
                # Fallback to legacy if needed
                try:
                    ee.data.createAsset({"type": "ImageCollection"}, destination)
                except Exception as e:
                    logger.error(f"Error creating collection: {e}")
                    return

        # Get list of source images
        source_list = ee.data.listAssets({"parent": source})
        source_names = [os.path.basename(asset["name"]) for asset in source_list.get("assets", [])]

        # Get list of destination images
        collection_asset = get_asset_safe(destination)
        if not collection_asset:
            logger.error(f"Could not access destination collection {destination}")
            return

        collection_path = collection_asset["name"]
        destination_list = ee.data.listAssets({"parent": collection_path})
        destination_names = [os.path.basename(asset["name"]) for asset in destination_list.get("assets", [])]

        # Find images that need to be copied
        images_to_copy = set(source_names) - set(destination_names)
        total_images = len(images_to_copy)

        if not images_to_copy:
            logger.info("All images already exist in destination collection. Nothing to copy.")
            return

        logger.info(f"Copying {total_images} images in parallel with {max_workers} workers...")

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
                future = executor.submit(copy_asset_wrapper, source_path, dest_path)
                futures[future] = item

            # Process results with progress bar
            with tqdm(total=total_images, desc="Copying images", unit="image") as pbar:
                for future in concurrent.futures.as_completed(futures):
                    item = futures[future]

                    # Check if we've received an interrupt
                    if interrupt_received:
                        logger.warning("Interrupt received, cancelling remaining copy operations...")
                        # Cancel remaining futures
                        for f in futures:
                            if not f.done():
                                f.cancel()
                        break

                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        logger.error(f"Error copying {item}: {e}")
                        results.append(False)

                    processed_count += 1
                    pbar.update(1)

        finally:
            # Always shut down the executor
            executor.shutdown(wait=False)

        if interrupt_received:
            logger.warning(f"Operation interrupted. Copied {processed_count} of {total_images} images.")
        else:
            success_count = sum(results)
            failed_count = total_images - success_count
            logger.info(f"Successfully copied {success_count} of {total_images} images")
            if failed_count > 0:
                logger.warning(f"{failed_count} images failed to copy")

    except Exception as e:
        logger.error(f"Error in collection copy: {e}", exc_info=True)


def copy_asset_wrapper(source: str, destination: str) -> bool:
    """Wrapper for copying assets in thread pool."""
    try:
        ee.data.copyAsset(source, destination)
        return True
    except Exception as e:
        logger.debug(f"Failed to copy {source}: {e}")
        return False


def get_folder_structure(path: str) -> list[str]:
    """Recursively gather all folders under a path."""
    folder_list = []

    def recursive_get_folders(current_path: str) -> None:
        try:
            asset_info = get_asset_safe(current_path)
            if not asset_info:
                return

            asset_type = asset_info.get("type", "").upper()
            if asset_type == "FOLDER":
                folder_list.append(asset_info["name"])
                children = ee.data.listAssets({"parent": current_path})
                for child in children.get("assets", []):
                    if child.get("type", "").upper() == "FOLDER":
                        recursive_get_folders(child["name"])
        except Exception as e:
            logger.error(f"Error accessing {current_path}: {e}")

    recursive_get_folders(path)
    return sorted(list(set(folder_list)))


# Global flag to track interrupt status
interrupt_received = False


def handle_interrupt(sig, frame):
    """Handle interrupt signals gracefully."""
    global interrupt_received
    if not interrupt_received:
        logger.warning("Interrupt received! Gracefully shutting down... (This may take a moment)")
        logger.info("Press Ctrl+C again to force immediate exit (may leave tasks in an inconsistent state)")
        interrupt_received = True
    else:
        logger.error("Forced exit requested. Exiting immediately.")
        sys.exit(1)


def copy(path: str, fpath: str, max_workers: int = 10) -> None:
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
        # Initialize EE if not already initialized
        try:
            ee.data.getAssetRoots()
        except:
            logger.info("Initializing Earth Engine...")
            ee.Initialize()

        logger.info(f"Starting copy operation from {path} to {fpath}")

        asset_info = get_asset_safe(path)
        if not asset_info:
            logger.error(f"Source asset not found: {path}")
            return

        asset_type = asset_info.get("type", "").upper()
        logger.info(f"Source asset type: {asset_type}")

        if asset_type == "FOLDER":
            # Copy folder structure
            logger.info("Scanning folder structure...")
            folders = get_folder_structure(path)
            logger.info(f"Found {len(folders)} folders to copy")

            # Get path prefixes for replacement
            initial_path_suffix = path.split("/")[-1]
            source_asset = get_asset_safe(path)
            if not source_asset:
                logger.error(f"Cannot access source path: {path}")
                return
            replace_string = "/".join(source_asset["name"].split("/")[:-1]) + "/" + initial_path_suffix

            final_path_suffix = fpath.split("/")[-1]
            parent_path = "/".join(fpath.split("/")[:-1]) + "/"
            parent_asset = get_asset_safe(parent_path)
            if not parent_asset:
                logger.error(f"Cannot access destination parent path: {parent_path}")
                return
            replaced_string = parent_asset["name"] + "/" + final_path_suffix

            logger.info(f"Path mapping: {replace_string} -> {replaced_string}")

            # Create folder structure
            for folder in folders:
                if interrupt_received:
                    logger.warning("Operation interrupted. Stopping folder creation.")
                    break

                new_folder = folder.replace(replace_string, replaced_string)
                create_folder(new_folder)

                # Process assets in this folder
                try:
                    children = ee.data.listAssets({"parent": folder})
                    for child in children.get("assets", []):
                        if interrupt_received:
                            logger.warning("Operation interrupted. Stopping asset processing.")
                            break

                        child_type = child.get("type", "").upper()
                        child_path = child["name"]
                        child_dest = child_path.replace(replace_string, replaced_string)

                        if child_type == "IMAGE_COLLECTION":
                            copy_image_collection(child_path, child_dest, max_workers)
                        elif child_type == "IMAGE":
                            copy_asset(child_path, child_dest, "image")
                        elif child_type == "TABLE":
                            copy_asset(child_path, child_dest, "table")
                        elif child_type == "FEATURE_VIEW":
                            copy_asset(child_path, child_dest, "feature view")

                        # Check interrupt again after each asset
                        if interrupt_received:
                            break
                except Exception as e:
                    logger.error(f"Error processing assets in folder {folder}: {e}")

        elif asset_type == "IMAGE":
            # Copy individual image
            copy_asset(path, fpath, "image")

        elif asset_type == "IMAGE_COLLECTION":
            # Copy collection
            copy_image_collection(path, fpath, max_workers)

        elif asset_type in ("TABLE", "FEATURE_VIEW"):
            # Copy table or feature view
            copy_asset(path, fpath, asset_type.lower().replace("_", " "))

        else:
            logger.error(f"Unsupported asset type: {asset_type}")

    except Exception as e:
        if not interrupt_received:
            logger.error(f"Error copying assets: {e}", exc_info=True)
    finally:
        # Restore original signal handler
        signal.signal(signal.SIGINT, original_sigint_handler)

        if interrupt_received:
            logger.warning("Copy operation was interrupted and has been stopped.")
            logger.warning("Some assets may have been copied while others were not.")
        else:
            logger.info("Copy operation completed successfully.")
