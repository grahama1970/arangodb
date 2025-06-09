"""
ArangoDB Agent Commands Module
Module: agent_commands.py
Description: Functions for agent commands operations

Provides CLI commands for inter-module communication between ArangoDB and Marker.
This module implements the communication mechanism described in docs/correspondence/module_communication.md.

Links:
- Communication Protocol: docs/correspondence/module_communication.md
- ArangoDB: https://www.arangodb.com/docs/stable/

Sample Input/Output:
- Input: Message requests from Marker
- Output: Processed responses and actions in ArangoDB
"""

import os
import sys
import json
import time
import typer
import shutil
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List, Any

from loguru import logger

# Set up application
app = typer.Typer(
    name="agent",
    help="Inter-module communication commands",
    add_completion=False
)

# Constants
MARKER_PATH = "/home/graham/workspace/experiments/marker"
MARKER_MESSAGES_DIR = os.path.join(MARKER_PATH, "messages")
ARANGODB_MESSAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "messages")

# Ensure message directories exist
os.makedirs(os.path.join(MARKER_MESSAGES_DIR, "from_arangodb"), exist_ok=True)
os.makedirs(os.path.join(MARKER_MESSAGES_DIR, "to_arangodb"), exist_ok=True)
os.makedirs(os.path.join(ARANGODB_MESSAGES_DIR, "from_marker"), exist_ok=True)
os.makedirs(os.path.join(ARANGODB_MESSAGES_DIR, "to_marker"), exist_ok=True)


@app.command("process-message")
def process_message(
    message_file: Path = typer.Argument(..., help="Path to message file from Marker")
):
    """
    Process a message from Marker module.
    
    This command reads a message from Marker, analyzes it using Claude Code,
    and takes appropriate actions in ArangoDB.
    """
    # Check if message file exists
    if not message_file.exists():
        typer.echo(f"Error: Message file not found: {message_file}")
        raise typer.Exit(code=1)
    
    typer.echo(f"Processing message from file: {message_file}")
    
    # Read message
    try:
        with open(message_file, 'r') as f:
            message = json.load(f)
    except json.JSONDecodeError:
        typer.echo("Error: Invalid JSON in message file")
        raise typer.Exit(code=1)
    
    # Validate message format
    if not all(field in message for field in ["source", "target", "type", "content"]):
        typer.echo("Error: Invalid message format. Required fields: source, target, type, content")
        raise typer.Exit(code=1)
    
    # Check message source
    if message["source"] != "marker":
        typer.echo(f"Error: Invalid message source: {message['source']}. Expected: marker")
        raise typer.Exit(code=1)
    
    # Create Claude Code processor script
    processor_script = create_processor_script(message)
    
    # Execute Claude Code processor
    try:
        execute_processor_script(processor_script, message)
    except Exception as e:
        typer.echo(f"Error executing processor script: {e}")
        raise typer.Exit(code=1)
    
    typer.echo("Message processed successfully")


