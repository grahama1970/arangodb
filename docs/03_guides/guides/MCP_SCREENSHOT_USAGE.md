# MCP Screenshot Usage for D3.js Verification

This guide explains how to use the MCP Puppeteer server to capture and verify D3.js visualizations in Claude Code.

## Quick Setup

1. Add to your `.mcp.json`:
```json
{
  "mcpServers": {
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
      "env": {
        "launchOptions": "{ \"headless\": true }"
      }
    }
  }
}
```

2. Restart Claude Code to load the MCP server

## Usage Examples

### Taking a Screenshot
```
Take a screenshot of file://[absolute-path]/test.html and save it as test_screenshot.png
```

### Verifying Elements
```
Navigate to file://[absolute-path]/test.html and check if an SVG element with class "d3-visualization" exists
```

### Executing JavaScript Validation
```
Navigate to file://[absolute-path]/test.html and execute JavaScript to check if window.d3 is defined and return the version
```

## Task Integration

For each D3.js visualization task, include these steps:

1. **Generate test HTML**:
   ```
   Create test_output/force_test.html with the D3 force layout visualization
   ```

2. **Capture screenshot**:
   ```
   Take a screenshot of file://[path]/test_output/force_test.html and save as test_output/force_screenshot.png
   ```

3. **Validate DOM**:
   ```
   Navigate to file://[path]/test_output/force_test.html and verify:
   - SVG element exists
   - At least 10 nodes with class "node" exist
   - At least 15 links with class "link" exist
   ```

4. **Check D3 loading**:
   ```
   Execute JavaScript: return { d3Version: d3.version, nodesCount: d3.selectAll('.node').size() }
   ```

## Report Documentation

Add to your task report:

```markdown
## Screenshot Verification

### Force Layout Test
- **Test File**: `test_output/force_test.html`
- **Screenshot**: `test_output/force_screenshot.png`
- **MCP Validation**:
  ```
  Puppeteer navigation successful
  SVG element found: ✓
  Node count: 50
  Link count: 75
  D3 version: 7.8.5
  ```
- **Manual Verification Required**: Check screenshot for proper layout
```

## Common Commands

1. **Full page screenshot**:
   ```
   Take a full page screenshot of [URL] and save as [filename]
   ```

2. **Element screenshot**:
   ```
   Take a screenshot of the element with selector "[selector]" at [URL]
   ```

3. **Wait for element**:
   ```
   Navigate to [URL] and wait for element "[selector]" to be visible, then take a screenshot
   ```

4. **Check viewport**:
   ```
   Set viewport to 1200x800, navigate to [URL], and take a screenshot
   ```

## Troubleshooting

### Issue: Screenshot timing
**Solution**: Wait for specific elements or animations
```
Navigate to [URL], wait for 2 seconds, then take a screenshot
```

### Issue: File paths
**Solution**: Always use absolute file:// paths
```
file:///home/user/project/test_output/test.html
```

### Issue: Element not found
**Solution**: Check selectors and wait for load
```
Navigate to [URL], wait for selector "svg.visualization" to appear, then take a screenshot
```

## Best Practices

1. Always use absolute file paths with file:// protocol
2. Wait for specific elements rather than arbitrary timeouts
3. Capture both full page and specific element screenshots
4. Document viewport size if it matters
5. Save screenshots with descriptive names
6. Include timestamp if running multiple times

## Security Note

The Puppeteer MCP server can access local files and network resources. Only use it with trusted content and paths.