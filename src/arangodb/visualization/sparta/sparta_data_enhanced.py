"""
Enhanced SPARTA Data Processor with comprehensive threat techniques
Based on SPARTA v2.0 from The Aerospace Corporation
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
from enum import Enum

class ThreatActorType(Enum):
    """Types of threat actors in space domain"""
    NATION_STATE = "nation_state"
    COMPETITOR = "competitor"
    HACKTIVIST = "hacktivist"
    INSIDER = "insider"
    CRIMINAL = "criminal"
    TERRORIST = "terrorist"

@dataclass
class SPARTATactic:
    """Enhanced SPARTA tactic with additional metadata"""
    id: str
    name: str
    description: str
    mitre_mapping: Optional[str] = None
    objectives: List[str] = field(default_factory=list)
    typical_actors: List[ThreatActorType] = field(default_factory=list)
    
@dataclass
class SPARTATechnique:
    """Enhanced SPARTA technique with comprehensive attributes"""
    id: str
    name: str
    description: str
    tactic_ids: List[str]
    severity: str
    examples: List[str]
    countermeasures: List[str]
    space_specific: bool = True
    detection_difficulty: str = "medium"
    exploitation_complexity: str = "medium"
    required_resources: str = "medium"
    typical_actors: List[ThreatActorType] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    indicators: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    sub_techniques: List[str] = field(default_factory=list)
    platforms: List[str] = field(default_factory=list)
    data_sources: List[str] = field(default_factory=list)
    
class EnhancedSPARTADataProcessor:
    """Process comprehensive SPARTA threat matrix data"""
    
    # Comprehensive SPARTA Tactics
    TACTICS = [
        SPARTATactic(
            id="ST0001",
            name="Reconnaissance",
            description="Gathering information about spacecraft systems and operations",
            mitre_mapping="TA0043",
            objectives=["Identify targets", "Discover vulnerabilities", "Map system architecture"],
            typical_actors=[ThreatActorType.NATION_STATE, ThreatActorType.COMPETITOR]
        ),
        SPARTATactic(
            id="ST0002",
            name="Resource Development",
            description="Establishing resources and capabilities for space system attacks",
            mitre_mapping="TA0042",
            objectives=["Acquire tools", "Develop exploits", "Build infrastructure"],
            typical_actors=[ThreatActorType.NATION_STATE, ThreatActorType.CRIMINAL]
        ),
        SPARTATactic(
            id="ST0003",
            name="Initial Access",
            description="Gaining initial foothold in spacecraft systems",
            mitre_mapping="TA0001",
            objectives=["Establish presence", "Gain control", "Enable further operations"],
            typical_actors=[ThreatActorType.NATION_STATE, ThreatActorType.INSIDER]
        ),
        SPARTATactic(
            id="ST0004",
            name="Execution",
            description="Running malicious code on spacecraft systems",
            mitre_mapping="TA0002",
            objectives=["Execute payloads", "Trigger actions", "Modify behavior"],
            typical_actors=[ThreatActorType.NATION_STATE, ThreatActorType.TERRORIST]
        ),
        SPARTATactic(
            id="ST0005",
            name="Persistence",
            description="Maintaining presence in spacecraft systems",
            mitre_mapping="TA0003",
            objectives=["Survive reboots", "Maintain access", "Avoid detection"],
            typical_actors=[ThreatActorType.NATION_STATE]
        ),
        SPARTATactic(
            id="ST0006",
            name="Privilege Escalation",
            description="Gaining higher-level permissions in spacecraft systems",
            mitre_mapping="TA0004",
            objectives=["Gain admin access", "Access restricted functions", "Bypass controls"],
            typical_actors=[ThreatActorType.NATION_STATE, ThreatActorType.INSIDER]
        ),
        SPARTATactic(
            id="ST0007",
            name="Defense Evasion",
            description="Avoiding detection by spacecraft security measures",
            mitre_mapping="TA0005",
            objectives=["Hide activities", "Bypass monitoring", "Blend with normal operations"],
            typical_actors=[ThreatActorType.NATION_STATE]
        ),
        SPARTATactic(
            id="ST0008",
            name="Discovery",
            description="Exploring spacecraft systems and data",
            mitre_mapping="TA0007",
            objectives=["Map systems", "Find data", "Identify targets"],
            typical_actors=[ThreatActorType.NATION_STATE, ThreatActorType.COMPETITOR]
        ),
        SPARTATactic(
            id="ST0009",
            name="Lateral Movement",
            description="Moving between spacecraft subsystems",
            mitre_mapping="TA0008",
            objectives=["Access other systems", "Expand control", "Reach targets"],
            typical_actors=[ThreatActorType.NATION_STATE]
        ),
        SPARTATactic(
            id="ST0010",
            name="Collection",
            description="Gathering data from spacecraft systems",
            mitre_mapping="TA0009",
            objectives=["Steal data", "Monitor operations", "Capture credentials"],
            typical_actors=[ThreatActorType.NATION_STATE, ThreatActorType.COMPETITOR]
        ),
        SPARTATactic(
            id="ST0011",
            name="Command and Control",
            description="Communicating with compromised spacecraft systems",
            mitre_mapping="TA0011",
            objectives=["Maintain control", "Send commands", "Receive data"],
            typical_actors=[ThreatActorType.NATION_STATE]
        ),
        SPARTATactic(
            id="ST0012",
            name="Exfiltration",
            description="Stealing data from spacecraft systems",
            mitre_mapping="TA0010",
            objectives=["Extract data", "Send to adversary", "Avoid detection"],
            typical_actors=[ThreatActorType.NATION_STATE, ThreatActorType.COMPETITOR]
        ),
        SPARTATactic(
            id="ST0013",
            name="Impact",
            description="Disrupting, degrading, or destroying spacecraft operations",
            mitre_mapping="TA0040",
            objectives=["Deny service", "Destroy data", "Physical damage"],
            typical_actors=[ThreatActorType.NATION_STATE, ThreatActorType.TERRORIST]
        )
    ]
    
    # Comprehensive SPARTA Techniques (expanded set)
    TECHNIQUES = [
        # Reconnaissance Techniques
        SPARTATechnique(
            id="REC-0001",
            name="Gather Spacecraft Documentation",
            description="Collect technical specifications, design documents, and operational procedures",
            tactic_ids=["ST0001"],
            severity="medium",
            examples=[
                "Searching public patent databases",
                "Accessing conference presentations",
                "Mining academic papers",
                "Social engineering engineers"
            ],
            countermeasures=[
                "Classify sensitive documentation",
                "Limit public technical disclosures",
                "Security awareness training",
                "Information handling procedures"
            ],
            detection_difficulty="hard",
            exploitation_complexity="low",
            required_resources="low",
            typical_actors=[ThreatActorType.COMPETITOR, ThreatActorType.NATION_STATE],
            platforms=["Ground Station", "Development Environment"],
            data_sources=["Web logs", "Document access logs", "Email monitoring"]
        ),
        
        SPARTATechnique(
            id="REC-0002",
            name="Monitor Launch Activities",
            description="Observe and analyze spacecraft launch preparations and activities",
            tactic_ids=["ST0001"],
            severity="low",
            examples=[
                "Monitoring public launch schedules",
                "Observing launch site activities",
                "Tracking regulatory filings",
                "Social media monitoring"
            ],
            countermeasures=[
                "Operational security procedures",
                "Limited public information",
                "Controlled information release"
            ],
            detection_difficulty="very_hard",
            exploitation_complexity="very_low",
            platforms=["Public Sources"],
            indicators=["Unusual interest in launch schedules", "Pattern of information requests"]
        ),
        
        SPARTATechnique(
            id="REC-0005",
            name="RF Signal Intelligence",
            description="Intercept and analyze spacecraft RF communications",
            tactic_ids=["ST0001"],
            severity="high",
            examples=[
                "Software-defined radio monitoring",
                "Signal pattern analysis",
                "Frequency scanning",
                "Protocol reverse engineering"
            ],
            countermeasures=[
                "Signal encryption",
                "Frequency hopping",
                "Directional antennas",
                "Signal authentication"
            ],
            detection_difficulty="medium",
            exploitation_complexity="medium",
            required_resources="medium",
            typical_actors=[ThreatActorType.NATION_STATE],
            platforms=["RF Systems", "Ground Station"],
            data_sources=["RF monitoring", "Spectrum analysis", "Anomaly detection"]
        ),
        
        SPARTATechnique(
            id="REC-0006",
            name="Supply Chain Reconnaissance",
            description="Map spacecraft component suppliers and development partners",
            tactic_ids=["ST0001"],
            severity="medium",
            examples=[
                "Vendor relationship mapping",
                "Component sourcing research",
                "Partner vulnerability assessment",
                "Third-party risk analysis"
            ],
            countermeasures=[
                "Supply chain security program",
                "Vendor vetting procedures",
                "Component authentication",
                "Trusted supplier programs"
            ],
            detection_difficulty="hard",
            exploitation_complexity="low",
            platforms=["Supply Chain", "Business Systems"],
            typical_actors=[ThreatActorType.NATION_STATE, ThreatActorType.COMPETITOR]
        ),
        
        # Initial Access Techniques
        SPARTATechnique(
            id="IA-0001",
            name="Exploit Public-Facing Application",
            description="Compromise internet-facing ground station applications",
            tactic_ids=["ST0003"],
            severity="critical",
            examples=[
                "Web application vulnerabilities",
                "API endpoint exploitation",
                "Remote code execution",
                "SQL injection attacks"
            ],
            countermeasures=[
                "Web application firewall",
                "Regular security updates",
                "Input validation",
                "Penetration testing"
            ],
            detection_difficulty="medium",
            exploitation_complexity="medium",
            required_resources="low",
            typical_actors=[ThreatActorType.CRIMINAL, ThreatActorType.NATION_STATE],
            platforms=["Ground Station", "Mission Control"],
            data_sources=["Web logs", "IDS/IPS", "Application logs"],
            indicators=["Unusual web requests", "Error spikes", "Authentication failures"]
        ),
        
        SPARTATechnique(
            id="IA-0004",
            name="Compromise Ground Infrastructure",
            description="Gain access through ground station systems",
            tactic_ids=["ST0003"],
            severity="critical",
            examples=[
                "Phishing ground operators",
                "Exploiting ground system vulnerabilities",
                "Physical access to facilities",
                "Insider threats"
            ],
            countermeasures=[
                "Multi-factor authentication",
                "Network segmentation",
                "Physical security controls",
                "Background checks"
            ],
            detection_difficulty="medium",
            exploitation_complexity="medium",
            platforms=["Ground Station", "Mission Control"],
            prerequisites=["Knowledge of ground infrastructure"],
            typical_actors=[ThreatActorType.NATION_STATE, ThreatActorType.INSIDER]
        ),
        
        SPARTATechnique(
            id="IA-0007",
            name="Supply Chain Compromise",
            description="Introduce vulnerabilities through spacecraft components or software",
            tactic_ids=["ST0003"],
            severity="critical",
            examples=[
                "Hardware backdoors",
                "Compromised software libraries",
                "Malicious firmware",
                "Counterfeit components"
            ],
            countermeasures=[
                "Component verification",
                "Secure development lifecycle",
                "Code signing",
                "Hardware authentication"
            ],
            detection_difficulty="very_hard",
            exploitation_complexity="high",
            required_resources="high",
            typical_actors=[ThreatActorType.NATION_STATE],
            platforms=["Spacecraft", "Ground Systems"],
            data_sources=["Supply chain audits", "Component testing", "Code reviews"]
        ),
        
        SPARTATechnique(
            id="IA-0008",
            name="Rogue Commanding",
            description="Send unauthorized commands to spacecraft",
            tactic_ids=["ST0003"],
            severity="critical",
            examples=[
                "RF signal spoofing",
                "Command injection",
                "Replay attacks",
                "Protocol exploitation"
            ],
            countermeasures=[
                "Command authentication",
                "Encrypted command links",
                "Anti-replay mechanisms",
                "Command verification"
            ],
            detection_difficulty="easy",
            exploitation_complexity="high",
            required_resources="medium",
            platforms=["Spacecraft", "RF Systems"],
            indicators=["Unexpected commands", "Command counter anomalies", "RF interference"]
        ),
        
        # Execution Techniques
        SPARTATechnique(
            id="EX-0001",
            name="Command Injection",
            description="Inject malicious commands into spacecraft command stream",
            tactic_ids=["ST0004"],
            severity="high",
            examples=[
                "SQL command injection",
                "Buffer overflow exploitation",
                "Format string attacks",
                "Script injection"
            ],
            countermeasures=[
                "Input validation",
                "Command whitelisting",
                "Parameterized queries",
                "Secure coding practices"
            ],
            detection_difficulty="medium",
            exploitation_complexity="medium",
            platforms=["Spacecraft", "Ground Station"],
            data_sources=["Command logs", "Anomaly detection", "System monitoring"]
        ),
        
        SPARTATechnique(
            id="EX-0002",
            name="Malicious Code Upload",
            description="Upload and execute malicious code on spacecraft",
            tactic_ids=["ST0004"],
            severity="critical",
            examples=[
                "Firmware modification",
                "Script uploads",
                "Binary exploitation",
                "Memory corruption"
            ],
            countermeasures=[
                "Code signing verification",
                "Secure boot",
                "Upload restrictions",
                "Integrity monitoring"
            ],
            detection_difficulty="medium",
            exploitation_complexity="high",
            required_resources="medium",
            platforms=["Spacecraft", "Onboard Systems"],
            indicators=["Unexpected uploads", "Memory anomalies", "Performance degradation"]
        ),
        
        SPARTATechnique(
            id="EX-0005",
            name="Exploit Spacecraft Vulnerabilities",
            description="Leverage software or hardware vulnerabilities in spacecraft systems",
            tactic_ids=["ST0004"],
            severity="critical",
            examples=[
                "Zero-day exploits",
                "Known vulnerability exploitation",
                "Hardware design flaws",
                "Protocol weaknesses"
            ],
            countermeasures=[
                "Regular patching",
                "Vulnerability scanning",
                "Security testing",
                "Secure design practices"
            ],
            detection_difficulty="hard",
            exploitation_complexity="very_high",
            platforms=["Spacecraft", "Embedded Systems"],
            typical_actors=[ThreatActorType.NATION_STATE]
        ),
        
        # Persistence Techniques
        SPARTATechnique(
            id="PER-0001",
            name="Modify Flight Software",
            description="Alter spacecraft flight software to maintain persistence",
            tactic_ids=["ST0005"],
            severity="critical",
            examples=[
                "Bootloader modification",
                "Kernel rootkits",
                "Service installation",
                "Scheduled task creation"
            ],
            countermeasures=[
                "Secure boot",
                "Code integrity checking",
                "Change detection",
                "Regular audits"
            ],
            detection_difficulty="very_hard",
            exploitation_complexity="very_high",
            platforms=["Spacecraft"],
            typical_actors=[ThreatActorType.NATION_STATE]
        ),
        
        SPARTATechnique(
            id="PER-0002",
            name="Hardware Implants",
            description="Install persistent hardware backdoors",
            tactic_ids=["ST0005"],
            severity="critical",
            examples=[
                "Malicious chips",
                "Hardware keyloggers",
                "Radio implants",
                "Modified components"
            ],
            countermeasures=[
                "Hardware verification",
                "X-ray inspection",
                "Component authentication",
                "Secure supply chain"
            ],
            detection_difficulty="very_hard",
            exploitation_complexity="very_high",
            required_resources="very_high",
            platforms=["Spacecraft", "Hardware"],
            typical_actors=[ThreatActorType.NATION_STATE]
        ),
        
        # Defense Evasion Techniques
        SPARTATechnique(
            id="DE-0001",
            name="Disable Security Features",
            description="Turn off or bypass spacecraft security mechanisms",
            tactic_ids=["ST0007"],
            severity="high",
            examples=[
                "Disabling logging",
                "Turning off encryption",
                "Bypassing authentication",
                "Modifying security policies"
            ],
            countermeasures=[
                "Security feature monitoring",
                "Tamper detection",
                "Redundant controls",
                "Configuration management"
            ],
            detection_difficulty="easy",
            exploitation_complexity="medium",
            platforms=["Spacecraft", "Security Systems"],
            indicators=["Security alerts", "Configuration changes", "Missing logs"]
        ),
        
        SPARTATechnique(
            id="DE-0003",
            name="Telemetry Manipulation",
            description="Alter or disable spacecraft telemetry to hide activities",
            tactic_ids=["ST0007"],
            severity="high",
            examples=[
                "Telemetry suppression",
                "Data modification",
                "Timestamp manipulation",
                "False status reporting"
            ],
            countermeasures=[
                "Telemetry authentication",
                "Redundant monitoring",
                "Anomaly detection",
                "Data integrity checks"
            ],
            detection_difficulty="medium",
            exploitation_complexity="medium",
            platforms=["Spacecraft", "Telemetry Systems"],
            data_sources=["Telemetry analysis", "Ground verification", "Cross-checking"]
        ),
        
        # Lateral Movement Techniques
        SPARTATechnique(
            id="LM-0001",
            name="Exploit Internal Buses",
            description="Move between spacecraft subsystems via internal communication buses",
            tactic_ids=["ST0009"],
            severity="high",
            examples=[
                "MIL-STD-1553 exploitation",
                "SpaceWire attacks",
                "CAN bus manipulation",
                "I2C/SPI exploitation"
            ],
            countermeasures=[
                "Bus encryption",
                "Access control",
                "Traffic monitoring",
                "Segmentation"
            ],
            detection_difficulty="hard",
            exploitation_complexity="high",
            platforms=["Spacecraft", "Bus Systems"],
            prerequisites=["Bus access", "Protocol knowledge"],
            typical_actors=[ThreatActorType.NATION_STATE]
        ),
        
        SPARTATechnique(
            id="LM-0002",
            name="Subsystem Hopping",
            description="Move between isolated spacecraft subsystems",
            tactic_ids=["ST0009"],
            severity="medium",
            examples=[
                "Shared memory exploitation",
                "Inter-process communication abuse",
                "Service exploitation",
                "Privilege escalation"
            ],
            countermeasures=[
                "Subsystem isolation",
                "Access controls",
                "Monitoring",
                "Least privilege"
            ],
            detection_difficulty="medium",
            exploitation_complexity="high",
            platforms=["Spacecraft", "Onboard Systems"]
        ),
        
        # Collection Techniques
        SPARTATechnique(
            id="COL-0001",
            name="Sensor Data Collection",
            description="Gather data from spacecraft sensors and instruments",
            tactic_ids=["ST0010"],
            severity="high",
            examples=[
                "Camera hijacking",
                "Sensor data interception",
                "Scientific data theft",
                "Navigation data collection"
            ],
            countermeasures=[
                "Data encryption",
                "Access controls",
                "Audit logging",
                "Data classification"
            ],
            detection_difficulty="medium",
            exploitation_complexity="medium",
            platforms=["Spacecraft", "Payload Systems"],
            typical_actors=[ThreatActorType.NATION_STATE, ThreatActorType.COMPETITOR]
        ),
        
        SPARTATechnique(
            id="COL-0002",
            name="Memory Scraping",
            description="Extract sensitive data from spacecraft memory",
            tactic_ids=["ST0010"],
            severity="high",
            examples=[
                "RAM dumping",
                "Cache extraction",
                "Buffer reading",
                "Swap file analysis"
            ],
            countermeasures=[
                "Memory encryption",
                "Secure deletion",
                "Access controls",
                "Memory protection"
            ],
            detection_difficulty="hard",
            exploitation_complexity="high",
            platforms=["Spacecraft", "Onboard Systems"],
            data_sources=["Memory forensics", "Performance monitoring"]
        ),
        
        # Command and Control Techniques
        SPARTATechnique(
            id="C2-0001",
            name="RF Command Channel",
            description="Establish covert command channel via RF communications",
            tactic_ids=["ST0011"],
            severity="high",
            examples=[
                "Covert RF channels",
                "Protocol tunneling",
                "Steganography",
                "Side-channel communication"
            ],
            countermeasures=[
                "RF monitoring",
                "Protocol analysis",
                "Anomaly detection",
                "Channel authentication"
            ],
            detection_difficulty="hard",
            exploitation_complexity="high",
            platforms=["Spacecraft", "RF Systems"],
            indicators=["Unusual RF patterns", "Unexpected transmissions"]
        ),
        
        # Exfiltration Techniques
        SPARTATechnique(
            id="EXF-0003",
            name="Downlink Hijacking",
            description="Use spacecraft downlink to exfiltrate stolen data",
            tactic_ids=["ST0012"],
            severity="high",
            examples=[
                "Telemetry manipulation",
                "Covert channels",
                "Data hiding",
                "Scheduled exfiltration"
            ],
            countermeasures=[
                "Downlink monitoring",
                "Data validation",
                "Encryption",
                "Bandwidth monitoring"
            ],
            detection_difficulty="medium",
            exploitation_complexity="medium",
            platforms=["Spacecraft", "Communication Systems"],
            data_sources=["Downlink analysis", "Data volume monitoring"]
        ),
        
        # Impact Techniques
        SPARTATechnique(
            id="IMP-0001",
            name="Denial of Control",
            description="Prevent operators from controlling spacecraft",
            tactic_ids=["ST0013"],
            severity="critical",
            examples=[
                "Command lockout",
                "Control system corruption",
                "Authentication bypass",
                "Operator exclusion"
            ],
            countermeasures=[
                "Redundant control paths",
                "Emergency procedures",
                "Backup systems",
                "Manual overrides"
            ],
            detection_difficulty="easy",
            exploitation_complexity="medium",
            platforms=["Spacecraft", "Control Systems"],
            indicators=["Loss of control", "Command failures", "System unresponsiveness"]
        ),
        
        SPARTATechnique(
            id="IMP-0002",
            name="Spacecraft Hijacking",
            description="Take complete control of spacecraft operations",
            tactic_ids=["ST0013"],
            severity="critical",
            examples=[
                "Full system compromise",
                "Autonomous operation override",
                "Mission redirection",
                "Spacecraft weaponization"
            ],
            countermeasures=[
                "Multi-factor authentication",
                "Hardware security modules",
                "Fail-safe mechanisms",
                "International monitoring"
            ],
            detection_difficulty="easy",
            exploitation_complexity="very_high",
            required_resources="very_high",
            platforms=["Spacecraft"],
            typical_actors=[ThreatActorType.NATION_STATE, ThreatActorType.TERRORIST]
        ),
        
        SPARTATechnique(
            id="IMP-0004",
            name="Kinetic Effects",
            description="Cause physical damage or dangerous maneuvers",
            tactic_ids=["ST0013"],
            severity="critical",
            examples=[
                "Collision course programming",
                "Thruster exhaustion",
                "Solar panel misalignment",
                "Thermal damage"
            ],
            countermeasures=[
                "Safety interlocks",
                "Autonomous collision avoidance",
                "Ground verification required",
                "Hardware limiters"
            ],
            detection_difficulty="easy",
            exploitation_complexity="high",
            platforms=["Spacecraft", "Propulsion Systems"],
            indicators=["Unusual maneuvers", "Trajectory changes", "System alarms"]
        ),
        
        SPARTATechnique(
            id="IMP-0005",
            name="Data Destruction",
            description="Delete or corrupt critical spacecraft data",
            tactic_ids=["ST0013"],
            severity="high",
            examples=[
                "Memory wiping",
                "Firmware corruption",
                "Configuration deletion",
                "Log destruction"
            ],
            countermeasures=[
                "Data backups",
                "Write protection",
                "Integrity checking",
                "Recovery procedures"
            ],
            detection_difficulty="easy",
            exploitation_complexity="medium",
            platforms=["Spacecraft", "Data Storage"],
            data_sources=["File system monitoring", "Integrity checks", "Backup verification"]
        )
    ]
    
    def __init__(self):
        self.tactics_map = {t.id: t for t in self.TACTICS}
        self.techniques_map = {t.id: t for t in self.TECHNIQUES}
        
    def get_enhanced_matrix_data(self) -> Dict[str, Any]:
        """Get enhanced matrix data with all metadata"""
        tactics_data = []
        for tactic in self.TACTICS:
            tactics_data.append({
                "id": tactic.id,
                "name": tactic.name,
                "description": tactic.description,
                "mitre_mapping": tactic.mitre_mapping,
                "objectives": tactic.objectives,
                "typical_actors": [actor.value for actor in tactic.typical_actors]
            })
        
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
                    "exploitation_complexity": tech.exploitation_complexity,
                    "required_resources": tech.required_resources,
                    "typical_actors": [actor.value for actor in tech.typical_actors],
                    "prerequisites": tech.prerequisites,
                    "indicators": tech.indicators,
                    "references": tech.references,
                    "platforms": tech.platforms,
                    "data_sources": tech.data_sources
                })
        
        return {
            "tactics": tactics_data,
            "techniques": techniques_data,
            "metadata": {
                "version": "2.0",
                "last_updated": datetime.now().isoformat(),
                "source": "The Aerospace Corporation SPARTA Framework",
                "total_tactics": len(self.TACTICS),
                "total_techniques": len(self.TECHNIQUES),
                "total_mappings": len(techniques_data)
            }
        }
    
    def get_techniques_by_actor(self, actor_type: ThreatActorType) -> List[SPARTATechnique]:
        """Get all techniques typically used by a specific actor type"""
        return [t for t in self.TECHNIQUES if actor_type in t.typical_actors]
    
    def get_techniques_by_platform(self, platform: str) -> List[SPARTATechnique]:
        """Get all techniques applicable to a specific platform"""
        return [t for t in self.TECHNIQUES if platform in t.platforms]
    
    def get_high_risk_techniques(self) -> List[SPARTATechnique]:
        """Get techniques with critical severity and low complexity"""
        return [
            t for t in self.TECHNIQUES 
            if t.severity == "critical" and 
            t.exploitation_complexity in ["low", "very_low"]
        ]
    
    def generate_attack_scenarios(self) -> List[Dict[str, Any]]:
        """Generate realistic attack scenarios"""
        scenarios = [
            {
                "name": "Nation State Satellite Takeover",
                "description": "Complete compromise of satellite for intelligence gathering",
                "actor": ThreatActorType.NATION_STATE.value,
                "techniques": ["REC-0005", "IA-0007", "EX-0005", "PER-0001", "LM-0001", "COL-0001", "EXF-0003"],
                "impact": "Total loss of satellite control and data",
                "likelihood": "low",
                "mitigation_priority": "critical"
            },
            {
                "name": "Competitor Industrial Espionage",
                "description": "Stealing proprietary satellite technology and data",
                "actor": ThreatActorType.COMPETITOR.value,
                "techniques": ["REC-0001", "IA-0001", "COL-0001", "EXF-0003"],
                "impact": "Loss of competitive advantage",
                "likelihood": "medium",
                "mitigation_priority": "high"
            },
            {
                "name": "Hacktivist Disruption",
                "description": "Publicized disruption of satellite operations",
                "actor": ThreatActorType.HACKTIVIST.value,
                "techniques": ["IA-0001", "EX-0001", "IMP-0001"],
                "impact": "Temporary loss of service, reputation damage",
                "likelihood": "medium",
                "mitigation_priority": "medium"
            }
        ]
        return scenarios
