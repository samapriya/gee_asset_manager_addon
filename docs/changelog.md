# Changelog

### v0.5.5
- added folder migration tools
- improved recursive folder search & copy, move and permissions tools
- major improvements to copy and move tools for better migration of nested Folders
- Minor improvements and cleanup

### v0.5.4
- Updated search tool to use updated endpoint
- Search tool no longer downloads zip or parses CSV
- Minor improvements

### v0.5.2
- Updated copy tool to allow for non mirrored copy
- Updated task and task cancel tools to account for states Pending and Cancelling

### v0.5.1
- Updated quota tool to handle GCP projects inside GEE
- Updated Folder size reporting

### v0.5.0
- Updated to use earthengine-api>= 0.1.222
- Copy and move tool improvements to facilitate cloud alpha support.
- Updated task check tool to account for operations based handling.
-
### v0.4.9
- Fixed [issue 11](https://github.com/samapriya/gee_asset_manager_addon/issues/11).
- Updated to recent API calls based on Issue and general improvements
- Added auto version check from pypi.

### v0.4.7
- Fixed issue with delete tool and shell call.
- Fixed issue with copy and move function for single collections

### v0.4.6
- Now inclues asset_url and thumbnail_url for search.
- Formatting and general improvements.

### v0.4.5
- Now inclues license in sdist
- Fixed issue with app2script tool and string and text parsing.
- Added readme and version tools.
- Added readme docs and deployed environment.

### v0.4.4
- Removed git dependency and used urllib instead based on [feedback](https://github.com/samapriya/gee_asset_manager_addon/issues/10)
- Created conda forge release based on [Issue 10](https://github.com/samapriya/gee_asset_manager_addon/issues/10)

### v0.4.2
- Fixed relative import issue for earthengine.
- Fixed image collection move tool to parse ee object type correctly as image_collection.

### v0.4.1
- Made enhancement [Issue 9](https://github.com/samapriya/gee_asset_manager_addon/issues/9).
- Search tool now return earth engine asset snippet and start and end dates as JSON object.
- Removed pretty table dependency.

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

### v0.3.3
- General improvements
- Added tool to get underlying code from earthengine app

### v0.3.1
- Updated list and asset size functions
- Updated function to generate earthengine asset report
- General optimization and improvements to distribution
- Better error handling

### v0.3.0
- Removed upload function
- Upload handles by [geeup](https://github.com/samapriya/geeup)
- General optimization and improvements to distribution
- Better error handling

### v0.2.8
- Uses poster for streaming upload more stable with memory issues and large files
- Poster dependency limits use to Py 2.7 will fix in the new version

### v0.2.6
- Major improvement to move, batch copy, and task reporting
- Major improvements to access tool to allow users read/write permission to entire Folder/collection.

### v0.2.5
- Handles bandnames during upload thanks to Lukasz for original upload code
- Removed manifest option, that can be handled by seperate tool (ppipe)

### v0.2.3
- Removing the initialization loop error

### v0.2.2
- Added improvement to earthengine authorization

### v0.2.1
- Added capability to handle PlanetScope 4Band Surface Reflectance Metadata Type
- General Improvements

### v0.2.0
- Tool improvements and enhancements

### v0.1.9
- New tool EE_Report was added

### v0.1.8
- Fixed issues with install
- Dependencies now part of setup.py
- Updated Parser and general improvements
