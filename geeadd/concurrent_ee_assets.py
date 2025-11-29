import concurrent.futures
import csv
import json
import time
from collections import defaultdict
from pathlib import Path

import ee
from google.auth.transport.requests import AuthorizedSession

ee.Authenticate()

session = AuthorizedSession(
    ee.data.get_persistent_credentials()
)

def legacy_roots():
    """Fetch all legacy root assets"""
    legacy_root_list = []
    url = 'https://earthengine.googleapis.com/v1/projects/earthengine-legacy:listAssets'

    response = session.get(url=url)

    for asset in response.json().get('assets', []):
        #print(asset['id'])
        legacy_root_list.append(asset['id'])
    return legacy_root_list


def legacy_list_assets(parent: str, stats: dict | None = None, show_paths: bool = True) -> list[dict]:
    """List assets for a given parent path"""
    url = f'https://earthengine.googleapis.com/v1/projects/earthengine-legacy/assets/{parent}:listAssets'

    try:
        response = session.get(url=url)
        response.raise_for_status()

        assets = response.json().get('assets', [])

        # Print individual asset paths if requested
        if show_paths:
            for asset in assets:
                print(f"{asset['id']} - {asset['type']}")

        # Update stats if provided
        if stats is not None:
            for asset in assets:
                asset_type = asset['type']
                stats[asset_type] += 1
                stats['total'] += 1

            # Only print dynamic stats if we're showing paths
            if show_paths:
                print(f"\rProcessed: {stats['total']} assets | "
                      f"FOLDER: {stats.get('FOLDER', 0)} | "
                      f"IMAGE: {stats.get('IMAGE', 0)} | "
                      f"IMAGE_COLLECTION: {stats.get('IMAGE_COLLECTION', 0)} | "
                      f"TABLE: {stats.get('TABLE', 0)} | "
                      f"FEATURE_VIEW: {stats.get('FEATURE_VIEW', 0)}",
                      end='', flush=True)

        return assets
    except Exception as e:
        print(f"Error fetching assets for {parent}: {e}")
        return []


def list_assets(parent: str, stats: dict | None = None, show_paths: bool = True) -> list[dict]:
    """List assets for a given parent path (non-legacy)"""
    url = f'https://earthengine.googleapis.com/v1/projects/{parent}:listAssets'

    try:
        response = session.get(url=url)
        response.raise_for_status()

        assets = response.json().get('assets', [])

        # Print individual asset paths if requested
        if show_paths:
            for asset in assets:
                print(f"{asset['id']} - {asset['type']}")

        # Update stats if provided
        if stats is not None:
            for asset in assets:
                asset_type = asset['type']
                stats[asset_type] += 1
                stats['total'] += 1

            # Only print dynamic stats if we're showing paths
            if show_paths:
                print(f"\rProcessed: {stats['total']} assets | "
                      f"FOLDER: {stats.get('FOLDER', 0)} | "
                      f"IMAGE: {stats.get('IMAGE', 0)} | "
                      f"IMAGE_COLLECTION: {stats.get('IMAGE_COLLECTION', 0)} | "
                      f"TABLE: {stats.get('TABLE', 0)} | "
                      f"FEATURE_VIEW: {stats.get('FEATURE_VIEW', 0)}",
                      end='', flush=True)

        return assets
    except Exception as e:
        print(f"Error fetching assets for {parent}: {e}")
        return []


def legacy_list_assets_concurrent(
    parents: list[str],
    max_workers: int = 10,
    recursive: bool = False,
    stats: dict | None = None,
    show_paths: bool = True
) -> dict[str, list[dict]]:
    """
    Concurrently fetch assets for multiple parent paths

    Args:
        parents: List of parent paths to fetch assets from
        max_workers: Maximum number of concurrent workers
        recursive: If True, recursively fetch all nested folders. If False, only direct children (max_depth=1)
        stats: Optional dictionary to track statistics across all calls
        show_paths: If True, print individual asset paths

    Returns:
        Dictionary mapping parent paths to their assets
    """
    if stats is None:
        stats = defaultdict(int)

    results = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_parent = {
            executor.submit(legacy_list_assets, parent, stats, show_paths): parent
            for parent in parents
        }

        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_parent):
            parent = future_to_parent[future]
            try:
                assets = future.result()
                results[parent] = assets

                # If recursive, process subfolders
                if recursive:
                    folders = [asset['id'] for asset in assets if asset.get('type') == 'FOLDER']
                    if folders:
                        # Recursively process subfolders
                        subfolder_results = legacy_list_assets_concurrent(
                            folders,
                            max_workers=max_workers,
                            recursive=True,
                            stats=stats,
                            show_paths=show_paths
                        )
                        results.update(subfolder_results)

            except Exception as e:
                print(f"\nError processing {parent}: {e}")
                results[parent] = []

    return results


def list_assets_concurrent(
    parents: list[str],
    max_workers: int = 10,
    recursive: bool = False,
    stats: dict | None = None,
    show_paths: bool = True
) -> dict[str, list[dict]]:
    """
    Concurrently fetch assets for multiple parent paths (non-legacy)

    Args:
        parents: List of parent paths to fetch assets from
        max_workers: Maximum number of concurrent workers
        recursive: If True, recursively fetch all nested folders. If False, only direct children (max_depth=1)
        stats: Optional dictionary to track statistics across all calls
        show_paths: If True, print individual asset paths

    Returns:
        Dictionary mapping parent paths to their assets
    """
    if stats is None:
        stats = defaultdict(int)

    results = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_parent = {
            executor.submit(list_assets, parent, stats, show_paths): parent
            for parent in parents
        }

        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_parent):
            parent = future_to_parent[future]
            try:
                assets = future.result()
                results[parent] = assets

                # If recursive, process subfolders
                if recursive:
                    folders = [asset['id'] for asset in assets if asset.get('type') == 'FOLDER']
                    if folders:
                        # Recursively process subfolders
                        subfolder_results = list_assets_concurrent(
                            folders,
                            max_workers=max_workers,
                            recursive=True,
                            stats=stats,
                            show_paths=show_paths
                        )
                        results.update(subfolder_results)

            except Exception as e:
                print(f"\nError processing {parent}: {e}")
                results[parent] = []

    return results


