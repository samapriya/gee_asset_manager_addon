# Delete Assets tool

The Delete Assets tool in GEEadd is a powerful utility designed to facilitate asset management within Google Earth Engine (GEE). This tool empowers users to perform recursive deletions of Earth Engine assets, including folders, collections, images, and their child assets. However, it is important to exercise caution while using this tool, as it permanently removes assets and their associated data.

#### Key Features

- **Comprehensive Asset Deletion**: The Delete Assets tool allows users to perform recursive deletions of assets, ensuring that entire hierarchies of assets can be removed with a single command.

- **Use with Caution**: Due to the recursive nature of this tool, it will delete not only the specified asset but also all its child assets, including images, collections, and folders. Therefore, it is essential to use this tool with caution to avoid unintentional data loss.

#### Usage

Using the Delete Assets tool is straightforward, requiring only the specification of the target Earth Engine asset for deletion.

```bash
geeadd delete --id "asset_path_to_delete"
```

- `--id`: The full path to the asset you want to delete. This tool will recursively remove all child assets, including images, collections, and folders associated with the specified asset.

#### Example

Here's an example demonstrating how to use the Delete Assets tool to remove an Earth Engine asset and all its child assets:

```bash
geeadd delete --id "users/your_username/your_collection"
```

![Delete GEE Assets](https://user-images.githubusercontent.com/6677629/80338936-9d2a7c80-882b-11ea-948e-20baf061a2f2.gif)
