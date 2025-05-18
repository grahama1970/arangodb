# ArangoDB Memory Bank Documentation

Welcome to the ArangoDB Memory Bank documentation. This guide helps you navigate our documentation structure.

## 📍 Documentation Map

```
docs/
├── 🏠 INDEX.md              # Start here - Documentation index
├── 📢 BETA_ANNOUNCEMENT.md  # Beta release announcement
├── 📋 BETA_RELEASE_NOTES.md # Detailed release notes
├── 💡 CAPABILITIES_AND_LIMITATIONS.md # Feature status
├── 🏗️ SYSTEM_OVERVIEW.md   # Architecture overview
├── 📐 GLOBAL_CODING_STANDARDS.md # Development standards
│
├── api/
│   └── python_api.md       # Python API reference
│
├── architecture/          # Technical architecture docs
│   ├── ARANGO_USAGE.md    # ArangoDB specifics
│   ├── COLLECTION_SCHEMAS.md # Data schemas
│   ├── EMBEDDING_OPERATIONS.md # Vector handling
│   └── FIXED_SEMANTIC_SEARCH.md # Search implementation
│
├── design/               # Design documents
│   └── cli_consistency_final_report.md
│
├── features/             # Feature documentation
│   └── community_detection.md
│
├── feedback/             # User feedback & analysis
│   ├── 004_graphiti_parity_analysis.md
│   └── 005_memory_conversation_comparison.md
│
├── guides/               # How-to guides
│   ├── BETA_TESTING_GUIDE.md # Beta testing guide
│   ├── TEMPORAL_MODEL_GUIDE.md # Bi-temporal features
│   ├── TASK_GUIDELINES.md # Development process
│   └── TROUBLESHOOTING.md # Problem solving
│
├── reports/              # Status reports
│   ├── 025_cli_validation_report.md
│   ├── 026_field_standardization_complete.md
│   ├── 027_view_optimization_complete.md
│   └── README.md         # Reports index
│
├── tasks/                # Development tasks
│   └── [Task files...]   # Active development tasks
│
├── troubleshooting/      # Specific issues
│   └── APPROX_NEAR_COSINE_USAGE.md
│
├── usage/                # User guides
│   ├── CLI_GUIDE.md      # CLI reference
│   ├── quick_reference_guide.md # Quick commands
│   └── agent_integration_guide.md # AI integration
│
└── archive/              # Historical docs
    └── iteration1/       # Old iteration docs
```

## 🚀 Quick Links

### New Users
1. [Beta Announcement](BETA_ANNOUNCEMENT.md) - Start here
2. [System Overview](SYSTEM_OVERVIEW.md) - Understand the system
3. [CLI Guide](usage/CLI_GUIDE.md) - Learn commands
4. [Python API](api/python_api.md) - Programming interface

### Developers
1. [Global Coding Standards](GLOBAL_CODING_STANDARDS.md) - Code style
2. [Task Guidelines](guides/TASK_GUIDELINES.md) - Development process
3. [Architecture Docs](architecture/) - Technical details

### Troubleshooting
1. [General Guide](guides/TROUBLESHOOTING.md) - Common issues
2. [Database Issues](architecture/ARANGODB_TROUBLESHOOTING.md) - ArangoDB
3. [Search Problems](architecture/SEARCH_API_ISSUES.md) - Search issues

## 📂 Finding Information

### By Topic
- **Getting Started**: See [INDEX.md](INDEX.md)
- **CLI Commands**: See [CLI_GUIDE.md](usage/CLI_GUIDE.md)
- **API Reference**: See [python_api.md](api/python_api.md)
- **Architecture**: See [architecture/](architecture/)
- **Troubleshooting**: See [guides/TROUBLESHOOTING.md](guides/TROUBLESHOOTING.md)

### By User Type
- **End Users**: Start with [usage/](usage/)
- **Developers**: Start with [guides/](guides/)
- **Beta Testers**: Start with [BETA_TESTING_GUIDE.md](guides/BETA_TESTING_GUIDE.md)

### By Task
- **Install/Setup**: See [BETA_RELEASE_NOTES.md](BETA_RELEASE_NOTES.md)
- **Learn Commands**: See [CLI_GUIDE.md](usage/CLI_GUIDE.md)
- **Integrate**: See [agent_integration_guide.md](usage/agent_integration_guide.md)
- **Develop**: See [TASK_GUIDELINES.md](guides/TASK_GUIDELINES.md)

## 🔍 Recent Updates
- Consolidated CLI documentation into single guide
- Reorganized documentation structure for clarity
- Archived outdated iteration 1 documents
- Updated INDEX.md with clearer navigation

Last Updated: 2025-05-18