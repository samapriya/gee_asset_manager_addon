"""
Google Earth Engine Batch Asset Deletion Module
Efficiently delete assets with recursive traversal, concurrent processing, and graceful interruption.
"""

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

from datetime import datetime
import concurrent.futures
import json
import logging
import signal
import sys
import time

import ee
from tqdm import tqdm

# Configure module logger
logger = logging.getLogger(__name__)

# Global flag to track interrupt status
interrupt_received = False

# Global list to track assets
asset_list = []


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


def get_asset(path: str) -> tuple[str | None, str | None]:
    """
    Get asset information and add to asset_list.

    Args:
        path: Asset path to retrieve

    Returns:
        Tuple of (asset_name, asset_type) or (None, None) on error
    """
    try:
        parser = ee.data.getAsset(path)
        asset_type = parser["type"].lower()
        asset_list.append({"path": parser["name"], "type": asset_type})
        return parser["name"], asset_type
    except Exception as e:
        logger.debug(f"Error processing {path}: {e}")
        return None, None


def recursive_parallel(path: str, max_workers: int = 10) -> list[dict]:
    """
    Recursively gather all assets under a path using parallel execution.

    Args:
        path: Root path to start recursive search
        max_workers: Maximum number of concurrent threads

    Returns:
        List of asset dictionaries with 'path' and 'type' keys
    """
    try:
        path_info = ee.data.getAsset(path)
        asset_type = path_info["type"].lower()

        if asset_type in ["folder", "image_collection"]:
            children = ee.data.listAssets({"parent": path})
            paths = [child["name"] for child in children["assets"]]

            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                results = list(executor.map(get_asset, paths))
                new_folders = [
                    res[0]
                    for res in results
                    if res[1] in ["folder", "image_collection"] and res[0] is not None
                ]
                # Recursively process subfolders
                executor.map(lambda p: recursive_parallel(p, max_workers), new_folders)
    except Exception as e:
        logger.error(f"Error in recursive processing of {path}: {e}")

    return asset_list


def delete_with_retry(asset_path: str, max_retries: int = 3) -> dict[str, any]:
    """
    Delete a single asset with retry logic and specific error handling.

    Args:
        asset_path: Full path to the asset
        max_retries: Maximum number of retry attempts

    Returns:
        Dictionary with deletion result including status, error info, and metadata
    """
    for attempt in range(max_retries):
        try:
            ee.data.deleteAsset(asset_path)
            return {
                'asset_id': asset_path,
                'status': 'success',
                'attempt': attempt + 1,
                'timestamp': datetime.now().isoformat()
            }
        except ee.EEException as e:
            error_msg = str(e).lower()

            # Handle specific error cases
            if "not found" in error_msg:
                logger.debug(f"Asset not found (may have been deleted): {asset_path}")
                return {
                    'asset_id': asset_path,
                    'status': 'success',
                    'note': 'already_deleted'
                }

            if "permission denied" in error_msg:
                logger.error(f"Permission denied: {asset_path}")
                return {
                    'asset_id': asset_path,
                    'status': 'failed',
                    'error': 'permission_denied',
                    'error_message': str(e)
                }

            if "delete its children" in error_msg:
                logger.warning(f"Asset {asset_path} has children; delaying deletion")
                time.sleep(1)
                if max_retries > 1:
                    return delete_with_retry(asset_path, max_retries - 1)
                else:
                    return {
                        'asset_id': asset_path,
                        'status': 'failed',
                        'error': 'has_children',
                        'error_message': str(e)
                    }

            # Retry with exponential backoff for other errors
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.warning(f"Attempt {attempt + 1} failed for {asset_path}: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to delete {asset_path} after {max_retries} attempts: {e}")
                return {
                    'asset_id': asset_path,
                    'status': 'failed',
                    'error': 'max_retries_exceeded',
                    'error_message': str(e),
                    'attempts': max_retries
                }
        except Exception as e:
            logger.error(f"Unexpected error deleting {asset_path}: {e}")
            return {
                'asset_id': asset_path,
                'status': 'failed',
                'error': 'unexpected_error',
                'error_message': str(e)
            }

    return {
        'asset_id': asset_path,
        'status': 'failed',
        'error': 'max_retries_exceeded'
    }


