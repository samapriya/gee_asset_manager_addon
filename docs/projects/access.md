# Change asset permissions

This tool allows you to set asset access for either folder , collection or image recursively meaning you can add collection access properties for multiple assets at the same time.

![geeadd_access](https://user-images.githubusercontent.com/6677629/80338721-0c53a100-882b-11ea-9475-e210ea701433.gif)

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
