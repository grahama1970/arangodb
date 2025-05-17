# Scripts Directory

This directory contains utility scripts and examples for the ArangoDB project.

## Main Scripts

- `agent_memory_usage_example.py` - Example of how to use the Memory Agent
- `setup_project.sh` - Project setup script
- `cli_verification.sh` - CLI verification script  
- `cli_verification_fixed.sh` - Fixed version of CLI verification
- `test_cross_encoder_reranking.sh` - Test cross-encoder functionality
- `restart_terminal.py` - Terminal restart utility

## Archive Directory

The `archive/` subdirectory contains:
- Old test scripts that have been replaced by proper tests in `/tests/`
- Debug scripts used during development
- Deprecated verification scripts
- `fix_bugs.sh` - Old bug fix script
- `test_all_cli_commands.sh` - Replaced by tests in `/tests/cli/`
- `verify_cli_temporal_parameters.py` - Old verification script
- `debug_collections.py` - Collection debugging tool

These are kept for historical reference but should not be used in production.

## _archive Directory

Contains old configuration files like `pyproject.toml` backups.

## Usage

To run any script:
```bash
# Python scripts
python scripts/agent_memory_usage_example.py

# Shell scripts
bash scripts/setup_project.sh
```

## Note

For running tests, use the proper test suite in `/tests/` instead of the archived test scripts.