#Search GEE data catalog

The search tool was added since v0.3.4 to enable users to search inside the Google Earth Engine catalog for images matching specific keywords and looks for matching images using names, ids , tags and so on. The result is reported as a JSON and include the Earth Engine asset type snippet along with start and end dates. Try for example


```
geeadd search --keywords "fire"
```

![geeadd_search_json](https://user-images.githubusercontent.com/6677629/80329038-0223a980-880f-11ea-9abf-ecb7b63ae2c0.gif)

The search tool also includes the capability to search within the community datasets catalog since v0.5.4.

```
geeadd search --keywords ph --source community
```

![community_search](https://user-images.githubusercontent.com/6677629/111101250-852d1b80-8517-11eb-9173-eef523216f08.gif)
