# Task status

This script counts all currently running, cancelled, pending and failed tasks and requires no arguments. You can now pass task state or even a task id to get specific info about a task such as description, uris, eecus used and so on.

![geeadd_tasks](https://user-images.githubusercontent.com/6677629/80340101-07dcb780-882e-11ea-9727-6f614012f4b1.gif)

```
> geeadd tasks -h
usage: geeadd tasks [-h] [--state STATE] [--id ID]

options:
  -h, --help     show this help message and exit

Optional named arguments:
  --state STATE  Query by state type COMPLETED|PENDING|RUNNING|FAILED
  --id ID        Query by task id
```
