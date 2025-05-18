# Combined Screenshot & Analysis MCP Design

If you want to build a combined MCP tool for D3.js verification, here's a design template:

## Core Features

1. **Single Command**: `verify_visualization`
2. **Integrated Workflow**:
   - Navigate to URL
   - Wait for D3 elements
   - Take screenshot
   - Analyze with vision API
   - Return combined report

## Implementation Outline

```python
# Combined MCP Server Structure
class D3VerificationMCP:
    def __init__(self):
        self.browser = None
        self.vision_client = None
    
    async def verify_visualization(self, url: str, output_path: str):
        # 1. Take screenshot
        screenshot_path = await self.capture_screenshot(url, output_path)
        
        # 2. Analyze image
        analysis = await self.analyze_image(screenshot_path)
        
        # 3. Get DOM validation
        dom_stats = await self.validate_dom(url)
        
        # 4. Combine results
        return {
            "screenshot": screenshot_path,
            "visual_analysis": analysis,
            "dom_validation": dom_stats,
            "status": self.determine_status(analysis, dom_stats)
        }
```

## Configuration

```json
{
  "mcpServers": {
    "d3-verifier": {
      "command": "python",
      "args": ["-m", "d3_verifier.server"],
      "env": {
        "VISION_PROVIDER": "anthropic",
        "ANTHROPIC_API_KEY": "key",
        "HEADLESS": "true"
      }
    }
  }
}
```

## Advantages

1. **Single tool call**: `Verify D3 visualization at [URL]`
2. **Optimized workflow**: No manual coordination
3. **Consistent output format**
4. **Custom D3-specific checks**

## Development Steps

1. Fork an existing MCP screenshot tool
2. Add vision API integration
3. Create D3-specific validation logic
4. Package as single MCP server
5. Test with various D3 layouts

## Estimated Effort

- Initial development: 2-3 days
- Testing & refinement: 1-2 days
- Documentation: 1 day
- Total: ~1 week

## Maintenance Considerations

- API version updates
- Puppeteer/Playwright updates
- Vision API changes
- D3.js version compatibility
```

However, given the effort required, I still recommend starting with the two separate tools and only building a combined tool if the workflow becomes problematic in practice.