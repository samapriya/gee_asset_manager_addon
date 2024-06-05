# EE API Enabled Projects tool

The projects tool is a relatively new add and allows the owners of cloud projects to understand which cloud projects have earth engine api enabled. The tool only works on cloud projects you own because it needs to query all permissions to check for this. These are also the projects you should be able to add to your earth engine code editor.

#### Prerequisites
* This tool assumes you have gcloud installed and authenticated. It does check for these two things as it tries to run the tool.
* This assumes that the user has enabled the earth engine api on these projects since this is what the tool is checking for.

#### Features
- **Automatically checks gcloud installation and config** this is handy because it allows the user to know if they check their base configuration
- **Prints Project Name and Number** this is useful as a list to know which projects to set if needed for your python projects as well or to find out which projects to use in code editor.

#### Sample run

```
geeadd projects

```

![enabled_projects-censor](https://github.com/samapriya/awesome-gee-community-datasets/assets/6677629/19353761-e962-46f8-b768-ac11c492ef38)

#### Sample output

```
gcloud is installed and authenticated

Checking Earth Engine permissions for all projects...

Project Name: abc Project Number: 77544
Project Name: def Project Number: 433
Project Name: ghi Project Number: 107921
Project Name: ijk Project Number: 225

```
