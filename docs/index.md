# Google Earth Engine Batch Asset Manager with Addons

<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 8px; color: white; margin: 2rem 0;">
  <h2 style="margin-top: 0; color: white;">geeadd - Modern CLI for Google Earth Engine</h2>
  <p style="font-size: 1.1rem; margin-bottom: 0;">A powerful command-line tool for managing Google Earth Engine assets, tasks, and projects with an intuitive grouped interface.</p>
</div>

## Overview

**geeadd** is a comprehensive command-line interface (CLI) tool designed to simplify and enhance your Google Earth Engine workflow. It provides organized command groups for managing projects, assets, tasks, and utilities.

## Key Features

### 🗂️ **Projects Management**
- View Earth Engine quota across all projects
- List GCP projects with EE API enabled
- Generate interactive project dashboards

### 📦 **Assets Management**
- Copy, move, and delete assets efficiently
- Manage access permissions
- Get detailed asset information
- Calculate asset sizes

### ⚙️ **Tasks Management**
- List and filter running tasks
- Cancel tasks individually or in bulk
- Monitor task status and performance

### 🛠️ **Utilities**
- Extract scripts from public EE apps
- Search the GEE catalog with relevance ranking
- Generate comprehensive asset reports
- Create ColorBrewer palettes for visualization

## Command Structure

geeadd organizes commands into logical groups:

<div style="background: var(--md-code-bg-color); padding: 1.5rem; border-radius: 6px; border-left: 4px solid #667eea; margin: 1rem 0;">
<pre><code>geeadd
├── readme          # Open documentation
├── projects        # Project management
│   ├── enabled     # List EE-enabled projects
│   ├── dashboard   # Generate project dashboard
│   └── quota       # View quota information
├── assets          # Asset management
│   ├── info        # Display asset details
│   ├── copy        # Copy assets
│   ├── move        # Move assets
│   ├── access      # Manage permissions
│   ├── delete      # Delete assets
│   ├── delete-meta # Remove metadata
│   └── size        # Calculate asset size
├── tasks           # Task management
│   ├── list        # List tasks
│   └── cancel      # Cancel tasks
└── utils           # Utility commands
    ├── app2script  # Extract app scripts
    ├── search      # Search GEE catalog
    ├── report      # Generate asset reports
    └── palette     # ColorBrewer palettes
</code></pre>
</div>

## Quick Start

### Installation

<div style="background: var(--md-code-bg-color); padding: 1rem; border-radius: 6px; margin: 1rem 0;">
<pre><code class="language-bash">pip install geeadd
</code></pre>
</div>

### Basic Usage

View all available commands:

<div style="background: var(--md-code-bg-color); padding: 1rem; border-radius: 6px; margin: 1rem 0;">
<pre><code class="language-bash">geeadd --help
</code></pre>
</div>

Get help for a specific group:

<div style="background: var(--md-code-bg-color); padding: 1rem; border-radius: 6px; margin: 1rem 0;">
<pre><code class="language-bash">geeadd projects --help
geeadd assets --help
geeadd tasks --help
geeadd utils --help
</code></pre>
</div>

## Common Workflows

### Check Your Quota

<div style="background: var(--md-code-bg-color); padding: 1rem; border-radius: 6px; margin: 1rem 0;">
<pre><code class="language-bash"># View quota for all projects
geeadd projects quota

# View quota for specific project
geeadd projects quota --project my-project
</code></pre>
</div>

### Manage Assets

<div style="background: var(--md-code-bg-color); padding: 1rem; border-radius: 6px; margin: 1rem 0;">
<pre><code class="language-bash"># Get asset information
geeadd assets info projects/my-project/assets/my-collection

# Copy assets
geeadd assets copy --initial projects/my-project/assets/old --final projects/my-project/assets/new

# Check asset size
geeadd assets size projects/my-project/assets/my-collection
</code></pre>
</div>

### Monitor Tasks

<div style="background: var(--md-code-bg-color); padding: 1rem; border-radius: 6px; margin: 1rem 0;">
<pre><code class="language-bash"># List all tasks summary
geeadd tasks list

# List only running tasks
geeadd tasks list --state RUNNING

# Cancel all pending tasks
geeadd tasks cancel pending
</code></pre>
</div>

## Migration from Old Commands

If you've used geeadd before, some commands have been reorganized:

| Old Command | New Command |
|-------------|-------------|
| `geeadd quota` | `geeadd projects quota` |
| `geeadd projects` | `geeadd projects enabled` |
| `geeadd cancel` | `geeadd tasks cancel` |
| `geeadd copy` | `geeadd assets copy` |
| `geeadd move` | `geeadd assets move` |
| `geeadd access` | `geeadd assets access` |
| `geeadd delete` | `geeadd assets delete` |
| `geeadd app2script` | `geeadd utils app2script` |
| `geeadd search` | `geeadd utils search` |
| `geeadd ee_report` | `geeadd utils report` |

<div style="background: #fff3cd; border: 1px solid #ffc107; padding: 1rem; border-radius: 6px; margin: 1rem 0;">
<strong>⚠️ Note:</strong> Old commands still work but show deprecation warnings. Update to new commands for the best experience.
</div>

## Why Grouped Commands?

The new grouped structure provides several benefits:

- **Better Organization**: Related commands are grouped together
- **Easier Discovery**: Find commands by category
- **Clearer Purpose**: Command names are more descriptive
- **Scalability**: Easy to add new commands within existing groups

## Getting Help

- **Documentation**: Visit [https://geeadd.geetools.xyz/](https://geeadd.geetools.xyz/)
- **GitHub**: [github.com/samapriya/gee_asset_manager_addon](https://github.com/samapriya/gee_asset_manager_addon)
- **Issues**: Report bugs or request features on GitHub

## Next Steps

Explore the documentation sections:

- [**Prerequisites and Installation**](installation.md) - Get started with geeadd
- [**Projects Management**](projects/quota.md) - Manage your GEE projects
- [**Assets Management**](assets/info.md) - Work with your assets
- [**Tasks Management**](tasks/list.md) - Monitor and control tasks
- [**Utilities**](utils/app2script.md) - Helpful utility commands

---

<div style="text-align: center; padding: 2rem 0; color: var(--md-default-fg-color--light);">
  <p>Made with ❤️ by Samapriya Roy</p>
</div>
