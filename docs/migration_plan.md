# ArangoDB Test Migration Plan

## Current Structure Analysis

### Validation Scripts to Migrate:
- validate_arango_setup.py -> tests/integration/test_arango_setup.py
- validate_db_connection.py -> tests/integration/test_db_connection.py
- validate_crud_commands.py -> tests/integration/test_crud_commands.py
- validate_graph_commands.py -> tests/integration/test_graph_commands.py
- validate_search_commands.py -> tests/integration/test_search_commands.py
- validate_bm25_search.py -> tests/integration/test_bm25_search.py
- validate_vector_search.py -> tests/integration/test_vector_search.py
- validate_memory_commands.py -> tests/integration/test_memory_commands.py
- validate_table_visualization.py -> tests/validation/test_table_visualization.py
- validate_main_cli.py -> tests/e2e/test_main_cli.py
- validate_cli_final.py -> tests/e2e/test_cli_final.py
- validate_all_commands.py -> tests/e2e/test_all_commands.py
- validate_all_modules_fixed.py -> tests/validation/test_all_modules.py
- quick_validation.py -> tests/smoke/test_quick_validation.py
- validate_constants.py -> tests/unit/test_constants.py

## New Directory Structure:
tests/
├── unit/               # Fast, isolated tests
├── integration/        # Component integration tests
├── validation/         # Output/data validation tests
├── e2e/               # End-to-end workflow tests
├── smoke/             # Quick sanity checks
└── performance/       # Performance benchmarks
