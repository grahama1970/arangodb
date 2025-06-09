"""
SPARTA threat matrix CLI commands

Module: sparta_commands.py
Description: Functions for sparta commands operations
"""

import typer
from typing import Optional
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
import json

# Import SPARTA modules
from ..visualization.sparta import (
    SPARTADataProcessor,
    ThreatCalculator,
    SPARTAMatrixGenerator
)
from ..visualization.sparta.sparta_data_enhanced import (
    EnhancedSPARTADataProcessor,
    ThreatActorType
)
from ..visualization.sparta.matrix_generator_v0 import SPARTAMatrixGeneratorV0

app = typer.Typer(help="SPARTA Space Cybersecurity Threat Matrix Commands")
console = Console()

@app.command()
def generate(
    output_path: str = typer.Option("visualizations/sparta/sparta_matrix.html", help="Output file path"),
    enhanced: bool = typer.Option(False, help="Use enhanced data processor"),
    v0_style: bool = typer.Option(True, help="Use Vercel V0 design style"),
    include_analytics: bool = typer.Option(True, help="Include analytics dashboard")
):
    """Generate SPARTA threat matrix visualization"""
    console.print(Panel("️ SPARTA Threat Matrix Generator", style="bold blue"))
    
    try:
        # Create output directory
        output_dir = Path(output_path).parent
        output_dir.mkdir(exist_ok=True, parents=True)
        
        if v0_style:
            console.print("Using Vercel V0 design system...", style="cyan")
            generator = SPARTAMatrixGeneratorV0()
            result = generator.generate_v0_visualization(output_path)
        else:
            console.print("Using standard visualization...", style="cyan")
            generator = SPARTAMatrixGenerator()
            result = generator.generate_html_visualization(output_path, include_analytics)
        
        console.print(f" Visualization generated: {result}", style="green")
        
    except Exception as e:
        console.print(f" Error: {str(e)}", style="red")
        raise typer.Exit(1)


@app.command()
def stats():
    """Display SPARTA matrix statistics"""
    console.print(Panel(" SPARTA Matrix Statistics", style="bold blue"))
    
    # Use enhanced processor for more data
    processor = EnhancedSPARTADataProcessor()
    calculator = ThreatCalculator()
    
    data = processor.get_enhanced_matrix_data()
    
    # Basic stats
    console.print("Total Tactics: [bold cyan]{}[/bold cyan]".format(data["metadata"]["total_tactics"]))
    console.print("Total Techniques: [bold cyan]{}[/bold cyan]".format(data["metadata"]["total_techniques"]))
    console.print("Total Mappings: [bold cyan]{}[/bold cyan]".format(data["metadata"]["total_mappings"]))
    
    # Severity distribution
    severity_table = Table(title="Threat Severity Distribution", box=box.ROUNDED)
    severity_table.add_column("Severity", style="cyan")
    severity_table.add_column("Count", justify="right")
    severity_table.add_column("Percentage", justify="right")
    
    total_techniques = len(processor.TECHNIQUES)
    for severity in ["critical", "high", "medium", "low"]:
        count = len([t for t in processor.TECHNIQUES if t.severity == severity])
        percentage = (count / total_techniques * 100) if total_techniques > 0 else 0
        severity_table.add_row(
            severity.capitalize(),
            str(count),
            f"{percentage:.1f}%"
        )
    
    console.print(severity_table)
    
    # Actor distribution
    actor_table = Table(title="Threat Actor Coverage", box=box.ROUNDED)
    actor_table.add_column("Actor Type", style="cyan")
    actor_table.add_column("Techniques", justify="right")
    
    for actor_type in ThreatActorType:
        techniques = processor.get_techniques_by_actor(actor_type)
        actor_table.add_row(
            actor_type.value.replace("_", " ").title(),
            str(len(techniques))
        )
    
    console.print(actor_table)
    
    # System resilience
    matrix_data = processor.get_enhanced_matrix_data()
    enhanced_techniques = []
    for tech in matrix_data["techniques"]:
        metrics = calculator.calculate_threat_metrics(tech)
        tech["risk_score"] = metrics.risk_score
        enhanced_techniques.append(tech)
    
    matrix_data["techniques"] = enhanced_techniques
    resilience = calculator.calculate_system_resilience(matrix_data)
    
    console.print(Panel(
                "System Resilience Score: [bold green]{:.1f}%[/bold green]\n".format(resilience["weighted_resilience_score"]) +
                "Coverage: {:.1f}%\n".format(resilience["coverage_percentage"]) +
                "Average Countermeasures: {:.1f}".format(resilience["average_countermeasures_per_technique"]),
        title="System Resilience",
        style="green"
    ))


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    field: str = typer.Option("all", help="Field to search: all, name, description, id")
):
    """Search for techniques in SPARTA matrix"""
    console.print(f" Searching for: [bold]{query}[/bold]")
    
    processor = EnhancedSPARTADataProcessor()
    results = []
    
    query_lower = query.lower()
    
    for tech in processor.TECHNIQUES:
        if field == "all":
            if (query_lower in tech.name.lower() or
                query_lower in tech.description.lower() or
                query_lower in tech.id.lower() or
                any(query_lower in ex.lower() for ex in tech.examples) or
                any(query_lower in cm.lower() for cm in tech.countermeasures)):
                results.append(tech)
        elif field == "name" and query_lower in tech.name.lower():
            results.append(tech)
        elif field == "description" and query_lower in tech.description.lower():
            results.append(tech)
        elif field == "id" and query_lower in tech.id.lower():
            results.append(tech)
    
    if results:
        console.print(f"\nFound {len(results)} results:")
        
        for tech in results:
            panel_content = f"[bold]ID:[/bold] {tech.id}\n"
            panel_content += f"[bold]Name:[/bold] {tech.name}\n"
            panel_content += f"[bold]Severity:[/bold] {tech.severity}\n"
            panel_content += f"[bold]Description:[/bold] {tech.description}\n"
            panel_content += f"[bold]Tactics:[/bold] {', '.join(tech.tactic_ids)}"
            
            style = {
                "critical": "red",
                "high": "yellow",
                "medium": "blue",
                "low": "green"
            }.get(tech.severity, "white")
            
            console.print(Panel(panel_content, title=tech.name, style=style, box=box.ROUNDED))
    else:
        console.print("No results found.", style="yellow")


