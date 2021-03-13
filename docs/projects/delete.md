# Delete Assets

The delete is recursive, meaning it will delete also all children assets: images, collections and folders. Use with caution!

![geeadd_delete](https://user-images.githubusercontent.com/6677629/80338936-9d2a7c80-882b-11ea-948e-20baf061a2f2.gif)

```
> geeadd delete -h
usage: geeadd delete [-h] --id ID

optional arguments:
  -h, --help  show this help message and exit

Required named arguments.:
  --id ID     Full path to asset for deletion. Recursively removes all
              folders, collections and images.
```
