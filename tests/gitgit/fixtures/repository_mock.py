"""
Mocking utilities for creating test repositories.
"""
import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional

def create_mock_repository(
    base_dir: str,
    structure_file: str,
    repo_name: Optional[str] = None
) -> str:
    """
    Create a mock repository with a given structure.
    
    Args:
        base_dir: Base directory where the repository will be created
        structure_file: Path to the JSON file defining the repository structure
        repo_name: Optional name override for the repository (defaults to name in structure file)
        
    Returns:
        Path to the created repository
    """
    # Load the repository structure
    with open(structure_file, 'r') as f:
        structure = json.load(f)
    
    # Get repository name
    repo_name = repo_name or structure['repo_name']
    repo_path = os.path.join(base_dir, f"{repo_name}_sparse")
    
    # Create the repository
    if os.path.exists(repo_path):
        shutil.rmtree(repo_path)
    os.makedirs(repo_path)
    
    # Create files
    for file_info in structure['files']:
        file_path = os.path.join(repo_path, file_info['path'])
        
        # Create directory if needed
        directory = os.path.dirname(file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        # Write file content
        with open(file_path, 'w') as f:
            f.write(file_info['content'])
    
    return repo_path

def create_expected_output_files(
    repo_path: str,
    mock_llm_summary: bool = False,
    mock_code_metadata: bool = False
) -> Dict[str, str]:
    """
    Create expected output files for a repository.
    
    Args:
        repo_path: Path to the repository
        mock_llm_summary: Whether to create a mock LLM summary
        mock_code_metadata: Whether to create mock code metadata
        
    Returns:
        Dictionary mapping output file names to their paths
    """
    output_files = {}
    
    # Get all files in the repository
    all_files = []
    for root, _, files in os.walk(repo_path):
        for file in files:
            rel_path = os.path.relpath(os.path.join(root, file), repo_path)
            all_files.append(rel_path)
    
    # Create SUMMARY.txt
    summary_path = os.path.join(repo_path, "SUMMARY.txt")
    with open(summary_path, "w") as f:
        f.write(f"Directory: {repo_path}\n")
        f.write(f"Files analyzed: {len(all_files)}\n")
        f.write("Total bytes: 1024\n")
        f.write("Estimated tokens: 256\n")
        f.write("Files included:\n")
        for file_path in sorted(all_files):
            f.write(f"{file_path}\n")
    output_files["SUMMARY.txt"] = summary_path
    
    # Create DIGEST.txt
    digest_path = os.path.join(repo_path, "DIGEST.txt")
    with open(digest_path, "w") as f:
        for file_path in sorted(all_files):
            full_path = os.path.join(repo_path, file_path)
            f.write("=" * 48 + "\n")
            f.write(f"File: {file_path}\n")
            f.write("=" * 48 + "\n")
            with open(full_path, "r") as file_handle:
                f.write(file_handle.read() + "\n\n")
    output_files["DIGEST.txt"] = digest_path
    
    # Create TREE.txt
    tree_path = os.path.join(repo_path, "TREE.txt")
    with open(tree_path, "w") as f:
        f.write(f"{repo_path}/\n")
        
        # Group files by directory
        dirs = {}
        for file_path in sorted(all_files):
            parts = file_path.split('/')
            if len(parts) == 1:
                # File in root directory
                f.write(f"    {file_path}\n")
            else:
                # File in subdirectory
                dir_name = parts[0]
                if dir_name not in dirs:
                    dirs[dir_name] = []
                dirs[dir_name].append('/'.join(parts[1:]))
        
        # Write subdirectories
        for dir_name, files in sorted(dirs.items()):
            f.write(f"    {dir_name}/\n")
            for file_path in sorted(files):
                if '/' in file_path:
                    # Nested directory
                    subparts = file_path.split('/')
                    f.write(f"        {subparts[0]}/\n")
                    f.write(f"            {subparts[1]}\n")
                else:
                    f.write(f"        {file_path}\n")
    output_files["TREE.txt"] = tree_path
    
    # Create LLM_SUMMARY.txt if requested
    if mock_llm_summary:
        llm_summary_path = os.path.join(repo_path, "LLM_SUMMARY.txt")
        with open(llm_summary_path, "w") as f:
            f.write("# Summary\n\n")
            f.write("This is a mock LLM summary of the repository.\n\n")
            f.write("The repository contains the following files:\n\n")
            f.write("# Table Of Contents\n\n")
            for file_path in sorted(all_files):
                f.write(f"- {file_path}\n")
        output_files["LLM_SUMMARY.txt"] = llm_summary_path
    
    # Create code metadata if requested
    if mock_code_metadata:
        metadata_path = os.path.join(repo_path, "CODE_METADATA.json")
        metadata = {
            "functions": [
                {"name": "main", "file": "src/main.py", "line": 1},
                {"name": "calculate_sum", "file": "src/utils.py", "line": 1},
                {"name": "calculate_product", "file": "src/utils.py", "line": 5}
            ],
            "classes": [
                {"name": "TestMain", "file": "tests/test_main.py", "line": 4},
                {"name": "TestUtils", "file": "tests/test_utils.py", "line": 4}
            ],
            "imports": [
                {"module": "unittest", "file": "tests/test_main.py"},
                {"module": "unittest", "file": "tests/test_utils.py"}
            ]
        }
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        output_files["CODE_METADATA.json"] = metadata_path
    
    return output_files

def create_chunked_files(repo_path: str) -> Dict[str, str]:
    """
    Create chunked files for a repository.
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        Dictionary mapping chunk file names to their paths
    """
    chunk_files = {}
    
    # Create chunks directory
    chunks_dir = os.path.join(repo_path, "chunks")
    os.makedirs(chunks_dir, exist_ok=True)
    
    # Create chunks for select files
    for file_name in ["README.md", "src/main.py", "src/utils.py"]:
        full_path = os.path.join(repo_path, file_name)
        if os.path.exists(full_path):
            # Read the file
            with open(full_path, "r") as f:
                content = f.read()
            
            # Create chunks
            chunks = []
            lines = content.split("\n")
            for i in range(0, len(lines), 3):
                chunk = "\n".join(lines[i:i+3])
                if chunk:
                    chunks.append({
                        "text": chunk,
                        "start_line": i + 1,
                        "end_line": min(i + 3, len(lines)),
                        "metadata": {
                            "file": file_name,
                            "repo": os.path.basename(repo_path)
                        }
                    })
            
            # Clean file name for saving
            clean_name = file_name.replace("/", "_")
            chunk_file = os.path.join(chunks_dir, f"{clean_name}.chunks.json")
            
            # Save chunks
            with open(chunk_file, "w") as f:
                json.dump(chunks, f, indent=2)
            
            chunk_files[os.path.basename(chunk_file)] = chunk_file
    
    return chunk_files

def create_parsed_markdown_files(repo_path: str) -> Dict[str, str]:
    """
    Create parsed markdown files for a repository.
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        Dictionary mapping parsed file names to their paths
    """
    parsed_files = {}
    
    # Create parsed directory
    parsed_dir = os.path.join(repo_path, "parsed")
    os.makedirs(parsed_dir, exist_ok=True)
    
    # Find all markdown files
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, repo_path)
                
                # Read the file
                with open(file_path, "r") as f:
                    content = f.read()
                
                # Extract headings
                headings = []
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if line.startswith("#"):
                        level = len(line) - len(line.lstrip("#"))
                        text = line.lstrip("# ")
                        headings.append({
                            "level": level,
                            "text": text,
                            "line": i + 1
                        })
                
                # Create simple structure
                structure = {
                    "metadata": {
                        "file": rel_path,
                        "repo": os.path.basename(repo_path)
                    },
                    "headings": headings,
                    "content": content
                }
                
                # Clean file name for saving
                clean_name = rel_path.replace("/", "_")
                parsed_file = os.path.join(parsed_dir, f"{clean_name}.parsed.json")
                
                # Save parsed structure
                with open(parsed_file, "w") as f:
                    json.dump(structure, f, indent=2)
                
                parsed_files[os.path.basename(parsed_file)] = parsed_file
    
    return parsed_files

