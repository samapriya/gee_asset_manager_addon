# Asset Size tool

The Asset Size tool in geeadd provides users with a convenient means to query the size of Earth Engine assets, including images, image collections, tables, and folders. This tool offers valuable insights by displaying the number of assets and their total size, presented in easily comprehensible formats such as kilobytes (KB), megabytes (MB), gigabytes (GB), or terabytes (TB), depending on the size.

#### Key Features

- **Asset Size Query**: The Asset Size tool enables users to query the size of Earth Engine assets swiftly and accurately.

- **Informative Output**: The tool delivers clear and informative output, providing users with the number of assets and their cumulative size in human-readable formats.

#### Usage

Using the Asset Size tool is straightforward, requiring only the specification of the target Earth Engine asset.

```bash
geeadd assetsize --asset "your_asset_path_here"
```

- `--asset`: The Earth Engine asset for which you want to obtain size properties.

#### Example

Here's an example illustrating how to use the Asset Size tool to determine the size of an Earth Engine asset:

```bash
geeadd assetsize --asset "users/your_username/your_collection"
```

![Asset Size GEE Tool](https://user-images.githubusercontent.com/6677629/80339754-55a4f000-882d-11ea-928c-2434de130078.gif)
