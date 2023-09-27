# Copy Assets tool

The Copy Assets tool in geeadd offers a versatile solution for copying Earth Engine assets efficiently. With its recursive capabilities, this tool empowers users to duplicate entire folders, collections, images, or tables seamlessly. Additionally, it allows users with read access to assets from other users to copy assets from their repositories, enhancing collaboration and asset management.

#### Key Features

- **Comprehensive Asset Duplication**: The Copy Assets tool enables users to perform recursive copying of Earth Engine assets, ensuring that entire hierarchies of assets can be effortlessly duplicated.

- **User-Friendly Interface**: The tool offers a straightforward command-line interface, making it accessible to users of all experience levels.

- **Copy Assets from Other Users**: Users with read access to assets from other users can utilize this tool to copy assets from their repositories, facilitating collaborative projects and data sharing.

#### Usage

Using the Copy Assets tool is simple and intuitive, allowing users to specify the source and destination paths for asset duplication.

```bash
geeadd copy --initial "existing_asset_path" --final "new_asset_path"
```

- `--initial`: The existing path of the assets you want to copy.

- `--final`: The new path where you want to duplicate the assets.

#### Example

Here's an example demonstrating how to use the Copy Assets tool to duplicate Earth Engine assets:

```bash
geeadd copy --initial "users/your_username/your_collection" --final "users/your_username/copied_collection"
```

![Copy GEE Assets](https://user-images.githubusercontent.com/6677629/80337918-183e6380-8829-11ea-8482-7359e88fdd75.gif)

The Copy Assets tool in geeadd simplifies asset duplication and promotes efficient asset management within Google Earth Engine.
