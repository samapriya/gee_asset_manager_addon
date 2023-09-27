# Tasks tool

The Tasks tool in geeadd provides a streamlined approach to monitor and manage tasks within Google Earth Engine (GEE). It offers comprehensive insights into the status of ongoing tasks, including those that are running, cancelled, pending, and failed. Additionally, the tool allows for detailed task-specific information retrieval by providing either the task state or a specific task ID.

#### Key Features

- **Task Status Overview**: The Tasks tool offers a quick summary of tasks currently in progress, cancelled, pending, and those that have encountered failures. This enables users to effectively track the progress and status of their Earth Engine tasks.

- **Detailed Task Information**: Users have the ability to retrieve detailed information about a specific task by providing either the task state or a unique task ID. This information includes task descriptions, URIs, and the resources (EECUs) utilized by the task.

#### Usage

Using the Tasks tool is straightforward. You can either get an overview of all tasks or retrieve specific information about a particular task.

![geeadd_tasks](https://github.com/samapriya/gee_asset_manager_addon/assets/6677629/c211974d-de0b-4fde-b7d2-07e69143e0fb)

```
> geeadd tasks -h
usage: geeadd tasks [-h] [--state STATE] [--id ID]

options:
  -h, --help     show this help message and exit

Optional named arguments:
  --state STATE  Query by state type COMPLETED|PENDING|RUNNING|FAILED
  --id ID        Query by task id
```
