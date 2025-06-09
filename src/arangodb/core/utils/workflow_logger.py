"""
Workflow Tracking Module for ArangoDB Knowledge Graph System
Module: workflow_logger.py

This module provides detailed logging for complex workflows, integrating
with the memory system and providing step-tracking and performance metrics.

Features:
- Workflow tracking with start/complete/fail states
- Step-level tracking with timing and metadata
- Error handling and reporting
- Integration with the main logger
"""

import os
import sys
import uuid
import time
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Callable, Union
from functools import wraps
from loguru import logger

# Define log levels
class LogLevel:
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"
    CRITICAL = "CRITICAL"

# Define component types
class ComponentType:
    SEARCH = "SEARCH"
    MEMORY = "MEMORY"
    GRAPH = "GRAPH"
    LLM = "LLM"
    EMBEDDING = "EMBEDDING"
    DATABASE = "DATABASE"
    CLI = "CLI"
    SYSTEM = "SYSTEM"

class WorkflowLogger:
    """
    Logger for complex workflows.
    
    This class provides methods for tracking workflow steps,
    recording metadata, and timing operations.
    """
    
    def __init__(self, name: str, workflow_id: Optional[str] = None):
        """Initialize a workflow logger with a unique ID."""
        self.workflow_id = workflow_id or f"wf_{uuid.uuid4().hex[:8]}"
        self.name = name
        self.steps = []
        self.current_step = None
        self.start_time = time.time()
        self.end_time = None
        self.status = "started"
        self.error = None
        
        logger.info(f"Workflow '{name}' started with ID {self.workflow_id}")
    
    def log_data(self, data: Dict[str, Any], level: str = LogLevel.INFO, 
                source: str = ComponentType.SYSTEM, description: Optional[str] = None):
        """Log data with the specified level and source."""
        msg = f"[{self.workflow_id}] {description or 'Data point'}"
        
        if level == LogLevel.DEBUG:
            logger.debug(f"{msg}: {data}")
        elif level == LogLevel.INFO:
            logger.info(f"{msg}: {data}")
        elif level == LogLevel.WARNING:
            logger.warning(f"{msg}: {data}")
        elif level == LogLevel.ERROR:
            logger.error(f"{msg}: {data}")
        elif level == LogLevel.SUCCESS:
            logger.success(f"{msg}: {data}")
        elif level == LogLevel.CRITICAL:
            logger.critical(f"{msg}: {data}")
    
    def start_step(self, step_name: str):
        """Start a new step in the workflow."""
        if self.current_step:
            logger.warning(f"Starting step '{step_name}' before completing '{self.current_step['name']}'")
            
        self.current_step = {
            "name": step_name,
            "status": "started",
            "start_time": time.time(),
            "end_time": None,
            "elapsed_time": None,
            "metadata": {},
            "error": None
        }
        
        logger.debug(f"[{self.workflow_id}] Step '{step_name}' started")
    
    def complete_step(self, step_name: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        """Complete the current step with optional metadata."""
        if not self.current_step:
            logger.warning(f"Attempting to complete step '{step_name}' but no step is active")
            return
            
        if step_name and step_name != self.current_step["name"]:
            logger.warning(f"Completing step '{step_name}' but current step is '{self.current_step['name']}'")
            
        end_time = time.time()
        elapsed = end_time - self.current_step["start_time"]
        
        self.current_step["status"] = "completed"
        self.current_step["end_time"] = end_time
        self.current_step["elapsed_time"] = elapsed
        
        if metadata:
            self.current_step["metadata"].update(metadata)
        
        logger.debug(f"[{self.workflow_id}] Step '{self.current_step['name']}' completed in {elapsed:.2f}s")
        
        # Add to steps list and reset current
        self.steps.append(self.current_step)
        self.current_step = None
    
    def fail_step(self, step_name: Optional[str] = None, error: Optional[str] = None):
        """Mark the current step as failed with error information."""
        if not self.current_step:
            logger.warning(f"Attempting to fail step '{step_name}' but no step is active")
            return
            
        if step_name and step_name != self.current_step["name"]:
            logger.warning(f"Failing step '{step_name}' but current step is '{self.current_step['name']}'")
            
        end_time = time.time()
        elapsed = end_time - self.current_step["start_time"]
        
        self.current_step["status"] = "failed"
        self.current_step["end_time"] = end_time
        self.current_step["elapsed_time"] = elapsed
        self.current_step["error"] = error
        
        logger.error(f"[{self.workflow_id}] Step '{self.current_step['name']}' failed after {elapsed:.2f}s: {error}")
        
        # Add to steps list and reset current
        self.steps.append(self.current_step)
        self.current_step = None
    
    def complete_workflow(self, metadata: Optional[Dict[str, Any]] = None):
        """Complete the workflow with optional metadata."""
        if self.current_step:
            logger.warning(f"Completing workflow with active step '{self.current_step['name']}'")
            self.complete_step()
            
        self.end_time = time.time()
        self.status = "completed"
        
        elapsed = self.end_time - self.start_time
        logger.info(f"Workflow '{self.name}' completed in {elapsed:.2f}s")
        
        if metadata:
            for key, value in metadata.items():
                setattr(self, key, value)
    
    def fail_workflow(self, error: Optional[str] = None):
        """Mark the workflow as failed with error information."""
        if self.current_step:
            self.fail_step(error=error)
            
        self.end_time = time.time()
        self.status = "failed"
        self.error = error
        
        elapsed = self.end_time - self.start_time
        logger.error(f"Workflow '{self.name}' failed after {elapsed:.2f}s: {error}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a dictionary summary of the workflow."""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "status": self.status,
            "start_time": datetime.fromtimestamp(self.start_time, tz=timezone.utc).isoformat(),
            "end_time": datetime.fromtimestamp(self.end_time, tz=timezone.utc).isoformat() if self.end_time else None,
            "elapsed_time": self.end_time - self.start_time if self.end_time else time.time() - self.start_time,
            "steps": self.steps,
            "error": self.error
        }
    
    def to_json(self) -> str:
        """Convert the workflow summary to JSON."""
        return json.dumps(self.get_summary())

class RepositoryWorkflow:
    """
    Workflow tracker for repository operations.
    
    This class extends the basic workflow tracking with
    repository-specific functionality.
    """
    
    def __init__(self, repo_name: str, repo_url: str, workflow_id: Optional[str] = None):
        """Initialize a repository workflow tracker."""
        self.repo_name = repo_name
        self.repo_url = repo_url
        self.workflow_logger = WorkflowLogger(f"Repository: {repo_name}", workflow_id)
    
    def log_llm_request(self, model: str, prompt_tokens: int, prompt_length: int):
        """Log an LLM request."""
        self.workflow_logger.log_data(
            {
                "model": model,
                "prompt_tokens": prompt_tokens,
                "prompt_length": prompt_length
            },
            level=LogLevel.INFO,
            source=ComponentType.LLM,
            description="LLM request"
        )
    
    def log_error(self, error: Exception, context: str = ""):
        """Log an error with context."""
        self.workflow_logger.log_data(
            {
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context
            },
            level=LogLevel.ERROR,
            source=ComponentType.SYSTEM,
            description="Error occurred"
        )

def track_workflow(name: Optional[str] = None):
    """
    Decorator to track a function as a workflow.
    
    Args:
        name: Optional name for the workflow (uses function name if None)
    
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            workflow_name = name or func.__name__
            workflow = WorkflowLogger(workflow_name)
            
            try:
                result = func(*args, **kwargs, workflow=workflow)
                workflow.complete_workflow()
                return result
            except Exception as e:
                workflow.fail_workflow(error=str(e))
                raise
        
        return wrapper
    
    return decorator

def track_repo_summarization(func):
    """
    Decorator specifically for repository summarization.
    
    Args:
        func: Function to decorate
    
    Returns:
        Decorated function
    """
    @wraps(func)
    def wrapper(digest_path: str, summary_path: str, *args, **kwargs):
        repo_name = os.path.basename(os.path.dirname(digest_path))
        
        # Create a repo workflow object
        repo_workflow = RepositoryWorkflow(
            repo_name=repo_name,
            repo_url=f"file://{os.path.dirname(digest_path)}"
        )
        
        # Create a new workflow step
        repo_workflow.workflow_logger.start_step("Read repository digest")
        
        try:
            result = func(digest_path, summary_path, *args, **kwargs, repo_workflow=repo_workflow)
            repo_workflow.workflow_logger.complete_workflow()
            return result
        except Exception as e:
            repo_workflow.log_error(e, context="Repository summarization")
            repo_workflow.workflow_logger.fail_workflow(error=str(e))
            raise
    
    return wrapper

# Self-validation when run directly
if __name__ == "__main__":
    # Configure logging for standalone testing
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    print("=== Testing WorkflowLogger ===")
    
    try:
        # Create a test workflow
        workflow = WorkflowLogger("Test Workflow")
        
        # Log test data
        workflow.log_data({"test_key": "test_value"}, level=LogLevel.INFO)
        
        # Test steps
        workflow.start_step("Step 1")
        time.sleep(0.1)  # Simulate work
        workflow.complete_step(metadata={"step_result": "success"})
        
        workflow.start_step("Step 2")
        time.sleep(0.2)  # Simulate work
        workflow.fail_step(error="Simulated error")
        
        workflow.start_step("Step 3")
        time.sleep(0.1)  # Simulate work
        workflow.complete_step()
        
        # Complete workflow
        workflow.complete_workflow()
        
        # Print summary
        print("\nWorkflow Summary:")
        print(json.dumps(workflow.get_summary(), indent=2))
        
        print("\n=== WorkflowLogger Tests Passed ===")
        sys.exit(0)
    except Exception as e:
        print(f"\n=== WorkflowLogger Tests Failed: {e} ===")
        sys.exit(1)
