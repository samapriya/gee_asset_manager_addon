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

import itertools
import logging
from typing import List, Tuple

import ee

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Asset type constants
ASSET_TYPE_FOLDER = "folder"
ASSET_TYPE_IMAGE = "image"
ASSET_TYPE_IMAGE_COLLECTION = "image_collection"
ASSET_TYPE_TABLE = "table"
ASSET_TYPE_FEATURE_VIEW = "feature_view"


class AssetCollector:
    """Helper class to collect and organize Earth Engine assets."""

    def __init__(self):
        self.images = []
        self.collections = []
        self.tables = []
        self.folders = []

    def clear(self):
        """Clear all collected assets."""
        self.images.clear()
        self.collections.clear()
        self.tables.clear()
        self.folders.clear()

    def get_all_assets(self) -> List[str]:
        """Get a flat list of all collected assets."""
        return list(set(itertools.chain(self.collections, self.tables, self.images)))


def get_folder_recursive(path: str, folder_list: List[str]) -> None:
    """
    Recursively collect all folder paths.

    Args:
        path: Asset path to start from
        folder_list: List to append discovered folders to
    """
    try:
        asset = ee.data.getAsset(path)
        if asset["type"].lower() == ASSET_TYPE_FOLDER:
            if path not in folder_list:
                folder_list.append(asset["name"])

            children = ee.data.listAssets({"parent": asset["name"]})
            for child in children.get("assets", []):
                child_name = child["name"]
                if child["type"].lower() == ASSET_TYPE_FOLDER and child_name not in folder_list:
                    get_folder_recursive(child_name, folder_list)
    except Exception as e:
        logger.error(f"Error accessing folder {path}: {e}")


def parse_asset_path(path: str) -> Tuple[List[str], List[str], List[str], List[str]]:
    """
    Parse an asset path and collect all assets within it.

    Args:
        path: Earth Engine asset path to parse

    Returns:
        Tuple of (collections, tables, images, folders)
    """
    collector = AssetCollector()

    try:
        asset = ee.data.getAsset(path)
        asset_type = asset["type"].lower()

        if asset_type == ASSET_TYPE_FOLDER:
            # Recursively collect all folders
            get_folder_recursive(path, collector.folders)
            collector.folders = sorted(list(set(collector.folders)))

            # Process each folder
            for folder in collector.folders:
                try:
                    children = ee.data.listAssets({"parent": folder})
                    for child in children.get("assets", []):
                        child_type = child["type"].lower()
                        child_id = child["id"]

                        if child_type == ASSET_TYPE_IMAGE_COLLECTION:
                            collector.collections.append(child_id)
                        elif child_type == ASSET_TYPE_IMAGE:
                            collector.images.append(child_id)
                        elif child_type in [ASSET_TYPE_TABLE, ASSET_TYPE_FEATURE_VIEW]:
                            collector.tables.append(child_id)
                except Exception as e:
                    logger.error(f"Error processing folder {folder}: {e}")

        elif asset_type == ASSET_TYPE_IMAGE:
            collector.images.append(path)
        elif asset_type == ASSET_TYPE_IMAGE_COLLECTION:
            collector.collections.append(path)
        elif asset_type in [ASSET_TYPE_TABLE, ASSET_TYPE_FEATURE_VIEW]:
            collector.tables.append(path)
        else:
            logger.warning(f"Unknown asset type: {asset_type}")

    except Exception as e:
        logger.error(f"Error parsing asset path {path}: {e}")

    return (
        collector.collections,
        collector.tables,
        collector.images,
        collector.folders
    )


def format_user_identifier(user: str) -> str:
    """
    Format user identifier according to Earth Engine requirements.

    Args:
        user: User email or identifier

    Returns:
        Properly formatted user identifier
    """
    user = user.strip()

    # Handle special cases
    if user.lower() == "allusers":
        return "allUsers"

    # Check if already prefixed
    if user.startswith(("user:", "group:", "serviceAccount:", "domain:")):
        return user

    # Add appropriate prefix
    if user.endswith("googlegroups.com"):
        return f"group:{user}"
    elif user.endswith("gserviceaccount.com"):
        return f"serviceAccount:{user}"
    elif "@" in user and "." in user:  # Domain format
        # Check if it's a domain (no username part)
        if user.count("@") == 0:
            return f"domain:{user}"
        return f"user:{user}"
    else:
        return f"user:{user}"


