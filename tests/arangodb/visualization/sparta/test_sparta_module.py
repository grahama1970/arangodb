"""
Comprehensive tests for SPARTA visualization module
"""

import pytest
import json
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))

from src.arangodb.visualization.sparta import (
    SPARTADataProcessor,
    ThreatCalculator,
    SPARTAMatrixGenerator
)

class TestSPARTADataProcessor:
    """Test SPARTA data processing functionality"""
    
    def test_initialization(self):
        """Test processor initialization"""
        processor = SPARTADataProcessor()
        assert len(processor.TACTICS) == 9
        assert len(processor.TECHNIQUES) >= 13
        assert all(t.id in processor.tactics_map for t in processor.TACTICS)
        assert all(t.id in processor.techniques_map for t in processor.TECHNIQUES)
    
    def test_get_matrix_data(self):
        """Test matrix data generation"""
        processor = SPARTADataProcessor()
        data = processor.get_matrix_data()
        
        assert "tactics" in data
        assert "techniques" in data
        assert "metadata" in data
        
        assert len(data["tactics"]) == 9
        assert all(key in data["tactics"][0] for key in ["id", "name", "description"])
        assert data["metadata"]["version"] == "2.0"
    
    def test_get_technique_by_tactic(self):
        """Test technique filtering by tactic"""
        processor = SPARTADataProcessor()
        
        # Test reconnaissance techniques
        recon_techniques = processor.get_technique_by_tactic("ST0001")
        assert len(recon_techniques) > 0
        assert all("ST0001" in t.tactic_ids for t in recon_techniques)
        
        # Test impact techniques
        impact_techniques = processor.get_technique_by_tactic("ST0009")
        assert len(impact_techniques) > 0
        assert all("ST0009" in t.tactic_ids for t in impact_techniques)
    
    def test_get_techniques_by_severity(self):
        """Test technique filtering by severity"""
        processor = SPARTADataProcessor()
        
        critical = processor.get_techniques_by_severity("critical")
        high = processor.get_techniques_by_severity("high")
        medium = processor.get_techniques_by_severity("medium")
        low = processor.get_techniques_by_severity("low")
        
        assert len(critical) > 0
        assert all(t.severity == "critical" for t in critical)
        
        # Verify severity distribution makes sense
        total = len(critical) + len(high) + len(medium) + len(low)
        assert total == len(processor.TECHNIQUES)


class TestThreatCalculator:
    """Test threat calculation algorithms"""
    
    @pytest.fixture
    def sample_technique(self):
        """Sample technique for testing"""
        return {
            "id": "TEST-001",
            "name": "Test Technique",
            "severity": "high",
            "exploitation_complexity": "medium",
            "detection_difficulty": "hard",
            "countermeasures": ["CM1", "CM2", "CM3"]
        }
    
    def test_risk_score_calculation(self, sample_technique):
        """Test risk score calculation"""
        calculator = ThreatCalculator()
        score = calculator.calculate_risk_score(sample_technique)
        
        assert isinstance(score, float)
        assert 0 <= score <= 100
        
        # Test edge cases
        critical_tech = {**sample_technique, "severity": "critical", "countermeasures": []}
        critical_score = calculator.calculate_risk_score(critical_tech)
        assert critical_score > score
        
        low_tech = {**sample_technique, "severity": "low", "countermeasures": ["CM1", "CM2", "CM3", "CM4", "CM5"]}
        low_score = calculator.calculate_risk_score(low_tech)
        assert low_score < score
    
    def test_threat_metrics(self, sample_technique):
        """Test comprehensive threat metrics calculation"""
        calculator = ThreatCalculator()
        metrics = calculator.calculate_threat_metrics(sample_technique)
        
        assert hasattr(metrics, "risk_score")
        assert hasattr(metrics, "impact_score")
        assert hasattr(metrics, "likelihood_score")
        assert hasattr(metrics, "detection_score")
        assert hasattr(metrics, "mitigation_effectiveness")
        
        assert all(0 <= getattr(metrics, attr) <= 100 for attr in 
                  ["risk_score", "impact_score", "likelihood_score", "detection_score", "mitigation_effectiveness"])
    
    def test_attack_chain_analysis(self):
        """Test attack chain analysis"""
        calculator = ThreatCalculator()
        
        chain = [
            {"id": "T1", "severity": "medium", "exploitation_complexity": "low", "detection_difficulty": "medium", "countermeasures": ["CM1"]},
            {"id": "T2", "severity": "high", "exploitation_complexity": "medium", "detection_difficulty": "hard", "countermeasures": ["CM1", "CM2"]},
            {"id": "T3", "severity": "critical", "exploitation_complexity": "high", "detection_difficulty": "very_hard", "countermeasures": []}
        ]
        
        analysis = calculator.analyze_attack_chain(chain)
        
        assert "chain_length" in analysis
        assert "average_risk_score" in analysis
        assert "cumulative_risk_score" in analysis
        assert "chain_complexity" in analysis
        assert "detection_probability" in analysis
        
        assert analysis["chain_length"] == 3
        assert analysis["detection_probability"] > 0
    
    def test_system_resilience_calculation(self):
        """Test system resilience calculation"""
        calculator = ThreatCalculator()
        processor = SPARTADataProcessor()
        
        matrix_data = processor.get_matrix_data()
        resilience = calculator.calculate_system_resilience(matrix_data)
        
        assert "coverage_percentage" in resilience
        assert "average_countermeasures_per_technique" in resilience
        assert "weighted_resilience_score" in resilience
        assert "total_countermeasures" in resilience
        
        assert 0 <= resilience["coverage_percentage"] <= 100
        assert 0 <= resilience["weighted_resilience_score"] <= 100
    
    def test_critical_paths_identification(self):
        """Test critical attack path identification"""
        calculator = ThreatCalculator()
        processor = SPARTADataProcessor()
        
        matrix_data = processor.get_matrix_data()
        paths = calculator.identify_critical_paths(matrix_data)
        
        assert isinstance(paths, list)
        assert len(paths) >= 1
        
        for path in paths:
            assert isinstance(path, list)
            assert all(isinstance(tech_id, str) for tech_id in path)


