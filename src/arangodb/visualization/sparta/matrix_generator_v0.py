"""
SPARTA Matrix Generator with Vercel V0 Design System
Modern, responsive, interactive visualization following 2025 style guide

Module: matrix_generator_v0.py
"""

from typing import Dict, List, Any, Optional
import json
from pathlib import Path
from datetime import datetime
from .sparta_data import SPARTADataProcessor
from .threat_calculator import ThreatCalculator

class SPARTAMatrixGeneratorV0:
    """Generate SPARTA threat matrix with Vercel V0 design aesthetics"""
    
    def __init__(self):
        self.data_processor = SPARTADataProcessor()
        self.threat_calculator = ThreatCalculator()
        self.template_path = Path(__file__).parent / "v0_matrix_template.html"
        
    def generate_v0_visualization(self, output_path: str) -> str:
        """Generate modern V0-styled visualization"""
        # Get enhanced matrix data
        matrix_data = self.data_processor.get_matrix_data()
        
        # Enhance with calculations
        enhanced_data = self._enhance_matrix_data(matrix_data)
        
        # Generate HTML from template
        html_content = self._generate_v0_html(enhanced_data)
        
        # Write output
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_path
    
    def _enhance_matrix_data(self, matrix_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance matrix data with calculations and analytics"""
        # Calculate metrics for each technique
        enhanced_techniques = []
        for tech in matrix_data["techniques"]:
            metrics = self.threat_calculator.calculate_threat_metrics(tech)
            tech_enhanced = tech.copy()
            tech_enhanced.update({
                "risk_score": metrics.risk_score,
                "impact_score": metrics.impact_score,
                "likelihood_score": metrics.likelihood_score,
                "detection_score": metrics.detection_score,
                "mitigation_effectiveness": metrics.mitigation_effectiveness
            })
            enhanced_techniques.append(tech_enhanced)
        
        matrix_data["techniques"] = enhanced_techniques
        
        # Add comprehensive analytics
        matrix_data["analytics"] = {
            "tactic_coverage": self.threat_calculator.calculate_tactic_coverage(enhanced_techniques),
            "system_resilience": self.threat_calculator.calculate_system_resilience(matrix_data),
            "critical_paths": self.threat_calculator.identify_critical_paths(matrix_data),
            "threat_heatmap": self.threat_calculator.generate_threat_heatmap(matrix_data),
            "threat_distribution": self._calculate_threat_distribution(enhanced_techniques),
            "top_threats": self._get_top_threats(enhanced_techniques, limit=10),
            "mitigation_coverage": self._calculate_mitigation_coverage(enhanced_techniques)
        }
        
        return matrix_data
    
    def _calculate_threat_distribution(self, techniques: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate distribution of threats by severity"""
        distribution = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0
        }
        
        for tech in techniques:
            severity = tech.get("severity", "medium")
            distribution[severity] += 1
        
        return distribution
    
    def _get_top_threats(self, techniques: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
        """Get top threats by risk score"""
        sorted_threats = sorted(techniques, key=lambda t: t.get("risk_score", 0), reverse=True)
        return sorted_threats[:limit]
    
    def _calculate_mitigation_coverage(self, techniques: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate mitigation coverage statistics"""
        total = len(techniques)
        with_mitigations = sum(1 for t in techniques if len(t.get("countermeasures", [])) > 0)
        
        by_severity = {}
        for severity in ["critical", "high", "medium", "low"]:
            severity_techniques = [t for t in techniques if t.get("severity") == severity]
            severity_with_mitigation = sum(1 for t in severity_techniques if len(t.get("countermeasures", [])) > 0)
            
            by_severity[severity] = {
                "total": len(severity_techniques),
                "mitigated": severity_with_mitigation,
                "percentage": (severity_with_mitigation / len(severity_techniques) * 100) if severity_techniques else 0
            }
        
        return {
            "overall_percentage": (with_mitigations / total * 100) if total > 0 else 0,
            "total_techniques": total,
            "techniques_with_mitigation": with_mitigations,
            "by_severity": by_severity
        }
    
    def _generate_v0_html(self, matrix_data: Dict[str, Any]) -> str:
        """Generate HTML content with V0 design system"""
        # Read template
        template_content = self._read_template()
        
        # Replace placeholder with actual data
        data_json = json.dumps(matrix_data, indent=2)
        html_content = template_content.replace(
            "const matrixData = {{ matrix_data | tojson }};",
            f"const matrixData = {data_json};"
        )
        
        return html_content
    
    def _read_template(self) -> str:
        """Read the V0 HTML template"""
        # For now, return a simplified template
        # In production, this would read from the v0_matrix_template.html file
        return self._get_v0_template()
    
    def _get_v0_template(self) -> str:
        """Get the V0-styled HTML template"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SPARTA Space Cybersecurity Threat Matrix</title>
    
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    
    <!-- Inter Font -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    
    <!-- D3.js -->
    <script src="https://d3js.org/d3.v7.min.js"></script>
    
    <style>
        :root {
            --color-primary-start: #4F46E5;
            --color-primary-end: #6366F1;
            --color-secondary: #6B7280;
            --color-background: #F9FAFB;
            --color-accent: #10B981;
            --font-family-base: 'Inter', system-ui, sans-serif;
            --border-radius-base: 8px;
            --transition-duration: 250ms;
            --transition-timing: cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        * {
            font-family: var(--font-family-base);
        }
        
        body {
            background: linear-gradient(180deg, #F9FAFB 0%, #F3F4F6 100%);
            min-height: 100vh;
        }
        
        .gradient-primary {
            background: linear-gradient(135deg, var(--color-primary-start) 0%, var(--color-primary-end) 100%);
        }
        
        .card-hover:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
        }
        
        .matrix-cell {
            transition: all 200ms ease-in-out;
            cursor: pointer;
        }
        
        .matrix-cell:hover {
            filter: brightness(1.1);
            transform: scale(1.02);
        }
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #F3F4F6;
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #D1D5DB;
            border-radius: 4px;
        }
    </style>
</head>
<body class="antialiased text-gray-900">
    <!-- Header -->
    <header class="sticky top-0 z-50 bg-white/90 backdrop-blur-lg border-b border-gray-100">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex items-center justify-between h-16">
                <div class="flex items-center space-x-4">
                    <div class="flex items-center space-x-2">
                        <div class="w-8 h-8 gradient-primary rounded-lg flex items-center justify-center">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
                                <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z"/>
                            </svg>
                        </div>
                        <h1 class="text-xl font-semibold">SPARTA Matrix</h1>
                    </div>
                    <span class="text-sm text-gray-500">v2.0</span>
                </div>
            </div>
        </div>
    </header>
    
    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <!-- Stats Grid -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div class="bg-white rounded-xl shadow-sm p-6 card-hover">
                <h3 class="text-sm text-gray-500 mb-1">System Resilience</h3>
                <p class="text-2xl font-bold text-gray-900" id="resilience-score">--</p>
            </div>
            <div class="bg-white rounded-xl shadow-sm p-6 card-hover">
                <h3 class="text-sm text-gray-500 mb-1">Total Techniques</h3>
                <p class="text-2xl font-bold text-gray-900" id="total-techniques">--</p>
            </div>
            <div class="bg-white rounded-xl shadow-sm p-6 card-hover">
                <h3 class="text-sm text-gray-500 mb-1">Critical Threats</h3>
                <p class="text-2xl font-bold text-red-600" id="critical-threats">--</p>
            </div>
            <div class="bg-white rounded-xl shadow-sm p-6 card-hover">
                <h3 class="text-sm text-gray-500 mb-1">Coverage</h3>
                <p class="text-2xl font-bold text-green-600" id="coverage">--</p>
            </div>
        </div>
        
        <!-- Matrix Container -->
        <div class="bg-white rounded-xl shadow-sm p-6">
            <h2 class="text-2xl font-semibold mb-6">SPARTA Threat Matrix</h2>
            <div id="matrix-container" class="overflow-x-auto">
                <svg id="sparta-matrix"></svg>
            </div>
        </div>
    </main>
    
    <script>
        // Matrix data will be injected here
        const matrixData = {{ matrix_data | tojson }};
        
        // Initialize on load
        document.addEventListener('DOMContentLoaded', () => {
            updateStats();
            renderMatrix();
        });
        
        function updateStats() {
            const analytics = matrixData.analytics;
            const resilience = analytics.system_resilience;
            
            document.getElementById('resilience-score').textContent = resilience.weighted_resilience_score.toFixed(1) + '%';
            document.getElementById('total-techniques').textContent = matrixData.techniques.length;
            document.getElementById('critical-threats').textContent = matrixData.techniques.filter(t => t.severity === 'critical').length;
            document.getElementById('coverage').textContent = resilience.coverage_percentage.toFixed(1) + '%';
        }
        
        function renderMatrix() {
            const container = document.getElementById('matrix-container');
            const width = container.clientWidth;
            const height = 600;
            
            const svg = d3.select('#sparta-matrix')
                .attr('width', width)
                .attr('height', height);
            
            const margin = {top: 100, right: 40, bottom: 40, left: 40};
            const innerWidth = width - margin.left - margin.right;
            const innerHeight = height - margin.top - margin.bottom;
            
            const g = svg.append('g')
                .attr('transform', `translate(${margin.left},${margin.top})`);
            
            // Calculate dimensions
            const tacticWidth = innerWidth / matrixData.tactics.length;
            const cellHeight = 40;
            
            // Create gradient
            const defs = svg.append('defs');
            const gradient = defs.append('linearGradient')
                .attr('id', 'tacticGradient')
                .attr('x1', '0%')
                .attr('x2', '100%');
            
            gradient.append('stop')
                .attr('offset', '0%')
                .style('stop-color', '#4F46E5');
            
            gradient.append('stop')
                .attr('offset', '100%')
                .style('stop-color', '#6366F1');
            
            // Render tactics
            const tactics = g.selectAll(\.tactic')
                .data(matrixData.tactics)
                .enter()
                .append('g')
                .attr('transform', (d, i) => `translate(${i * tacticWidth}, 0)`);
            
            tactics.append('rect')
                .attr('width', tacticWidth - 4)
                .attr('height', 60)
                .attr('rx', 8)
                .attr('fill', 'url(#tacticGradient)');
            
            tactics.append('text')
                .attr('x', tacticWidth / 2)
                .attr('y', 30)
                .attr('text-anchor', 'middle')
                .attr('fill', 'white')
                .attr('font-weight', '600')
                .attr('font-size', '14px')
                .text(d => d.name);
            
            // Render techniques
            matrixData.tactics.forEach((tactic, tacticIndex) => {
                const techniques = matrixData.techniques.filter(t => t.tactic_id === tactic.id);
                
                g.selectAll(`.technique-${tactic.id}`)
                    .data(techniques)
                    .enter()
                    .append('rect')
                    .attr('x', tacticIndex * tacticWidth)
                    .attr('y', (d, i) => 80 + i * (cellHeight + 4))
                    .attr('width', tacticWidth - 4)
                    .attr('height', cellHeight)
                    .attr('rx', 6)
                    .attr('fill', d => getSeverityColor(d.severity))
                    .attr('class', 'matrix-cell')
                    .on('mouseover', showTooltip)
                    .on('mouseout', hideTooltip);
            });
        }
        
        function getSeverityColor(severity) {
            const colors = {
                critical: '#DC2626',
                high: '#F59E0B',
                medium: '#3B82F6',
                low: '#10B981'
            };
            return colors[severity] || '#6B7280';
        }
        
        function showTooltip(event, d) {
            // Implement tooltip
        }
        
        function hideTooltip() {
            // Hide tooltip
        }
    </script>
</body>
</html>"""

    def generate_interactive_features(self) -> Dict[str, Any]:
        """Generate configuration for interactive features"""
        return {
            "search": {
                "enabled": True,
                "fields": ["name", "description", "id", "examples", "countermeasures"],
                "fuzzy": True
            },
            "filters": {
                "severity": ["all", "critical", "high", "medium", "low"],
                "detection": ["all", "very_hard", "hard", "medium", "easy", "very_easy"],
                "complexity": ["all", "very_high", "high", "medium", "low", "very_low"]
            },
            "views": {
                "grid": "Traditional matrix grid view",
                "heatmap": "Risk-based heatmap visualization",
                "list": "Sortable table view",
                "graph": "Network graph of relationships"
            },
            "export": {
                "formats": ["json", "csv", "pdf", "pptx"],
                "customizable": True
            },
            "animations": {
                "transitions": "250ms cubic-bezier(0.4, 0, 0.2, 1)",
                "hover_effects": True,
                "loading_states": True
            }
        }
