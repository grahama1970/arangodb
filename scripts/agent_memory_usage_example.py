"""
Agent Memory Usage Example
==========================

This script demonstrates how an AI agent would use the ArangoDB memory system
with Graphiti integration for maintaining conversation context and building knowledge.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

from arangodb.core.memory.memory_agent import MemoryAgent
from arangodb.core.arango_setup import connect_arango, ensure_database
from colorama import init, Fore, Style

init(autoreset=True)


class AIAssistant:
    """Example AI assistant that uses the memory system."""
    
    def __init__(self):
        """Initialize the assistant with memory capabilities."""
        # Connect to database
        client = connect_arango()
        self.db = ensure_database(client)
        
        # Initialize memory agent
        self.memory = MemoryAgent(db=self.db)
        
        # Track conversation
        self.conversation_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def process_message(self, user_message: str) -> str:
        """Process a user message and return a response."""
        print(f"\n{Fore.YELLOW}User:{Style.RESET_ALL} {user_message}")
        
        # 1. Search for relevant context
        print(f"{Fore.BLUE}[Memory] Searching for relevant context...{Style.RESET_ALL}")
        context = self._search_context(user_message)
        
        # 2. Generate response (simulated)
        response = self._generate_response(user_message, context)
        print(f"{Fore.GREEN}Assistant:{Style.RESET_ALL} {response}")
        
        # 3. Store the interaction
        print(f"{Fore.BLUE}[Memory] Storing interaction...{Style.RESET_ALL}")
        self._store_interaction(user_message, response)
        
        return response
    
    def _search_context(self, query: str) -> List[Dict[str, Any]]:
        """Search memory for relevant context."""
        # Search recent memories (last 30 days)
        results = self.memory.temporal_search(
            query_text=query,
            point_in_time=datetime.now(),
            top_n=5
        )
        
        relevant_memories = results.get('results', [])
        print(f"  Found {len(relevant_memories)} relevant memories")
        
        # Display top contexts
        for i, memory in enumerate(relevant_memories[:3]):
            content = memory['doc'].get('content', '')[:50]
            score = memory.get('combined_score', 0)
            print(f"  {i+1}. {content}... (score: {score:.3f})")
        
        return relevant_memories
    
    def _generate_response(self, user_message: str, context: List[Dict]) -> str:
        """Generate a response based on user message and context."""
        # This is where you'd use an LLM to generate a response
        # For this example, we'll use predefined responses
        
        responses = {
            "python": "Python is a versatile programming language known for its simplicity and readability.",
            "decorators": "Python decorators are a powerful feature that allow you to modify or enhance functions without changing their source code.",
            "functions": "Functions in Python are defined using the 'def' keyword and are first-class objects.",
            "classes": "Python classes provide a way to bundle data and functionality together using object-oriented programming.",
            "memory": "I use a sophisticated memory system to remember our conversations and provide better context.",
        }
        
        # Simple keyword matching for demo
        for keyword, response in responses.items():
            if keyword.lower() in user_message.lower():
                return response
        
        return "I understand your question. Let me provide some information based on what I know."
    
    def _store_interaction(self, user_message: str, response: str):
        """Store the interaction in memory."""
        result = self.memory.store_conversation(
            user_message=user_message,
            agent_response=response,
            conversation_id=self.conversation_id,
            metadata={
                "timestamp": datetime.now().isoformat(),
                "session_id": self.conversation_id,
                "message_count": self._get_message_count()
            }
        )
        
        print(f"  Stored as memory: {result.get('memory_key')}")
        print(f"  Entities extracted: {result.get('entity_count', 0)}")
        print(f"  Relationships created: {result.get('relationship_count', 0)}")
    
    def _get_message_count(self) -> int:
        """Get the number of messages in current conversation."""
        # Simple implementation - in production, query the database
        return 1
    
    def show_conversation_history(self):
        """Display the conversation history."""
        print(f"\n{Fore.CYAN}=== Conversation History ==={Style.RESET_ALL}")
        
        # Search for all messages in this conversation
        results = self.memory.temporal_search(
            query_text=self.conversation_id,
            point_in_time=datetime.now(),
            top_n=20
        )
        
        memories = results.get('results', [])
        print(f"Found {len(memories)} messages in this conversation\n")
        
        for memory in memories:
            doc = memory['doc']
            content = doc.get('content', '')
            timestamp = doc.get('start_time', '')
            
            # Parse and display the conversation
            if content.startswith("User:"):
                print(f"{Fore.YELLOW}{content}{Style.RESET_ALL}")
            print(f"{Fore.GRAY}[{timestamp}]{Style.RESET_ALL}\n")


def demonstrate_agent_memory():
    """Demonstrate how an agent uses the memory system."""
    print(f"{Fore.GREEN}=== AI Assistant Memory Demo ==={Style.RESET_ALL}\n")
    
    # Create assistant
    assistant = AIAssistant()
    
    # Simulate a conversation
    messages = [
        "What is Python?",
        "Can you explain Python decorators?",
        "How do Python functions work?",
        "Tell me about your memory system",
        "What did we discuss about Python earlier?"
    ]
    
    for message in messages:
        assistant.process_message(message)
        print("-" * 50)
    
    # Show conversation history
    assistant.show_conversation_history()
    
    # Demonstrate temporal search
    print(f"\n{Fore.CYAN}=== Temporal Search Demo ==={Style.RESET_ALL}")
    print("Searching for Python-related discussions from the last hour...")
    
    recent_memories = assistant.memory.temporal_search(
        query_text="Python",
        point_in_time=datetime.now(),
        top_n=10
    )
    
    print(f"Found {recent_memories.get('total', 0)} recent Python discussions")


if __name__ == "__main__":
    # Run the demonstration
    demonstrate_agent_memory()
    
    print(f"\n{Fore.GREEN}✓ Memory system demonstration complete{Style.RESET_ALL}")
    print(f"{Fore.BLUE}Key Takeaways:{Style.RESET_ALL}")
    print("1. Agents can search past conversations for context")
    print("2. All interactions are automatically stored with embeddings")
    print("3. Temporal search allows time-based retrieval")
    print("4. Relationships connect related memories")
    print("5. The system maintains conversation continuity")