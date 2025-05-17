# ArangoDB Documentation

This directory contains all documentation for the ArangoDB Memory Agent System.

## Documentation Structure

```
docs/
├── README.md               # This file
├── GLOBAL_CODING_STANDARDS.md  # Project-wide development standards
├── SYSTEM_OVERVIEW.md      # System architecture and capabilities
├── api/                    # API documentation
│   └── python_api.md       # Python API reference
├── architecture/           # Architecture and design documents
│   ├── ARANGODB_FUNCTION_CHANGES.md
│   ├── ARANGO_USAGE.md
│   ├── EMBEDDING_DIMENSIONS.md
│   ├── TEMPORAL_RELATIONSHIPS_SUMMARY.md
│   └── ...
├── features/               # Feature documentation
│   └── community_detection.md
├── guides/                 # How-to guides and tutorials
│   ├── CLI_USAGE.md
│   ├── TASK_GUIDELINES.md
│   ├── TROUBLESHOOTING.md
│   └── ...
├── reports/               # Implementation reports
│   ├── 024_critical_graphiti_features_report.md
│   ├── CLEANUP_SUMMARY.md
│   └── ...
├── tasks/                 # Task specifications
│   └── ...
├── troubleshooting/       # Troubleshooting guides
│   └── APPROX_NEAR_COSINE_USAGE.md
└── archive/              # Archived documentation
```

## Key Documents

### Getting Started
- [System Overview](SYSTEM_OVERVIEW.md) - High-level architecture
- [Python API](api/python_api.md) - API reference
- [CLI Usage](guides/CLI_USAGE.md) - Command-line interface

### Development
- [Global Coding Standards](GLOBAL_CODING_STANDARDS.md) - Development guidelines
- [Task Guidelines](guides/TASK_GUIDELINES.md) - Task management
- [Troubleshooting](guides/TROUBLESHOOTING.md) - Common issues

### Architecture
- [ArangoDB Usage](architecture/ARANGO_USAGE.md) - Database patterns
- [Temporal Relationships](architecture/TEMPORAL_RELATIONSHIPS_SUMMARY.md) - Time-based data model
- [Embedding Dimensions](architecture/EMBEDDING_DIMENSIONS.md) - Vector search details

### Reports
- [Latest Reports](reports/) - Implementation and progress reports
- [Feature Reports](reports/024_critical_graphiti_features_report.md) - Feature completion status

## Contributing

When adding new documentation:
1. Place it in the appropriate subdirectory
2. Use clear, descriptive filenames
3. Update this README if adding a new major document
4. Follow markdown best practices