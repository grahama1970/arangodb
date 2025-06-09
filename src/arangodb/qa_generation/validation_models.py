"""
Validation models for Q&A generation errors and retries.
Module: validation_models.py
Description: Data models and schemas for validation models

This module defines models for validation errors and retry messages.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class QAValidationError(BaseModel):
    """Validation error for Q&A generation."""
    
    error_type: str = Field(..., description="Type of validation error")
    error_message: str = Field(..., description="Detailed error message")
    missing_fields: List[str] = Field(default_factory=list, description="Missing required fields")
    invalid_fields: Dict[str, str] = Field(default_factory=dict, description="Invalid fields and reasons")
    fix_suggestion: str = Field(..., description="Suggestion for fixing the error")
    
    def to_retry_message(self) -> str:
        """Convert error to retry message for LLM."""
        message = f"ERROR: {self.error_type}\n\n"
        message += f"Issue: {self.error_message}\n\n"
        
        if self.missing_fields:
            message += f"Missing fields: {', '.join(self.missing_fields)}\n"
        
        if self.invalid_fields:
            message += "Invalid fields:\n"
            for field, reason in self.invalid_fields.items():
                message += f"  - {field}: {reason}\n"
        
        message += f"\nFix: {self.fix_suggestion}\n\n"
        message += "Please regenerate the Q&A pair following these requirements:\n"
        message += "1. Include 'question', 'thinking', and 'answer' fields\n"
        message += "2. Answer must be factual and found in the provided content\n"
        message += "3. Thinking should explain the reasoning process\n"
        message += "4. Question should be clear and specific\n"
        
        return message


class QARetryContext(BaseModel):
    """Context for Q&A generation retry."""
    
    attempt_number: int = Field(..., description="Current retry attempt")
    previous_errors: List[QAValidationError] = Field(default_factory=list, description="Previous validation errors")
    original_prompt: str = Field(..., description="Original generation prompt")
    section_content: str = Field(..., description="Section content for validation")
    temperature: float = Field(..., description="Temperature used for generation")
    
    def build_retry_prompt(self) -> str:
        """Build retry prompt with error context."""
        prompt = "Previous generation attempts failed. Please fix the following issues:\n\n"
        
        for i, error in enumerate(self.previous_errors[-3:], 1):  # Show last 3 errors
            prompt += f"Attempt {i} Error:\n"
            prompt += error.to_retry_message()
            prompt += "\n---\n\n"
        
        prompt += "ORIGINAL REQUEST:\n"
        prompt += self.original_prompt
        prompt += "\n\nREMEMBER: The answer MUST be directly found in the provided content."
        
        return prompt