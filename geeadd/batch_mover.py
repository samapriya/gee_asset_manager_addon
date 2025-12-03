"""Optimized batch asset moving module for Google Earth Engine.

SPDX-License-Identifier: Apache-2.0
"""

import concurrent.futures
import logging
import os
import signal
import sys
import time
from functools import wraps
from typing import Any

import ee
import tqdm as tqdm_module

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global flag to track interrupt status
interrupt_received = False

# Global list to track folders
folder_list = []


def retry_on_ee_error(max_retries: int = 3, backoff_factor: float = 2):
    """Decorator for retrying EE operations with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Multiplier for exponential backoff delay

    Returns:
        Decorated function with retry logic

    Example:
        @retry_on_ee_error(max_retries=3)
        def my_ee_operation():
            return ee.data.getAsset('path/to/asset')
    """
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


def handle_interrupt(sig, frame):
    """Handle interrupt signals gracefully.

    Args:
        sig: Signal number
        frame: Current stack frame
    """
    global interrupt_received
    if not interrupt_received:
        logger.warning("Interrupt received! Gracefully shutting down... (This may take a moment)")
        logger.info("Press Ctrl+C again to force immediate exit (may leave tasks in an inconsistent state)")
        interrupt_received = True
    else:
        logger.error("Forced exit requested. Exiting immediately.")
        sys.exit(1)


def camel_case(s: str) -> str:
    """Convert string to camel case (Title Case).

    Args:
        s: Input string to convert

    Returns:
        Title-cased string
    """
    words = s.split()
    return " ".join(word.title() for word in words)


def get_asset_safe(asset_path: str) -> dict[str, Any] | None:
    """Safely get asset with proper error handling.

    Args:
        asset_path: Path to the Earth Engine asset

    Returns:
        Asset metadata dictionary or None if not found
    """
    try:
        return ee.data.getAsset(asset_path)
    except ee.EEException as e:
        if 'not found' in str(e).lower() or 'does not exist' in str(e).lower():
            return None
        raise
    except Exception:
        return None


def create_folder(folder_path: str, replace_string: str, replaced_string: str) -> None:
    """Create a folder if it doesn't exist, handling both cloud and legacy folders.

    Args:
        folder_path: Path where the folder should be created
        replace_string: String to replace in the path
        replaced_string: Replacement string for the path
    """
    folder_path = folder_path.replace(replace_string, replaced_string)

    try:
        asset = get_asset_safe(folder_path)
        if asset:
            logger.info(f"Folder exists: {asset['id']}")
            return
    except Exception:
        pass

    logger.info(f"Folder does not exist: Creating {folder_path}")
    try:
        # Try modern approach first
        ee.data.createAsset({"type": "FOLDER"}, folder_path)
    except Exception:
        # Fallback to legacy if needed
        try:
            ee.data.createAsset({"type": "Folder"}, folder_path)
        except Exception as e:
            logger.error(f"Error creating folder {folder_path}: {e}")


@retry_on_ee_error(max_retries=3)
def move_asset(
    source: str,
    replace_string: str | None,
    replaced_string: str,
    fpath: str,
    ftype: str = "asset"
) -> bool:
    """Move a single asset with appropriate error handling and messaging.

    Args:
        source: Source asset path
        replace_string: String to replace in the path (optional)
        replaced_string: Replacement string for the path
        fpath: Destination path
        ftype: Type of asset being moved (for logging)

    Returns:
        True if asset was moved, False if it already exists or on error
    """
    if replace_string == replaced_string or replace_string is None:
        final = fpath
    else:
        final = source.replace(replace_string, replaced_string)

    try:
        # Check if destination already exists
        if get_asset_safe(final):
            logger.info(f"{camel_case(ftype)} already moved: {final}")
            return False
    except Exception:
        pass

    try:
        logger.info(f"Moving {camel_case(ftype)} to {final}")
        ee.data.renameAsset(source, final)
        return True
    except Exception as e:
        logger.error(f"Error moving {source} to {final}: {e}")
        return False


