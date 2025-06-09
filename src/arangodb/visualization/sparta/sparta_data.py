"""
Module: sparta_data.py

Sample Input:
>>> # See function docstrings for specific examples

Expected Output:
>>> # See function docstrings for expected results

Example Usage:
>>> # Import and use as needed based on module functionality
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json

@dataclass
class SPARTATactic:
    """Represents a SPARTA tactic"""
    id: str
    name: str
    description: str
    mitre_mapping: Optional[str] = None
    
@dataclass
class SPARTATechnique:
    """Represents a SPARTA technique or sub-technique"""
    id: str
    name: str
    description: str
    tactic_ids: List[str]
    severity: str  # critical, high, medium, low
    examples: List[str]
    countermeasures: List[str]
    space_specific: bool = True
    detection_difficulty: str = "medium"
    exploitation_complexity: str = "medium"
    
class SPARTADataProcessor:
    """Process and structure SPARTA threat matrix data"""
    
    # SPARTA Tactics based on research
    TACTICS = [
        SPARTATactic(
            id="ST0001",
            name="Reconnaissance",
            description="Threat actor is trying to gather information about the spacecraft or space mission",
            mitre_mapping="TA0043"
        ),
        SPARTATactic(
            id="ST0002", 
            name="Resource Development",
            description="Threat actor is trying to establish resources they can use to support operations",
            mitre_mapping="TA0042"
        ),
        SPARTATactic(
            id="ST0003",
            name="Initial Access",
            description="Threat actor is trying to get point of presence/command execution on the spacecraft",
            mitre_mapping="TA0001"
        ),
        SPARTATactic(
            id="ST0004",
            name="Execution",
            description="Threat actor is trying to execute malicious code on the spacecraft",
            mitre_mapping="TA0002"
        ),
        SPARTATactic(
            id="ST0005",
            name="Persistence",
            description="Threat actor is trying to maintain their foothold on the spacecraft",
            mitre_mapping="TA0003"
        ),
        SPARTATactic(
            id="ST0006",
            name="Defense Evasion",
            description="Threat actor is trying to avoid being detected",
            mitre_mapping="TA0005"
        ),
        SPARTATactic(
            id="ST0007",
            name="Lateral Movement",
            description="Threat actor is trying to move through across sub-systems of the spacecraft",
            mitre_mapping="TA0008"
        ),
        SPARTATactic(
            id="ST0008",
            name="Exfiltration",
            description="Threat actor is trying to steal information",
            mitre_mapping="TA0010"
        ),
        SPARTATactic(
            id="ST0009",
            name="Impact",
            description="Threat actor is trying to manipulate, interrupt, or destroy the space system(s) and/or data",
            mitre_mapping="TA0040"
        )
    ]
    
    # Sample SPARTA Techniques
    TECHNIQUES = [
        # Reconnaissance techniques
        SPARTATechnique(
            id="REC-0001",
            name="Gather Spacecraft Design Information",
            description="Adversaries may gather design specifications and technical documentation about target spacecraft",
            tactic_ids=["ST0001"],
            severity="medium",
            examples=["Accessing public technical papers", "Social engineering spacecraft engineers"],
            countermeasures=["Limit public disclosure of technical details", "Security awareness training"],
            detection_difficulty="hard"
        ),
        SPARTATechnique(
            id="REC-0005",
            name="Eavesdrop on Communications",
            description="Monitor spacecraft-ground station communications to gather intelligence",
            tactic_ids=["ST0001"],
            severity="high",
            examples=["RF signal interception", "Network traffic monitoring"],
            countermeasures=["Encryption of all communications", "Frequency hopping"],
            exploitation_complexity="low"
        ),
        
        # Initial Access techniques
        SPARTATechnique(
            id="IA-0004",
            name="Compromise Ground Station",
            description="Gain access to spacecraft through compromised ground control systems",
            tactic_ids=["ST0003"],
            severity="critical",
            examples=["Phishing ground station operators", "Exploiting ground system vulnerabilities"],
            countermeasures=["Multi-factor authentication", "Network segmentation", "Regular security audits"],
            detection_difficulty="medium"
        ),
        SPARTATechnique(
            id="IA-0008",
            name="Rogue Radio Frequency Commands",
            description="Send unauthorized commands via radio frequency to spacecraft",
            tactic_ids=["ST0003"],
            severity="critical",
            examples=["Command replay attacks", "RF signal spoofing"],
            countermeasures=["Command authentication", "Encrypted command links"],
            exploitation_complexity="high"
        ),
        
        # Execution techniques
        SPARTATechnique(
            id="EX-0001",
            name="Replay Valid Commands",
            description="Capture and replay legitimate commands to cause unintended actions",
            tactic_ids=["ST0004"],
            severity="high",
            examples=["Recording and replaying thruster commands", "Replaying mode change commands"],
            countermeasures=["Command counters", "Timestamp validation", "Nonce-based authentication"],
            detection_difficulty="medium"
        ),
        SPARTATechnique(
            id="EX-0005",
            name="Exploit Hardware/Firmware Corruption",
            description="Leverage vulnerabilities in spacecraft hardware or firmware",
            tactic_ids=["ST0004"],
            severity="critical",
            examples=["Buffer overflow in flight software", "Firmware backdoors"],
            countermeasures=["Secure coding practices", "Hardware security modules", "Code signing"],
            exploitation_complexity="very_high"
        ),
        
        # Persistence techniques
        SPARTATechnique(
            id="PER-0002",
            name="Backdoor Flight Software",
            description="Install persistent backdoors in spacecraft flight software",
            tactic_ids=["ST0005"],
            severity="critical",
            examples=["Hidden command interfaces", "Trojanized software updates"],
            countermeasures=["Code reviews", "Integrity monitoring", "Secure boot"],
            detection_difficulty="very_hard"
        ),
        
        # Defense Evasion techniques
        SPARTATechnique(
            id="DE-0003",
            name="Disable Telemetry",
            description="Turn off or corrupt telemetry to hide malicious activities",
            tactic_ids=["ST0006"],
            severity="high",
            examples=["Disabling health monitoring", "Corrupting sensor data"],
            countermeasures=["Redundant telemetry paths", "Anomaly detection"],
            exploitation_complexity="medium"
        ),
        
        # Lateral Movement techniques
        SPARTATechnique(
            id="LM-0001",
            name="Exploit Bus Systems",
            description="Move between spacecraft subsystems via internal bus connections",
            tactic_ids=["ST0007"],
            severity="high",
            examples=["MIL-STD-1553 exploitation", "SpaceWire attacks"],
            countermeasures=["Bus encryption", "Access control lists", "Network segmentation"],
            detection_difficulty="hard"
        ),
        
        # Exfiltration techniques
        SPARTATechnique(
            id="EXF-0003",
            name="Downlink Sensitive Data",
            description="Use spacecraft downlink to exfiltrate sensitive mission data",
            tactic_ids=["ST0008"],
            severity="high",
            examples=["Stealing encryption keys", "Exfiltrating mission data"],
            countermeasures=["Data classification", "Downlink monitoring", "Encryption"],
            exploitation_complexity="low"
        ),
        
        # Impact techniques
        SPARTATechnique(
            id="IMP-0002",
            name="Denial of Service",
            description="Prevent spacecraft from performing its mission",
            tactic_ids=["ST0009"],
            severity="critical",
            examples=["CPU exhaustion", "Memory corruption", "Thruster depletion"],
            countermeasures=["Resource monitoring", "Watchdog timers", "Graceful degradation"],
            detection_difficulty="easy"
        ),
        SPARTATechnique(
            id="IMP-0004",
            name="Manipulate Sensor Readings",
            description="Alter sensor data to cause incorrect spacecraft behavior",
            tactic_ids=["ST0009"],
            severity="critical",
            examples=["GPS spoofing", "Star tracker manipulation"],
            countermeasures=["Sensor fusion", "Sanity checks", "Redundant sensors"],
            exploitation_complexity="high"
        ),
        SPARTATechnique(
            id="IMP-0005",
            name="Trigger Unintended Maneuvers",
            description="Cause spacecraft to perform dangerous orbital maneuvers",
            tactic_ids=["ST0009"],
            severity="critical",
            examples=["Unauthorized thruster firing", "Attitude control disruption"],
            countermeasures=["Command verification", "Safety interlocks", "Ground approval required"],
            detection_difficulty="easy"
        )
    ]
    
    def __init__(self):
        self.tactics_map = {t.id: t for t in self.TACTICS}
        self.techniques_map = {t.id: t for t in self.TECHNIQUES}
        
    def get_matrix_data(self) -> Dict[str, Any]:
        """Get formatted data for D3.js visualization"""
        # Format tactics
        tactics_data = [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "mitre_mapping": t.mitre_mapping
            }
            for t in self.TACTICS
        ]
        
        # Format techniques with additional metadata
        techniques_data = []
        for tech in self.TECHNIQUES:
            for tactic_id in tech.tactic_ids:
                techniques_data.append({
                    "id": tech.id,
                    "name": tech.name,
                    "description": tech.description,
                    "tactic_id": tactic_id,
                    "severity": tech.severity,
                    "examples": tech.examples,
                    "countermeasures": tech.countermeasures,
                    "space_specific": tech.space_specific,
                    "detection_difficulty": tech.detection_difficulty,
                    "exploitation_complexity": tech.exploitation_complexity
                })
        
        return {
            "tactics": tactics_data,
            "techniques": techniques_data,
            "metadata": {
                "version": "2.0",
                "last_updated": datetime.now().isoformat(),
                "source": "The Aerospace Corporation SPARTA Framework"
            }
        }
    
    def get_technique_by_tactic(self, tactic_id: str) -> List[SPARTATechnique]:
        """Get all techniques for a specific tactic"""
        return [t for t in self.TECHNIQUES if tactic_id in t.tactic_ids]
    
    def get_techniques_by_severity(self, severity: str) -> List[SPARTATechnique]:
        """Get all techniques of a specific severity level"""
        return [t for t in self.TECHNIQUES if t.severity == severity]
    
    def export_to_json(self, filepath: str):
        """Export matrix data to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.get_matrix_data(), f, indent=2)
        
        # Resource Development technique
        SPARTATechnique(
            id="RD-0001",
            name="Develop Exploit Tools",
            description="Adversaries develop tools and exploits targeting spacecraft systems",
            tactic_ids=["ST0002"],
            severity="medium",
            examples=["Custom malware development", "Zero-day exploit creation"],
            countermeasures=["Threat intelligence", "Vulnerability management"],
            detection_difficulty="very_hard",
            exploitation_complexity="very_high"
        ),
