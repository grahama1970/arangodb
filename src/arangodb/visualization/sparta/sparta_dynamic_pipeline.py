#!/usr/bin/env python3
"""
SPARTA Dynamic Pipeline
Manages the complete flow from SPARTA ingestion to visualization updates
Ensures 100% technique coverage and dynamic actor profile switching
"""

import json
import os
import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from arango import ArangoClient
import websocket
import threading
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SPARTADynamicPipeline:
    """Complete pipeline for SPARTA data processing and visualization"""
    
    def __init__(self, arango_config: Dict[str, Any] = None):
        self.arango_config = arango_config or {
            'host': 'localhost',
            'port': 8529,
            'username': 'root',
            'password': 'password',
            'database': 'sparta'
        }
        self.client = None
        self.db = None
        self.ws_client = None
        self.technique_cache = {}
        self.actor_profiles = self._initialize_actor_profiles()
        
    def _initialize_actor_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Initialize comprehensive actor profiles"""
        return {
            'script_kiddie': {
                'name': 'Script Kiddie',
                'max_complexity': 'low',
                'max_resources': 'low',
                'typical_tactics': ['ST0001', 'ST0003', 'ST0013'],
                'excluded_tactics': ['ST0005', 'ST0006', 'ST0009', 'ST0011'],
                'severity_preference': ['low', 'medium']
            },
            'hacktivist': {
                'name': 'Hacktivist',
                'max_complexity': 'medium',
                'max_resources': 'medium',
                'typical_tactics': ['ST0001', 'ST0003', 'ST0007', 'ST0012', 'ST0013'],
                'severity_preference': ['medium', 'high']
            },
            'criminal': {
                'name': 'Criminal Organization',
                'max_complexity': 'medium',
                'max_resources': 'high',
                'typical_tactics': ['ST0001', 'ST0002', 'ST0003', 'ST0010', 'ST0012'],
                'focus': 'financial_gain'
            },
            'competitor': {
                'name': 'Industry Competitor',
                'max_complexity': 'high',
                'max_resources': 'high',
                'typical_tactics': ['ST0001', 'ST0008', 'ST0010', 'ST0012'],
                'focus': 'espionage'
            },
            'insider': {
                'name': 'Malicious Insider',
                'max_complexity': 'medium',
                'max_resources': 'low',
                'typical_tactics': ['ST0003', 'ST0006', 'ST0010', 'ST0012'],
                'advantages': ['authorized_access', 'knowledge_of_systems']
            },
            'nation_state': {
                'name': 'Nation State Actor',
                'max_complexity': 'very_high',
                'max_resources': 'very_high',
                'all_tactics': True,
                'all_techniques': True
            },
            'china': {
                'name': 'Chinese APT',
                'max_complexity': 'very_high',
                'max_resources': 'very_high',
                'all_tactics': True,
                'emphasis': ['persistence', 'collection', 'supply_chain'],
                'preferred_techniques': ['REC-0002', 'REC-0004', 'IA-0002', 'PER-0003', 'COL-0003']
            },
            'russia': {
                'name': 'Russian APT',
                'max_complexity': 'very_high',
                'max_resources': 'very_high',
                'all_tactics': True,
                'emphasis': ['disruption', 'destruction'],
                'preferred_techniques': ['IA-0003', 'DEF-0003', 'IMP-0001', 'IMP-0005']
            },
            'iran': {
                'name': 'Iranian APT',
                'max_complexity': 'high',
                'max_resources': 'high',
                'typical_tactics': ['ST0001', 'ST0003', 'ST0004', 'ST0007', 'ST0013'],
                'focus': 'regional_targets'
            },
            'north_korea': {
                'name': 'North Korean APT',
                'max_complexity': 'high',
                'max_resources': 'medium',
                'typical_tactics': ['ST0001', 'ST0003', 'ST0010', 'ST0012'],
                'focus': 'financial_and_espionage'
            }
        }
        
    def connect_arangodb(self):
        """Connect to ArangoDB"""
        try:
            self.client = ArangoClient(hosts=f"http://{self.arango_config['host']}:{self.arango_config['port']}")
            
            # Connect to _system database first
            sys_db = self.client.db('_system', 
                                   username=self.arango_config['username'],
                                   password=self.arango_config['password'])
            
            # Create SPARTA database if not exists
            if not sys_db.has_database(self.arango_config['database']):
                sys_db.create_database(self.arango_config['database'])
                
            # Connect to SPARTA database
            self.db = self.client.db(self.arango_config['database'],
                                    username=self.arango_config['username'],
                                    password=self.arango_config['password'])
            
            # Ensure collections exist
            self._ensure_collections()
            
            logger.info("Connected to ArangoDB")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to ArangoDB: {e}")
            return False
            
    def _ensure_collections(self):
        """Ensure all required collections exist"""
        collections = [
            'tactics', 'techniques', 'actors', 'analyses', 
            'attack_chains', 'indicators', 'threat_profiles'
        ]
        
        edge_collections = [
            'implements_tactic', 'uses_technique', 'part_of_chain',
            'detected_in', 'performed_by'
        ]
        
        for collection in collections:
            if not self.db.has_collection(collection):
                self.db.create_collection(collection)
                logger.info(f"Created collection: {collection}")
                
        for edge_collection in edge_collections:
            if not self.db.has_collection(edge_collection):
                self.db.create_collection(edge_collection, edge=True)
                logger.info(f"Created edge collection: {edge_collection}")
                
    def import_sparta_data(self, import_file: str) -> Dict[str, int]:
        """Import SPARTA data into ArangoDB"""
        logger.info(f"Importing SPARTA data from {import_file}")
        
        with open(import_file, 'r') as f:
            import_data = json.load(f)
            
        stats = {
            'tactics': 0,
            'techniques': 0,
            'edges': 0
        }
        
        # Import tactics
        tactics_collection = self.db.collection('tactics')
        for tactic in import_data['collections']['tactics']:
            try:
                tactics_collection.insert(tactic, overwrite=True)
                stats['tactics'] += 1
            except Exception as e:
                logger.error(f"Error inserting tactic {tactic['_key']}: {e}")
                
        # Import techniques with 100% coverage assurance
        techniques_collection = self.db.collection('techniques')
        for technique in import_data['collections']['techniques']:
            # Ensure all required fields
            technique['created_at'] = datetime.now().isoformat()
            technique['last_updated'] = datetime.now().isoformat()
            technique['usage_count'] = 0
            
            try:
                techniques_collection.insert(technique, overwrite=True)
                stats['techniques'] += 1
                self.technique_cache[technique['_key']] = technique
            except Exception as e:
                logger.error(f"Error inserting technique {technique['_key']}: {e}")
                
        # Import edges
        for edge_type, edges in import_data['edges'].items():
            edge_collection = self.db.collection(edge_type)
            for edge in edges:
                try:
                    edge_collection.insert(edge, overwrite=True)
                    stats['edges'] += 1
                except Exception as e:
                    logger.error(f"Error inserting edge: {e}")
                    
        # Create actor profiles
        self._create_actor_profiles()
        
        logger.info(f"Import complete: {stats}")
        return stats
        
    def _create_actor_profiles(self):
        """Create actor profiles in database"""
        actors_collection = self.db.collection('actors')
        
        for actor_id, profile in self.actor_profiles.items():
            actor_doc = {
                '_key': actor_id,
                'name': profile['name'],
                'profile': profile,
                'created_at': datetime.now().isoformat()
            }
            
            try:
                actors_collection.insert(actor_doc, overwrite=True)
            except Exception as e:
                logger.error(f"Error creating actor profile {actor_id}: {e}")
                
    def get_techniques_for_actor(self, actor_profile: str) -> List[Dict[str, Any]]:
        """Get techniques available to specific actor profile"""
        if actor_profile == 'all':
            # Return all techniques
            query = """
            FOR t IN techniques
                RETURN t
            """
        else:
            profile = self.actor_profiles.get(actor_profile, {})
            
            if profile.get('all_techniques'):
                # Nation state actors have access to all techniques
                query = """
                FOR t IN techniques
                    RETURN t
                """
            else:
                # Filter based on actor capabilities
                max_complexity = profile.get('max_complexity', 'medium')
                typical_tactics = profile.get('typical_tactics', [])
                excluded_tactics = profile.get('excluded_tactics', [])
                
                query = """
                FOR t IN techniques
                    LET complexity_ok = (
                        @max_complexity == 'very_high' OR
                        (t.complexity == 'low') OR
                        (@max_complexity == 'low' AND t.complexity == 'low') OR
                        (@max_complexity == 'medium' AND t.complexity IN ['low', 'medium']) OR
                        (@max_complexity == 'high' AND t.complexity IN ['low', 'medium', 'high'])
                    )
                    LET tactic_ok = (
                        LENGTH(@typical_tactics) == 0 OR
                        LENGTH(INTERSECTION(t.tactic_ids, @typical_tactics)) > 0
                    )
                    LET not_excluded = (
                        LENGTH(@excluded_tactics) == 0 OR
                        LENGTH(INTERSECTION(t.tactic_ids, @excluded_tactics)) == 0
                    )
                    FILTER complexity_ok AND tactic_ok AND not_excluded
                    RETURN t
                """
                
        cursor = self.db.aql.execute(
            query,
            bind_vars={
                'max_complexity': profile.get('max_complexity', 'medium'),
                'typical_tactics': profile.get('typical_tactics', []),
                'excluded_tactics': profile.get('excluded_tactics', [])
            }
        )
        
        return list(cursor)
        
    def update_visualization(self, actor_profile: str = 'all', pdf_analysis: Dict[str, Any] = None):
        """Send update to visualization via WebSocket"""
        try:
            # Get filtered techniques
            techniques = self.get_techniques_for_actor(actor_profile)
            
            # Get all tactics
            tactics_cursor = self.db.aql.execute("FOR t IN tactics RETURN t")
            tactics = list(tactics_cursor)
            
            # Build update message
            update_data = {
                'type': 'matrix_update',
                'actor_profile': actor_profile,
                'tactics': [
                    {
                        'id': t['_key'],
                        'name': t['name'],
                        'description': t['description']
                    }
                    for t in tactics
                ],
                'techniques': [
                    {
                        'id': t['_key'],
                        'name': t['name'],
                        'description': t['description'],
                        'severity': t['severity'],
                        'tactic_ids': t.get('tactic_ids', []),
                        'active': True,
                        'complexity': t.get('complexity', 'medium'),
                        'detection_difficulty': t.get('detection_difficulty', 'medium'),
                        'countermeasures': t.get('countermeasures', [])
                    }
                    for t in techniques
                ],
                'metadata': {
                    'total_techniques': len(techniques),
                    'timestamp': datetime.now().isoformat(),
                    'coverage_percentage': (len(techniques) / len(self.technique_cache)) * 100
                }
            }
            
            # Add PDF analysis results if provided
            if pdf_analysis:
                update_data['pdf_analysis'] = pdf_analysis
                
            # Send via WebSocket
            self._send_websocket_update(update_data)
            
            logger.info(f"Sent visualization update for actor: {actor_profile}")
            
        except Exception as e:
            logger.error(f"Error updating visualization: {e}")
            
    def _send_websocket_update(self, data: Dict[str, Any]):
        """Send update via WebSocket connection"""
        ws_url = "ws://localhost:5000/socket.io/?EIO=4&transport=websocket"
        
        try:
            if not self.ws_client or not self.ws_client.connected:
                self.ws_client = websocket.WebSocket()
                self.ws_client.connect(ws_url)
                
            message = json.dumps({
                'type': 'data_update',
                'data': data
            })
            
            self.ws_client.send(message)
            
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            
    def process_pdf_analysis(self, pdf_path: str, extraction_result: Dict[str, Any]):
        """Process PDF analysis results and update visualization"""
        # Store analysis in ArangoDB
        analyses_collection = self.db.collection('analyses')
        
        analysis_doc = {
            '_key': f"analysis_{int(time.time())}",
            'pdf_path': pdf_path,
            'timestamp': datetime.now().isoformat(),
            'detected_techniques': extraction_result.get('detected_techniques', []),
            'detected_tactics': extraction_result.get('detected_tactics', []),
            'indicators': extraction_result.get('indicators', {}),
            'threat_assessment': extraction_result.get('threat_assessment', {})
        }
        
        try:
            analyses_collection.insert(analysis_doc)
            
            # Create edges for detected techniques
            for tech_id in extraction_result.get('detected_techniques', []):
                edge_doc = {
                    '_from': f"analyses/{analysis_doc['_key']}",
                    '_to': f"techniques/{tech_id}",
                    'confidence': extraction_result.get('threat_assessment', {}).get('score', 0)
                }
                self.db.collection('detected_in').insert(edge_doc)
                
            # Determine likely actor profile
            actor_profile = self._determine_actor_from_techniques(
                extraction_result.get('detected_techniques', [])
            )
            
            # Update visualization with PDF analysis
            self.update_visualization(
                actor_profile=actor_profile,
                pdf_analysis=analysis_doc
            )
            
            logger.info(f"Processed PDF analysis: {pdf_path}")
            
        except Exception as e:
            logger.error(f"Error processing PDF analysis: {e}")
            
    def _determine_actor_from_techniques(self, technique_ids: List[str]) -> str:
        """Determine most likely actor based on detected techniques"""
        if not technique_ids:
            return 'unknown'
            
        # Get technique details
        techniques = []
        for tech_id in technique_ids:
            if tech_id in self.technique_cache:
                techniques.append(self.technique_cache[tech_id])
                
        if not techniques:
            return 'unknown'
            
        # Score each actor profile
        actor_scores = {}
        
        for actor_id, profile in self.actor_profiles.items():
            score = 0
            
            # Check complexity match
            max_complexity = profile.get('max_complexity', 'medium')
            complexity_levels = ['low', 'medium', 'high', 'very_high']
            
            for tech in techniques:
                tech_complexity = tech.get('complexity', 'medium')
                if max_complexity == 'very_high':
                    score += 1
                elif complexity_levels.index(tech_complexity) <= complexity_levels.index(max_complexity):
                    score += 1
                    
            # Check tactic alignment
            if 'typical_tactics' in profile:
                for tech in techniques:
                    if any(tactic in profile['typical_tactics'] for tactic in tech.get('tactic_ids', [])):
                        score += 2
                        
            # Check preferred techniques
            if 'preferred_techniques' in profile:
                for tech_id in technique_ids:
                    if tech_id in profile['preferred_techniques']:
                        score += 3
                        
            actor_scores[actor_id] = score
            
        # Return actor with highest score
        if actor_scores:
            return max(actor_scores, key=actor_scores.get)
        else:
            return 'nation_state'  # Default to nation state for unknown patterns
            
    def run_continuous_update_loop(self, interval: int = 30):
        """Run continuous update loop for live data changes"""
        logger.info(f"Starting continuous update loop (interval: {interval}s)")
        
        while True:
            try:
                # Check for new analyses
                query = """
                FOR a IN analyses
                    FILTER a.processed != true
                    LIMIT 10
                    RETURN a
                """
                
                cursor = self.db.aql.execute(query)
                new_analyses = list(cursor)
                
                for analysis in new_analyses:
                    # Process and send updates
                    actor_profile = self._determine_actor_from_techniques(
                        analysis.get('detected_techniques', [])
                    )
                    self.update_visualization(actor_profile, analysis)
                    
                    # Mark as processed
                    self.db.collection('analyses').update(
                        analysis['_key'],
                        {'processed': True}
                    )
                    
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("Stopping update loop")
                break
            except Exception as e:
                logger.error(f"Error in update loop: {e}")
                time.sleep(interval)


def main():
    """Main pipeline execution"""
    # Initialize pipeline
    pipeline = SPARTADynamicPipeline({
        'host': 'localhost',
        'port': 8529,
        'username': 'root',
        'password': 'your_password',  # Update this
        'database': 'sparta'
    })
    
    # Connect to ArangoDB
    if not pipeline.connect_arangodb():
        logger.error("Failed to connect to ArangoDB")
        return
        
    # Import SPARTA data
    import_file = '/home/graham/workspace/experiments/arangodb/sparta_arangodb_import.json'
    if os.path.exists(import_file):
        stats = pipeline.import_sparta_data(import_file)
        print(f"\nImport Statistics:")
        print(f"Tactics: {stats['tactics']}")
        print(f"Techniques: {stats['techniques']}")
        print(f"Edges: {stats['edges']}")
    else:
        logger.error(f"Import file not found: {import_file}")
        return
        
    # Test actor profile filtering
    print("\nTesting actor profiles:")
    for actor_id in ['script_kiddie', 'nation_state', 'china']:
        techniques = pipeline.get_techniques_for_actor(actor_id)
        print(f"{actor_id}: {len(techniques)} techniques available")
        
    # Run continuous update loop
    print("\nStarting continuous update loop...")
    pipeline.run_continuous_update_loop()
    

if __name__ == '__main__':
    main()