def move_image_collection(
    source: str,
    replace_string: str | None,
    replaced_string: str,
    fpath: str,
    max_workers: int = 10
) -> None:
    """Move an image collection with parallel execution for speed.

    Args:
        source: Source image collection path
        replace_string: String to replace in the path (optional)
        replaced_string: Replacement string for the path
        fpath: Destination path
        max_workers: Maximum number of parallel worker threads
    """
    global interrupt_received

    if replace_string == replaced_string or replace_string is None:
        collection_path = fpath
    else:
        collection_path = source.replace(replace_string, replaced_string)

    try:
        # Create the collection if it doesn't exist
        dest_asset = get_asset_safe(collection_path)
        if dest_asset:
            logger.info(f"Collection exists: {dest_asset['id']}")
        else:
            logger.info(f"Collection does not exist: Creating {collection_path}")
            try:
                # Try modern approach first
                ee.data.createAsset({"type": "IMAGE_COLLECTION"}, collection_path)
            except Exception:
                # Fallback to legacy if needed
                try:
                    ee.data.createAsset({"type": "ImageCollection"}, collection_path)
                except Exception as e:
                    logger.error(f"Error creating collection: {e}")
                    return

        # Get list of source images
        source_list = ee.data.listAssets({"parent": source})
        source_names = [
            os.path.basename(asset["name"]) for asset in source_list.get("assets", [])
        ]

        # Get list of destination images - fetch asset again after potential creation
        collection_asset = get_asset_safe(collection_path)
        if not collection_asset:
            logger.error(f"Could not access destination collection {collection_path}")
            return

        collection_path = collection_asset["name"]
        final_list = ee.data.listAssets({"parent": collection_path})
        final_names = [
            os.path.basename(asset["name"]) for asset in final_list.get("assets", [])
        ]

        # Find images that need to be moved
        diff = set(source_names) - set(final_names)
        total_images = len(diff)

        if not diff:
            logger.info("All images already exist in destination collection. Nothing to move.")
            return

        logger.info(f"Moving a total of {total_images} images with {max_workers} workers...")

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
                future = executor.submit(move_asset_wrapper, source_path, dest_path)
                futures[future] = item

            # Process results with progress bar
            with tqdm_module.tqdm(total=total_images, desc="Moving images", unit="image") as pbar:
                for future in concurrent.futures.as_completed(futures):
                    item = futures[future]

                    # Check if we've received an interrupt
                    if interrupt_received:
                        logger.warning("Interrupt received, cancelling remaining move operations...")
                        # Cancel remaining futures
                        for f in futures:
                            if not f.done():
                                f.cancel()
                        break

                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        logger.error(f"Error moving {item}: {e}")
                        results.append(False)

                    processed_count += 1
                    pbar.update(1)

        finally:
            # Always shut down the executor
            executor.shutdown(wait=False)

        if interrupt_received:
            logger.warning(f"Operation interrupted. Moved {processed_count} of {total_images} images.")
        else:
            success_count = sum(results)
            failed_count = total_images - success_count
            logger.info(f"Successfully moved {success_count} of {total_images} images")
            if failed_count > 0:
                logger.warning(f"{failed_count} images failed to move")

    except Exception as e:
        logger.error(f"Error in collection move: {e}", exc_info=True)
        raise


def move_asset_wrapper(source: str, destination: str) -> bool:
    """Wrapper for moving assets in thread pool.

    Args:
        source: Source asset path
        destination: Destination asset path

    Returns:
        True if move succeeded, False otherwise
    """
    try:
        ee.data.renameAsset(source, destination)
        return True
    except Exception as e:
        logger.debug(f"Failed to move {source}: {e}")
        return False


def delete_asset_safe(asset_path: str) -> bool:
    """Safely delete an asset with proper error handling.

    Args:
        asset_path: Path to the asset to delete

    Returns:
        True if deletion succeeded, False otherwise
    """
    try:
        ee.data.deleteAsset(asset_path)
        logger.info(f"Deleted: {asset_path}")
        return True
    except ee.EEException as e:
        logger.error(f"Error deleting {asset_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error deleting {asset_path}: {e}")
        return False


def cleanup_empty_structure(path: str, skip_root: bool = False) -> None:
    """Recursively remove empty folders and collections from a path.

    Args:
        path: Root path to clean up
        skip_root: If True, don't delete the root folder itself (only children)
    """
    global interrupt_received

    if interrupt_received:
        logger.warning("Interrupt received, skipping cleanup")
        return

    try:
        asset = get_asset_safe(path)
        if not asset:
            return

        asset_type = asset.get("type", "").upper()
        asset_name = asset["name"]

        # Handle folders
        if asset_type == "FOLDER":
            # First, recursively clean up children
            try:
                children = ee.data.listAssets({"parent": asset_name})
                child_assets = children.get("assets", [])

                for child in child_assets:
                    if interrupt_received:
                        break
                    cleanup_empty_structure(child["name"])

                # After cleaning children, check if folder is now empty
                remaining = ee.data.listAssets({"parent": asset_name})
                if not remaining.get("assets", []) and not skip_root:
                    logger.info(f"Removing empty folder: {asset_name}")
                    delete_asset_safe(asset_name)

            except Exception as e:
                logger.error(f"Error cleaning up folder {asset_name}: {e}")

        # Handle image collections
        elif asset_type == "IMAGE_COLLECTION":
            try:
                images = ee.data.listAssets({"parent": asset_name})
                if not images.get("assets", []):
                    logger.info(f"Removing empty collection: {asset_name}")
                    delete_asset_safe(asset_name)
            except Exception as e:
                logger.error(f"Error cleaning up collection {asset_name}: {e}")

    except Exception as e:
        logger.error(f"Error in cleanup_empty_structure for {path}: {e}")


