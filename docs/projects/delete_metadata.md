# Delete asset metadata

This tool allows you to delete a specific property across a metadata. This is useful to reset any property for an ingested collection.

![geeadd_delete_metadata](https://user-images.githubusercontent.com/6677629/80341015-a9b0d400-882f-11ea-84ad-d7ac46798cc7.gif)

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