def setup_complete_test_repository(
    base_dir: str,
    structure_file: str,
    repo_name: Optional[str] = None,
    with_llm_summary: bool = False,
    with_code_metadata: bool = False,
    with_chunks: bool = False,
    with_parsed_markdown: bool = False
) -> Dict[str, Any]:
    """
    Set up a complete test repository with all expected outputs.
    
    Args:
        base_dir: Base directory where the repository will be created
        structure_file: Path to the JSON file defining the repository structure
        repo_name: Optional name override for the repository
        with_llm_summary: Whether to create a mock LLM summary
        with_code_metadata: Whether to create mock code metadata
        with_chunks: Whether to create chunked files
        with_parsed_markdown: Whether to create parsed markdown files
        
    Returns:
        Dictionary with repository information and paths to created files
    """
    # Create repository
    repo_path = create_mock_repository(base_dir, structure_file, repo_name)
    
    # Create standard output files
    output_files = create_expected_output_files(
        repo_path, 
        mock_llm_summary=with_llm_summary,
        mock_code_metadata=with_code_metadata
    )
    
    result = {
        "repo_path": repo_path,
        "output_files": output_files
    }
    
    # Create chunked files if requested
    if with_chunks:
        chunk_files = create_chunked_files(repo_path)
        result["chunk_files"] = chunk_files
    
    # Create parsed markdown files if requested
    if with_parsed_markdown:
        parsed_files = create_parsed_markdown_files(repo_path)
        result["parsed_files"] = parsed_files
    
    return result