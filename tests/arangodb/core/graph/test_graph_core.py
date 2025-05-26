import subprocess
import sys
from datetime import datetime

# Generate unique test keys
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
test_key1 = f"test_doc_{timestamp}_1"
test_key2 = f"test_doc_{timestamp}_2"

# First create two documents
cmd1 = ["uv", "run", "python", "-m", "arangodb.cli.main", "crud", "add-lesson", "--key", test_key1, "--problem", "Test problem 1", "--solution", "Test solution 1"]
result1 = subprocess.run(cmd1, capture_output=True, text=True)
print(f"Create doc1 - Exit code: {result1.returncode}")

cmd2 = ["uv", "run", "python", "-m", "arangodb.cli.main", "crud", "add-lesson", "--key", test_key2, "--problem", "Test problem 2", "--solution", "Test solution 2"]
result2 = subprocess.run(cmd2, capture_output=True, text=True)
print(f"Create doc2 - Exit code: {result2.returncode}")

# Now create relationship
cmd_rel = ["uv", "run", "python", "-m", "arangodb.cli.main", "graph", "add-relationship", test_key1, test_key2, "--type", "RELATED", "--rationale", "Test relationship"]
result_rel = subprocess.run(cmd_rel, capture_output=True, text=True)

print(f"\nCreate relationship - Exit code: {result_rel.returncode}")
print("STDOUT:", result_rel.stdout)
print("STDERR:", result_rel.stderr)