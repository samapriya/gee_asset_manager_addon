# Change asset permissions

This tool allows you to set asset access for either folder , collection or image recursively meaning you can add collection access properties for multiple assets at the same time. Updates to v1.0.0 and later does not require user email parsing so you can pass it an individual user email, a google group or a google service account and it should work without your needing to specify type.

![geeadd_access](https://user-images.githubusercontent.com/6677629/80338721-0c53a100-882b-11ea-9475-e210ea701433.gif)

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
