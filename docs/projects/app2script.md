# GEE App to Script tool

The App to Script tool in geeadd offers a convenient way to extract the underlying Earth Engine code from any public Earth Engine application. This tool provides two options: it can either print out the code or export it into a JavaScript file for easy integration into the Google Earth Engine code editor.

#### Key Features

- **Code Extraction**: The tool seamlessly retrieves the Earth Engine code that powers any public Earth Engine application, providing users with a clear understanding of the underlying code structure.

- **JavaScript Export**: Users have the option to export the code directly into a JavaScript file. This file can be opened in any text editor, allowing for easy modification and integration into the Google Earth Engine code editor.

#### Usage

Using the App to Script tool is straightforward. Simply provide the URL of the public Earth Engine application you want to extract the code from.

```bash
# Print out the Earth Engine code
geeadd app2script --url "https://gena.users.earthengine.app/view/urban-lights"
```

```bash
# Export the code to a JavaScript file
geeadd app2script --url "https://gena.users.earthengine.app/view/urban-lights" --outfile "Full path to javascript.js"
```

- `--url`: The URL of the public Earth Engine application.

- `--outfile`: (Optional) The full path to the JavaScript file where you want to export the code.

![GEE App to Script](https://user-images.githubusercontent.com/6677629/80331908-59c61300-8817-11ea-8075-fb0095f91dab.gif)

#### Example

The following example demonstrates how to use the App to Script tool to extract and export Earth Engine code:

```bash
# Print out the Earth Engine code
geeadd app2script --url "https://gena.users.earthengine.app/view/urban-lights"
```



