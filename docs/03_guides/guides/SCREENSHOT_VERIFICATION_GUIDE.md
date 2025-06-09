# Screenshot Verification Guide for D3.js Visualizations

This guide explains how to capture and verify screenshots of D3.js visualizations using the MCP Puppeteer server integration.

## Overview

When implementing visualization tasks (like Task 028), we need to verify that D3.js graphs render correctly. Since Claude Code cannot directly interpret images, we use the official MCP Puppeteer server to capture screenshots and validate rendering success.

## MCP Server Configuration

Add the following to your `.mcp.json` file:

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

Location options:
- Project-specific: `.cursor/mcp.json` or `.vscode/mcp.json`
- Global: `~/.cursor/mcp.json` or `~/.vscode/mcp.json`

## Required Tools

1. **MCP Puppeteer Server** - Configured via `.mcp.json`
2. **Claude Code** - With MCP integration enabled
3. **Chrome** - Automatically managed by Puppeteer

## Screenshot Verification Process

### 1. Basic Screenshot Capture

```javascript
const puppeteer = require('puppeteer');

async function captureD3Visualization(htmlPath, outputPath) {
    const browser = await puppeteer.launch();
    const page = await browser.newPage();
    
    // Set consistent viewport for reproducible screenshots
    await page.setViewport({ width: 1200, height: 800 });
    
    // Load the D3 visualization
    await page.goto(`file://${htmlPath}`, {
        waitUntil: 'networkidle2'
    });
    
    // Wait for the visualization to render
    await page.waitForSelector('svg', { visible: true });
    
    // Additional wait for D3 animations to complete
    await page.waitForTimeout(1000);
    
    // Capture screenshot
    await page.screenshot({ 
        path: outputPath,
        fullPage: true 
    });
    
    await browser.close();
    return outputPath;
}
```

### 2. Validation Before Screenshot

```javascript
async function validateAndCapture(htmlPath, outputPath) {
    const browser = await puppeteer.launch();
    const page = await browser.newPage();
    
    await page.setViewport({ width: 1200, height: 800 });
    await page.goto(`file://${htmlPath}`, {
        waitUntil: 'networkidle2'
    });
    
    // Validate D3 elements are present
    const validation = await page.evaluate(() => {
        const svg = document.querySelector('svg');
        const nodes = document.querySelectorAll('.nodes circle');
        const links = document.querySelectorAll('.links line');
        
        return {
            svgPresent: !!svg,
            svgDimensions: svg ? { 
                width: svg.getAttribute('width'), 
                height: svg.getAttribute('height') 
            } : null,
            nodeCount: nodes.length,
            linkCount: links.length,
            hasD3: typeof d3 !== 'undefined',
            animations: {
                // Check if force simulation is running
                forceActive: window.simulation ? 
                    window.simulation.alpha() > 0 : false
            }
        };
    });
    
    // Log validation results
    console.log('Validation Results:', validation);
    
    // Only capture if validation passes
    if (validation.svgPresent && validation.nodeCount > 0) {
        await page.screenshot({ 
            path: outputPath,
            fullPage: true 
        });
        console.log(`Screenshot saved to: ${outputPath}`);
    } else {
        throw new Error('Visualization validation failed');
    }
    
    await browser.close();
    return { outputPath, validation };
}
```

### 3. Layout-Specific Verification

For different D3 layouts, use specific validation:

```javascript
// Force-directed graph validation
async function validateForceGraph(page) {
    return await page.evaluate(() => {
        const simulation = window.simulation || d3.select('svg').datum();
        return {
            simulationActive: simulation && simulation.alpha() > 0,
            nodePositions: Array.from(document.querySelectorAll('.nodes circle'))
                .map(node => ({
                    cx: node.getAttribute('cx'),
                    cy: node.getAttribute('cy')
                })),
            linkPositions: Array.from(document.querySelectorAll('.links line'))
                .map(link => ({
                    x1: link.getAttribute('x1'),
                    y1: link.getAttribute('y1'),
                    x2: link.getAttribute('x2'),
                    y2: link.getAttribute('y2')
                }))
        };
    });
}

// Tree layout validation
async function validateTreeLayout(page) {
    return await page.evaluate(() => {
        return {
            nodeCount: document.querySelectorAll('.node').length,
            linkCount: document.querySelectorAll('.link').length,
            hasCollapsible: document.querySelectorAll('.node.collapsed').length > 0,
            treeDepth: Math.max(...Array.from(document.querySelectorAll('.node'))
                .map(node => node.getAttribute('transform'))
                .map(transform => {
                    const match = transform.match(/translate\((\d+),/);
                    return match ? parseInt(match[1]) : 0;
                }))
        };
    });
}
```

## Integration with Task Verification

### Report Template Addition

Add this section to each visualization task report:

```markdown
## Screenshot Verification

### Test 1: [Layout Name] Rendering
- **HTML File**: `test_output/[layout]_test.html`
- **Screenshot**: `test_output/[layout]_screenshot.png`
- **Validation Results**:
  ```json
  {
    "svgPresent": true,
    "svgDimensions": { "width": "960", "height": "600" },
    "nodeCount": 50,
    "linkCount": 75,
    "renderTime": "1.2s"
  }
  ```
- **Visual Verification Required**: Manual inspection of screenshot needed
- **Status**: PASS ✓

### Browser Compatibility
- Chrome (headless): ✓ Tested
- Chrome (standard): ⚠️ Requires manual verification
- Firefox: ⚠️ Not tested
- Safari: ⚠️ Not tested
```

## Task Implementation Checklist

For any task involving D3.js visualizations, include:

- [ ] Create test HTML file with sample data
- [ ] Implement screenshot capture script
- [ ] Add DOM validation before screenshot
- [ ] Capture screenshot with consistent viewport
- [ ] Save validation results to report
- [ ] Include screenshot path in report
- [ ] Note that manual visual verification is required
- [ ] Add browser compatibility notes

## Example CLI Command

```bash
# Create a CLI command for screenshot verification
arangodb viz verify --input test.html --output screenshot.png --validate
```

## Common Issues and Solutions

### Issue 1: Timing Problems
**Problem**: Screenshot captures before D3 animation completes
**Solution**: Use custom wait conditions or completion signals

```javascript
// Add to your D3 code
simulation.on("end", () => {
    window.d3SimulationComplete = true;
});

// In Puppeteer
await page.waitForFunction('window.d3SimulationComplete === true');
```

### Issue 2: Missing Elements
**Problem**: SVG elements not found
**Solution**: Verify selectors and wait for proper page load

```javascript
await page.waitForSelector('svg#visualization', { 
    visible: true,
    timeout: 30000 
});
```

### Issue 3: Viewport Issues
**Problem**: Graph cut off or too small
**Solution**: Set appropriate viewport and use full page capture

```javascript
await page.setViewport({ width: 1920, height: 1080 });
await page.screenshot({ fullPage: true });
```

## Report Requirements

Each visualization task MUST include:

1. Screenshot file path
2. Validation results (JSON format)
3. Browser/environment tested
4. Any rendering issues found
5. Note about manual verification requirement

## Summary

Since Claude Code cannot directly interpret images, we use:
1. Automated DOM validation to verify element presence
2. Screenshot capture for human verification
3. Detailed reporting of validation results
4. Clear documentation of what requires manual checking

This approach ensures that D3.js visualizations are properly tested and documented, even without direct image interpretation capabilities.