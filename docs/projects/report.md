# Assets Report tool

The Assets Report tool in geeadd is a robust utility designed to provide users with comprehensive insights into their Google Earth Engine (GEE) assets. This tool performs a recursive analysis of all your assets, including images, image collections, and tables, generating a detailed report that contains a wealth of information. The report includes essential fields such as asset type, path, number of assets, size in megabytes (MB), units, owner, readers, and writers for each asset. Please note that generating a detailed report may take some time due to the thorough analysis involved.

#### Key Features

- **Comprehensive Asset Reporting**: The Assets Report tool offers an in-depth analysis of all your GEE assets, enabling you to gain a comprehensive understanding of your asset inventory.

- **Detailed Information**: The generated report includes crucial asset details, such as type, path, quantity, size, ownership, and access permissions, making it a valuable resource for asset management and monitoring.

#### Usage

Using the Assets Report tool is straightforward, requiring only the specification of the location where you want to save the generated report in CSV format.

```bash
geeadd ee_report --outfile "report_file_location.csv"
```

- `--outfile`: The full path to the location where you want to save the report in CSV format.

#### Example

Here's an example demonstrating how to use the Assets Report tool to generate a comprehensive report of your GEE assets:

```bash
geeadd ee_report --outfile "C:\johndoe\report.csv"
```

![Generate GEE Assets Report](https://user-images.githubusercontent.com/6677629/80339534-d9121180-882c-11ea-9bbb-f50973a9950f.gif)

The Assets Report Tool in geeadd empowers users with a wealth of asset-related insights, facilitating effective asset management, auditing, and monitoring within the Google Earth Engine environment.
