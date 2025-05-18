"""
View Configuration Module

Provides centralized configuration for ArangoDB views and their management policies.
"""

from typing import Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum


class ViewUpdatePolicy(Enum):
    """View update policies."""
    ALWAYS_RECREATE = "always_recreate"  # Always recreate (old behavior)
    CHECK_CONFIG = "check_config"        # Only recreate if config changed (optimized)
    NEVER_RECREATE = "never_recreate"    # Never recreate unless forced


@dataclass
class ViewConfiguration:
    """Configuration for a specific view."""
    name: str
    collection: str
    fields: List[str]
    analyzers: List[str] = field(default_factory=lambda: ["text_en"])
    update_policy: ViewUpdatePolicy = ViewUpdatePolicy.CHECK_CONFIG
    cache_ttl: int = 3600  # Cache TTL in seconds
    
    def to_properties(self) -> Dict[str, Any]:
        """Convert to ArangoDB view properties format."""
        return {
            "links": {
                self.collection: {
                    "analyzers": self.analyzers,
                    "includeAllFields": False,
                    "fields": {field: {} for field in self.fields}
                }
            }
        }


# Default view configurations
VIEW_CONFIGS = {
    "agent_memory_view": ViewConfiguration(
        name="agent_memory_view",
        collection="agent_memories",
        fields=["content", "summary", "tags", "metadata.context"],
        update_policy=ViewUpdatePolicy.CHECK_CONFIG
    ),
    "compacted_summaries_view": ViewConfiguration(
        name="compacted_summaries_view",
        collection="compacted_summaries",
        fields=["content", "source_message_ids", "metadata.method"],
        update_policy=ViewUpdatePolicy.CHECK_CONFIG
    ),
    "memory_view": ViewConfiguration(
        name="memory_view",
        collection="memory_documents",
        fields=["content", "title", "summary", "tags"],
        update_policy=ViewUpdatePolicy.CHECK_CONFIG
    ),
    "glossary_view": ViewConfiguration(
        name="glossary_view",
        collection="agent_glossary",
        fields=["term", "definition", "context", "related_terms"],
        update_policy=ViewUpdatePolicy.CHECK_CONFIG
    ),
}


def get_view_config(view_name: str) -> ViewConfiguration:
    """Get configuration for a specific view."""
    if view_name not in VIEW_CONFIGS:
        # Return a default config if not found
        return ViewConfiguration(
            name=view_name,
            collection=view_name.replace("_view", ""),
            fields=["content"],
            update_policy=ViewUpdatePolicy.CHECK_CONFIG
        )
    return VIEW_CONFIGS[view_name]


def set_global_update_policy(policy: ViewUpdatePolicy):
    """Set the update policy for all views."""
    for config in VIEW_CONFIGS.values():
        config.update_policy = policy


# Environment-based configuration
import os

# Allow environment variable to control view recreation behavior
env_policy = os.getenv("ARANGO_VIEW_UPDATE_POLICY", "check_config").lower()
if env_policy == "always_recreate":
    set_global_update_policy(ViewUpdatePolicy.ALWAYS_RECREATE)
elif env_policy == "never_recreate":
    set_global_update_policy(ViewUpdatePolicy.NEVER_RECREATE)
# Default is CHECK_CONFIG


if __name__ == "__main__":
    """Test view configuration."""
    print("=== View Configuration Test ===")
    
    # Test configuration retrieval
    memory_config = get_view_config("agent_memory_view")
    print(f"\nMemory View Config:")
    print(f"  Name: {memory_config.name}")
    print(f"  Collection: {memory_config.collection}")
    print(f"  Fields: {memory_config.fields}")
    print(f"  Policy: {memory_config.update_policy.value}")
    
    # Test properties conversion
    properties = memory_config.to_properties()
    print(f"\nProperties:")
    print(f"  {properties}")
    
    # Test environment variable
    print(f"\nEnvironment Policy: {env_policy}")
    
    print("\n✅ View configuration module loaded successfully")