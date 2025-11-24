# EE API Enabled Projects Tool

The Projects tool allows owners of cloud projects to identify which Google Cloud Projects have the Earth Engine API enabled. This is essential for managing your GEE resources across multiple projects.

## Overview

<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1.5rem; border-radius: 8px; color: white; margin: 1.5rem 0;">
  <h3 style="margin-top: 0; color: white;">Discover Your EE-Enabled Projects</h3>
  <p style="margin-bottom: 0;">Quickly identify all Google Cloud Projects where you can use Earth Engine, including project names and numbers.</p>
</div>

## Prerequisites

<div style="background: #fff3cd; border: 1px solid #ffc107; padding: 1rem; border-radius: 6px; margin: 1rem 0;">
<strong>⚠️ Requirements:</strong>
<ul style="margin-bottom: 0;">
<li><strong>gcloud CLI</strong> must be installed and authenticated</li>
<li>You must be an <strong>owner</strong> of the projects (to query permissions)</li>
<li>Earth Engine API must be enabled on the projects you want to discover</li>
</ul>
</div>

## Features

- **🔍 Automatic Detection**: Checks gcloud installation and authentication
- **📋 Project Details**: Lists project names and numbers
- **✅ Permission Verification**: Confirms Earth Engine API is enabled
- **🎯 Ready for Code Editor**: Projects listed can be added to GEE Code Editor

## Usage

### List All EE-Enabled Projects

<div style="background: var(--md-code-bg-color); padding: 1rem; border-radius: 6px; margin: 1rem 0; border-left: 4px solid #667eea;">
<pre><code class="language-bash">geeadd projects enabled
</code></pre>
</div>

## Sample Output

When you run the command, you'll see output similar to this:

```
gcloud is installed and authenticated

Checking Earth Engine permissions for all projects...

Project Name: my-earth-engine-project    Project Number: 77544
Project Name: satellite-imagery-analysis  Project Number: 433
Project Name: gis-processing-pipeline     Project Number: 107921
Project Name: environmental-monitoring    Project Number: 225
```

## Understanding the Output

### Project Name
The human-readable name of your Google Cloud Project. This is what you typically see in the GCP Console.

### Project Number
The unique numerical identifier for your project. This is useful for:
- API calls that require project numbers
- Setting project context in Python scripts
- Identifying projects programmatically

## Use Cases

### Setting Up Python Projects

Use the project information to configure your Earth Engine Python scripts:

<div style="background: var(--md-code-bg-color); padding: 1rem; border-radius: 6px; margin: 1rem 0; border-left: 4px solid #667eea;">
<pre><code class="language-python">import ee

# Use project name from the output
ee.Initialize(project='my-earth-engine-project')
</code></pre>
</div>

### Adding Projects to Code Editor

The listed projects are those you can add to your Earth Engine Code Editor:

1. Run `geeadd projects enabled` to get project names
2. Open [code.earthengine.google.com](https://code.earthengine.google.com)
3. Use the project names to switch between projects in the Code Editor

### Auditing Your Projects

Quickly identify which projects have Earth Engine access:

<div style="background: var(--md-code-bg-color); padding: 1rem; border-radius: 6px; margin: 1rem 0; border-left: 4px solid #667eea;">
<pre><code class="language-bash"># List projects, then check quota for each
geeadd projects enabled

# Check quota for specific project
geeadd projects quota --project my-earth-engine-project
</code></pre>
</div>

## What the Tool Checks

The tool performs the following checks:

1. **gcloud Installation**: Verifies gcloud CLI is installed
2. **Authentication**: Confirms you're logged in to gcloud
3. **Project Access**: Queries all projects you own
4. **EE API Status**: Checks if Earth Engine API is enabled on each project

## Prerequisites Setup

### Installing gcloud CLI

If gcloud is not installed:

<div style="background: var(--md-code-bg-color); padding: 1rem; border-radius: 6px; margin: 1rem 0; border-left: 4px solid #667eea;">
<pre><code class="language-bash"># macOS (using Homebrew)
brew install google-cloud-sdk

# Linux
curl https://sdk.cloud.google.com | bash

# Windows
# Download from: https://cloud.google.com/sdk/docs/install
</code></pre>
</div>

### Authenticating gcloud

<div style="background: var(--md-code-bg-color); padding: 1rem; border-radius: 6px; margin: 1rem 0; border-left: 4px solid #667eea;">
<pre><code class="language-bash"># Authenticate with your Google account
gcloud auth login

# Set default project (optional)
gcloud config set project my-earth-engine-project
</code></pre>
</div>

### Enabling Earth Engine API

To enable Earth Engine API on a project:

<div style="background: var(--md-code-bg-color); padding: 1rem; border-radius: 6px; margin: 1rem 0; border-left: 4px solid #667eea;">
<pre><code class="language-bash"># Using gcloud
gcloud services enable earthengine.googleapis.com --project=my-project

# Or visit the GCP Console
# https://console.cloud.google.com/apis/library/earthengine.googleapis.com
</code></pre>
</div>

## Troubleshooting

### "gcloud not found"

If you see this error:

1. Install gcloud CLI using the instructions above
2. Restart your terminal after installation
3. Verify installation: `gcloud --version`

### "Not authenticated"

If you're not authenticated:

<div style="background: var(--md-code-bg-color); padding: 1rem; border-radius: 6px; margin: 1rem 0; border-left: 4px solid #667eea;">
<pre><code class="language-bash">gcloud auth login
</code></pre>
</div>

### "No projects found"

If no projects are listed:

- You may not be an owner of any projects with EE API enabled
- Enable Earth Engine API on at least one project you own
- Check your project permissions in [GCP Console](https://console.cloud.google.com)

### Permission Errors

This tool requires **owner** permissions because it queries all project permissions. If you only have editor/viewer access, you won't see those projects listed.

## Tips and Best Practices

<div style="background: #d4edda; border: 1px solid #c3e6cb; padding: 1rem; border-radius: 6px; margin: 1rem 0;">
<strong>💡 Pro Tips:</strong>
<ul style="margin-bottom: 0;">
<li>Save the output to a file for reference: <code>geeadd projects enabled > my-projects.txt</code></li>
<li>Use project numbers for API calls requiring numerical IDs</li>
<li>Keep track of which projects are for production vs. development</li>
<li>Regularly audit your projects to ensure proper organization</li>
</ul>
</div>

## Integration with Other Tools

### With Quota Tool

<div style="background: var(--md-code-bg-color); padding: 1rem; border-radius: 6px; margin: 1rem 0; border-left: 4px solid #667eea;">
<pre><code class="language-bash"># List projects
geeadd projects enabled

# Check quota for each project
geeadd projects quota --project my-earth-engine-project
</code></pre>
</div>

### With Dashboard Tool

<div style="background: var(--md-code-bg-color); padding: 1rem; border-radius: 6px; margin: 1rem 0; border-left: 4px solid #667eea;">
<pre><code class="language-bash"># Generate dashboard for all projects
geeadd projects dashboard

# Output will include all EE-enabled projects
</code></pre>
</div>

## Related Commands

- [`geeadd projects quota`](quota.md) - Check quota for your projects
- [`geeadd projects dashboard`](dashboard.md) - Generate interactive dashboard
- [`geeadd assets info`](../assets/info.md) - Get details about specific assets

---

<div style="background: var(--md-code-bg-color); padding: 1rem; border-radius: 6px; margin: 2rem 0;">
<strong>Need Help?</strong><br>
For more information, run: <code>geeadd projects enabled --help</code>
</div>