@app.command("send-message")
def send_message(
    content: str = typer.Argument(..., help="Message content"),
    message_type: str = typer.Option("request", help="Message type (request/response/notification)")
):
    """
    Send a message to Marker module.
    
    This command creates a message file for Marker and triggers
    the Marker module to process it.
    """
    # Validate message type
    valid_types = ["request", "response", "notification"]
    if message_type not in valid_types:
        typer.echo(f"Error: Invalid message type: {message_type}. Valid types: {', '.join(valid_types)}")
        raise typer.Exit(code=1)
    
    # Create message
    message = {
        "source": "arangodb",
        "target": "marker",
        "type": message_type,
        "content": content,
        "timestamp": datetime.now().isoformat(),
        "metadata": {
            "version": "1.0"
        }
    }
    
    # Save message to Marker's incoming directory
    message_file = os.path.join(MARKER_MESSAGES_DIR, "from_arangodb", f"message_{int(time.time())}.json")
    try:
        with open(message_file, 'w') as f:
            json.dump(message, f, indent=2)
    except Exception as e:
        typer.echo(f"Error saving message file: {e}")
        raise typer.Exit(code=1)
    
    typer.echo(f"Message saved to: {message_file}")
    
    # Attempt to trigger Marker's process-message command
    try:
        # Check if Marker has the agent_commands.py file
        marker_agent_path = os.path.join(MARKER_PATH, "marker", "cli", "agent_commands.py")
        if os.path.exists(marker_agent_path):
            # Create temporary script to trigger Marker's process-message command
            marker_script = create_marker_trigger_script(message_file)
            
            # Execute script to trigger Marker's process-message
            result = subprocess.run(
                ["python", marker_script],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                typer.echo("Successfully notified Marker of message")
            else:
                typer.echo(f"Warning: Failed to trigger Marker's processing: {result.stderr}")
        else:
            # Marker agent_commands.py doesn't exist yet
            typer.echo(f"Note: Marker processing not triggered - {marker_agent_path} doesn't exist")
            typer.echo("If you need to implement it in Marker, use the claude_code_for_marker command")
    except Exception as e:
        typer.echo(f"Warning: Failed to trigger Marker processing: {e}")
    
    typer.echo("Message sent successfully")


@app.command("claude_code_for_marker")
def claude_code_for_marker():
    """
    Generate and execute Claude Code to create agent_commands.py in Marker.
    
    This command creates a script for Claude Code to implement the
    communication mechanism in the Marker module.
    """
    typer.echo("Creating and executing Claude Code to implement agent_commands.py in Marker...")
    
    # Create a script for Claude Code
    marker_implementation_script = create_marker_implementation_script()
    
    # Execute Claude Code to implement in Marker
    try:
        result = subprocess.run(
            ["claude-code", marker_implementation_script],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            typer.echo("Successfully created agent_commands.py in Marker")
        else:
            typer.echo(f"Error: Claude Code execution failed: {result.stderr}")
            raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Error executing Claude Code: {e}")
        raise typer.Exit(code=1)
    
    typer.echo("Marker implementation complete")


def create_processor_script(message: Dict) -> str:
    """Create a temporary script for Claude Code to process the message."""
    # Create temporary script file
    fd, script_path = tempfile.mkstemp(suffix='.py', prefix='arangodb_processor_')
    os.close(fd)
    
    # Escape any quotes in the message for embedding in the script
    message_str = json.dumps(message)
    
    # Create processor script content
    script_content = f"""
# ArangoDB processor script
import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Set working directory to ArangoDB module
os.chdir("{os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))}")

# Load message
message = {message_str}

print(f"Processing message: {{message.get('content', '')}}")

# Message format example:
# {{"source": "marker", "target": "arangodb", "type": "request", "content": "text content"}}

# Process based on message type
message_type = message.get("type")
content = message.get("content", "")

# Create response template
response = {{
    "source": "arangodb",
    "target": "marker",
    "type": "response",
    "content": "",
    "timestamp": datetime.now().isoformat(),
    "metadata": {{
        "request_timestamp": message.get("timestamp"),
        "changes_made": False,
        "files_modified": []
    }}
}}

# Process message based on content
if "format" in content.lower():
    # This is a request to change output format
    print("Processing format change request...")
    
    # Example processing for format changes
    try:
        # Example: Check if 'question_type' → 'type' change is requested
        if "question_type" in content.lower() and "type" in content.lower():
            # Find files that might need changing
            exporter_path = "src/arangodb/qa_generation/exporter.py"
            
            # Read the file
            if os.path.exists(exporter_path):
                with open(exporter_path, 'r') as f:
                    exporter_content = f.read()
                
                # Make changes (simplified example)
                if "question_type" in exporter_content:
                    new_content = exporter_content.replace("question_type", "type")
                    
                    # Write changes
                    with open(exporter_path, 'w') as f:
                        f.write(new_content)
                    
                    response["content"] = "Updated QA export format: changed 'question_type' to 'type'"
                    response["metadata"]["changes_made"] = True
                    response["metadata"]["files_modified"] = [exporter_path]
                else:
                    response["content"] = "Exporter doesn't use 'question_type' field"
            else:
                response["content"] = f"Exporter file not found: {{exporter_path}}"
        else:
            response["content"] = "Format change requested, but specifics unclear"
    except Exception as e:
        response["content"] = f"Error processing format change: {{str(e)}}"
        response["metadata"]["error"] = str(e)

elif "api" in content.lower() or "endpoint" in content.lower():
    # API-related request
    print("Processing API change request...")
    
    # Example processing for API changes
    response["content"] = "API update request noted, but we need specifics to implement"
    
elif "qa" in content.lower() or "generation" in content.lower():
    # QA generation-related request
    print("Processing QA generation request...")
    
    response["content"] = "QA generation changes requested. Please provide specific implementation details."

elif "pdf" in content.lower() or "export" in content.lower():
    # PDF export information request
    print("Processing PDF export information request...")
    
    # Gather information about PDF export
    pdf_export_info = {{
        "export_format": "JSON",
        "structure": {{
            "document": {{
                "id": "string",
                "title": "string",
                "metadata": "object",
                "pages": [
                    {{
                        "page_num": "integer",
                        "blocks": [
                            {{
                                "block_id": "string",
                                "type": "string (text, table, image, section_header, etc.)",
                                "text": "string (content)",
                                "position": "object (coordinates)"
                            }}
                        ]
                    }}
                ]
            }},
            "raw_corpus": {{
                "full_text": "string (entire document text)",
                "pages": ["array of page texts"]
            }}
        }},
        "processing": [
            "Document parsing with Marker",
            "Structural analysis and section identification",
            "Content extraction (text, tables, images)",
            "ArangoDB rendering for graph storage",
            "Relationship creation between elements",
            "Q&A pair generation from content"
        ],
        "integration_path": "scripts/marker_integration.py",
        "arangodb_collections": [
            "document_objects - stores document elements",
            "documents - stores document metadata",
            "content_relationships - stores relationships between elements"
        ]
    }}
    
    response["content"] = "PDF export information: Marker extracts structured content from PDFs and creates a hierarchical document representation with sections, blocks, and relationships. The MarkerConnector in ArangoDB stores this in a graph structure and generates Q&A pairs."
    response["metadata"]["pdf_export_info"] = pdf_export_info

else:
    # General inquiry
    response["content"] = "Message received, but I'm not sure what action is requested. Please specify what changes or information you need."

# Save response for Marker
response_dir = "{os.path.join(MARKER_MESSAGES_DIR, 'from_arangodb')}"
os.makedirs(response_dir, exist_ok=True)

response_file = os.path.join(response_dir, f"response_{{int(datetime.now().timestamp())}}.json")
with open(response_file, "w") as f:
    json.dump(response, f, indent=2)

print(f"Response saved to {{response_file}}")

# Try to notify Marker
try:
    marker_agent_path = os.path.join("{MARKER_PATH}", "marker", "cli", "agent_commands.py")
    if os.path.exists(marker_agent_path):
        subprocess.run([
            "cd", "{MARKER_PATH}", "&&",
            "python", "-m", "marker.cli.agent_commands", "process-message", response_file
        ], check=False, shell=True)
        print("Notified Marker of response")
except Exception as e:
    print(f"Failed to notify Marker: {{e}}")
"""

    # Write script content to file
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    return script_path


def create_marker_trigger_script(message_file: str) -> str:
    """Create a temporary script to trigger Marker's process-message command."""
    # Create temporary script file
    fd, script_path = tempfile.mkstemp(suffix='.py', prefix='marker_trigger_')
    os.close(fd)
    
    # Create script content
    script_content = f"""
import os
import sys
import subprocess

# Add Marker to path
sys.path.insert(0, "{MARKER_PATH}")

# Try to import Marker's agent_commands
try:
    from marker.cli.agent_commands import process_message
    
    # Call the process_message function directly
    process_message("{message_file}")
    print("Successfully called Marker's process_message function")
except ImportError:
    # Fall back to subprocess if import fails
    try:
        result = subprocess.run([
            "cd", "{MARKER_PATH}", "&&",
            "python", "-m", "marker.cli.agent_commands", "process-message", "{message_file}"
        ], check=True, shell=True, capture_output=True, text=True)
        print(f"Successfully called Marker's CLI command:\\n{{result.stdout}}")
    except subprocess.CalledProcessError as e:
        print(f"Error calling Marker's CLI command: {{e}}\\n{{e.stderr}}")
    except Exception as e:
        print(f"Error: {{e}}")
"""

    # Write script content to file
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    return script_path


def create_marker_implementation_script() -> str:
    """Create a script for Claude Code to implement agent_commands.py in Marker."""
    # Create temporary script file
    fd, script_path = tempfile.mkstemp(suffix='.py', prefix='marker_implementation_')
    os.close(fd)
    
    # For now, just create a simple instruction file
    script_content = '''
# Claude Code script to create agent_commands.py in Marker
import os
import sys
import json
import tempfile
import subprocess
from pathlib import Path

# Set working directory to Marker module
os.chdir("{MARKER_PATH}")

# Create the CLI directory if it doesn't exist
os.makedirs("marker/cli", exist_ok=True)

# Template for Marker's agent_commands.py
agent_commands_content = """Marker Agent Commands Module

Provides CLI commands for inter-module communication between Marker and ArangoDB.
This module implements the communication mechanism described in inter-module communication documentation.

Links:
- Communication Protocol: docs/correspondence/module_communication.md
- Marker: https://github.com/example/marker

Sample Input/Output:
- Input: Message requests from ArangoDB
- Output: Processed responses and actions in Marker
"""

import os
import sys
import json
import time
import typer
import shutil
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List, Any

# Set up application
app = typer.Typer(
    name="agent",
    help="Inter-module communication commands",
    add_completion=False
)

# Constants
ARANGODB_PATH = "/home/graham/workspace/experiments/arangodb"
MARKER_MESSAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "messages")
ARANGODB_MESSAGES_DIR = os.path.join(ARANGODB_PATH, "messages")

# Ensure message directories exist
os.makedirs(os.path.join(MARKER_MESSAGES_DIR, "from_arangodb"), exist_ok=True)
os.makedirs(os.path.join(MARKER_MESSAGES_DIR, "to_arangodb"), exist_ok=True)
os.makedirs(os.path.join(ARANGODB_MESSAGES_DIR, "from_marker"), exist_ok=True)
os.makedirs(os.path.join(ARANGODB_MESSAGES_DIR, "to_marker"), exist_ok=True)


@app.command("process-message")
def process_message(
    message_file: Path = typer.Argument(..., help="Path to message file from ArangoDB")
):
    """
    Process a message from ArangoDB module.
    
    This command reads a message from ArangoDB, analyzes it using Claude Code,
    and takes appropriate actions in Marker.
    """
    # Check if message file exists
    if not message_file.exists():
        typer.echo(f"Error: Message file not found: {{message_file}}")
        raise typer.Exit(code=1)
    
    typer.echo(f"Processing message from file: {{message_file}}")
    
    # Read message
    try:
        with open(message_file, 'r') as f:
            message = json.load(f)
    except json.JSONDecodeError:
        typer.echo("Error: Invalid JSON in message file")
        raise typer.Exit(code=1)
    
    # Validate message format
    if not all(field in message for field in ["source", "target", "type", "content"]):
        typer.echo("Error: Invalid message format. Required fields: source, target, type, content")
        raise typer.Exit(code=1)
    
    # Check message source
    if message["source"] != "arangodb":
        typer.echo(f"Error: Invalid message source: {{message['source']}}. Expected: arangodb")
        raise typer.Exit(code=1)
    
    # Create Claude Code processor script
    processor_script = create_processor_script(message)
    
    # Execute Claude Code processor
    try:
        execute_processor_script(processor_script, message)
    except Exception as e:
        typer.echo(f"Error executing processor script: {{e}}")
        raise typer.Exit(code=1)
    
    typer.echo("Message processed successfully")


@app.command("send-message")
def send_message(
    content: str = typer.Argument(..., help="Message content"),
    message_type: str = typer.Option("request", help="Message type (request/response/notification)")
):
    """
    Send a message to ArangoDB module.
    
    This command creates a message file for ArangoDB and triggers
    the ArangoDB module to process it.
    """
    # Validate message type
    valid_types = ["request", "response", "notification"]
    if message_type not in valid_types:
        typer.echo(f"Error: Invalid message type: {{message_type}}. Valid types: {{', '.join(valid_types)}}")
        raise typer.Exit(code=1)
    
    # Create message
    message = {{
        "source": "marker",
        "target": "arangodb",
        "type": message_type,
        "content": content,
        "timestamp": datetime.now().isoformat(),
        "metadata": {{
            "version": "1.0"
        }}
    }}
    
    # Save message to ArangoDB's incoming directory
    message_file = os.path.join(ARANGODB_MESSAGES_DIR, "from_marker", f"message_{{int(time.time())}}.json")
    try:
        with open(message_file, 'w') as f:
            json.dump(message, f, indent=2)
    except Exception as e:
        typer.echo(f"Error saving message file: {{e}}")
        raise typer.Exit(code=1)
    
    typer.echo(f"Message saved to: {{message_file}}")
    
    # Attempt to trigger ArangoDB's process-message command
    try:
        result = subprocess.run(
            [
                "cd", ARANGODB_PATH, "&&",
                "python", "-m", "arangodb.cli.agent_commands", "process-message", message_file
            ],
            capture_output=True,
            text=True,
            check=False,
            shell=True
        )
        
        if result.returncode == 0:
            typer.echo("Successfully notified ArangoDB of message")
        else:
            typer.echo(f"Warning: Failed to trigger ArangoDB's processing: {{result.stderr}}")
    except Exception as e:
        typer.echo(f"Warning: Failed to trigger ArangoDB processing: {{e}}")
    
    typer.echo("Message sent successfully")


def create_processor_script(message: Dict) -> str:
    """Create a temporary script for Claude Code to process the message."""
    # Create temporary script file
    fd, script_path = tempfile.mkstemp(suffix='.py', prefix='marker_processor_')
    os.close(fd)
    
    # Escape any quotes in the message for embedding in the script
    message_str = json.dumps(message)
    
    # Create processor script content
    script_content = f"""
# Marker processor script
import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Set working directory to Marker module
os.chdir("{os.path.dirname(os.path.dirname(os.path.dirname(__file__)))}")

# Load message
message = {message_str}

print(f"Processing message: {{message.get('content', '')}}")

# Message format example:
# {{"source": "arangodb", "target": "marker", "type": "request", "content": "text content"}}

# Process based on message type
message_type = message.get("type")
content = message.get("content", "")

# Create response template
response = {{
    "source": "marker",
    "target": "arangodb",
    "type": "response",
    "content": "",
    "timestamp": datetime.now().isoformat(),
    "metadata": {{
        "request_timestamp": message.get("timestamp"),
        "changes_made": False,
        "files_modified": []
    }}
}}

# Process message based on content 
# Implementation will vary based on Marker's specific capabilities
# This is just a template

# Save response for ArangoDB
response_dir = "{os.path.join(ARANGODB_MESSAGES_DIR, 'from_marker')}"
os.makedirs(response_dir, exist_ok=True)

response_file = os.path.join(response_dir, f"response_{{int(datetime.now().timestamp())}}.json")
with open(response_file, "w") as f:
    json.dump(response, f, indent=2)

print(f"Response saved to {{response_file}}")

# Try to notify ArangoDB
try:
    subprocess.run([
        "cd", "{ARANGODB_PATH}", "&&",
        "python", "-m", "arangodb.cli.agent_commands", "process-message", response_file
    ], check=False, shell=True)
    print("Notified ArangoDB of response")
except Exception as e:
    print(f"Failed to notify ArangoDB: {{e}}")
"""
    
    # Write the script content to file
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    return script_path


def execute_processor_script(script_path: str, message: Dict) -> None:
    """Execute the processor script using Claude Code or directly."""
    try:
        # First try to execute with Claude Code if available
        try:
            subprocess.run(["claude-code", script_path], check=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            # Fall back to direct execution if Claude Code not available
            subprocess.run(["python", script_path], check=True)
        
    except Exception as e:
        raise Exception(f"Failed to execute processor script: {{e}}")


if __name__ == "__main__":
    app()
"""

# Write the agent_commands.py file
agent_commands_path = "marker/cli/agent_commands.py"
with open(agent_commands_path, "w") as f:
    f.write(agent_commands_content)

print(f"Created {agent_commands_path}")

# Ensure proper imports in __init__.py
init_path = "marker/cli/__init__.py"
if os.path.exists(init_path):
    with open(init_path, "r") as f:
        init_content = f.read()
    
    # Check if we need to add agent_commands import
    if "agent_commands" not in init_content:
        # Add import if needed
        if init_content.strip():
            with open(init_path, "a") as f:
                f.write("\\nfrom marker.cli.agent_commands import app as agent_app\\n")
        else:
            with open(init_path, "w") as f:
                f.write("from marker.cli.agent_commands import app as agent_app\\n")
        
        print(f"Updated {init_path} with agent_commands import")
else:
    # Create __init__.py if it doesn't exist
    with open(init_path, "w") as f:
        f.write("from marker.cli.agent_commands import app as agent_app\\n")
    
    print(f"Created {init_path} with agent_commands import")

# Create messages directory structure
os.makedirs("messages/from_arangodb", exist_ok=True)
os.makedirs("messages/to_arangodb", exist_ok=True)

# Implementation instructions for Marker agent_commands.py
print("Please implement agent_commands.py in the Marker module with process-message and send-message commands.")
print("Refer to docs/correspondence/module_communication.md for details.")
'''

    # Write script content to file
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    return script_path


def execute_processor_script(script_path: str, message: Dict) -> None:
    """Execute the processor script using Claude Code."""
    try:
        # Execute with Claude Code
        subprocess.run(["claude-code", script_path], check=True)
    except Exception as e:
        raise Exception(f"Failed to execute processor script: {e}")


if __name__ == "__main__":
    app()