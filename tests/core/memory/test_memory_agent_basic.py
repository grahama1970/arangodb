import subprocess
import sys
import time

# First store a memory
cmd_store = ["uv", "run", "python", "-m", "arangodb.cli.main", "memory", "store", 
             "--user-message", "What is the capital of France?",
             "--agent-response", "The capital of France is Paris",
             "--conversation-id", "test_conv_123"]
             
result_store = subprocess.run(cmd_store, capture_output=True, text=True)
print("Store - Exit code:", result_store.returncode)
print("Store - STDOUT:", result_store.stdout[:200])

# Wait a bit for indexing
time.sleep(3)

# Now search for it
cmd_search = ["uv", "run", "python", "-m", "arangodb.cli.main", "memory", "search", "capital France", "--top-n", "5"]
result_search = subprocess.run(cmd_search, capture_output=True, text=True)

print("\nSearch - Exit code:", result_search.returncode)
print("Search - STDOUT:", result_search.stdout)
print("Search - STDERR:", result_search.stderr)