def is_legacy_path(path: str, legacy_root_list: list[str]) -> bool:
    """Check if a path is a legacy asset path"""
    # Users paths are always legacy
    if path.startswith('users/'):
        return True

    # Check if path starts with projects/
    if path.startswith('projects/'):
        # Extract the part after projects/
        rest = path[9:]  # Remove 'projects/'

        # Check if it's earthengine-legacy
        if rest.startswith('earthengine-legacy'):
            return True

    # Check if path itself is a legacy root
    if path in legacy_root_list:
        return True

    # Check if path is under any legacy root
    for root in legacy_root_list:
        if path.startswith(root + '/'):
            return True

    return False


def export_to_csv(assets: list[dict], filepath: str) -> None:
    """Export assets to CSV file"""
    if not assets:
        print(f"No assets to export to {filepath}")
        return

    # Get all unique keys from all assets
    fieldnames = set()
    for asset in assets:
        fieldnames.update(asset.keys())
    fieldnames = sorted(fieldnames)

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(assets)

    print(f"\nExported {len(assets)} assets to {filepath}")


def export_to_json(assets: list[dict], filepath: str) -> None:
    """Export assets to JSON file"""
    if not assets:
        print(f"No assets to export to {filepath}")
        return

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(assets, f, indent=2, ensure_ascii=False)

    print(f"\nExported {len(assets)} assets to {filepath}")


def get_all_assets(
    parent: str,
    max_workers: int = 10,
    recursive: bool = False,
    export_path: str | None = None
) -> list[dict]:
    """
    Get all assets under a parent path. Automatically detects legacy vs modern API.

    Args:
        parent: Parent path to fetch assets from
        max_workers: Maximum number of concurrent workers
        recursive: If True, recursively fetch ALL nested folders. If False, only direct children
        export_path: Optional path to export results. Use .csv or .json extension. If None, print to console.

    Returns:
        List of all assets found (flattened)
    """
    stats = defaultdict(int)

    # Determine if we should show paths (only if not exporting)
    show_paths = export_path is None

    # Auto-detect if legacy or modern
    legacy_root_list = legacy_roots()
    is_legacy = is_legacy_path(parent, legacy_root_list)

    print(f"\nFetching assets from: {parent}")
    print(f"API: {'Legacy' if is_legacy else 'Modern'}")
    print(f"Mode: {'Recursive (all depths)' if recursive else 'Direct children only'}")
    if export_path:
        print(f"Export: {export_path}")
    print()

    if is_legacy:
        results_dict = legacy_list_assets_concurrent(
            [parent],
            max_workers=max_workers,
            recursive=recursive,
            stats=stats,
            show_paths=show_paths
        )
    else:
        results_dict = list_assets_concurrent(
            [parent.replace('projects/', '')],
            max_workers=max_workers,
            recursive=recursive,
            stats=stats,
            show_paths=show_paths
        )

    # Flatten results into a single list
    all_assets = []
    for parent_path, assets in results_dict.items():
        all_assets.extend(assets)

    # Print final stats if we're exporting (didn't print during processing)
    if not show_paths:
        print(f"\nProcessed: {stats['total']} assets | "
              f"FOLDER: {stats.get('FOLDER', 0)} | "
              f"IMAGE: {stats.get('IMAGE', 0)} | "
              f"IMAGE_COLLECTION: {stats.get('IMAGE_COLLECTION', 0)} | "
              f"TABLE: {stats.get('TABLE', 0)} | "
              f"FEATURE_VIEW: {stats.get('FEATURE_VIEW', 0)}")

    # Export if path provided
    if export_path:
        export_path_lower = export_path.lower()
        if export_path_lower.endswith('.csv'):
            export_to_csv(all_assets, export_path)
        elif export_path_lower.endswith('.json'):
            export_to_json(all_assets, export_path)
        else:
            print(f"\nWarning: Unknown file extension for {export_path}. Supported: .csv, .json")

    return all_assets


# Example usage
if __name__ == "__main__":
    # Example 1: Export to CSV (no console path printing, only final stats)
    print("=== Example 1: Export to CSV ===")
    start_time = time.time()
    assets = get_all_assets(
        'projects/sat-io/open-datasets',
        recursive=True,
        export_path='assets_output.csv'
    )
    end_time = time.time()
    print(f"Time: {end_time - start_time:.2f} seconds\n")

    # # Example 2: Export to JSON
    # print("\n=== Example 2: Export to JSON ===")
    # start_time = time.time()
    # assets = get_all_assets(
    #     'projects/space-geographer/assets/land-loss',
    #     recursive=False,
    #     export_path='assets_output.json'
    # )
    # end_time = time.time()
    # print(f"Time: {end_time - start_time:.2f} seconds\n")

    # # Example 3: No export (print paths to console, stats printed at end)
    # print("\n=== Example 3: Console Output Only ===")
    # start_time = time.time()
    # assets = get_all_assets(
    #     'projects/space-geographer/assets/land-loss',
    #     recursive=False,
    #     export_path=None  # Will print paths during processing
    # )
    # end_time = time.time()
    # print(f"\nTime: {end_time - start_time:.2f} seconds\n")
