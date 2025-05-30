# Check ArangoDB Module Status

Check the status of ArangoDB module and connections.

## Usage

```bash
arango module-status [--collections] [--connections] [--metrics]
```

## Arguments

- `--collections`: Show collection statistics
- `--connections`: Show module connections
- `--metrics`: Show performance metrics

## Examples

```bash
# Basic status
/arango-module-status

# With collections
/arango-module-status --collections

# Full metrics
/arango-module-status --metrics
```

---
*ArangoDB Module*
