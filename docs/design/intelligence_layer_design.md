# Intelligence Layer Design for Graph Generation

## Problem Statement
Users say: "Show me customers most related by pizza preferences"
Current system requires: Complex AQL query writing

## Proposed Intelligence Layer

### 1. Intent Recognition
```python
class GraphIntentRecognizer:
    def analyze_request(self, user_input: str) -> GraphIntent:
        """
        Patterns to detect:
        - "customers most related by X" → similarity network
        - "show connections between X and Y" → relationship graph
        - "how are X connected" → path analysis
        - "group X by Y" → clustering visualization
        """
        
        intent_patterns = {
            'similarity': ['related by', 'similar', 'alike', 'comparable'],
            'connections': ['connected', 'relationships', 'links between'],
            'hierarchy': ['hierarchy', 'tree', 'parent-child', 'flows from'],
            'clustering': ['group by', 'categorize', 'cluster', 'organize']
        }
        
        # Use LLM + pattern matching to determine intent
        return GraphIntent(
            type='similarity',
            entities=['customers'],
            relationship_basis=['pizza preferences'],
            suggested_layout='force'
        )
```

### 2. Smart AQL Generator
```python
class SmartAQLGenerator:
    def generate_similarity_query(self, entities: str, basis: str) -> str:
        """Generate AQL for similarity networks"""
        
        if entities == 'customers' and 'pizza' in basis:
            return """
            // Auto-generated similarity query
            LET customer_preferences = (
                FOR c IN customers
                    FOR order IN 1..1 OUTBOUND c customer_orders
                        FOR pizza IN 1..1 OUTBOUND order order_items
                            FOR ingredient IN 1..1 OUTBOUND pizza pizza_ingredients
                                COLLECT customer_id = c._key, customer_name = c.name, 
                                        ingredient_name = ingredient.name
                                RETURN {customer_id, customer_name, ingredient: ingredient_name}
            )
            
            LET similarity_pairs = (/* similarity logic */)
            
            RETURN {
                nodes: /* customer nodes */,
                links: /* similarity links */
            }
            """
    
    def generate_hierarchy_query(self, entities: str) -> str:
        """Generate AQL for hierarchical relationships"""
        # Template for tree/hierarchy queries
        
    def generate_connection_query(self, entity1: str, entity2: str) -> str:
        """Generate AQL for connection analysis"""
        # Template for shortest path / connection queries
```

### 3. Conversational Graph Interface
```python
class ConversationalGraphGenerator:
    def __init__(self):
        self.intent_recognizer = GraphIntentRecognizer()
        self.aql_generator = SmartAQLGenerator()
        self.viz_engine = D3VisualizationEngine()
    
    async def process_graph_request(self, user_input: str) -> GraphResponse:
        """
        User: "Show me customers most related by pizza preferences"
        
        Returns: {
            'type': 'graph',
            'title': 'Customer Similarity by Pizza Preferences', 
            'graphData': {...},
            'layout': 'force',
            'explanation': 'This shows 3 customers connected by shared ingredient preferences...',
            'query_used': 'Generated AQL query...',
            'insights': ['John and Jane both prefer pepperoni', ...]
        }
        """
        
        # 1. Understand intent
        intent = self.intent_recognizer.analyze_request(user_input)
        
        # 2. Generate appropriate AQL
        aql_query = self.aql_generator.generate_for_intent(intent)
        
        # 3. Execute query
        graph_data = await self.execute_aql(aql_query)
        
        # 4. Generate insights
        insights = self.analyze_graph_patterns(graph_data)
        
        # 5. Return for chat integration
        return GraphResponse(
            type='graph',
            title=intent.suggested_title,
            graphData=graph_data,
            layout=intent.suggested_layout,
            explanation=self.generate_explanation(graph_data, intent),
            insights=insights
        )
```

### 4. Usage Examples

**Human:** "Show me customers most related by pizza preferences"
**Agent:** *Generates similarity network graph inline* "Here's a network showing customer relationships based on shared pizza topping preferences. John and Jane are most similar (3 shared ingredients), while Bob is connected through 1 shared preference."

**Human:** "How are pizzas connected to ingredients?"
**Agent:** *Generates ingredient network* "This bipartite graph shows all pizza-ingredient relationships. Margherita pizza uses the fewest ingredients (3), while Meat Lovers uses the most (4)."

**Human:** "Show me the flow from customers to orders to pizzas"
**Agent:** *Generates Sankey diagram* "Here's the order flow. You can see John placed the largest order, and Pepperoni is the most popular pizza choice."

## Integration Points

1. **MCP Integration**: Agent can call graph generation functions
2. **Chat UI**: React components render graphs inline
3. **Human Access**: Same interface available to human users
4. **Context Awareness**: Graphs maintain conversation context
5. **Follow-up Questions**: "Show me just the high-similarity customers" → filters existing graph

## Benefits
- ✅ Natural language to graph
- ✅ No AQL expertise required
- ✅ Inline chat integration
- ✅ Agent and human can both use
- ✅ Contextual and conversational
- ✅ Real-time graph generation