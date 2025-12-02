"""Reporting tool for Google Earth Engine.

SPDX-License-Identifier: Apache-2.0
"""

import csv
import json
import logging
import signal
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import DefaultDict

import ee
from google.auth.transport.requests import AuthorizedSession

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
shutdown_requested = False


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global shutdown_requested
    print("\nShutdown requested. Finishing current tasks...")
    shutdown_requested = True


# Register signal handler
signal.signal(signal.SIGINT, signal_handler)


@dataclass
class AssetInfo:
    """Data class for asset information"""
    asset_type: str
    path: str
    owner: str
    readers: str
    writers: str


def get_sa_credentials_path() -> tuple[Path, Path]:
    """
    Get the service account credentials directory and file path.

    Returns:
        tuple: (sa_dir, sa_file) where both are Path objects
    """
    home_dir = Path.home()
    sa_dir = home_dir / '.config' / 'earthengine'
    sa_file = sa_dir / 'credentials'

    return sa_dir, sa_file


def get_authenticated_session() -> tuple[AuthorizedSession, str | None]:
    """
    Get an authenticated session without re-initializing Earth Engine.

    Returns:
        tuple: (session, project_name) where session is an AuthorizedSession
               and project_name is the project ID (or None for default auth)
    """
    sa_dir, sa_file = get_sa_credentials_path()

    if sa_file.exists():
        try:
            with open(sa_file) as f:
                sa_data = json.load(f)
                service_account_email = sa_data.get('client_email')

            if service_account_email:
                # Create session from service account credentials
                credentials = ee.ServiceAccountCredentials(service_account_email, str(sa_file))
                session = AuthorizedSession(credentials)

                # Extract project name from service account email
                project_name = service_account_email.split('@')[1].split('.')[0]

                return session, project_name
        except Exception as e:
            logger.warning(f"Could not load service account credentials: {e}")

    # Fallback to default authentication
    session = AuthorizedSession(ee.data.get_persistent_credentials())
    return session, None


def legacy_roots(session: AuthorizedSession) -> list[str]:
    """Get all legacy root asset paths"""
    legacy_root_list = []
    url = 'https://earthengine.googleapis.com/v1/projects/earthengine-legacy:listAssets'

    try:
        response = session.get(url=url)
        for asset in response.json().get('assets', []):
            legacy_root_list.append(asset['id'])
    except Exception as e:
        logger.error(f"Error getting legacy roots: {e}")

    return legacy_root_list


def is_legacy_path(path: str, legacy_root_list: list[str]) -> bool:
    """Check if a path is a legacy asset path"""
    # Users paths are always legacy
    if path.startswith('users/'):
        return True

    # Check if path itself is a legacy root
    if path in legacy_root_list:
        return True

    # Check if path is under any legacy root
    for root in legacy_root_list:
        if path.startswith(root + '/'):
            return True

    return False


def list_assets_legacy(parent: str, session: AuthorizedSession) -> list[dict]:
    """List assets using legacy API - excludes images inside collections"""
    # Extract the path after 'projects/'
    if parent.startswith('projects/'):
        parent_path = parent
    elif parent.startswith('users/'):
        parent_path = parent
    else:
        parent_path = f'projects/{parent}'

    url = f'https://earthengine.googleapis.com/v1/projects/earthengine-legacy/assets/{parent_path}:listAssets'

    try:
        response = session.get(url=url)
        assets = response.json().get('assets', [])

        # Filter out IMAGE assets - they're inside IMAGE_COLLECTIONs
        # We want: FOLDER, IMAGE_COLLECTION, TABLE, FEATURE_VIEW
        filtered = [a for a in assets if a.get('type') != 'IMAGE']

        return filtered
    except Exception as e:
        logger.error(f"Error listing legacy assets in {parent}: {e}")
        return []


