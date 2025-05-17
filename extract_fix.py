def extract_llm_response(response: Any) -> str:
    """
    Extract the text content from an LLM response.
    
    Args:
        response: The response object from an LLM
        
    Returns:
        str: The extracted text content
    """
    try:
        if hasattr(response, 'choices') and response.choices:
            # Handle list of Choices objects
            if isinstance(response.choices, list) and len(response.choices) > 0:
                choice = response.choices[0]
                # If it's a string representation of Choices
                if isinstance(choice, str) and 'content=' in choice:
                    # Parse out content from string representation
                    content_start = choice.find('content=') + 9  # +9 for 'content=' and the quote
                    content_end = choice.find(", content_start)
                    if content_end > content_start:
                        return choice[content_start:content_end]
                # If its a proper object