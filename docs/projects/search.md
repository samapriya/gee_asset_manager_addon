# Search Tool

The Search tool, empowers users to explore the extensive [Google Earth Engine data catalog](https://developers.google.com/earth-engine/datasets/catalog) as well as the [Awesome GEE Community Catalog](https://gee-community-catalog.org/) effortlessly. It enables users to search for images that match specific keywords, searching based on names, IDs, tags, and more. The search results are conveniently presented in JSON format, providing valuable information such as Earth Engine asset types, start and end dates, and additional details.

#### Key Features

- **Efficient Data Catalog Search**: The Search tool allows users to efficiently explore the Google Earth Engine data catalog using custom keywords and search criteria. It simplifies the process of finding relevant Earth Engine assets.

- **Comprehensive Search Results**: The tool reports search results in JSON format, presenting essential information about the matched assets, including asset types, start and end dates, and other relevant details.

- **Community Dataset Support**: Starting from GEEadd version 0.5.4, the Search tool includes the capability to search within the community datasets catalog. This feature expands the search scope to include community-contributed datasets, further enriching the available data resources.

#### Usage

Using the Search tool is straightforward. You can specify keywords and, if desired, the source of the data catalog.

```bash
# Search for images matching the keyword "fire" in the Earth Engine data catalog
geeadd search --keywords "fire"
```

```bash
# Search for images in the community-contributed datasets catalog
geeadd search --keywords "ph" --source community
```

- `--keywords`: The keywords or search terms you want to use to find matching Earth Engine assets.

- `--source`: (Optional) The source of the data catalog you want to search in (default is Earth Engine data catalog).

## Example

Here's an example demonstrating how to use the Search tool to find Earth Engine assets:

```bash
# Search for images matching the keyword "fire" in the Earth Engine data catalog
geeadd search --keywords "fire"
```

![GEE Data Catalog Search](https://user-images.githubusercontent.com/6677629/80329038-0223a980-880f-11ea-9abf-ecb7b63ae2c0.gif)

The Search tool in GEEadd simplifies the process of discovering relevant Earth Engine assets, providing users with a powerful tool for accessing geospatial data within the Earth Engine ecosystem. Additionally, the tool's support for community-contributed datasets enhances its utility, making it an invaluable resource for Earth Engine users.

![community_search](https://user-images.githubusercontent.com/6677629/111101250-852d1b80-8517-11eb-9173-eef523216f08.gif)