def list_assets_modern(parent: str, session: AuthorizedSession) -> list[dict]:
    """List assets using modern API - excludes images inside collections"""
    # Extract project ID - parent could be:
    # - "space-geographer" (just project ID)
    # - "projects/space-geographer" (with projects/ prefix)
    # - "space-geographer/assets/subfolder" (project ID with path)

    if parent.startswith('projects/'):
        # Remove 'projects/' prefix
        parent = parent[9:]

    # Now parent is like: "space-geographer" or "space-geographer/assets/subfolder"
    url = f'https://earthengine.googleapis.com/v1/projects/{parent}:listAssets'

    try:
        response = session.get(url=url)
        assets = response.json().get('assets', [])

        # Filter out IMAGE assets - they're either inside IMAGE_COLLECTIONs or standalone
        # We want: FOLDER, IMAGE_COLLECTION, TABLE, FEATURE_VIEW
        # We DON'T want: Individual IMAGE assets (they're inside collections)
        filtered = [a for a in assets if a.get('type') != 'IMAGE']

        return filtered
    except Exception as e:
        logger.error(f"Error listing modern assets in {parent}: {e}")
        return []


def get_asset_acl(asset_path: str) -> tuple[str, str, str]:
    """Get asset ACL (owners, readers, writers)"""
    try:
        acl = ee.data.getAssetAcl(asset_path)
        owners = ",".join(acl.get("owners", [])) or "self"
        readers = ",".join(acl.get("readers", [])) or "self"
        writers = ",".join(acl.get("writers", [])) or "self"
        return owners, readers, writers
    except Exception as e:
        logger.error(f"Error getting ACL for {asset_path}: {e}")
        return "", "", ""


def list_assets_recursive(
    parent_path: str,
    session: AuthorizedSession,
    is_legacy: bool,
    asset_list: list[dict] | None = None,
    stats: dict | None = None
) -> list[dict]:
    """
    Recursively list all assets in a folder and subfolders.

    Args:
        parent_path: Path to the Earth Engine folder
        session: Authorized session for API calls
        is_legacy: Whether to use legacy API
        asset_list: List to accumulate results
        stats: Dictionary to track statistics

    Returns:
        List of dicts with asset information
    """
    global shutdown_requested

    if shutdown_requested:
        return asset_list or []

    if asset_list is None:
        asset_list = []

    if stats is None:
        stats = defaultdict(int)

    try:
        # Get assets based on legacy or modern API
        if is_legacy:
            assets = list_assets_legacy(parent_path, session)
        else:
            assets = list_assets_modern(parent_path, session)

        for asset in assets:
            if shutdown_requested:
                break

            # Use 'id' field which has the clean path (without projects/earthengine-legacy/assets/ prefix)
            asset_id = asset.get('id', asset.get('name'))
            assert isinstance(asset_id, str)  # For mypy.
            asset_type = asset['type']

            # Add to list
            asset_list.append({
                'type': asset_type,
                'path': asset_id
            })

            # Update stats
            stats[asset_type] += 1
            stats['total'] += 1

            # Print dynamic update
            print(f"\rProcessed: {stats['total']} assets | "
                  f"FOLDER: {stats.get('FOLDER', 0)} | "
                  f"IMAGE: {stats.get('IMAGE', 0)} | "
                  f"IMAGE_COLLECTION: {stats.get('IMAGE_COLLECTION', 0)} | "
                  f"TABLE: {stats.get('TABLE', 0)} | "
                  f"FEATURE_VIEW: {stats.get('FEATURE_VIEW', 0)}",
                  end='', flush=True)

            # ONLY recurse into FOLDER type assets
            # Explicitly DO NOT recurse into IMAGE_COLLECTION, TABLE, IMAGE, or FEATURE_VIEW
            if asset_type == 'FOLDER':
                list_assets_recursive(asset_id, session, is_legacy, asset_list, stats)

    except Exception as e:
        logger.error(f"Error listing assets in {parent_path}: {e}")

    return asset_list


def process_asset(asset: dict) -> AssetInfo | None:
    """Process a single asset and return its info"""
    global shutdown_requested

    if shutdown_requested:
        return None

    try:
        asset_path = asset['path']
        asset_type = asset['type']

        # Get ACL
        owner, readers, writers = get_asset_acl(asset_path)

        return AssetInfo(
            asset_type=asset_type.lower(),
            path=asset_path,
            owner=owner,
            readers=readers,
            writers=writers
        )
    except Exception as e:
        logger.error(f"Error processing {asset['path']}: {e}")
        return None


def write_csv(output_path: str, results: list[AssetInfo]):
    """Write results to CSV file"""
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["type", "path", "owner", "readers", "writers"])

        for result in results:
            writer.writerow([
                result.asset_type,
                result.path,
                result.owner,
                result.readers,
                result.writers
            ])


