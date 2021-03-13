# GEE app source

This tool writes out or prints the underlying earthengine code for any public earthengine app. The tool has an option to export the code into a javascript file that you can then paste into Google Earth Engine code editor.

![geeadd_app2script](https://user-images.githubusercontent.com/6677629/80331908-59c61300-8817-11ea-8075-fb0095f91dab.gif)

Simple setup can be

```
geeadd app2script --url "https://gena.users.earthengine.app/view/urban-lights"
```

or write to a javascript file which you can then open with any text editor and paste in earthengine code editor

```
geeadd app2script --url "https://gena.users.earthengine.app/view/urban-lights" --outfile "Full path to javascript.js"
```
