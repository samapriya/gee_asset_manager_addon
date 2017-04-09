# Google Earth Engine Batch Asset Manager with Addons
Google Earth Engine Batch Asset Manager with Addons is an extension of the one developed by Lukasz [here](https://github.com/tracek/gee_asset_manager) and additional tools were added to include functionality for moving assets, conversion of objects to fusion table, cleaning folders, querying tasks. The ambition is apart from helping user with batch actions on assets along with interacting and extending capabilities of existing GEE CLI. It is developed case by case basis to include more features in the future as it becomes available or as need arises. tab.

## Table of contents
* [Installation](#installation)
* [Getting started](#getting-started)
    * [Batch uploader](#batch-uploader)
    * [Parsing metadata](#parsing-metadata)
* [Usage examples](#usage-examples)
    * [Delete a collection with content:](#delete-a-collection-with-content)
    * [Upload a directory with images and associate properties with each image:](#upload-a-directory-with-images-and-associate-properties-with-each-image)
	* [Upload a directory with images with specific NoData value to a selected destination:](#upload-a-directory-with-images-with-specific-nodata-value-to-a-selected-destination)
	* [Task Query](#task-query)
	* [Asset Mover](#asset-mover)
	* [Convert to Fusion Table](#convert-to-fusion-table)
	* [Cleanup Utility](#cleanup-utility)
	* [Cancel all tasks](#cancel-all-tasks)

## Installation
We assume Earth Engine Python API is installed and EE authorised as desribed [here](https://developers.google.com/earth-engine/python_install). To install:
```
git clone https://github.com/samapriya/gee_asset_manager_addon
cd gee_asset_manager_addon && pip install .
```

Installation is an optional step; the application can be also run
directly by executing geeadd.py script. The advantage of having it
installed is being able to execute geeadd as any command line tool. I
recommend installation within virtual environment. To install run
```
pip setup.py develop
```


## Getting started

As usual, to print help:
```
usage: geeadd.py [-h]
                 {delete,taskquery,mover,convert2ft,cleanout,upload,cancel}
                 ...

Google Earth Engine Batch Asset Manager with Addons

positional arguments:
  {delete,taskquery,mover,convert2ft,cleanout,upload,cancel}
    delete              Deletes collection and all items inside. Supports
                        Unix-like wildcards.
    taskquery           Queries currently running, enqued and uploaded assets
    mover               Moves all assets from one folder to other
    convert2ft          Uploads a given feature collection to Google Fusion
                        Table.
    cleanout            Clear folders with datasets from earlier downloaded
    upload              Batch Asset Uploader.
    cancel              Cancel all running tasks

optional arguments:
  -h, --help            show this help message and exit
```

To obtain help for a specific functionality, simply call it with _help_
switch, e.g.: `geeadd upload -h`. If you didn't install geeadd, then you
can run it just by going to _geeadd_ directory and running `python
geeadd.py [arguments go here]`

## Batch uploader
The script creates an Image Collection from GeoTIFFs in your local
directory. By default, the collection name is the same as the local
directory name; with optional parameter you can provide a different
name. Another optional parameter is a path to a CSV file with metadata
for images, which is covered in the next section:
[Parsing metadata](#parsing-metadata).



```
usage: geeadd.py upload [-h] -u USER --source SOURCE --dest DEST [-m METADATA]
                        [--large] [--nodata NODATA]

optional arguments:
  -h, --help            show this help message and exit

Required named arguments.:
  -u USER, --user USER  Google account name (gmail address).
  --source SOURCE       Path to the directory with images for upload.
  --dest DEST           Destination. Full path for upload to Google Earth
                        Engine, e.g. users/johndoe/myponycollection

Optional named arguments:
  -m METADATA, --metadata METADATA
                        Path to CSV with metadata.
  --large               (Advanced) Use multipart upload. Might help if upload
                        of large files is failing on some systems. Might cause
                        other issues.
  --nodata NODATA       The value to burn into the raster as NoData (missing
                        data)
```

### Parsing metadata
By metadata we understand here the properties associated with each image. Thanks to these, GEE user can easily filter collection based on specified criteria. The file with metadata should be organised as follows:

| filename (without extension) | property1 header | property2 header |
|------------------------------|------------------|------------------|
| file1                        | value1           | value2           |
| file2                        | value3           | value4           |

Note that header can contain only letters, digits and underscores. 

Example:

| id_no     | class      | category | binomial             |system:time_start|
|-----------|------------|----------|----------------------|-----------------|
| my_file_1 | GASTROPODA | EN       | Aaadonta constricta  |1478943081000    |
| my_file_2 | GASTROPODA | CR       | Aaadonta irregularis |1478943081000    |

The corresponding files are my_file_1.tif and my_file_2.tif. With each of the files five properties are associated: id_no, class, category, binomial and system:time_start. The latter is time in Unix epoch format, in milliseconds, as documented in GEE glosary. The program will match the file names from the upload directory with ones provided in the CSV and pass the metadata in JSON format:

```
{ id_no: my_file_1, class: GASTROPODA, category: EN, binomial: Aaadonta constricta, system:time_start: 1478943081000}
```

The program will report any illegal fields, it will also complain if not all of the images passed for upload have metadata associated. User can opt to ignore it, in which case some assets will have no properties.

Having metadata helps in organising your asstets, but is not mandatory - you can skip it.

## Usage examples

### Delete a collection with content:

The delete is recursive, meaning it will delete also all children assets: images, collections and folders. Use with caution!
```
geeadd delete users/johndoe/test
```

Console output:
```
2016-07-17 16:14:09,212 :: oauth2client.client :: INFO :: Attempting refresh to obtain initial access_token
2016-07-17 16:14:09,213 :: oauth2client.client :: INFO :: Refreshing access_token
2016-07-17 16:14:10,842 :: root :: INFO :: Attempting to delete collection test
2016-07-17 16:14:16,898 :: root :: INFO :: Collection users/johndoe/test removed
```

### Delete all directories / collections based on a Unix-like pattern

```
geeadd delete users/johndoe/*weird[0-9]?name*
```


### Upload a directory with images to your myfolder/mycollection and associate properties with each image:
```
geeadd upload -u johndoe@gmail.com --source path_to_directory_with_tif -m path_to_metadata.csv --dest users/johndoe/myfolder/myponycollection
```
The script will prompt the user for Google account password. The program will also check that all properties in path_to_metadata.csv do not contain any illegal characters for GEE. Don't need metadata? Simply skip this option.

### Upload a directory with images with specific NoData value to a selected destination 
```
geeadd upload -u johndoe@gmail.com --source path_to_directory_with_tif --dest users/johndoe/myfolder/myponycollection --nodata 222
```
In this case we need to supply full path to the destination, which is helpful when we upload to a shared folder. In the provided example we also burn value 222 into all rasters for missing data (NoData).

### Task Query
This script can be used intermittently to look at running, failed and ready(waiting) tasks. It can also be used to query tasks when uploading assets to collection by providing collection pathway.
```
usage: geeadd.py taskquery [-h] [--destination DESTINATION]

optional arguments:
  -h, --help            show this help message and exit
  --destination DESTINATION
                        Full path to asset where you are uploading files

geeadd.py taskquery "users/johndoe/myfolder/myponycollection"						
```

### Asset Mover
This script allows us to recursively move assets from one collection to the other.
```
usage: geeadd.py mover [-h] [--assetpath ASSETPATH] [--finalpath FINALPATH]

optional arguments:
  -h, --help            show this help message and exit
  --assetpath ASSETPATH
                        Existing path of assets
  --finalpath FINALPATH
                        New path for assets
geeadd.py mover --assetpath "users/johndoe/myfolder/myponycollection" --destination "users/johndoe/myfolder/myotherponycollection"					
```

### Convert to Fusion Table
Once validated with gdal and google fusion table it can be used to convert any geoObject to google fusion table. Forked and contributed by Gennadii [here](https://github.com/gena/ogr2ft). The scripts can be used only with a specific google account
```
usage: geeadd.py convert2ft [-h] --i I --o O [--add_missing]

optional arguments:
  -h, --help     show this help message and exit
  --i I          input feature source (KML, SHP, SpatiLite, etc.)
  --o O          output Fusion Table name
  --add_missing  add missing features from the last inserted feature index

geeadd.py convert2ft --i "./aoi.kml" --o "converted_aoi"
```

### Cleanup Utility
This script is used to clean folders once all processes have been completed. In short this is a function to clear folder on local machine.
```
usage: geeadd.py cleanout [-h] [--dirpath DIRPATH]

optional arguments:
  -h, --help         show this help message and exit
  --dirpath DIRPATH  Folder you want to delete after all processes have been
                     completed
geeadd.py cleanout --dirpath "./folder"
```
### Cancel all tasks
This is a simpler tool, can be called directly from the earthengine cli as well
```
earthengine cli command
earthengine task cancel all

usage: geeadd.py cancel [-h]

optional arguments:
  -h, --help  show this help message and exit
```