def write_json(output_path: str, results: list[AssetInfo]):
    """Write results to JSON file"""
    json_data = [asdict(result) for result in results]

    with open(output_path, 'w') as jsonfile:
        json.dump(json_data, jsonfile, indent=2)


def ee_report(output_path: str, asset_path: str | None = None, max_workers: int = 5, output_format: str = 'csv'):
    """
    Generate Earth Engine asset report.

    Args:
        output_path: Path to output file
        asset_path: Specific asset path to report on (None = all root assets)
        max_workers: Number of parallel workers for processing
        output_format: Output format ('csv' or 'json')
    """
    global shutdown_requested

    ee.Initialize()

    # Get authenticated session and project name
    session, project_name = get_authenticated_session()

    logger.info("Starting Earth Engine asset report generation...")

    if project_name:
        logger.info(f"Using service account with project: {project_name}")

    # Get legacy roots
    legacy_root_list = legacy_roots(session)
    logger.info(f"Found {len(legacy_root_list)} legacy root locations")

    # Determine which paths to process
    paths_to_process = []

    if asset_path:
        # Check if it's a legacy path
        is_legacy = is_legacy_path(asset_path, legacy_root_list)
        paths_to_process.append((asset_path, is_legacy))
        logger.info(f"Processing {'legacy' if is_legacy else 'modern'} asset path: {asset_path}")
    else:
        # If using service account and no path specified, use the project name
        if project_name:
            asset_path = f"projects/{project_name}"
            is_legacy = is_legacy_path(asset_path, legacy_root_list)
            paths_to_process.append((asset_path, is_legacy))
            logger.info(f"Processing service account project: {asset_path}")
        else:
            # Process all root assets
            roots = ee.data.getAssetRoots()
            for root in roots:
                root_id = root['id']
                is_legacy = is_legacy_path(root_id, legacy_root_list)
                paths_to_process.append((root_id, is_legacy))
            logger.info(f"Discovering assets in {len(paths_to_process)} root location(s)...")

    # Collect all assets
    print()  # New line for dynamic updates
    all_assets = []
    stats: DefaultDict[str, int] = defaultdict(int)

    for path, is_legacy in paths_to_process:
        if shutdown_requested:
            break

        try:
            # Get asset info to determine type
            if is_legacy:
                asset_info = ee.data.getAsset(path)
                asset_type = asset_info['type']
            else:
                # For modern projects, try to get asset info first
                try:
                    asset_info = ee.data.getAsset(path)
                    asset_type = asset_info['type']
                except:
                    # If that fails, treat it as a folder and list directly
                    asset_type = 'FOLDER'

            all_assets.append({'type': asset_type, 'path': path})
            stats[asset_type] += 1
            stats['total'] += 1

            # Only recurse into actual folders, not image collections or other types
            if asset_type == 'FOLDER':
                children = list_assets_recursive(path, session, is_legacy, [], stats)
                all_assets.extend(children)

        except Exception as e:
            logger.error(f"Error accessing {path}: {e}")
            continue

    print()  # New line after dynamic updates

    if shutdown_requested:
        logger.info("Discovery interrupted by user.")
        sys.exit(0)

    logger.info(f"Found {len(all_assets)} assets. Processing ACLs...")

    # Process assets in parallel
    results = []
    processed = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_asset = {
            executor.submit(process_asset, asset): asset
            for asset in all_assets
        }

        for future in as_completed(future_to_asset):
            if shutdown_requested:
                logger.info("Cancelling remaining tasks...")
                executor.shutdown(wait=False, cancel_futures=True)
                break

            result = future.result()
            if result:
                results.append(result)
                processed += 1

                # Show progress
                if processed % 100 == 0 or processed == len(all_assets):
                    print(f"\rProcessing ACLs: {processed}/{len(all_assets)}", end='', flush=True)

    print()  # New line after progress

    if shutdown_requested:
        logger.info(f"Report generation interrupted. Partial results ({len(results)} assets) will be saved.")

    # Write output based on format
    if output_format.lower() == 'json':
        write_json(output_path, results)
    else:
        write_csv(output_path, results)

    logger.info(f"Report complete! {len(results)} assets written to: {output_path}")
