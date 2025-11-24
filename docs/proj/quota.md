## Mac Window Style for MkDocs Material

This guide shows how to create macOS-style terminal windows in your MkDocs Material documentation.

## 1. CSS Setup

Add the following CSS to your `extra.css` file:

```css
/* Container for the fake window */
.mac-window {
    background-color: #1e1e2e;
    /* Dark terminal background */
    border-radius: 8px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    margin: 1em 0;
    padding-top: 35px;
    /* Space for the "title bar" */
    position: relative;
    overflow: hidden;
}

/* The Red/Yellow/Green buttons */
.mac-window::before {
    content: "";
    position: absolute;
    top: 12px;
    left: 15px;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background-color: #ff5f56;
    /* Red dot */
    box-shadow:
        20px 0 0 #ffbd2e,
        /* Yellow dot (offset 20px) */
        40px 0 0 #27c93f;
    /* Green dot (offset 40px) */
    z-index: 2;
}

/* Optional: Add a title in the center of the bar */
.mac-window[data-title]::after {
    content: attr(data-title);
    position: absolute;
    top: 10px;
    left: 0;
    right: 0;
    text-align: center;
    color: #888;
    font-family: sans-serif;
    font-size: 12px;
    font-weight: bold;
}

/* Fix the inner code block styling to blend in */
.mac-window .md-typeset__scrollwrap,
.mac-window .highlight {
    margin: 0 !important;
    border-radius: 0 0 8px 8px !important;
    background: transparent !important;
}

.mac-window code {
    background-color: transparent !important;
    font-family: "JetBrains Mono", "Fira Code", monospace;
    /* Optional fancy font */
}
```

## 2. Configuration

Make sure your `mkdocs.yml` includes the extra CSS:

```yaml
extra_css:
  - stylesheets/extra.css
```

## 3. Usage in Markdown

Now, when writing your documentation, wrap your code blocks in a `div` with the class `mac-window`.

### Basic Example

<div class="mac-window" markdown="1">

```bash
# Cloud project
geeadd projects quota --project projects/my-project

# Legacy project
geeadd projects quota --project users/username
```

</div>

**Note:** The `markdown="1"` attribute is crucial - it tells MkDocs Material to process the markdown inside the div.

### Example with Title

You can also use the `data-title` attribute to show a title in the window bar:

<div class="mac-window" data-title="bash" markdown="1">

```bash
# Short project name (auto-detects type)
geeadd projects quota --project my-project
```

</div>

### Raw Markdown Code

When writing in your `.md` files, use this format:

```markdown
<div class="mac-window" markdown="1">

```bash
# Your code here
geeadd projects quota --project my-project
```

</div>
```

## Alternative: Using Plugins

If you prefer not to write CSS, there are plugins that offer similar aesthetics, though they might not look *exactly* like your screenshot out of the box:

1. **mkdocs-termynal**: Good for animated typing effects.
2. **mkdocs-terminal**: A full theme that makes the entire site look like a terminal.
