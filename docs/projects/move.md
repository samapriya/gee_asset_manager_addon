# Move Assets tool

The Asset Move tool in geeadd is a versatile utility designed to simplify asset management within Google Earth Engine (GEE). This tool empowers users to perform recursive moves of entire Earth Engine assets, including folders, collections, images, and tables, from one location to another effortlessly.

#### Key Features

- **Effortless Asset Relocation**: The Asset Move tool streamlines the process of moving Earth Engine assets, ensuring that entire hierarchies of assets can be relocated with ease.

- **User-Friendly Interface**: The tool offers an intuitive command-line interface, making it accessible to users of all experience levels.

#### Usage

Using the Asset Move tool is simple and straightforward, allowing users to specify the source and destination paths for asset relocation.

```bash
geeadd move --initial "existing_asset_path" --final "new_asset_path"
```

- `--initial`: The existing path of the assets you want to move.

- `--final`: The new path where you want to relocate the assets.

#### Example

Here's an example illustrating how to use the Asset Move tool to efficiently manage Earth Engine assets:

```bash
geeadd move --initial "users/your_username/your_collection" --final "users/your_username/new_collection"
```

![Move GEE Assets](https://user-images.githubusercontent.com/6677629/80338068-779c7380-8829-11ea-815e-8e1f68896154.gif)

The Asset Move tool in geeadd simplifies asset relocation, making it an invaluable asset for users seeking to organize and manage their Earth Engine assets efficiently.
