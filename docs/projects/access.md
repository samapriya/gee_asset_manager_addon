# Change asset permissions

The Access tool in geeadd empowers users to efficiently manage asset access permissions within Google Earth Engine (GEE). This tool streamlines the process of setting access properties for folders, collections, or images, and it does so recursively. This means you can apply access configurations to multiple assets simultaneously, saving you valuable time and effort.

#### Key Features

- **Recursive Access Configuration**: The Access tool enables you to apply access permissions recursively. This functionality allows you to set access properties for multiple assets at once, ensuring efficient and consistent management of your Earth Engine assets.

- **Simplified User Identification**: Starting from version 1.0.0 and onwards, the Access tool eliminates the need for manual email parsing. You can now directly provide an individual user email, a Google group, or a Google service account without specifying the type. This enhancement streamlines the process and makes it more user-friendly.

#### Usage
Using the Access tool is straightforward. Simply call the function and provide the necessary arguments.

![geeadd_access](https://github.com/samapriya/gee_asset_manager_addon/assets/6677629/54954596-4583-4b56-a9ac-54b33fef8631)

```
> geeadd access -h
usage: geeadd access [-h] --asset ASSET --user USER --role ROLE

options:
  -h, --help     show this help message and exit

Required named arguments.:
  --asset ASSET  This is the path to the earth engine asset whose permission you are changing folder/collection/image
  --user USER    Can be user email or serviceAccount like account@gserviceaccount.com or groups like group@googlegroups.com or try using "allUsers" to make it public
  --role ROLE    Choose between reader, writer or delete
```
