# SPARTA Threat Matrix Visualization

## Overview

This module implements an interactive D3.js visualization for the SPARTA (Space Attack Research and Tactic Analysis) threat matrix, as developed by The Aerospace Corporation. The visualization provides a comprehensive view of space-based cybersecurity threats, their relationships, and mitigation strategies.

## Features

### 1. Interactive Threat Matrix
- **Visual representation** of SPARTA tactics and techniques
- **Color-coded severity levels** (Critical, High, Medium, Low)
- **Hover tooltips** with detailed threat information
- **Click interactions** for expanded details

### 2. Threat Analytics
- **Risk scoring algorithm** combining impact, likelihood, and detection difficulty
- **System resilience metrics** based on countermeasure coverage
- **Critical attack path identification**
- **Threat distribution analysis**

### 3. Advanced Calculations
- **Composite risk scores** using weighted factors
- **Attack chain analysis** with cumulative risk assessment
- **Tactic coverage calculations**
- **Mitigation effectiveness scoring**

## Architecture

```
sparta/
├── __init__.py              # Module initialization
├── sparta_data.py           # SPARTA data structures and processor
├── threat_calculator.py     # Risk calculation algorithms
├── matrix_generator.py      # D3.js visualization generator
└── README.md               # This file
```

## Usage

### Basic Usage

```python
from arangodb.visualization.sparta import SPARTAMatrixGenerator

# Create generator
generator = SPARTAMatrixGenerator()

# Generate visualization
generator.generate_html_visualization("output.html", include_analytics=True)
```

### Data Processing

```python
from arangodb.visualization.sparta import SPARTADataProcessor

processor = SPARTADataProcessor()
matrix_data = processor.get_matrix_data()

# Get techniques for a specific tactic
recon_techniques = processor.get_technique_by_tactic("ST0001")

# Get high-severity techniques
critical_threats = processor.get_techniques_by_severity("critical")
```

### Threat Calculations

```python
from arangodb.visualization.sparta import ThreatCalculator

calculator = ThreatCalculator()

# Calculate risk for a technique
risk_score = calculator.calculate_risk_score(technique_data)

# Analyze attack chain
chain_analysis = calculator.analyze_attack_chain(technique_list)

# Calculate system resilience
resilience = calculator.calculate_system_resilience(matrix_data)
```

## SPARTA Framework

### Tactics (9 Total)
1. **ST0001 - Reconnaissance**: Gathering information about spacecraft
2. **ST0002 - Resource Development**: Establishing attack resources
3. **ST0003 - Initial Access**: Gaining spacecraft access
4. **ST0004 - Execution**: Running malicious code
5. **ST0005 - Persistence**: Maintaining foothold
6. **ST0006 - Defense Evasion**: Avoiding detection
7. **ST0007 - Lateral Movement**: Moving across subsystems
8. **ST0008 - Exfiltration**: Stealing information
9. **ST0009 - Impact**: Disrupting operations

### Risk Calculation Algorithm

```
Risk Score = (Impact × Likelihood × Detection Difficulty) / Mitigation Effectiveness

Where:
- Impact: Based on severity (Critical=1.0, High=0.75, Medium=0.5, Low=0.25)
- Likelihood: Inverse of exploitation complexity
- Detection Difficulty: How hard to detect (Very Hard=1.0 to Very Easy=0.2)
- Mitigation: Based on number of countermeasures
```

## Visualization Features

### Interactive Elements
- **Hover Effects**: Detailed technique information on hover
- **Click Actions**: Expand for countermeasures and examples
- **Filtering**: Filter by severity, tactic, or risk level
- **Search**: Find specific techniques or keywords

### Analytics Dashboard
- **System Resilience Score**: Overall security posture
- **Threat Distribution**: Breakdown by severity
- **Critical Paths**: Most dangerous attack sequences
- **Coverage Metrics**: Protected vs. unprotected techniques

## Data Sources

The SPARTA data is based on:
- The Aerospace Corporation SPARTA Framework (v2.0)
- Space-specific threat research
- Real-world spacecraft security incidents
- Academic and industry publications

## Integration with ArangoDB

The visualization can be integrated with the ArangoDB memory bank to:
- Store threat intelligence data
- Track security incidents
- Build knowledge graphs of attack patterns
- Generate dynamic threat assessments

## Future Enhancements

1. **Real-time Threat Updates**: Connect to threat intelligence feeds
2. **Custom Threat Scenarios**: User-defined attack chains
3. **Export Capabilities**: PDF reports, PowerPoint slides
4. **Machine Learning**: Predictive threat analysis
5. **Integration with MITRE ATT&CK**: Cross-reference mappings

## References

- [The Aerospace Corporation SPARTA](https://sparta.aerospace.org)
- [Understanding Space-Cyber Threats with SPARTA](https://aerospace.org/article/understanding-space-cyber-threats-sparta-matrix)
- [MITRE ATT&CK Framework](https://attack.mitre.org)

## Contributing

To add new techniques or update threat data:
1. Edit `sparta_data.py` to add techniques
2. Update severity and complexity ratings
3. Add countermeasures and examples
4. Run tests to ensure data integrity
5. Generate new visualization

## License

This implementation follows the same license as the main ArangoDB project.
