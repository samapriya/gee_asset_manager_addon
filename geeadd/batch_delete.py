import concurrent.futures
import signal
import sys
import time

import ee
from tqdm import tqdm

# Global flag to track interrupt status
interrupt_received = False

# Global list to track assets
asset_list = []
ee.Initialize()


def handle_interrupt(sig, frame):
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


def get_asset(path):
    """Get asset information and add to asset_list."""
    try:
        parser = ee.data.getAsset(path)
        asset_type = parser["type"].lower()
        asset_list.append({"path": parser["name"], "type": asset_type})
        return parser["name"], asset_type
    except Exception as e:
        print(f"Error processing {path}: {e}")
        return None, None


def recursive_parallel(path):
    """Recursively gather all assets under a path using parallel execution."""
    try:
        path_info = ee.data.getAsset(path)
        asset_type = path_info["type"].lower()

        if asset_type in ["folder", "image_collection"]:
            children = ee.data.listAssets({"parent": path})
            paths = [child["name"] for child in children["assets"]]

            with concurrent.futures.ThreadPoolExecutor() as executor:
                results = list(executor.map(get_asset, paths))
                new_folders = [
                    res[0]
                    for res in results
                    if res[1] in ["folder", "image_collection"] and res[0] is not None
                ]
                executor.map(recursive_parallel, new_folders)
    except Exception as e:
        print(f"Error in recursive processing of {path}: {e}")

    return asset_list


def delete_with_retry(asset_path, max_retries=3):
    for attempt in range(max_retries):
        try:
            ee.data.deleteAsset(asset_path)
            return True
        except ee.EEException as e:
            error_msg = str(e).lower()
            if "not found" in error_msg or "permission denied" in error_msg:
                print(f"Cannot delete {asset_path}: {e}")
                return True
            if "delete its children" in error_msg:
                print(f"Asset {asset_path} has children; delaying deletion")
                time.sleep(1)
                return (
                    delete_with_retry(asset_path, max_retries - 1)
                    if max_retries > 1
                    else False
                )
            if attempt < max_retries - 1:
                time.sleep(2**attempt)
            else:
                print(
                    f"Failed to delete {asset_path} after {max_retries} attempts: {e}"
                )
                return False
        except Exception as e:
            print(f"Unexpected error deleting {asset_path}: {e}")
            return False
    return False


def delete(ids, max_workers=10, max_retries=3):
    global interrupt_received, asset_list
    interrupt_received = False
    asset_list = []
    original_sigint_handler = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, handle_interrupt)
    try:
        try:
            initial_asset_info = ee.data.getAsset(ids)
            if not initial_asset_info:
                print(f"Asset not found: {ids}")
                return
        except Exception as e:
            print(f"Error getting asset info: {e}")
            return

        print(f"Gathering all assets under {ids}...")
        asset_list = recursive_parallel(ids)
        asset_list.sort(key=lambda x: x["path"].count("/"), reverse=True)

        if not asset_list:
            print("No assets found to delete.")
            return
        print(f"Found {len(asset_list)} assets to delete")

        successful_deletions = 0
        with tqdm(total=len(asset_list), desc="Deleting assets") as pbar:
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=max_workers
            ) as executor:
                future_to_asset = {
                    executor.submit(
                        delete_with_retry, asset["path"], max_retries
                    ): asset
                    for asset in asset_list
                }
                for future in concurrent.futures.as_completed(future_to_asset):
                    asset = future_to_asset[future]
                    if interrupt_received:
                        pbar.write(
                            "\nInterrupt received, cancelling remaining delete operations..."
                        )
                        for f in future_to_asset:
                            if not f.done():
                                f.cancel()
                        break
                    try:
                        if future.result():
                            successful_deletions += 1
                    except Exception as e:
                        pbar.write(f"Error deleting {asset['path']}: {e}")
                    pbar.update(1)
        print(f"\nSuccessfully deleted {successful_deletions}/{len(asset_list)} assets")
    except Exception as e:
        print(f"Unexpected error in deletion process: {e}")
    finally:
        signal.signal(signal.SIGINT, original_sigint_handler)
        if interrupt_received:
            print("\nDelete operation was interrupted and has been stopped.")
            print("Some assets may have been deleted while others were not.")


#delete("users/samapriya/LA_Datasets_Move")