class TestSPARTAMatrixGenerator:
    """Test matrix generation and visualization"""
    
    def test_generator_initialization(self):
        """Test generator initialization"""
        generator = SPARTAMatrixGenerator()
        assert hasattr(generator, "data_processor")
        assert hasattr(generator, "threat_calculator")
        assert hasattr(generator, "template_path")
    
    def test_enhanced_matrix_data_generation(self):
        """Test enhanced matrix data generation"""
        generator = SPARTAMatrixGenerator()
        data = generator.generate_enhanced_matrix_data()
        
        assert "tactics" in data
        assert "techniques" in data
        assert "analytics" in data
        
        # Check analytics components
        analytics = data["analytics"]
        assert "tactic_coverage" in analytics
        assert "system_resilience" in analytics
        assert "critical_paths" in analytics
        assert "threat_heatmap" in analytics
        
        # Verify techniques have risk scores
        for tech in data["techniques"]:
            assert "risk_score" in tech
            assert "impact_score" in tech
            assert "likelihood_score" in tech
    
    def test_export_formats(self, tmp_path):
        """Test data export in various formats"""
        generator = SPARTAMatrixGenerator()
        
        # Test JSON export
        json_path = tmp_path / "test_export.json"
        generator.export_matrix_data(str(json_path), format="json")
        assert json_path.exists()
        
        with open(json_path) as f:
            data = json.load(f)
            assert "tactics" in data
            assert "techniques" in data
        
        # Test CSV export
        csv_path = tmp_path / "test_export.csv"
        generator.export_matrix_data(str(csv_path), format="csv")
        assert csv_path.exists()
        
        # Verify CSV has headers
        with open(csv_path) as f:
            headers = f.readline()
            assert "ID" in headers
            assert "Risk Score" in headers
    
    def test_interactive_features_generation(self):
        """Test interactive feature configuration"""
        generator = SPARTAMatrixGenerator()
        features = generator.generate_interactive_features()
        
        assert "attack_chain_simulator" in features
        assert "threat_filter" in features
        assert "countermeasure_overlay" in features
        
        # Verify JavaScript code is present
        for feature in features.values():
            assert "function" in feature
            assert "{" in feature and "}" in feature


class TestIntegration:
    """Integration tests for the complete SPARTA module"""
    
    def test_end_to_end_visualization_generation(self, tmp_path):
        """Test complete visualization generation"""
        generator = SPARTAMatrixGenerator()
        
        output_path = tmp_path / "sparta_visualization.html"
        result = generator.generate_html_visualization(str(output_path), include_analytics=True)
        
        assert output_path.exists()
        assert result == str(output_path)
        
        # Verify HTML content
        with open(output_path) as f:
            content = f.read()
            assert "<html>" in content
            assert "SPARTA" in content
            assert "d3js" in content.lower()
            assert "matrixData" in content
    
    def test_data_consistency(self):
        """Test data consistency across components"""
        processor = SPARTADataProcessor()
        calculator = ThreatCalculator()
        
        matrix_data = processor.get_matrix_data()
        
        # Verify all techniques can be processed
        for tech in matrix_data["techniques"]:
            score = calculator.calculate_risk_score(tech)
            assert isinstance(score, float)
            assert 0 <= score <= 100
        
        # Verify tactic coverage
        coverage = calculator.calculate_tactic_coverage(matrix_data["techniques"])
        assert len(coverage) > 0
        
        # Verify all tactics have techniques
        for tactic in matrix_data["tactics"]:
            tactic_techniques = [t for t in matrix_data["techniques"] if t["tactic_id"] == tactic["id"]]
            assert len(tactic_techniques) > 0, f"No techniques for tactic {tactic['id']}"
    
    def test_performance(self):
        """Test performance with large datasets"""
        import time
        
        generator = SPARTAMatrixGenerator()
        
        start_time = time.time()
        data = generator.generate_enhanced_matrix_data()
        generation_time = time.time() - start_time
        
        # Should generate in reasonable time
        assert generation_time < 1.0  # Less than 1 second
        
        # Test with many techniques
        calculator = ThreatCalculator()
        techniques = data["techniques"] * 10  # Simulate 10x techniques
        
        start_time = time.time()
        for tech in techniques:
            calculator.calculate_risk_score(tech)
        calculation_time = time.time() - start_time
        
        # Should still be performant
        assert calculation_time < 2.0  # Less than 2 seconds for 10x data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
