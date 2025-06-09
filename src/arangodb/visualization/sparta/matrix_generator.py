"""
SPARTA Matrix Generator - Generate enhanced D3.js visualizations

Module: matrix_generator.py
"""

from typing import Dict, List, Any, Optional
import json
from pathlib import Path
from datetime import datetime
from .sparta_data import SPARTADataProcessor
from .threat_calculator import ThreatCalculator

class SPARTAMatrixGenerator:
    """Generate SPARTA threat matrix visualizations with D3.js"""
    
    def __init__(self):
        self.data_processor = SPARTADataProcessor()
        self.threat_calculator = ThreatCalculator()
        self.template_path = Path(__file__).parent.parent / "templates" / "sparta" / "threat_matrix.html"
        
    def generate_enhanced_matrix_data(self) -> Dict[str, Any]:
        """Generate enhanced matrix data with calculated metrics"""
        # Get base matrix data
        matrix_data = self.data_processor.get_matrix_data()
        
        # Enhance techniques with calculated metrics
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
        
        # Add analytics
        matrix_data["analytics"] = {
            "tactic_coverage": self.threat_calculator.calculate_tactic_coverage(enhanced_techniques),
            "system_resilience": self.threat_calculator.calculate_system_resilience(matrix_data),
            "critical_paths": self.threat_calculator.identify_critical_paths(matrix_data),
            "threat_heatmap": self.threat_calculator.generate_threat_heatmap(matrix_data)
        }
        
        return matrix_data
    
    def generate_html_visualization(self, output_path: str, include_analytics: bool = True) -> str:
        """Generate complete HTML visualization file"""
        # Get enhanced matrix data
        matrix_data = self.generate_enhanced_matrix_data()
        
        # Read template
        with open(self.template_path, 'r') as f:
            template = f.read()
        
        # Inject data into template
        # Find the placeholder and replace it
        placeholder = "const matrixData = {{ matrix_data | tojson }};"
        data_injection = f"const matrixData = {json.dumps(matrix_data, indent=2)};"
        
        html_content = template.replace(placeholder, data_injection)
        
        # Add analytics dashboard if requested
        if include_analytics:
            analytics_html = self._generate_analytics_section(matrix_data["analytics"])
            # Insert before closing body tag
            html_content = html_content.replace("</body>", f"{analytics_html}</body>")
        
        # Write output file
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        return output_path
    
    def _generate_analytics_section(self, analytics: Dict[str, Any]) -> str:
        """Generate HTML for analytics dashboard"""
        resilience = analytics["system_resilience"]
        
        html = """
    <div class="analytics-container" style="max-width: 1400px; margin: 20px auto; background: #1a1a1a; border-radius: 10px; padding: 20px; box-shadow: 0 0 30px rgba(0, 100, 255, 0.3);">
        <h2 style="color: #4a9eff; text-align: center;">SPARTA Threat Analytics</h2>
        
        <div class="analytics-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 20px;">
            
            <div class="analytics-card" style="background: #2a2a2a; padding: 15px; border-radius: 8px; border: 1px solid #333;">
                <h3 style="color: #4a9eff; margin-bottom: 10px;">System Resilience</h3>
                <div class="resilience-score" style="font-size: 48px; color: #4a9eff; text-align: center;">
                    {resilience_score}%
                </div>
                <div style="color: #888; font-size: 14px; margin-top: 10px;">
                    <p>Coverage: {coverage}%</p>
                    <p>Avg Countermeasures: {avg_counter}</p>
                    <p>Protected Techniques: {protected}/{total}</p>
                </div>
            </div>
            
            <div class="analytics-card" style="background: #2a2a2a; padding: 15px; border-radius: 8px; border: 1px solid #333;">
                <h3 style="color: #4a9eff; margin-bottom: 10px;">Critical Attack Paths</h3>
                <div id="critical-paths" style="color: #ccc;">
                    {paths_html}
                </div>
            </div>
            
            <div class="analytics-card" style="background: #2a2a2a; padding: 15px; border-radius: 8px; border: 1px solid #333;">
                <h3 style="color: #4a9eff; margin-bottom: 10px;">Threat Distribution</h3>
                <canvas id="threat-chart" width="300" height="200"></canvas>
            </div>
            
        </div>
    </div>
    
    <script>
        // Add threat distribution chart
        const threatCanvas = document.getElementById('threat-chart');
        if (threatCanvas) {{
            const ctx = threatCanvas.getContext('2d');
            // Simple bar chart for threat distribution
            const threats = matrixData.techniques;
            const severityCounts = {{
                critical: threats.filter(t => t.severity === 'critical').length,
                high: threats.filter(t => t.severity === 'high').length,
                medium: threats.filter(t => t.severity === 'medium').length,
                low: threats.filter(t => t.severity === 'low').length
            }};
            
            // Draw simple bar chart
            const colors = {{
                critical: '#5a1f1f',
                high: '#4a2f1f',
                medium: '#3a3f1f',
                low: '#1f3a1f'
            }};
            
            let x = 20;
            const barWidth = 60;
            const maxHeight = 150;
            const maxCount = Math.max(...Object.values(severityCounts));
            
            Object.entries(severityCounts).forEach(([severity, count]) => {{
                const height = (count / maxCount) * maxHeight;
                ctx.fillStyle = colors[severity];
                ctx.fillRect(x, 180 - height, barWidth, height);
                
                ctx.fillStyle = '#ccc';
                ctx.font = '12px Arial';
                ctx.textAlign = 'center';
                ctx.fillText(severity, x + barWidth/2, 195);
                ctx.fillText(count, x + barWidth/2, 175 - height);
                
                x += barWidth + 20;
            }});
        }}
    </script>
        """.format(
            resilience_score=resilience["weighted_resilience_score"],
            coverage=resilience["coverage_percentage"],
            avg_counter=resilience["average_countermeasures_per_technique"],
            protected=resilience["techniques_with_countermeasures"],
            total=resilience["total_techniques"],
            paths_html=self._format_critical_paths(analytics["critical_paths"])
        )
        
        return html
    
    def _format_critical_paths(self, paths: List[List[str]]) -> str:
        """Format critical paths for display"""
        if not paths:
            return "<p>No critical paths identified</p>"
        
        html_parts = []
        for i, path in enumerate(paths, 1):
            path_str = " → ".join(path)
            html_parts.append(f"<p style='margin: 5px 0;'><strong>Path {i}:</strong> {path_str}</p>")
        
        return "".join(html_parts)
    
    def export_matrix_data(self, output_path: str, format: str = "json") -> str:
        """Export matrix data in various formats"""
        matrix_data = self.generate_enhanced_matrix_data()
        
        if format == "json":
            with open(output_path, 'w') as f:
                json.dump(matrix_data, f, indent=2)
        elif format == "csv":
            # Export techniques as CSV
            import csv
            with open(output_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "ID", "Name", "Tactic", "Severity", "Risk Score",
                    "Detection Difficulty", "Exploitation Complexity",
                    "Countermeasures Count"
                ])
                for tech in matrix_data["techniques"]:
                    writer.writerow([
                        tech["id"],
                        tech["name"],
                        tech["tactic_id"],
                        tech["severity"],
                        tech.get("risk_score", "N/A"),
                        tech["detection_difficulty"],
                        tech["exploitation_complexity"],
                        len(tech["countermeasures"])
                    ])
        
        return output_path
    
    def generate_interactive_features(self) -> Dict[str, str]:
        """Generate JavaScript code for interactive features"""
        return {
            "attack_chain_simulator": """
                function simulateAttackChain(techniques) {
                    // Animate attack chain progression
                    techniques.forEach((techId, index) => {
                        setTimeout(() => {
                            d3.select(`#tech-${techId}`)
                                .transition()
                                .duration(500)
                                .style("fill", "#ff4444")
                                .transition()
                                .duration(500)
                                .style("fill", null);
                        }, index * 1000);
                    });
                }
            """,
            "threat_filter": """
                function filterBySeverity(severity) {
                    d3.selectAll(".technique-cell")
                        .style("opacity", d => d.severity === severity ? 1 : 0.2);
                }
            """,
            "countermeasure_overlay": """
                function showCountermeasures(techniqueId) {
                    const tech = matrixData.techniques.find(t => t.id === techniqueId);
                    if (tech && tech.countermeasures) {
                        // Display countermeasures in overlay
                        const overlay = d3.select("body").append("div")
                            .attr("class", "countermeasure-overlay")
                            .style("position", "fixed")
                            .style("top", "50%")
                            .style("left", "50%")
                            .style("transform", "translate(-50%, -50%)")
                            .style("background", "rgba(0,0,0,0.9)")
                            .style("padding", "20px")
                            .style("border-radius", "10px")
                            .style("z-index", "1000");
                        
                        overlay.append("h3").text("Countermeasures for " + tech.name);
                        const list = overlay.append("ul");
                        tech.countermeasures.forEach(cm => {
                            list.append("li").text(cm);
                        });
                        
                        overlay.on("click", function() { d3.select(this).remove(); });
                    }
                }
            """
        }