def set_asset_permissions(asset_path: str, user: str, role: str, project: str = None) -> None:
    """
    Set permissions for Earth Engine assets.

    Args:
        asset_path: Path to the asset or folder
        user: User email or identifier
        role: Permission role ('reader', 'writer', 'owner', or 'delete')
        project: Optional GCP project name for initialization
    """
    # Initialize Earth Engine
    try:
        if project:
            ee.Initialize(project=project)
        else:
            ee.Initialize()
    except Exception as e:
        logger.error(f"Error initializing Earth Engine: {e}")
        logger.info("Attempting to authenticate...")
        ee.Authenticate()
        if project:
            ee.Initialize(project=project)
        else:
            ee.Initialize()

    # Format user identifier
    user_formatted = format_user_identifier(user)

    # Parse asset path to get all assets
    collections, tables, images, folders = parse_asset_path(asset_path)
    asset_list = list(set(itertools.chain(collections, tables, images)))

    if not asset_list:
        logger.warning(f"No assets found at path: {asset_path}")
        return

    logger.info(f"Changing permissions for {len(asset_list)} asset(s)...")
    logger.info(f"User: {user_formatted}, Role: {role}")

    success_count = 0
    error_count = 0
    skip_count = 0

    for count, asset_id in enumerate(asset_list, 1):
        try:
            # Get current ACL
            acl = ee.data.getAssetAcl(asset_id)

            if role == "delete":
                # Remove user from all permission lists
                modified = False

                if user_formatted == "allUsers" and "all_users_can_read" in acl:
                    acl.pop("all_users_can_read")
                    modified = True

                for perm_type in ["readers", "writers", "owners"]:
                    if user_formatted in acl.get(perm_type, []):
                        acl[perm_type].remove(user_formatted)
                        modified = True

                if modified:
                    ee.data.setAssetAcl(asset_id, acl)
                    logger.info(f"[{count}/{len(asset_list)}] Removed {user_formatted} from {asset_id}")
                    success_count += 1
                else:
                    logger.debug(f"[{count}/{len(asset_list)}] {user_formatted} not found in ACL for {asset_id}: SKIPPING")
                    skip_count += 1

            elif role in ["reader", "writer", "owner"]:
                # Map role to permission list
                perm_map = {"reader": "readers", "writer": "writers", "owner": "owners"}
                target_list = perm_map[role]

                # Check if user already has this permission
                if user_formatted in acl.get(target_list, []):
                    logger.debug(f"[{count}/{len(asset_list)}] {user_formatted} already has {role} access to {asset_id}: SKIPPING")
                    skip_count += 1
                else:
                    # Add user to permission list
                    if target_list not in acl:
                        acl[target_list] = []
                    acl[target_list].append(user_formatted)

                    # Set the updated ACL
                    ee.data.setAssetAcl(asset_id, acl)
                    logger.info(f"[{count}/{len(asset_list)}] Added {user_formatted} as {role} for {asset_id}")
                    success_count += 1

            else:
                logger.error(f"Invalid role: {role}. Use 'reader', 'writer', 'owner', or 'delete'")
                return

        except Exception as e:
            logger.error(f"[{count}/{len(asset_list)}] Error updating {asset_id}: {e}")
            error_count += 1

    # Print summary
    logger.info(f"\n{'='*60}")
    logger.info(f"Summary:")
    logger.info(f"  Total assets: {len(asset_list)} with total of {success_count} successful changes.")
    if not skip_count==0:
        logger.info(f"  Skipped: {skip_count}")
    if not error_count==0:
        logger.info(f"  Errors: {error_count}")
    logger.info(f"{'='*60}")


# Convenience function for backwards compatibility
def access(collection_path: str, user: str, role: str, project: str = None) -> None:
    """
    Legacy function name for setting asset permissions.

    Args:
        collection_path: Path to the asset or folder
        user: User email or identifier
        role: Permission role ('reader', 'writer', 'owner', or 'delete')
        project: Optional GCP project name for initialization
    """
    set_asset_permissions(collection_path, user, role, project)


# Example usage
if __name__ == "__main__":
    # Example: Grant reader access to a user
    # set_asset_permissions(
    #     asset_path="projects/your-project/assets/your-folder",
    #     user="user@example.com",
    #     role="reader",
    #     project="your-cloud-project"
    # )

    # Example: Remove all permissions
    # set_asset_permissions(
    #     asset_path="projects/your-project/assets/your-folder",
    #     user="user@example.com",
    #     role="delete",
    #     project="your-cloud-project"
    # )

    pass