@app.command()
def export(
    output_path: str = typer.Argument(..., help="Output file path"),
    format: str = typer.Option("json", help="Export format: json, csv")
):
    """Export SPARTA matrix data"""
    console.print(f" Exporting to {format.upper()} format...")
    
    try:
        generator = SPARTAMatrixGenerator()
        generator.export_matrix_data(output_path, format=format)
        console.print(f" Exported to: {output_path}", style="green")
    except Exception as e:
        console.print(f" Error: {str(e)}", style="red")
        raise typer.Exit(1)


@app.command()
def scenarios():
    """Display attack scenarios"""
    console.print(Panel(" SPARTA Attack Scenarios", style="bold red"))
    
    processor = EnhancedSPARTADataProcessor()
    scenarios = processor.generate_attack_scenarios()
    
    for scenario in scenarios:
        # Create scenario panel
        content = f"[bold]Description:[/bold] {scenario['description']}\n"
        content += f"[bold]Actor:[/bold] {scenario['actor']}\n"
        content += f"[bold]Impact:[/bold] {scenario['impact']}\n"
        content += f"[bold]Likelihood:[/bold] {scenario['likelihood']}\n"
        content += f"[bold]Mitigation Priority:[/bold] {scenario['mitigation_priority']}\n\n"
        content += f"[bold]Attack Chain:[/bold]\n"
        
        for i, tech_id in enumerate(scenario['techniques'], 1):
            tech = processor.techniques_map.get(tech_id)
            if tech:
                content += f"  {i}. [{tech.severity}] {tech_id}: {tech.name}\n"
        
        style = {
            "critical": "red",
            "high": "yellow",
            "medium": "blue"
        }.get(scenario['mitigation_priority'], "white")
        
        console.print(Panel(content, title=scenario['name'], style=style, box=box.ROUNDED))


@app.command()
def analyze(
    technique_ids: str = typer.Argument(..., help="Comma-separated technique IDs for attack chain")
):
    """Analyze an attack chain"""
    console.print(Panel(" Attack Chain Analysis", style="bold yellow"))
    
    processor = SPARTADataProcessor()
    calculator = ThreatCalculator()
    
    # Parse technique IDs
    tech_ids = [tid.strip() for tid in technique_ids.split(",")]
    
    # Get technique data
    techniques = []
    for tech_id in tech_ids:
        tech = processor.techniques_map.get(tech_id)
        if tech:
            tech_dict = {
                "id": tech.id,
                "name": tech.name,
                "severity": tech.severity,
                "exploitation_complexity": tech.exploitation_complexity,
                "detection_difficulty": tech.detection_difficulty,
                "countermeasures": tech.countermeasures
            }
            techniques.append(tech_dict)
        else:
            console.print(f"⚠️  Unknown technique: {tech_id}", style="yellow")
    
    if techniques:
        # Analyze chain
        analysis = calculator.analyze_attack_chain(techniques)
        
        # Display chain
        console.print("\n[bold]Attack Chain:[/bold]")
        for i, tech in enumerate(techniques, 1):
            console.print(f"  {i}. {tech['id']}: {tech['name']}")
        
        # Display analysis
        console.print(f"\n[bold]Chain Analysis:[/bold]")
        console.print(f"  Chain Length: {analysis['chain_length']}")
        console.print(f"  Average Risk Score: {analysis['average_risk_score']:.1f}%")
        console.print(f"  Cumulative Risk: {analysis['cumulative_risk_score']:.1f}")
        console.print(f"  Chain Complexity: {analysis['chain_complexity']:.1f}%")
        console.print(f"  Detection Probability: {analysis['detection_probability']:.1f}%")
        
        # Risk assessment
        if analysis['average_risk_score'] > 75:
            console.print("\n⚠️  [bold red]CRITICAL RISK[/bold red]: This attack chain poses severe threat!")
        elif analysis['average_risk_score'] > 50:
            console.print("\n⚠️  [bold yellow]HIGH RISK[/bold yellow]: This attack chain requires immediate attention.")
        else:
            console.print("\n [bold green]MODERATE RISK[/bold green]: Standard security measures should be effective.")
    else:
        console.print(" No valid techniques found.", style="red")


if __name__ == "__main__":
    app()
