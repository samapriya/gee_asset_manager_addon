# Google Earth Engine Batch Asset Manager with Addons

[![PyPI version](https://badge.fury.io/py/geeadd.svg)](https://badge.fury.io/py/geeadd)
![Build Status](https://img.shields.io/badge/dynamic/json.svg?label=downloads&url=https%3A%2F%2Fpypistats.org%2Fapi%2Fpackages%2Fgeeadd%2Frecent%3Fperiod%3Dmonth&query=%24.data.last_month&colorB=blue&suffix=%2fmonth)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.1194308.svg)](https://doi.org/10.5281/zenodo.1194308)
[![Can I Use Python 3?](https://caniusepython3.com/project/geeadd.svg)](https://caniusepython3.com/project/geeadd)
[![Say Thanks!](https://img.shields.io/badge/Say%20Thanks-!-1EAEDB.svg)](https://saythanks.io/to/samapriya)

Google Earth Engine Batch Asset Manager with Addons is an extension of the one developed by Lukasz [here](https://github.com/tracek/gee_asset_manager) and additional tools were added to include functionality for moving assets, conversion of objects to fusion table, cleaning folders, querying tasks. The ambition is apart from helping user with batch actions on assets along with interacting and extending capabilities of existing GEE CLI. It is developed case by case basis to include more features in the future as it becomes available or as need arises.

## Table of contents
* [Installation](#installation)
* [Getting started](#getting-started)
* [Uploading](#uploading)
* [Usage examples](#usage-examples)
    * [EE User](#ee-user)
    * [Asset List](#asset-list)
    * [Asset Size](#asset-size)
    * [Earth Engine Asset Report](#earth-engine-asset-report)
    * [Task Query](#task-query)
    * [Task Report](#task-report)
    * [Delete a collection with content:](#delete-a-collection-with-content)
    * [Assets Move](#assets-move)
    * [Assets Copy](#assets-copy)
    * [Assets Access](#assets-access)
    * [Set Collection Property](#set-collection-property)
    * [Cancel all tasks](#cancel-all-tasks)

## Installation
We assume Earth Engine Python API is installed and EE authorised as desribed [here](https://developers.google.com/earth-engine/python_install).

Quick installation **```pip install geeadd```**

To install using github:
```
git clone https://github.com/samapriya/gee_asset_manager_addon
cd gee_asset_manager_addon && pip install -r requirements.txt
python setup.py install
```

Installation is an optional step; the application can be also run
directly by executing geeadd.py script. The advantage of having it
installed is being able to execute geeadd as any command line tool. I
recommend installation within virtual environment. To install run
```
python setup.py develop or python setup.py install

In a linux distribution
sudo python setup.py develop or sudo python setup.py install
```


## Getting started

As usual, to print help:

![geeadd_main](https://user-images.githubusercontent.com/6677629/57304133-c139fe80-70ac-11e9-987c-532aa5ee2ed8.png)

To obtain help for a specific functionality, simply call it with _help_ switch, e.g.: `geeadd upload -h`. If you didn't install geeadd, then you can run it just by going to _geeadd_ directory and running `python
geeadd.py [arguments go here]`

## Uploading
You can upload tables and rasters using [geeup](https://github.com/samapriya/geeup). This uses selenium to handle uploading and hence cannot be used in a headless environment.

## Usage examples

### EE User
This tool is designed to allow different users to change earth engine authentication credentials. The tool invokes the authentication call and copies the authentication key verification website to the clipboard which can then be pasted onto a browser and the generated key can be pasted back

### Create
This tool allows you to create a collection or folder in your earth engine root directory. The tool uses the system cli to achieve this and this has been included so as to reduce the need to switch between multiple tools and CLI.
```
usage: geeadd.py create [-h] --typ TYP --path PATH

optional arguments:
  -h, --help   show this help message and exit
  --typ TYP    Specify type: collection or folder
  --path PATH  This is the path for the earth engine asset to be created full
               path is needsed eg: users/johndoe/collection
```
### Asset List
This tool is designed to either print or output asset lists within folders or collections using earthengine ls tool functions.
```
usage: geeadd.py lst [-h] --location LOCATION --typ TYP [--items ITEMS]
                     [--output OUTPUT]

optional arguments:
  -h, --help           show this help message and exit

Required named arguments.:
  --location LOCATION  This it the location of your folder/collection
  --typ TYP            Whether you want the list to be printed or output as
                       text[print/report]

Optional named arguments:
  --items ITEMS        Number of items to list
  --output OUTPUT      Folder location for report to be exported
```

### Asset Size
This tool allows you to query the size of any Earth Engine asset[Images, Image Collections, Tables and Folders] and prints out the number of assets and total asset size in non-byte encoding meaning KB, MB, GB, TB depending on size.

```
usage: geeadd assetsize [-h] --asset ASSET

optional arguments:
  -h, --help     show this help message and exit
  --asset ASSET  Earth Engine Asset for which to get size properties
```

### Earth Engine Asset Report
This tool recursively goes through all your assets(Includes Images, ImageCollection,Table,) and generates a report containing the following fields
[Type,Asset Type, Path,Number of Assets,size(MB),unit,owner,readers,writers].

```
usage: geeadd.py ee_report [-h] --outfile OUTFILE

optional arguments:
  -h, --help         show this help message and exit
  --outfile OUTFILE  This it the location of your report csv file
```
A simple setup is the following
``` geeadd --outfile "C:\johndoe\report.csv"```

### Task Query
This script counts all currently running and ready tasks along with failed tasks.
```
usage: geeadd.py tasks [-h]

optional arguments:
  -h, --help  show this help message and exit

geeadd.py tasks
```

### Task Report
Sometimes it is important to generate a report based on all tasks that is running or has finished. Generated report includes taskId, data time, task status and type
```
usage: geeadd taskreport [-h] [--r R]

optional arguments:
  -h, --help  show this help message and exit
  --r R       Folder Path where the reports will be saved
```

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

### Assets Move
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

### Assets Copy
This script allows us to recursively copy assets from one collection to the other. If you have read acess to assets from another user this will also allow you to copy assets from their collections.
```
usage: geeadd.py copy [-h] [--initial INITIAL] [--final FINAL]

optional arguments:
  -h, --help         show this help message and exit
  --initial INITIAL  Existing path of assets
  --final FINAL      New path for assets
geeadd.py mover --initial "users/johndoe/myfolder/myponycollection" --final "users/johndoe/myfolder/myotherponycollection"
```

### Assets Access
This tool allows you to set asset acess for either folder , collection or image recursively meaning you can add collection access properties for multiple assets at the same time.
```
usage: geeadd.py access [-h] --asset ASSET --user USER --role ROLE

optional arguments:
  -h, --help     show this help message and exit
  --asset ASSET  This is the path to the earth engine asset whose permission
                 you are changing folder/collection/image
  --user USER    Full email address of the user, try using "AllUsers" to make
                 it public
  --role ROLE    Choose between reader, writer or delete
```

### Set Collection Property
This script is derived from the ee tool to set collection properties and will set overall properties for collection.
```
usage: geeadd.py collprop [-h] [--coll COLL] [--p P]

optional arguments:
  -h, --help   show this help message and exit
  --coll COLL  Path of Image Collection
  --p P        "system:description=Description"/"system:provider_url=url"/"sys
               tem:tags=tags"/"system:title=title
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

### Changelog

#### v0.3.0
- Removed upload function
- Upload handled by [geeup](https://github.com/samapriya/geeup)
- General optimization and improvements to distribution
- Better error handling

#### v0.2.8
- Uses poster for streaming upload more stable with memory issues and large files
- Poster dependency limits use to Py 2.7 will fix in the new version

#### v0.2.6
- Major improvement to move, batch copy, and task reporting
- Major improvements to access tool to allow users read/write permission to entire Folder/collection.

#### v0.2.5
- Handles bandnames during upload thanks to Lukasz for original upload code
- Removed manifest option, that can be handled by seperate tool (ppipe)

#### v0.2.3
- Removing the initialization loop error

#### v0.2.2
- Added improvement to earthengine authorization

#### v0.2.1
- Added capability to handle PlanetScope 4Band Surface Reflectance Metadata Type
- General Improvements

#### v0.2.0
- Tool improvements and enhancements

#### v0.1.9
- New tool EE_Report was added

#### v0.1.8
- Fixed issues with install
- Dependencies now part of setup.py
- Updated Parser and general improvements
