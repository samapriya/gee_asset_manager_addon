# Google Earth Engine Batch Asset Manager with Addons

[![Documentation](https://img.shields.io/badge/docs-geeadd.geetools.xyz-blue?style=for-the-badge&logo=read-the-docs)](https://samapriya.github.io/gee_asset_manager_addon/)
[![PyPI](https://img.shields.io/pypi/v/geeadd?style=for-the-badge&logo=pypi)](https://pypi.org/project/geeadd/)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg?style=for-the-badge)](https://opensource.org/licenses/Apache-2.0)
[![CI geeadd](https://img.shields.io/github/actions/workflow/status/samapriya/gee_asset_manager_addon/python-package.yml?style=for-the-badge&logo=github&label=CI%20geeadd)](https://github.com/samapriya/gee_asset_manager_addon/actions/workflows/python-package.yml)

**Powerful CLI tools for batch asset management in Google Earth Engine**

[Documentation](https://samapriya.github.io/gee_asset_manager_addon/) • [Installation](#installation) • [Quick Start](#quick-start) • [Features](#features)

---

## Overview

**geeadd** (Google Earth Engine Asset Manager with Addons) is a comprehensive command-line tool that extends the official Earth Engine CLI with powerful batch operations and asset management capabilities. Whether you're managing quotas, organizing assets, or performing bulk operations, geeadd streamlines your Earth Engine workflows.

![geeadd_main](https://i.imgur.com/SERUqBL.gif)

## Features

- **Project Management**: Monitor quotas, track enabled projects, generate interactive dashboards
- **Asset Operations**: Batch copy, move, delete, and manage permissions recursively
- **Task Management**: List, monitor, and cancel Earth Engine tasks efficiently
- **Utilities**: Search catalogs, extract app scripts, generate reports, create color palettes
- **Modern CLI**: Organized command groups with intuitive syntax
- **Performance**: Multi-threaded operations for handling large asset collections

## Installation

### Requirements
- Python 3.10+
- Earth Engine Python API (authenticated)

### Install via pip
```bash
pip install geeadd
```

### Install from source
```bash
git clone https://github.com/samapriya/gee_asset_manager_addon.git
cd gee_asset_manager_addon
pip install .
```

### Verify installation
```bash
geeadd --version
```

## 🎯 Quick Start

### Authenticate with Earth Engine
```bash
earthengine authenticate
```

### Check your quota
```bash
geeadd projects quota
```

### List your enabled projects
```bash
geeadd projects enabled
```

### Copy assets recursively
```bash
geeadd assets copy --initial "users/me/folder" --final "users/me/backup"
```

### Monitor tasks
```bash
geeadd tasks list
```

## 📚 Command Structure

Version 2.0.0 introduces organized command groups for better discoverability:

```
geeadd
├── projects     # Project and quota management
│   ├── quota
│   ├── enabled
│   └── dashboard
├── assets       # Asset operations
│   ├── info
│   ├── copy
│   ├── move
│   ├── delete
│   ├── delete-meta
│   ├── access
│   └── size
├── tasks        # Task management
│   ├── list
│   └── cancel
└── utils        # Utility commands
    ├── search
    ├── app2script
    ├── report
    └── palette
```

## 🔄 Migration from v1.x

If you're upgrading from version 1.2.1 or earlier, commands have been reorganized into logical groups. See the [migration guide](https://samapriya.github.io/gee_asset_manager_addon/#migration) for details.

**Example changes:**
- `geeadd quota` → `geeadd projects quota`
- `geeadd copy` → `geeadd assets copy`
- `geeadd tasks` → `geeadd tasks list`

## 📖 Documentation

Comprehensive documentation is available at **[geeadd.geetools.xyz](https://samapriya.github.io/gee_asset_manager_addon/)**

The documentation includes:
- Detailed command references
- Real-world workflow examples
- Best practices and troubleshooting
- Interactive examples

## Common Use Cases

### Monitor project storage

```bash
# Generate an interactive dashboard
geeadd projects dashboard --outdir ./dashboard.html

# Check specific project quota
geeadd projects quota --project "projects/my-project"
```

### Batch asset management

```bash
# Copy entire folder structure
geeadd assets copy --initial "users/me/production" --final "users/me/archive"

# Share assets with collaborators
geeadd assets access --asset "users/me/shared" --user "colleague@email.com" --role reader

# Calculate collection size
geeadd assets size "users/me/collection"
```

### Task monitoring

```bash
# View task summary
geeadd tasks list

# Monitor running tasks
geeadd tasks list --state RUNNING

# Cancel stuck tasks
geeadd tasks cancel pending
```

### Utilities

```bash
# Search Earth Engine catalog
geeadd utils search --keywords "Sentinel-2"

# Extract script from Earth Engine App
geeadd utils app2script --url "https://username.users.earthengine.app/view/myapp"

# Generate color palette
geeadd utils palette --name Blues --classes 5 --copy
```

## Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

## Full Documentation

For complete documentation, examples, and guides, visit:

### **[geeadd.geetools.xyz](https://samapriya.github.io/gee_asset_manager_addon/)**

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Support

If you find this tool useful, consider:

- Starring the project on [GitHub](https://github.com/samapriya/gee_asset_manager_addon)
- Sharing your feedback and use cases
- [Sponsoring on GitHub](https://github.com/sponsors/samapriya)


---

<div align="center">
Made with ❤️ by <a href="https://github.com/samapriya">Samapriya Roy</a>
</div>
