# ArangoDB-Marker Communication System Guide

This document outlines the standardized communication approach between ArangoDB and Marker modules, enabling seamless cooperation and adaptability through CLI commands, Claude Code agents, and file-based message exchange.

## Communication System Architecture

The communication system between ArangoDB and Marker follows a streamlined architecture:

```
ArangoDB Module                        Marker Module
┌───────────────────────┐             ┌───────────────────────┐
│                       │             │                       │
│  1. Identify need     │             │                       │
│     for communication │             │                       │
│                       │             │                       │
│  2. Create JSON       │             │                       │
│     message           │             │                       │
│                       │             │                       │
│  3. Execute Marker    │             │                       │
│     CLI command       │──────────► │  4. Receive message   │
│                       │             │                       │
│                       │             │  5. Spawn Claude Code │
│                       │             │     with custom       │
│                       │             │     system prompt     │
│                       │             │                       │
│                       │             │  6. Claude analyzes   │
│                       │             │     code and makes    │
│                       │             │     changes           │
│                       │             │                       │
│                       │             │  7. Create response   │
│                       │             │     message           │
│                       │             │                       │
│  9. Receive response  │  ◄──────────  8. Execute ArangoDB  │
│                       │             │     CLI command       │
│  10. Process response │             │                       │
│      with Claude Code │             │                       │
│                       │             │                       │
└───────────────────────┘             └───────────────────────┘
```

## Core Components

### 1. CLI Commands for Inter-Module Communication

ArangoDB exposes the following CLI commands for Marker communication:

#### Command: `process-message`

```bash
python -m arangodb.cli.agent_commands process-message /path/to/message.json
```

This command:
- Loads a JSON message from Marker
- Spawns Claude Code with an ArangoDB-specific system prompt
- Executes the necessary code modifications
- Generates a response message

#### Command: `send-message`

```bash
python -m arangodb.cli.agent_commands send-message "We've updated our API endpoint structure" --message-type notification
```

This command:
- Creates a JSON message with ArangoDB as the source
- Saves the message in Marker's message directory
- Executes Marker's CLI command to process the message

### 2. Message Format and Exchange

#### Message Structure

All messages follow a standardized JSON format:

```json
{
  "source": "arangodb",
  "target": "marker",
  "type": "request|response|notification",
  "content": "The actual message content describing the request or change",
  "timestamp": "2025-05-19T14:30:00Z",
  "metadata": {
    "priority": "high|medium|low",
    "version": "1.0",
    "related_files": ["src/arangodb/qa_generation/exporter.py"]
  }
}
```

#### Message Types

- **Request**: A request for changes or information from the target module
- **Response**: A response to a request, including confirmation of changes
- **Notification**: An informational message about changes that have been made

#### Message Exchange Directory

Messages are exchanged through a shared directory structure:

```
/home/graham/workspace/experiments/
  ├── marker/
  │   └── messages/
  │       ├── from_arangodb/
  │       └── to_arangodb/
  └── arangodb/
      └── messages/
          ├── from_marker/
          └── to_marker/
```

### 3. Claude Code Integration

ArangoDB uses Claude Code with customized system prompts to interpret and act on messages from Marker:

#### Execution Command

```bash
claude-code script.py --system-prompt "You are an ArangoDB expert focused on the ArangoDB-Marker integration..."
```

#### System Prompt Template

```
You are an ArangoDB database expert, tasked with handling communication between ArangoDB and Marker modules.

Focus areas:
- QA pair generation and export
- Graph data structures and operations
- AQL query optimization
- Vector search functionality
- Data format standardization

When interpreting messages from Marker:
1. Analyze the request carefully
2. Identify relevant code files in the ArangoDB codebase
3. Make minimal, precise changes to meet the requirements
4. Validate changes with existing tests
5. Document all modifications made
6. Respond with specific details about implemented changes

Key directories to consider:
- src/arangodb/qa_generation/: QA pair generation and export
- src/arangodb/db/: Database operations
- src/arangodb/graph/: Graph data structures and operations
- src/arangodb/search/: Vector search and semantic search
- src/arangodb/api/: API endpoints and interfaces

Always ensure backward compatibility and maintain consistent code style.
```

