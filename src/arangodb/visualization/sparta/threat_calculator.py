"""
SPARTA Threat Calculator - Algorithms for threat analysis and risk calculation

Module: threat_calculator.py
"""

from typing import Dict, List, Any, Tuple
from collections import defaultdict
import numpy as np
from dataclasses import dataclass
import math

@dataclass
class ThreatMetrics:
    """Metrics for a threat technique"""
    risk_score: float
    impact_score: float
    likelihood_score: float
    detection_score: float
    mitigation_effectiveness: float
    
class ThreatCalculator:
    """Calculate threat metrics and analyze SPARTA matrix data"""
    
    # Severity weights
    SEVERITY_WEIGHTS = {
        "critical": 1.0,
        "high": 0.75,
        "medium": 0.5,
        "low": 0.25
    }
    
    # Complexity weights (inverse - higher complexity = lower likelihood)
    COMPLEXITY_WEIGHTS = {
        "very_low": 1.0,
        "low": 0.8,
        "medium": 0.6,
        "high": 0.4,
        "very_high": 0.2
    }
    
    # Detection difficulty weights (inverse - harder to detect = higher risk)
    DETECTION_WEIGHTS = {
        "very_easy": 0.2,
        "easy": 0.4,
        "medium": 0.6,
        "hard": 0.8,
        "very_hard": 1.0
    }
    
    def __init__(self):
        self.threat_metrics_cache = {}
        
    def calculate_risk_score(self, technique: Dict[str, Any]) -> float:
        """
        Calculate overall risk score for a technique
        Risk = (Impact × Likelihood × Detection Difficulty) / Mitigation Effectiveness
        """
        severity = technique.get("severity", "medium")
        complexity = technique.get("exploitation_complexity", "medium")
        detection = technique.get("detection_difficulty", "medium")
        countermeasures = len(technique.get("countermeasures", []))
        
        # Calculate component scores
        impact_score = self.SEVERITY_WEIGHTS.get(severity, 0.5)
        likelihood_score = self.COMPLEXITY_WEIGHTS.get(complexity, 0.6)
        detection_score = self.DETECTION_WEIGHTS.get(detection, 0.6)
        
        # Mitigation effectiveness based on number of countermeasures
        mitigation_effectiveness = min(1.0, countermeasures * 0.2) if countermeasures > 0 else 0.1
        
        # Calculate composite risk score
        risk_score = (impact_score * likelihood_score * detection_score) / mitigation_effectiveness
        
        # Normalize to 0-100 scale
        risk_score = min(100, risk_score * 100)
        
        return round(risk_score, 2)
    
    def calculate_threat_metrics(self, technique: Dict[str, Any]) -> ThreatMetrics:
        """Calculate comprehensive threat metrics for a technique"""
        severity = technique.get("severity", "medium")
        complexity = technique.get("exploitation_complexity", "medium")
        detection = technique.get("detection_difficulty", "medium")
        countermeasures = len(technique.get("countermeasures", []))
        
        impact_score = self.SEVERITY_WEIGHTS.get(severity, 0.5) * 100
        likelihood_score = self.COMPLEXITY_WEIGHTS.get(complexity, 0.6) * 100
        detection_score = self.DETECTION_WEIGHTS.get(detection, 0.6) * 100
        mitigation_effectiveness = min(100, countermeasures * 20) if countermeasures > 0 else 10
        
        risk_score = self.calculate_risk_score(technique)
        
        return ThreatMetrics(
            risk_score=risk_score,
            impact_score=impact_score,
            likelihood_score=likelihood_score,
            detection_score=detection_score,
            mitigation_effectiveness=mitigation_effectiveness
        )
    
    def analyze_attack_chain(self, techniques: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze a potential attack chain (sequence of techniques)"""
        if not techniques:
            return {"error": "No techniques provided"}
        
        # Calculate cumulative risk
        cumulative_risk = 0
        chain_complexity = 1
        detection_probability = 0
        
        for tech in techniques:
            metrics = self.calculate_threat_metrics(tech)
            cumulative_risk += metrics.risk_score
            
            # Chain complexity increases multiplicatively
            complexity_factor = self.COMPLEXITY_WEIGHTS.get(
                tech.get("exploitation_complexity", "medium"), 0.6
            )
            chain_complexity *= complexity_factor
            
            # Detection probability increases with each step
            detection_prob = 1 - (metrics.detection_score / 100)
            detection_probability = 1 - ((1 - detection_probability) * (1 - detection_prob))
        
        # Normalize cumulative risk
        avg_risk = cumulative_risk / len(techniques)
        
        return {
            "chain_length": len(techniques),
            "average_risk_score": round(avg_risk, 2),
            "cumulative_risk_score": round(cumulative_risk, 2),
            "chain_complexity": round(chain_complexity * 100, 2),
            "detection_probability": round(detection_probability * 100, 2),
            "techniques": [t["id"] for t in techniques]
        }
    
    def calculate_tactic_coverage(self, techniques: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate threat coverage for each tactic"""
        tactic_techniques = defaultdict(list)
        
        for tech in techniques:
            tactic_id = tech.get("tactic_id")
            if tactic_id:
                tactic_techniques[tactic_id].append(tech)
        
        coverage = {}
        for tactic_id, techs in tactic_techniques.items():
            # Calculate average risk for the tactic
            risks = [self.calculate_risk_score(t) for t in techs]
            coverage[tactic_id] = {
                "technique_count": len(techs),
                "average_risk": round(np.mean(risks), 2) if risks else 0,
                "max_risk": round(max(risks), 2) if risks else 0,
                "min_risk": round(min(risks), 2) if risks else 0
            }
        
        return coverage
    
    def identify_critical_paths(self, matrix_data: Dict[str, Any]) -> List[List[str]]:
        """Identify critical attack paths through the SPARTA matrix"""
        techniques = matrix_data.get("techniques", [])
        tactics = matrix_data.get("tactics", [])
        
        # Group techniques by tactic
        tactic_techniques = defaultdict(list)
        for tech in techniques:
            tactic_techniques[tech["tactic_id"]].append(tech)
        
        # Find high-risk paths
        critical_paths = []
        
        # Simple path: Reconnaissance -> Initial Access -> Execution -> Impact
        basic_path = ["ST0001", "ST0003", "ST0004", "ST0009"]
        path_techniques = []
        
        for tactic_id in basic_path:
            tactic_techs = tactic_techniques.get(tactic_id, [])
            if tactic_techs:
                # Get highest risk technique for this tactic
                highest_risk_tech = max(
                    tactic_techs, 
                    key=lambda t: self.calculate_risk_score(t)
                )
                path_techniques.append(highest_risk_tech["id"])
        
        if len(path_techniques) == len(basic_path):
            critical_paths.append(path_techniques)
        
        # Advanced path including persistence and lateral movement
        advanced_path = ["ST0001", "ST0003", "ST0004", "ST0005", "ST0007", "ST0009"]
        adv_path_techniques = []
        
        for tactic_id in advanced_path:
            tactic_techs = tactic_techniques.get(tactic_id, [])
            if tactic_techs:
                highest_risk_tech = max(
                    tactic_techs,
                    key=lambda t: self.calculate_risk_score(t)
                )
                adv_path_techniques.append(highest_risk_tech["id"])
        
        if len(adv_path_techniques) == len(advanced_path):
            critical_paths.append(adv_path_techniques)
        
        return critical_paths
    
    def calculate_system_resilience(self, matrix_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate overall system resilience based on countermeasures"""
        techniques = matrix_data.get("techniques", [])
        
        total_techniques = len(techniques)
        total_countermeasures = sum(len(t.get("countermeasures", [])) for t in techniques)
        techniques_with_countermeasures = sum(
            1 for t in techniques if len(t.get("countermeasures", [])) > 0
        )
        
        # Calculate various resilience metrics
        coverage_ratio = techniques_with_countermeasures / total_techniques if total_techniques > 0 else 0
        avg_countermeasures = total_countermeasures / total_techniques if total_techniques > 0 else 0
        
        # Calculate weighted resilience based on threat severity
        weighted_resilience = 0
        for tech in techniques:
            severity_weight = self.SEVERITY_WEIGHTS.get(tech.get("severity", "medium"), 0.5)
            countermeasures = len(tech.get("countermeasures", []))
            tech_resilience = min(1.0, countermeasures * 0.25)  # Max out at 4 countermeasures
            weighted_resilience += severity_weight * tech_resilience
        
        normalized_resilience = (weighted_resilience / total_techniques * 100) if total_techniques > 0 else 0
        
        return {
            "coverage_percentage": round(coverage_ratio * 100, 2),
            "average_countermeasures_per_technique": round(avg_countermeasures, 2),
            "weighted_resilience_score": round(normalized_resilience, 2),
            "total_countermeasures": total_countermeasures,
            "techniques_with_countermeasures": techniques_with_countermeasures,
            "total_techniques": total_techniques
        }
    
    def generate_threat_heatmap(self, matrix_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate heatmap data for visualization"""
        techniques = matrix_data.get("techniques", [])
        heatmap_data = []
        
        for tech in techniques:
            metrics = self.calculate_threat_metrics(tech)
            heatmap_data.append({
                "technique_id": tech["id"],
                "tactic_id": tech["tactic_id"],
                "risk_score": metrics.risk_score,
                "impact": metrics.impact_score,
                "likelihood": metrics.likelihood_score,
                "detection_difficulty": metrics.detection_score,
                "mitigation": metrics.mitigation_effectiveness
            })
        
        return heatmap_data
