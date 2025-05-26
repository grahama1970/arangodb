#!/usr/bin/env python3
"""
Generate a complete MCP configuration including all sub-commands
"""

import json
import sys
import inspect
from pathlib import Path
from typing import Dict, Any, List
import typer

# Import the main app
sys.path.insert(0, str(Path(__file__).parent))
from src.arangodb.cli.main import app


def get_all_commands(app: typer.Typer, prefix: str = "") -> Dict[str, Any]:
    """Recursively get all commands including sub-commands"""
    tools = {}
    
    # Skip these commands
    skip_commands = {
        "generate-claude", "generate-mcp-config", "serve-mcp",
        "quickstart", "llm-help", "health"  # These are already in the config
    }
    
    # Process direct commands
    for command in app.registered_commands:
        cmd_name = command.name or command.callback.__name__
        full_name = f"{prefix}{cmd_name}" if prefix else cmd_name
        
        if cmd_name in skip_commands:
            continue
            
        func = command.callback
        if func is None:
            continue
            
        docstring = func.__doc__ or f"Execute {cmd_name}"
        
        # Extract parameters
        sig = inspect.signature(func)
        parameters = {}
        required = []
        
        for param_name, param in sig.parameters.items():
            if param_name in ['self', 'ctx']:
                continue
                
            # Type mapping
            param_type = "string"
            if param.annotation != param.empty:
                if param.annotation == int:
                    param_type = "integer"
                elif param.annotation == bool:
                    param_type = "boolean"
                elif param.annotation == float:
                    param_type = "number"
                    
            parameters[param_name] = {
                "type": param_type,
                "description": f"Parameter: {param_name}"
            }
            
            if param.default == param.empty:
                required.append(param_name)
        
        tools[full_name] = {
            "description": docstring.strip().split('\n')[0],
            "inputSchema": {
                "type": "object",
                "properties": parameters,
                "required": required
            }
        }
    
    # Process sub-groups
    for group_info in app.registered_groups:
        name = group_info.name
        typer_instance = group_info.typer_instance
        if isinstance(typer_instance, typer.Typer):
            sub_prefix = f"{prefix}{name}." if prefix else f"{name}."
            sub_tools = get_all_commands(typer_instance, sub_prefix)
            tools.update(sub_tools)
    
    return tools


def generate_full_mcp_config():
    """Generate complete MCP configuration with all commands"""
    
    # Get all tools including sub-commands
    all_tools = get_all_commands(app)
    
    # Build the MCP configuration
    config = {
        "name": "arangodb",
        "version": "2.0.0",
        "description": "Complete ArangoDB Memory Bank MCP server with all commands",
        "server": {
            "command": sys.executable,
            "args": [
                str(Path(__file__).parent / "src" / "arangodb" / "cli" / "main.py"),
                "serve-mcp",
                "--host", "localhost",
                "--port", "5000"
            ]
        },
        "tools": all_tools,
        "capabilities": {
            "tools": True,
            "prompts": False,
            "resources": False
        }
    }
    
    # Write the configuration
    output_path = Path("mcp_config_complete.json")
    with open(output_path, "w") as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Generated complete MCP config: {output_path}")
    print(f"📋 Includes {len(all_tools)} tools")
    
    # List categories
    categories = {}
    for tool_name in all_tools:
        if "." in tool_name:
            category = tool_name.split(".")[0]
            categories[category] = categories.get(category, 0) + 1
    
    if categories:
        print("\n📊 Tool categories:")
        for category, count in sorted(categories.items()):
            print(f"  - {category}: {count} commands")


if __name__ == "__main__":
    generate_full_mcp_config()