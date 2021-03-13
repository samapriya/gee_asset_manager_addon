# Asset Report

This tool recursively goes through all your assets(Includes Images, ImageCollection,Table,) and generates a report containing the following fields
[Type,Asset Type, Path,Number of Assets,size(MB),unit,owner,readers,writers]. This tool creates a detailed report and may take sometime to complete.

![geeadd_report](https://user-images.githubusercontent.com/6677629/80339534-d9121180-882c-11ea-9bbb-f50973a9950f.gif)

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
