# Scripts Directory

This directory contains organized utility scripts, tools, and examples for the ArangoDB Memory Bank project.

## Directory Structure

```
scripts/
├── README.md                  # This file
├── Makefile                   # Common build/dev tasks
├── run_quick_tests.sh        # Interactive test runner
├── cli_verification_fixed.sh # CLI verification utility
├── cli_json_output.sh        # CLI JSON output utility
├── agent_memory_usage_example.py # Memory agent usage example
├── requirements.json         # Requirements metadata
├── conf.py                   # Configuration file
├── setup/                    # Project setup scripts
│   ├── setup_project.sh     # Main project setup
│   └── requirements.txt     # Python dependencies
├── testing/                  # Testing utilities
│   ├── comprehensive_cli_test.py # Full CLI test suite
│   ├── quick_cli_test.py    # Quick CLI tests
│   ├── test_single_crud.py  # Single CRUD operation test
│   └── test_cross_encoder_reranking.sh # Cross-encoder tests
├── integration/             # Integration utilities
│   ├── marker_integration.py # Marker system integration
│   └── generate_full_mcp.py # MCP configuration generator
├── utilities/               # Development utilities
│   ├── check_collections.py # ArangoDB collection checker
│   ├── extract_issues.py   # Extract issues from code
│   ├── iterate.py          # Task iteration helper
│   ├── track_progress.py   # Progress tracking utility
│   ├── task_utils.py       # Task utility functions
│   ├── serve_visualizations.py # Visualization server
│   ├── validate_visualization_system.py # Visualization validator
│   └── verify_unsloth_exporter.py # Unsloth export verifier
├── migration/              # Database/code migration scripts
│   ├── migrate_cli.py     # CLI migration utility
│   ├── migrate_to_bitemporal.py # Bitemporal model migration
│   └── standardize_field_names.py # Field name standardization
├── validate/              # Validation scripts
│   └── [various validate_*.py files] # Module validators
├── archive/               # Archived/deprecated scripts
│   └── [old scripts]     # Historical scripts
└── _archive/             # Old configuration backups
    └── pyproject.toml    # Old project config
```

## Quick Reference

### Essential Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `run_full_test_report.py` | **Complete test verification with markdown reports** | `python scripts/run_full_test_report.py` |
| `run_quick_tests.sh` | Interactive test menu | `./scripts/run_quick_tests.sh` |
| `setup/setup_project.sh` | Set up development environment | `bash scripts/setup/setup_project.sh` |
| `cli_verification_fixed.sh` | Verify CLI commands work | `bash scripts/cli_verification_fixed.sh` |
| `agent_memory_usage_example.py` | Memory agent usage example | `python scripts/agent_memory_usage_example.py` |

### Development Utilities

| Script | Purpose | Usage |
|--------|---------|-------|
| `utilities/check_collections.py` | Check ArangoDB collections | `python scripts/utilities/check_collections.py` |
| `utilities/iterate.py` | Task iteration helper | `python scripts/utilities/iterate.py` |
| `utilities/track_progress.py` | Track development progress | `python scripts/utilities/track_progress.py` |
| `utilities/serve_visualizations.py` | Start visualization server | `python scripts/utilities/serve_visualizations.py` |

### Testing Utilities

| Script | Purpose | Usage |
|--------|---------|-------|
| `testing/comprehensive_cli_test.py` | Full CLI test suite | `python scripts/testing/comprehensive_cli_test.py` |
| `testing/quick_cli_test.py` | Quick CLI verification | `python scripts/testing/quick_cli_test.py` |
| `testing/test_single_crud.py` | Test single CRUD operation | `python scripts/testing/test_single_crud.py` |

### Integration Tools

| Script | Purpose | Usage |
|--------|---------|-------|
| `integration/marker_integration.py` | Marker system integration | `python scripts/integration/marker_integration.py` |
| `integration/generate_full_mcp.py` | Generate MCP configuration | `python scripts/integration/generate_full_mcp.py` |

### Migration Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `migration/migrate_cli.py` | Migrate CLI structure | `python scripts/migration/migrate_cli.py` |
| `migration/migrate_to_bitemporal.py` | Migrate to bitemporal model | `python scripts/migration/migrate_to_bitemporal.py` |
| `migration/standardize_field_names.py` | Standardize field names | `python scripts/migration/standardize_field_names.py` |

## Running Scripts

### Python Scripts
```bash
# From project root
python scripts/[category]/script_name.py

# Examples
python scripts/utilities/check_collections.py
python scripts/testing/quick_cli_test.py
```

### Shell Scripts
```bash
# Make executable if needed
chmod +x scripts/script_name.sh

# Run
./scripts/script_name.sh

# Examples
./scripts/run_quick_tests.sh
bash scripts/setup/setup_project.sh
```

## Environment Setup

Most scripts require:
1. **Active virtual environment**
2. **ArangoDB running** (for database-related scripts)
3. **Project dependencies installed**

```bash
# Setup environment
source .venv/bin/activate  # or uv venv
uv pip install -e .
```

## Validation Scripts

The `validate/` directory contains scripts to validate different modules:
- Use these to verify specific functionality works correctly
- All follow the pattern: `validate_[module]_[function].py`
- Run with real data, never mocked

## Archived Scripts

The `archive/` directory contains:
- **Old test scripts** replaced by proper pytest tests
- **Debug scripts** used during development
- **Deprecated utilities** superseded by better implementations

These are kept for historical reference but should not be used.

## Adding New Scripts

When adding new scripts:
1. **Choose the right directory** based on purpose
2. **Follow naming conventions**: descriptive, lowercase with underscores
3. **Add documentation** in the script header
4. **Update this README** if it's a commonly used script
5. **Make executable** if it's a shell script: `chmod +x script.sh`

## Common Tasks

```bash
# Complete test verification with markdown report
python scripts/run_full_test_report.py

# Quick interactive test menu
./scripts/run_quick_tests.sh

# Quick smoke test only
python scripts/run_full_test_report.py --quick

# Check if ArangoDB is working
python scripts/utilities/check_collections.py

# Verify CLI commands
bash scripts/cli_verification_fixed.sh

# Start visualization server
python scripts/utilities/serve_visualizations.py

# Generate MCP configuration
python scripts/integration/generate_full_mcp.py
```

---

For more information about the project structure, see the main [README.md](../README.md) and [CLAUDE.md](../CLAUDE.md).