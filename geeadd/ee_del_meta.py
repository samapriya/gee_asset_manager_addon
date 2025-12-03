"""Delete properties from Earth Engine assets.

SPDX-License-Identifier: Apache-2.0
"""

import logging
import os

import ee
import tqdm as tqdm_module

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_asset_safe(asset_path: str) -> dict | None:
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


def property_exists(asset_path: str, property_name: str) -> bool:
    """Check if a property exists on an asset.

    Args:
        asset_path: Path to the Earth Engine asset
        property_name: Name of the property to check

    Returns:
        True if property exists, False otherwise
    """
    try:
        asset_info = ee.data.getAsset(asset_path)
        properties = asset_info.get("properties", {})
        return property_name in properties
    except Exception:
        return False


def delprop(collection_path: str, property: str) -> None:
    """Delete a property from all assets in a collection or from a single image.

    Args:
        collection_path: Path to the Earth Engine asset (IMAGE or IMAGE_COLLECTION)
        property: Name of the property to delete

    Example:
        >>> delprop('users/samapriya/LA_ASSET_EXP/LS_UNMX_OTSU_MEDOID', 'gridded')
    """
    try:
        logger.info(f"Starting property deletion for: {collection_path}")
        logger.info(f"Property to delete: {property}")

        asset_info = get_asset_safe(collection_path)
        if not asset_info:
            logger.error(f"Asset not found: {collection_path}")
            return

        asset_type = asset_info.get("type", "").upper()
        logger.info(f"Asset type: {asset_type}")

        if asset_type == "IMAGE":
            assets_to_process = [collection_path]
            logger.info("Processing single image")
        elif asset_type == "IMAGE_COLLECTION":
            logger.info("Scanning image collection...")
            assets_list = ee.data.listAssets({"parent": collection_path})
            assets_to_process = [asset["name"] for asset in assets_list.get("assets", [])]
            logger.info(f"Found {len(assets_to_process)} images in collection")
        else:
            logger.error(f"Unsupported asset type: {asset_type}")
            logger.error("Only IMAGE and IMAGE_COLLECTION types are supported")
            return

        if not assets_to_process:
            logger.warning("No assets found to process")
            return

        # First, check if the property exists on any asset
        logger.info(f"Checking for property '{property}' existence...")
        assets_with_property = []

        for asset_path in assets_to_process:
            if property_exists(asset_path, property):
                assets_with_property.append(asset_path)

        if not assets_with_property:
            logger.warning(f"Property '{property}' does not exist on any of the {len(assets_to_process)} asset(s)")
            logger.info("Nothing to delete")
            return

        logger.info(f"Property '{property}' found on {len(assets_with_property)} of {len(assets_to_process)} asset(s)")
        logger.info(f"Deleting property '{property}' from {len(assets_with_property)} asset(s)...")

        nullgrid = {property: None}
        success_count = 0
        failed_count = 0

        # Use tqdm for progress tracking
        with tqdm_module.tqdm(total=len(assets_with_property), desc="Deleting property", unit="asset") as pbar:
            for asset_path in assets_with_property:
                try:
                    ee.data.setAssetProperties(asset_path, nullgrid)
                    success_count += 1
                    logger.debug(f"Successfully deleted property from: {asset_path}")
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Failed to delete property from {asset_path}: {e}")
                finally:
                    pbar.update(1)

        # Final summary
        logger.info("=" * 60)
        logger.info("Property deletion completed")
        logger.info(f"Total assets with property: {len(assets_with_property)}")
        logger.info(f"Successfully deleted: {success_count}")
        if failed_count > 0:
            logger.warning(f"Failed deletions: {failed_count}")
        if len(assets_to_process) > len(assets_with_property):
            logger.info(f"Skipped {len(assets_to_process) - len(assets_with_property)} assets (property not present)")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error during property deletion: {e}", exc_info=True)
        raise
