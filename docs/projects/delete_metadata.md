# Delete metadata tool

The Asset Metadata Delete tool in geeadd provides users with a valuable capability to delete specific properties from metadata associated with Earth Engine assets. This tool is particularly useful when you need to reset or remove a property value from the metadata of an ingested collection, image, or table.

#### Key Features

- **Selective Metadata Property Deletion**: The Asset Metadata Delete tool allows users to selectively delete a specific property from the metadata associated with an Earth Engine asset.

#### Usage

Using the Asset Metadata Delete tool is straightforward, requiring the specification of the target Earth Engine asset and the property to be deleted from its metadata.

```bash
geeadd delete_metadata --asset "asset_path_here" --property "metadata_property_to_delete"
```

- `--asset`: The path to the Earth Engine asset from which you want to remove a specific metadata property.

- `--property`: The name of the metadata property that you want to delete.

#### Example

Here's an example illustrating how to use the Asset Metadata Delete tool to remove a specific property from the metadata of an Earth Engine asset:

```bash
geeadd delete_metadata --asset "users/your_username/your_collection" --property "description"
```

![Delete Metadata GEE Asset](https://user-images.githubusercontent.com/6677629/80341015-a9b0d400-882f-11ea-84ad-d7ac46798cc7.gif)