def save_failed_assets(failed_assets: list[dict], filename: str | None = None) -> None:
    """
    Save list of failed assets to a JSON file.

    Args:
        failed_assets: List of failed asset dictionaries
        filename: Output filename (auto-generated if None)
    """
    if not failed_assets:
        logger.info("No failed assets to save")
        return

    if filename is None:
        filename = f'failed_deletions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

    try:
        with open(filename, 'w') as f:
            json.dump(failed_assets, f, indent=2)
        logger.info(f"Failed assets saved to: {filename}")
        print(f"Failed assets saved to: {filename}")
    except Exception as e:
        logger.error(f"Failed to save failed assets: {e}")


def delete(ids: str, max_workers: int = 10, max_retries: int = 3,
           verbose: bool = False) -> dict[str, any] | None:
    """
    Delete assets recursively with concurrent processing.

    This is the main function called by geeadd.py. It maintains backward compatibility
    while adding enhanced features like better error handling and statistics.

    Args:
        ids: Root asset path to delete (e.g., 'users/username/folder')
        max_workers: Maximum number of concurrent threads (default: 10)
        max_retries: Maximum retry attempts per asset (default: 3)
        verbose: Enable verbose logging (default: False)

    Returns:
        Dictionary with deletion summary statistics, or None if operation failed/cancelled

    Example:
        >>> delete('users/username/test_folder')
        >>> delete('users/username/test_folder', max_workers=20, max_retries=5)
    """
    global interrupt_received, asset_list
    interrupt_received = False
    asset_list = []
    failed_assets = []
    start_time = time.time()

    # Configure logging level
    if verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    # Set up interrupt handler
    original_sigint_handler = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, handle_interrupt)

    try:
        # Verify initial asset exists
        try:
            initial_asset_info = ee.data.getAsset(ids)
            if not initial_asset_info:
                print(f"Asset not found: {ids}")
                return None
        except Exception as e:
            print(f"Error getting asset info: {e}")
            return None

        # Gather all assets recursively
        print(f"Gathering all assets under {ids}...")
        asset_list = recursive_parallel(ids, max_workers)

        # Sort by depth (deepest first) to avoid parent-child deletion conflicts
        asset_list.sort(key=lambda x: x["path"].count("/"), reverse=True)

        if not asset_list:
            print("No assets found to delete.")
            return None

        print(f"Found {len(asset_list)} assets to delete")

        # Perform deletion
        successful_deletions = 0

        with tqdm(total=len(asset_list), desc="Deleting assets", unit="asset") as pbar:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_asset = {
                    executor.submit(delete_with_retry, asset["path"], max_retries): asset
                    for asset in asset_list
                }

                for future in concurrent.futures.as_completed(future_to_asset):
                    asset = future_to_asset[future]

                    # Check for interrupt
                    if interrupt_received:
                        pbar.write("\nInterrupt received, cancelling remaining delete operations...")
                        for f in future_to_asset:
                            if not f.done():
                                f.cancel()
                        break

                    try:
                        result = future.result()
                        if result['status'] == 'success':
                            successful_deletions += 1
                        else:
                            failed_assets.append(result)
                            if verbose:
                                pbar.write(f"Failed: {asset['path']} - {result.get('error', 'unknown error')}")
                    except Exception as e:
                        failed_assets.append({
                            'asset_id': asset['path'],
                            'status': 'failed',
                            'error': 'exception',
                            'error_message': str(e)
                        })
                        pbar.write(f"Error deleting {asset['path']}: {e}")

                    pbar.update(1)

        elapsed_time = time.time() - start_time

        # Print summary
        print(f"\nSuccessfully deleted {successful_deletions}/{len(asset_list)} assets")

        if verbose:
            print(f"Time elapsed: {elapsed_time:.2f} seconds")
            print(f"Rate: {len(asset_list) / elapsed_time:.2f} assets/second")

        # Save failed assets if any
        if failed_assets:
            save_failed_assets(failed_assets)
            print(f"\n{len(failed_assets)} assets failed to delete. See log file for details.")

        # Build summary
        summary = {
            'total_assets': len(asset_list),
            'deleted_successfully': successful_deletions,
            'failed_deletions': len(failed_assets),
            'elapsed_time_seconds': elapsed_time,
            'assets_per_second': len(asset_list) / elapsed_time if elapsed_time > 0 else 0,
            'interrupted': interrupt_received,
            'failed_assets': failed_assets
        }

        return summary

    except Exception as e:
        print(f"Unexpected error in deletion process: {e}")
        logger.error(f"Unexpected error in deletion process: {e}")
        return None
    finally:
        signal.signal(signal.SIGINT, original_sigint_handler)
        if interrupt_received:
            print("\nDelete operation was interrupted and has been stopped.")
            print("Some assets may have been deleted while others were not.")
