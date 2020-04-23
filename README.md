# Google Earth Engine Batch Asset Manager with Addons

[![PyPI version](https://badge.fury.io/py/geeadd.svg)](https://badge.fury.io/py/geeadd)
![Build Status](https://img.shields.io/badge/dynamic/json.svg?label=downloads&url=https%3A%2F%2Fpypistats.org%2Fapi%2Fpackages%2Fgeeadd%2Frecent%3Fperiod%3Dmonth&query=%24.data.last_month&colorB=blue&suffix=%2fmonth)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3762952.svg)](https://doi.org/10.5281/zenodo.3762952)
[![Can I Use Python 3?](https://caniusepython3.com/project/geeadd.svg)](https://caniusepython3.com/project/geeadd)


Google Earth Engine Batch Asset Manager with Addons is an extension of the one developed by Lukasz [here](https://github.com/tracek/gee_asset_manager) and additional tools were added to include functionality for moving assets, conversion of objects to fusion table, cleaning folders, querying tasks. The ambition is apart from helping user with batch actions on assets along with interacting and extending capabilities of existing GEE CLI. It is developed case by case basis to include more features in the future as it becomes available or as need arises.

If you use this tool to download data for your research, and find this tool useful, star and cite it as below

```
Samapriya Roy. (2020, April 23). samapriya/gee_asset_manager_addon: GEE Asset Manager with Addons (Version 0.4.0). Zenodo.
http://doi.org/10.5281/zenodo.3762952
```


## Table of contents
* [Installation](#installation)
* [Getting started](#getting-started)
* [Uploading](#uploading)
* [Usage examples](#usage-examples)
    * [quota](#quota)
    * [search](#search)
    * [App to Script](#app-to-script)
    * [Earth Engine Asset Report](#earth-engine-asset-report)
    * [Asset Size](#asset-size)
    * [Task Query](#task-query)
    * [Cancel tasks](#cancel-tasks)
    * [Assets Copy](#assets-copy)
    * [Assets Move](#assets-move)
    * [Assets Access](#assets-access)
    * [Delete](#delete)
    * [Delete Metadata](#delete-metadata)

## Installation
We assume Earth Engine Python API is installed and EE authorised as desribed [here](https://developers.google.com/earth-engine/python_install). From v0.3.4 onwards geeadd will only run on Python 3. Also with the new changes to the Earth Engine API library, the tool was completely modified to work with earthengine-api v0.1.127 and higher. Authenticate your earth engine client by using the following in your command line or terminal setup.

```
earthengine authenticate
```

Quick installation **```pip install geeadd```** or **```pip install geeadd --user```**

To install using github:
```
git clone https://github.com/samapriya/gee_asset_manager_addon
cd gee_asset_manager_addon && pip install -r requirements.txt
python setup.py install
```

The advantage of having it installed is being able to execute geeadd as any command line tool. I recommend installation within virtual environment. To install run
```
python setup.py develop or python setup.py install

In a linux distribution
sudo python setup.py develop or sudo python setup.py install
```


## Getting started

As usual, to print help:

![gee_main](https://user-images.githubusercontent.com/6677629/80064835-06964c80-8507-11ea-8b5d-70a985aaafab.png)

To obtain help for a specific functionality, simply call it with _help_ switch, e.g.: `geeadd copy -h`.


## Usage examples

### quota
This tool is the very basic of tools in the toolbox which gives you your current quota. This gives you the total used and remaining quota in all your legacy folders or user root folders. It requires no additional arguments just that your earthengine api is enabled.

```
> geeadd quota -h
usage: geeadd quota [-h]

optional arguments:
  -h, --help  show this help message and exit
```

### search
The search tool was added since v0.3.4 to enable users to search inside the Google Earth Engine catalog for images matching specific keywords and looks for matching images using names, ids , tags and so on. Try for example

```geeadd search --keywords "fire"```

```
> geeadd search -h
usage: geeadd search [-h] --keywords KEYWORDS

optional arguments:
  -h, --help           show this help message and exit

Required named arguments.:
  --keywords KEYWORDS  Keywords to search for can be id, provider, tag and so
                       on
```

### App to Script
This tool writes out or prints the underlying earthengine code for any public earthengine app. The tool has an option to export the code into a javascript file that you can then paste into Google Earth Engine code editor.

```
> geeadd app2script -h
usage: geeadd app2script [-h] --url URL [--outfile OUTFILE]

optional arguments:
  -h, --help         show this help message and exit

Required named arguments.:
  --url URL          Earthengine app url

Optional named arguments:
  --outfile OUTFILE  Write the script out to a .js file: Open in any text
                     editor
```

Simple setup can be

```
geeadd app2script --url "https://gena.users.earthengine.app/view/urban-lights"
```

or write to a javascript file which you can then open with any text editor and paste in earthengine code editor

```
geeadd app2script --url "https://gena.users.earthengine.app/view/urban-lights" --outfile "Full path to javascript.js"
```

### Earth Engine Asset Report
This tool recursively goes through all your assets(Includes Images, ImageCollection,Table,) and generates a report containing the following fields
[Type,Asset Type, Path,Number of Assets,size(MB),unit,owner,readers,writers]. This tool creates a detailed report and may take sometime to complete.

```
> geeadd ee_report -h
usage: geeadd ee_report [-h] --outfile OUTFILE

optional arguments:
  -h, --help         show this help message and exit

Required named arguments.:
  --outfile OUTFILE  This it the location of your report csv file
```

A simple setup is the following
``` geeadd --outfile "C:\johndoe\report.csv"```

### Asset Size
This tool allows you to query the size of any Earth Engine asset[Images, Image Collections, Tables and Folders] and prints out the number of assets and total asset size in non-byte encoding meaning KB, MB, GB, TB depending on size.

```
> geeadd assetsize -h
usage: geeadd assetsize [-h] --asset ASSET

optional arguments:
  -h, --help     show this help message and exit

Required named arguments.:
  --asset ASSET  Earth Engine Asset for which to get size properties
```

### Task Query
This script counts all currently running, cancelled, ready and failed tasks and requires no arguments.

```
> geeadd tasks -h
usage: geeadd tasks [-h]

optional arguments:
  -h, --help  show this help message and exit
```

### Cancel tasks
This is a simple tool to cancel tasks with specific controls. This allows you to cancel all tasks, all running tasks, all ready tasks or just a single task with a task id.

```
> geeadd cancel -h
usage: geeadd cancel [-h] --tasks TASKS

optional arguments:
  -h, --help     show this help message and exit

Required named arguments.:
  --tasks TASKS  You can provide tasks as running or ready or all or even a
                 single task id
```

### Assets Copy
This script allows us to recursively copy entire folders, collections, images or tables. If you have read acess to assets from another user this will also allow you to copy assets from their assets.

```
geeadd copy -h
usage: geeadd copy [-h] [--initial INITIAL] [--final FINAL]

optional arguments:
  -h, --help         show this help message and exit

Required named arguments.:
  --initial INITIAL  Existing path of assets
  --final FINAL      New path for assets
```

### Assets Move
This script allows us to recursively move assets from one collection to the other.

```
> geeadd move -h
usage: geeadd move [-h] [--initial INITIAL] [--final FINAL]

optional arguments:
  -h, --help         show this help message and exit

Required named arguments.:
  --initial INITIAL  Existing path of assets
  --final FINAL      New path for assets
```

### Assets Access
This tool allows you to set asset acess for either folder , collection or image recursively meaning you can add collection access properties for multiple assets at the same time.

```
> geeadd access -h
usage: geeadd access [-h] --asset ASSET --user USER --role ROLE

optional arguments:
  -h, --help     show this help message and exit

Required named arguments.:
  --asset ASSET  This is the path to the earth engine asset whose permission
                 you are changing folder/collection/image
  --user USER    "user:person@example.com" or "group:team@example.com" or
                 "serviceAccount:account@gserviceaccount.com", try using
                 "allUsers" to make it public
  --role ROLE    Choose between reader, writer or delete
```

### Delete
The delete is recursive, meaning it will delete also all children assets: images, collections and folders. Use with caution!

```
> geeadd delete -h
usage: geeadd delete [-h] --id ID

optional arguments:
  -h, --help  show this help message and exit

Required named arguments.:
  --id ID     Full path to asset for deletion. Recursively removes all
              folders, collections and images.
```

### Delete metadata
This tool allows you to delete a specific property across a metadata. This is useful to reset any property for an ingested collection.

```
> geeadd delete_metadata -h
usage: geeadd delete_metadata [-h] --asset ASSET --property PROPERTY

optional arguments:
  -h, --help           show this help message and exit

Required named arguments.:
  --asset ASSET        This is the path to the earth engine asset whose
                       permission you are changing collection/image
  --property PROPERTY  Metadata name that you want to delete
```

### Changelog

### v0.4.0
- Improved quota tools to get all quota and asset counts.
- Added a search tool to search GEE catalog using keywords.
- Improved parsing for app to script tool.
- Detailed asset root for all root folders and recursively
- Cancel tasks now allows you to choose, running, ready or specific task ids.
- Assets copy and move now allows you to copy entire folders, collectiona and assets recursively
- Updated assets access tool
- Delete metadata allows you to delete metadata for existing collection.
- Overall general improvements and optimization.

#### v0.3.3
- General improvements
- Added tool to get underlying code from earthengine app

#### v0.3.1
- Updated list and asset size functions
- Updated function to generate earthengine asset report
- General optimization and improvements to distribution
- Better error handling

#### v0.3.0
- Removed upload function
- Upload handles by [geeup](https://github.com/samapriya/geeup)
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