## Common Communication Scenarios

### 1. Data Format Changes

When Marker requests a change to ArangoDB's data output format:

```bash
# From Marker
python -m marker.cli.agent_commands send-message "We need your QA export format to use 'type' instead of 'question_type' and include source metadata" --message-type request
```

ArangoDB processing:
1. Loads the message
2. Executes Claude Code with ArangoDB system prompt
3. Identifies relevant code (e.g., `src/arangodb/qa_generation/exporter.py`)
4. Makes the requested changes
5. Runs validation tests
6. Creates response with details of changes made

### 2. API Interface Updates

When ArangoDB updates its API interface:

```bash
# From ArangoDB
python -m arangodb.cli.agent_commands send-message "We've updated our vector search endpoint to support additional parameters: 'limit', 'offset', and 'min_score'" --message-type notification
```

Marker processing:
1. Loads the notification
2. Executes Claude Code with Marker system prompt
3. Updates relevant code that interacts with ArangoDB's API
4. Ensures compatibility with new parameters
5. Runs validation tests

### 3. QA Generation Flow Changes

When Marker needs ArangoDB to modify its QA generation process:

```bash
# From Marker
python -m marker.cli.agent_commands send-message "We need to add document source tracking to all generated QA pairs" --message-type request
```

ArangoDB responds by:
1. Analyzing QA generation code
2. Adding source tracking to the QA generation pipeline
3. Updating database schema as needed
4. Updating the exporter to include source information
5. Sending a response with implementation details

## Implementation Guidelines

### For ArangoDB Developers

When implementing the module communication system:

1. **Message Handling**:
   - Validate all incoming messages against the JSON schema
   - Log all message exchanges for debugging purposes
   - Handle malformed messages gracefully

2. **Claude Code Integration**:
   - Ensure the system prompt provides comprehensive context
   - Keep Claude's workspace limited to relevant files only
   - Implement proper error handling for Claude Code execution

3. **Response Generation**:
   - Include specific details about changes made
   - Reference affected files and functions
   - Provide error information if a request couldn't be fulfilled

4. **Testing and Validation**:
   - Always run tests after making changes
   - Verify compatibility with Marker's requirements
   - Include validation results in response messages

### Security Considerations

1. **Input Validation**:
   - Validate all message content before processing
   - Sanitize file paths to prevent path traversal
   - Verify message source before executing actions

2. **Permission Management**:
   - Restrict Claude Code's file access to appropriate directories
   - Do not execute arbitrary commands from messages
   - Set appropriate permissions for message directories

## Troubleshooting

### Common Issues and Solutions

| Issue | Possible Cause | Solution |
|-------|---------------|----------|
| Message not received | Message directory missing | Check directory exists and has correct permissions |
| Changes not applied | Incorrect file path in message | Verify file paths and ensure they exist |
| Claude Code error | System prompt issues | Check system prompt for errors or context limitations |
| Invalid response format | Schema mismatch | Verify message format against schema documentation |
| CLI command not found | Path issues | Ensure module is in PYTHONPATH and CLI commands are registered |

## Module Communication Roadmap

1. **Phase 1: Basic Communication**
   - Implement CLI commands
   - Set up message exchange directories
   - Create basic Claude Code integration

2. **Phase 2: Enhanced Integration**
   - Add customized system prompts
   - Implement comprehensive validation
   - Create automated tests for message processing

3. **Phase 3: Advanced Features**
   - Add support for complex message types
   - Implement versioning for message format
   - Create message history tracking

## Conclusion

This communication system enables ArangoDB and Marker to operate as a cohesive ecosystem while maintaining modular independence. By using standardized CLI commands, structured messages, and intelligent Claude Code agents with module-specific knowledge, the modules can efficiently communicate requirements, implement changes, and maintain compatibility.

For more detailed technical specifications and implementation guidelines, refer to the comprehensive task list in the Marker project: `/docs/tasks/033_Module_Communication_System.md`.