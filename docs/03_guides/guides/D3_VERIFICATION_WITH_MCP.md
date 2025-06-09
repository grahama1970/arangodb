# D3.js Verification with MCP Servers

This guide explains how to use MCP servers to capture and analyze D3.js visualizations - combining Puppeteer for screenshots and image recognition for analysis.

## Overview

Since Claude Code cannot directly interpret images, we use a two-step approach:
1. **Puppeteer MCP**: Captures screenshots of D3.js visualizations
2. **Image Recognition MCP**: Analyzes the screenshots and provides descriptions

## MCP Server Configuration

Add both servers to your `.mcp.json` file:

```json
{
  "mcpServers": {
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
      "env": {
        "launchOptions": "{ \"headless\": true }"
      }
    },
    "image-recognition": {
      "command": "uvx",
      "args": ["mcp-image-recognition"],
      "env": {
        "VISION_PROVIDER": "anthropic",
        "ANTHROPIC_API_KEY": "your-anthropic-api-key",
        "FALLBACK_PROVIDER": "openai",
        "OPENAI_API_KEY": "your-openai-api-key",
        "OPENAI_MODEL": "gpt-4o"
      }
    }
  }
}
```

## Setup Steps

1. **Install dependencies**:
   - Puppeteer MCP will auto-install via npx
   - Image Recognition requires API keys for Anthropic or OpenAI

2. **Configure API Keys**:
   - Get Anthropic API key from https://console.anthropic.com/
   - Get OpenAI API key from https://platform.openai.com/
   - Add to environment or `.mcp.json`

3. **Restart Claude Code** to load the MCP servers

## Verification Workflow

### Step 1: Generate Test HTML
```
Create a test HTML file at test_output/force_test.html with D3 force-directed graph visualization
```

### Step 2: Capture Screenshot
```
Use Puppeteer to navigate to file:///absolute/path/test_output/force_test.html and take a screenshot, save as test_output/force_screenshot.png
```

### Step 3: Analyze Screenshot
```
Use image recognition to analyze test_output/force_screenshot.png and describe what visualization elements are visible
```

### Step 4: DOM Validation (via Puppeteer)
```
Use Puppeteer to navigate to file:///absolute/path/test_output/force_test.html and execute JavaScript to count nodes and links
```

## Example Task Verification

For a force-directed graph task:

1. **Take Screenshot**:
   ```
   Use Puppeteer to navigate to file:///home/user/project/test_output/force_test.html, wait for SVG to load, then take a screenshot as force_screenshot.png
   ```

2. **Analyze Image**:
   ```
   Use image recognition to analyze force_screenshot.png and identify:
   - Is there a visible graph with nodes and edges?
   - Are nodes properly distributed in space?
   - Are edges/links connecting nodes?
   - Any visual anomalies or rendering issues?
   ```

3. **Validate Structure**:
   ```
   Use Puppeteer to execute JavaScript on the page:
   return {
     nodeCount: document.querySelectorAll('.node').length,
     linkCount: document.querySelectorAll('.link').length,
     svgPresent: !!document.querySelector('svg'),
     d3Version: window.d3 ? d3.version : 'not loaded'
   }
   ```

## Report Template

Add this to your task verification report:

```markdown
## D3.js Visualization Verification

### Force-Directed Graph Test
- **Test File**: `test_output/force_test.html`
- **Screenshot**: `test_output/force_screenshot.png`

#### Screenshot Analysis (via Image Recognition MCP):
```
The image shows a force-directed graph visualization with:
- Approximately 50 blue circular nodes distributed across the canvas
- Multiple gray lines connecting nodes as edges
- Nodes appear to be properly spaced with force simulation
- SVG rendering is clean with no visual artifacts
- Graph has achieved stable layout with good node distribution
```

#### DOM Validation (via Puppeteer MCP):
```json
{
  "nodeCount": 50,
  "linkCount": 75,
  "svgPresent": true,
  "d3Version": "7.8.5"
}
```

#### Status: ✅ PASS
- Visual rendering confirmed via image analysis
- DOM structure validated
- D3.js loaded successfully
```

## Common Commands

### For Puppeteer MCP:
- `Navigate to [URL] and take a screenshot`
- `Take a full page screenshot of [URL] and save as [filename]`
- `Navigate to [URL] and execute JavaScript: [code]`
- `Wait for element [selector] at [URL] then take screenshot`

### For Image Recognition MCP:
- `Analyze image [filename] and describe what you see`
- `Check [filename] for any visual rendering issues`
- `Describe the graph structure visible in [filename]`
- `Identify the visualization type in [filename]`

## Best Practices

1. **Always use absolute paths** with file:// protocol for local files
2. **Wait for elements** before taking screenshots
3. **Capture multiple angles** if needed (full page, specific elements)
4. **Document both visual and DOM validation** results
5. **Save screenshots with descriptive names** including timestamp
6. **Use both MCPs together** for complete verification

## Alternative Configuration

If you prefer OpenAI as primary vision provider:

```json
{
  "mcpServers": {
    "image-recognition": {
      "command": "uvx",
      "args": ["mcp-image-recognition"],
      "env": {
        "VISION_PROVIDER": "openai",
        "OPENAI_API_KEY": "your-openai-api-key",
        "OPENAI_MODEL": "gpt-4o-mini",
        "FALLBACK_PROVIDER": "anthropic",
        "ANTHROPIC_API_KEY": "your-anthropic-api-key"
      }
    }
  }
}
```

## Troubleshooting

### Issue: API Key errors
**Solution**: Ensure API keys are correctly set in `.mcp.json` or environment

### Issue: Screenshot timing
**Solution**: Add wait conditions before capture
```
Navigate to [URL], wait for selector "svg" to be visible, wait 2 seconds for animation, then take screenshot
```

### Issue: Image recognition fails
**Solution**: Check file path and format (JPEG, PNG, GIF, WebP supported)

### Issue: MCP not loading
**Solution**: Restart Claude Code after updating `.mcp.json`

## Security Note

- Puppeteer MCP can access local files and network resources
- API keys should be kept secure
- Only analyze trusted images and content

## Summary

By combining:
1. **Puppeteer MCP** for screenshot capture
2. **Image Recognition MCP** for visual analysis

We can fully verify D3.js visualizations even though Claude Code cannot directly interpret images. This provides both structural validation (DOM) and visual verification (AI analysis).