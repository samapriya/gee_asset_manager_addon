Setup Guide

To verify the setup, here is the command structure for the project quota tool.

<!--
We use the markdown=&quot;1&quot; attribute on the content div.
This tells MkDocs to parse the content inside the div as Markdown
(rendering the code block and copy button), rather than plain text.
-->

<div class="terminal-window">
<div class="terminal-header">
<div class="terminal-button red"></div>
<div class="terminal-button yellow"></div>
<div class="terminal-button green"></div>
</div>
<div class="terminal-content" markdown="1">

# Cloud project
geeadd projects quota --project projects/my-project

# Legacy project
geeadd projects quota --project users/username

# Short project name (auto-detects type)
geeadd projects quota --project my-project


</div>
</div>

Explanation

md_in_html: I added this extension to mkdocs.yml. Without it, Markdown inside HTML tags (like the code block inside .terminal-content) acts unpredictably or gets ignored.

markdown="1": You must add this attribute to the <div class="terminal-content">. It explicitly triggers the Markdown parser for the content inside that div.

CSS Tweaks: I updated the CSS selector for the copy button to .terminal-content .md-clipboard to ensure it targets the standard MkDocs Material copy icon correctly.