def get_folder(path: str) -> None:
    """Get folder information and add to folder_list.

    Args:
        path: Path to the folder
    """
    asset = get_asset_safe(path)
    if not asset:
        return

    if asset.get("type", "").upper() == "FOLDER":
        folder_list.append(asset["name"])
        recursive(asset["name"])


def recursive(path: str) -> list[str]:
    """Recursively gather all folders under a path.

    Args:
        path: Root path to scan for folders

    Returns:
        List of folder paths
    """
    path_info = get_asset_safe(path)
    if not path_info:
        return folder_list

    if path_info.get("type", "").upper() == "FOLDER":
        path = path_info["name"]
        folder_list.append(path)
        children = ee.data.listAssets({"parent": path})
        for child in children.get("assets", []):
            if child["name"] not in folder_list:
                get_folder(child["name"])
    return folder_list


def mover(path: str, fpath: str, max_workers: int = 10, cleanup: bool = True) -> None:
    """Move Earth Engine assets from path to fpath.

    This function handles moving of individual assets (images, tables, feature views)
    as well as entire folders and image collections. For image collections, moving
    is performed in parallel for improved performance. After moving, empty source
    folders and collections are automatically cleaned up unless disabled.

    Args:
        path: Source asset path (e.g., 'projects/my-project/assets/source-folder')
        fpath: Destination asset path (e.g., 'projects/my-project/assets/dest-folder')
        max_workers: Maximum number of parallel workers for collection moving (default: 10)
        cleanup: If True, remove empty source folders/collections after moving (default: True)

    Example:
        # Move a single image
        mover('projects/my-project/assets/image1', 'projects/my-project/assets/image2')

        # Move an entire folder structure
        mover('projects/my-project/assets/folder1', 'projects/my-project/assets/folder2')

        # Move an image collection without cleanup
        mover('projects/my-project/assets/collection1',
              'projects/my-project/assets/collection2',
              cleanup=False)
    """
    global interrupt_received
    global folder_list

    interrupt_received = False
    folder_list = []

    # Set up signal handler for graceful interrupts
    original_sigint_handler = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, handle_interrupt)

    operation_successful = False

    try:
        logger.info(f"Starting move operation from {path} to {fpath}")

        asset_info = get_asset_safe(path)
        if not asset_info:
            logger.error(f"Initial path {path} not found")
            return

        asset_type = asset_info.get("type", "").upper()
        logger.info(f"Source asset type: {asset_type}")

        # Store original path for cleanup
        original_source_path = asset_info["name"]

        if asset_type == "FOLDER":
            # Move folder structure
            logger.info("Scanning folder structure...")
            gee_folder_path = recursive(path)
            gee_folder_path = sorted(list(set(folder_list)))
            logger.info(f"Total folders: {len(set(folder_list))}")

            # Get path prefixes for replacement
            initial_path_suffix = path.split("/")[-1]
            source_asset = get_asset_safe(path + "/")
            if not source_asset:
                logger.error(f"Cannot access source path: {path}")
                return
            replace_string = (
                "/".join(source_asset["name"].split("/")[:-1])
                + "/"
                + initial_path_suffix
            )

            # Get the final path
            final_path_suffix = fpath.split("/")[-1]
            parent_path = "/".join(fpath.split("/")[:-1]) + "/"
            parent_asset = get_asset_safe(parent_path)
            if not parent_asset:
                logger.error(f"Cannot access destination parent path: {parent_path}")
                return
            replaced_string = parent_asset["name"] + "/" + final_path_suffix

            logger.info(f"Path mapping: {replace_string} -> {replaced_string}")

            # Create folder structure
            for folder in gee_folder_path:
                if interrupt_received:
                    logger.warning("Operation interrupted. Stopping folder creation.")
                    break

                create_folder(folder, replace_string, replaced_string)

                # Process assets in this folder
                try:
                    children = ee.data.listAssets({"parent": folder})
                    for child in children.get("assets", []):
                        if interrupt_received:
                            logger.warning("Operation interrupted. Stopping asset processing.")
                            break

                        child_type = child.get("type", "").upper()
                        child_path = child["name"]

                        if child_type == "IMAGE_COLLECTION":
                            move_image_collection(
                                child_path,
                                replace_string,
                                replaced_string,
                                fpath,
                                max_workers,
                            )
                        elif child_type == "IMAGE":
                            move_asset(
                                child_path,
                                replace_string,
                                replaced_string,
                                fpath,
                                "image",
                            )
                        elif child_type == "TABLE":
                            move_asset(
                                child_path,
                                replace_string,
                                replaced_string,
                                fpath,
                                "table",
                            )
                        elif child_type == "FEATURE_VIEW":
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
                    logger.error(f"Error processing assets in folder {folder}: {e}")

        elif asset_type == "IMAGE":
            # Move individual image
            image_asset = get_asset_safe(path)
            if not image_asset:
                logger.error(f"Cannot access image: {path}")
                return

            path = image_asset["name"]
            initial_path_suffix = path.split("/")[-1]
            replace_string = (
                "/".join(image_asset["name"].split("/")[:-1])
                + "/"
                + initial_path_suffix
            )

            final_path_suffix = fpath.split("/")[-1]
            parent_path = "/".join(fpath.split("/")[:-1])
            parent_asset = get_asset_safe(parent_path)
            if not parent_asset:
                logger.error(f"Cannot access destination parent: {parent_path}")
                return
            replaced_string = parent_asset["name"] + "/" + final_path_suffix

            move_asset(path, replace_string, replaced_string, fpath, "image")

        elif asset_type == "IMAGE_COLLECTION":
            # Move collection
            coll_asset = get_asset_safe(path)
            if not coll_asset:
                logger.error(f"Cannot access collection: {path}")
                return

            path = coll_asset["name"]
            initial_list = ee.data.listAssets({"parent": path})
            assets_names = [
                os.path.basename(asset["name"]) for asset in initial_list.get("assets", [])
            ]

            initial_path_suffix = path.split("/")[-1]
            replace_string = (
                "/".join(path.split("/")[:-1]) + "/" + initial_path_suffix
            )
            
            # FIX: Calculate replaced_string properly instead of passing None
            final_path_suffix = fpath.split("/")[-1]
            parent_path = "/".join(fpath.split("/")[:-1])
            if parent_path:  # Only if there's a parent path
                parent_path += "/"
                parent_asset = get_asset_safe(parent_path)
                if not parent_asset:
                    logger.error(f"Cannot access destination parent: {parent_path}")
                    return
                replaced_string = parent_asset["name"] + "/" + final_path_suffix
            else:
                # If no parent path, use fpath directly
                replaced_string = fpath

            move_image_collection(path, replace_string, replaced_string, fpath, max_workers)

        elif asset_type == "TABLE":
            # Move table
            table_asset = get_asset_safe(path)
            if not table_asset:
                logger.error(f"Cannot access table: {path}")
                return

            path = table_asset["name"]
            replace_string = None
            parent_path = "/".join(fpath.split("/")[:-1]) + "/"
            parent_asset = get_asset_safe(parent_path)
            if not parent_asset:
                logger.error(f"Cannot access destination parent: {parent_path}")
                return
            replaced_string = parent_asset["name"]
            move_asset(path, replace_string, replaced_string, fpath, "table")

        elif asset_type == "FEATURE_VIEW":
            # Move feature view
            fv_asset = get_asset_safe(path)
            if not fv_asset:
                logger.error(f"Cannot access feature view: {path}")
                return

            path = fv_asset["name"]
            replace_string = None
            parent_path = "/".join(fpath.split("/")[:-1]) + "/"
            parent_asset = get_asset_safe(parent_path)
            if not parent_asset:
                logger.error(f"Cannot access destination parent: {parent_path}")
                return
            replaced_string = parent_asset["name"]
            move_asset(path, replace_string, replaced_string, fpath, "feature view")

        else:
            logger.error(f"Unsupported asset type: {asset_type}")
            return

        # CLEANUP PHASE - only if not interrupted and cleanup is enabled
        if cleanup and not interrupt_received:
            logger.info("Starting cleanup of source structure...")
            cleanup_empty_structure(original_source_path)
            logger.info("Cleanup completed.")

        # If we got here without raising an exception, operation was successful
        operation_successful = True

    except Exception as e:
        if not interrupt_received:
            logger.error(f"Error moving assets: {e}", exc_info=True)
    finally:
        # Restore original signal handler
        signal.signal(signal.SIGINT, original_sigint_handler)

        if interrupt_received:
            logger.warning("Move operation was interrupted and has been stopped.")
            logger.warning("Some assets may have been moved while others were not.")
            if cleanup:
                logger.warning("Cleanup was skipped due to interruption. You may need to manually remove empty folders.")
        elif operation_successful:
            logger.info("Move operation completed successfully.")
        else:
            logger.error("Move operation failed. Check the error messages above for details.")
