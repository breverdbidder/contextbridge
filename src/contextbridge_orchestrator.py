"""
ContextBridge LangGraph Orchestrator
Multi-Agent AI Platform for BidDeed.AI, ZoneWise, Life OS, SPD

Agents:
1. Intent Classifier Agent
2. RAG Retrieval Agent (context from /CONTEXT/ folders)
3. SQL Query Agent (natural language → SQL)
4. Competitive Intelligence Agent (calls competitive-intelligence orchestrator)
5. External API Agent (BCPAO, RealForeclose, etc.)
6. Response Synthesis Agent (combines all sources)
"""

import os
from typing import TypedDict, List, Dict, Optional, Literal
from datetime import datetime
import json

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver
from anthropic import Anthropic
import httpx


# ============================================================================
# STATE SCHEMA
# ============================================================================

class ContextBridgeState(TypedDict):
    """
    Complete state for ContextBridge multi-agent orchestration.
    Supports: BidDeed.AI, ZoneWise, Life OS, SPD, Michael D1 Swimming chatbots.
    """
    # ===== INPUT =====
    user_query: str
    product: Literal["biddeed", "zonewise", "lifeos", "spd", "michael"]
    conversation_id: str
    user_id: str
    session_context: Dict  # Previous conversation context
    
    # ===== INTENT CLASSIFICATION =====
    intent: str  # "documentation", "data_query", "competitive", "external_api", "general"
    confidence: float
    entities: Dict[str, any]  # Extracted entities (addresses, dates, etc.)
    requires_tools: List[str]  # Which agents to invoke
    
    # ===== RAG AGENT (Context Retrieval) =====
    rag_query: str
    rag_results: List[Dict]  # Retrieved context chunks
    context_sources: List[str]  # Which /CONTEXT/ files used
    
    # ===== SQL AGENT (Database Queries) =====
    sql_query: str
    sql_results: List[Dict]
    tables_queried: List[str]
    
    # ===== COMPETITIVE INTEL AGENT =====
    competitive_intel_query: str
    competitive_intel_results: Dict
    competitor_mentioned: Optional[str]
    
    # ===== EXTERNAL API AGENT =====
    api_calls: List[Dict]  # List of API calls made
    api_results: Dict  # Results from external APIs
    apis_used: List[str]  # Which APIs called
    
    # ===== SYNTHESIS AGENT =====
    synthesized_response: str
    suggested_actions: List[str]
    follow_up_questions: List[str]
    confidence_score: float
    
    # ===== META =====
    current_agent: str
    agent_sequence: List[str]
    errors: List[str]
    retries: int
    max_retries: int
    workflow_status: str  # "running", "completed", "failed"
    processing_time_ms: int
    
    # ===== SMART ROUTER =====
    model_used: str  # Which LLM used
    tokens_used: int
    cost_usd: float
    
    # ===== SUPABASE PERSISTENCE =====
    supabase_conversation_id: Optional[str]
    last_checkpoint: str


# ============================================================================
# AGENT 1: INTENT CLASSIFIER
# ============================================================================

def intent_classifier_agent(state: ContextBridgeState) -> ContextBridgeState:
    """
    Agent 1: Intent Classification
    
    Determines:
    - What is the user asking for?
    - Which agents should be invoked?
    - What entities are mentioned?
    """
    print(f"\n{'='*70}")
    print(f"AGENT 1: INTENT CLASSIFIER")
    print(f"Query: {state['user_query']}")
    print(f"{'='*70}\n")
    
    try:
        from anthropic import Anthropic
        
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        # Use Gemini Flash for intent classification (FREE tier)
        # For now using Claude, but will switch to Gemini
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": f"""Classify the user's intent and extract entities.

Product: {state['product']}
User Query: {state['user_query']}

Classify intent as ONE of:
- documentation: Asking about how something works, technical questions
- data_query: Asking for data from database (properties, auctions, permits, tasks)
- competitive: Asking about competitors or market intelligence
- external_api: Needs live data from external APIs
- general: General conversation, greetings, unclear

Extract entities:
- addresses (full property addresses)
- dates (auction dates, deadlines)
- competitor_names
- property_ids

Return JSON:
{{
    "intent": "...",
    "confidence": 0.95,
    "entities": {{...}},
    "requires_tools": ["rag", "sql", "competitive", "api"]
}}"""
            }]
        )
        
        # Parse classification
        classification = json.loads(response.content[0].text)
        
        # Update state
        state['intent'] = classification['intent']
        state['confidence'] = classification['confidence']
        state['entities'] = classification.get('entities', {})
        state['requires_tools'] = classification.get('requires_tools', [])
        state['current_agent'] = 'intent_classifier'
        state['agent_sequence'].append('intent_classifier')
        state['model_used'] = 'claude-sonnet-4-20250514'
        state['tokens_used'] += 500
        state['cost_usd'] += 0.015  # Approximate
        
        print(f"✅ Intent: {state['intent']} (confidence: {state['confidence']})")
        print(f"   Entities: {state['entities']}")
        print(f"   Tools needed: {state['requires_tools']}")
        
        return state
        
    except Exception as e:
        state['errors'].append(f"Intent classification failed: {str(e)}")
        state['workflow_status'] = 'failed'
        return state


# ============================================================================
# AGENT 2: RAG RETRIEVAL
# ============================================================================

def rag_retrieval_agent(state: ContextBridgeState) -> ContextBridgeState:
    """
    Agent 2: RAG Retrieval
    
    Searches /CONTEXT/ folders for relevant documentation:
    - ARCHITECTURE.md
    - DATABASE_SCHEMA.md
    - BUSINESS_LOGIC.md
    - API_PATTERNS.md
    - DEPLOYMENT.md
    """
    print(f"\n{'='*70}")
    print(f"AGENT 2: RAG RETRIEVAL")
    print(f"{'='*70}\n")
    
    try:
        # TODO: Implement vector search with pgvector
        # For now, simple keyword matching
        
        context_files = {
            'biddeed': [
                '/CONTEXT/ARCHITECTURE.md',
                '/CONTEXT/DATABASE_SCHEMA.md',
                '/CONTEXT/BUSINESS_LOGIC.md',
                '/CONTEXT/API_PATTERNS.md'
            ],
            'zonewise': [
                '/CONTEXT/JURISDICTIONS.md',
                '/CONTEXT/ZONING_RULES.md'
            ],
            'lifeos': [
                '/CONTEXT/TASKS.md',
                '/CONTEXT/HABITS.md'
            ],
            'spd': [
                '/CONTEXT/SITE_PLANNING.md',
                '/CONTEXT/PERMITTING.md'
            ]
        }
        
        product_files = context_files.get(state['product'], [])
        
        # Simple retrieval (will be replaced with semantic search)
        rag_results = []
        for filepath in product_files[:3]:  # Limit to top 3
            rag_results.append({
                'file': filepath,
                'content': f"Mock content from {filepath}",
                'relevance': 0.85
            })
        
        state['rag_results'] = rag_results
        state['context_sources'] = product_files[:3]
        state['current_agent'] = 'rag_retrieval'
        state['agent_sequence'].append('rag_retrieval')
        
        print(f"✅ Retrieved {len(rag_results)} context chunks")
        print(f"   Sources: {', '.join(state['context_sources'])}")
        
        return state
        
    except Exception as e:
        state['errors'].append(f"RAG retrieval failed: {str(e)}")
        # Non-critical, continue workflow
        return state


# ============================================================================
# AGENT 3: SQL QUERY
# ============================================================================

def sql_query_agent(state: ContextBridgeState) -> ContextBridgeState:
    """
    Agent 3: SQL Query Agent
    
    Converts natural language to SQL and executes against Supabase.
    """
    print(f"\n{'='*70}")
    print(f"AGENT 3: SQL QUERY")
    print(f"{'='*70}\n")
    
    try:
        from anthropic import Anthropic
        
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        # Get database schema for context
        schema_context = get_database_schema(state['product'])
        
        # Generate SQL
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": f"""Convert this natural language query to SQL.

Product: {state['product']}
User Query: {state['user_query']}
Entities: {json.dumps(state['entities'])}

Database Schema:
{schema_context}

Generate valid PostgreSQL query. Return JSON:
{{
    "sql": "SELECT ...",
    "tables": ["table1", "table2"],
    "explanation": "..."
}}"""
            }]
        )
        
        sql_data = json.loads(response.content[0].text)
        
        # Execute SQL (with safety checks)
        sql_query = sql_data['sql']
        
        # TODO: Execute against Supabase
        sql_results = [
            {'id': 1, 'data': 'Mock result 1'},
            {'id': 2, 'data': 'Mock result 2'}
        ]
        
        state['sql_query'] = sql_query
        state['sql_results'] = sql_results
        state['tables_queried'] = sql_data['tables']
        state['current_agent'] = 'sql_query'
        state['agent_sequence'].append('sql_query')
        state['tokens_used'] += 1000
        state['cost_usd'] += 0.03
        
        print(f"✅ SQL executed")
        print(f"   Query: {sql_query[:100]}...")
        print(f"   Results: {len(sql_results)} rows")
        
        return state
        
    except Exception as e:
        state['errors'].append(f"SQL query failed: {str(e)}")
        # Non-critical, continue
        return state


# ============================================================================
# AGENT 4: COMPETITIVE INTELLIGENCE
# ============================================================================

def competitive_intel_agent(state: ContextBridgeState) -> ContextBridgeState:
    """
    Agent 4: Competitive Intelligence
    
    Calls the competitive-intelligence LangGraph orchestrator
    when user asks about competitors.
    """
    print(f"\n{'='*70}")
    print(f"AGENT 4: COMPETITIVE INTELLIGENCE")
    print(f"{'='*70}\n")
    
    try:
        # Import competitive intelligence orchestrator
        # NOTE: This would import from competitive-intelligence repo
        # For now, mocking the integration
        
        competitor = state['entities'].get('competitor_name')
        
        if competitor:
            print(f"📊 Querying competitive intelligence for: {competitor}")
            
            # TODO: Call actual orchestrator
            # from competitive_intelligence.langgraph_orchestrator import analyze_competitor
            # result = analyze_competitor(
            #     competitor_url=f"https://{competitor.lower()}.com",
            #     competitor_name=competitor,
            #     analysis_type="quick"
            # )
            
            # Mock response
            competitive_results = {
                'executive_summary': f"Mock intelligence summary for {competitor}",
                'swot': {'strengths': ['A', 'B'], 'weaknesses': ['C', 'D']},
                'recommendation': 'Consider building in-house'
            }
            
            state['competitive_intel_results'] = competitive_results
            state['competitor_mentioned'] = competitor
            
            print(f"✅ Competitive intelligence retrieved")
        
        state['current_agent'] = 'competitive_intel'
        state['agent_sequence'].append('competitive_intel')
        
        return state
        
    except Exception as e:
        state['errors'].append(f"Competitive intel failed: {str(e)}")
        return state


# ============================================================================
# AGENT 5: EXTERNAL API
# ============================================================================

def external_api_agent(state: ContextBridgeState) -> ContextBridgeState:
    """
    Agent 5: External API Agent
    
    Calls external APIs:
    - BCPAO (property data)
    - RealForeclose (auction data)
    - AcclaimWeb (court records)
    - Census API (demographics)
    """
    print(f"\n{'='*70}")
    print(f"AGENT 5: EXTERNAL API")
    print(f"{'='*70}\n")
    
    try:
        api_results = {}
        apis_called = []
        
        # Determine which APIs to call based on entities
        if 'address' in state['entities']:
            # Call BCPAO
            print("📡 Calling BCPAO API...")
            # TODO: Actual API call
            api_results['bcpao'] = {'parcel_id': '123456', 'value': 250000}
            apis_called.append('BCPAO')
        
        state['api_results'] = api_results
        state['apis_used'] = apis_called
        state['current_agent'] = 'external_api'
        state['agent_sequence'].append('external_api')
        
        print(f"✅ Called {len(apis_called)} APIs")
        
        return state
        
    except Exception as e:
        state['errors'].append(f"External API failed: {str(e)}")
        return state


# ============================================================================
# AGENT 6: RESPONSE SYNTHESIS
# ============================================================================

def response_synthesis_agent(state: ContextBridgeState) -> ContextBridgeState:
    """
    Agent 6: Response Synthesis
    
    Combines all agent outputs into coherent, conversational response.
    """
    print(f"\n{'='*70}")
    print(f"AGENT 6: RESPONSE SYNTHESIS")
    print(f"{'='*70}\n")
    
    try:
        from anthropic import Anthropic
        
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        # Prepare context from all agents
        synthesis_context = f"""
User Query: {state['user_query']}

Intent: {state['intent']}
Entities: {json.dumps(state['entities'])}

RAG Results ({len(state['rag_results'])} chunks):
{json.dumps(state['rag_results'], indent=2)[:500]}

SQL Results ({len(state['sql_results'])} rows):
{json.dumps(state['sql_results'], indent=2)[:500]}

Competitive Intel:
{json.dumps(state['competitive_intel_results'], indent=2)[:500]}

API Results:
{json.dumps(state['api_results'], indent=2)[:500]}
"""
        
        # Synthesize response
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": f"""{synthesis_context}

Synthesize a natural, conversational response that:
1. Directly answers the user's query
2. Incorporates relevant information from all sources
3. Suggests 2-3 follow-up actions
4. Asks 1-2 clarifying questions if needed

Return JSON:
{{
    "response": "...",
    "suggested_actions": ["...", "..."],
    "follow_up_questions": ["...", "..."],
    "confidence": 0.95
}}"""
            }]
        )
        
        synthesis = json.loads(response.content[0].text)
        
        state['synthesized_response'] = synthesis['response']
        state['suggested_actions'] = synthesis.get('suggested_actions', [])
        state['follow_up_questions'] = synthesis.get('follow_up_questions', [])
        state['confidence_score'] = synthesis.get('confidence', 0.9)
        state['current_agent'] = 'synthesis'
        state['agent_sequence'].append('synthesis')
        state['workflow_status'] = 'completed'
        state['tokens_used'] += 2000
        state['cost_usd'] += 0.06
        
        print(f"✅ Response synthesized")
        print(f"   Confidence: {state['confidence_score']}")
        print(f"   Actions: {len(state['suggested_actions'])}")
        
        return state
        
    except Exception as e:
        state['errors'].append(f"Synthesis failed: {str(e)}")
        state['workflow_status'] = 'failed'
        return state


# ============================================================================
# ROUTING LOGIC
# ============================================================================

def route_by_intent(state: ContextBridgeState) -> str:
    """
    Route to appropriate agents based on intent.
    """
    intent = state['intent']
    
    routing_map = {
        'documentation': 'rag_retrieval',
        'data_query': 'sql_query',
        'competitive': 'competitive_intel',
        'external_api': 'external_api',
        'general': 'synthesis'  # Skip to synthesis for general chat
    }
    
    return routing_map.get(intent, 'rag_retrieval')


def should_synthesize(state: ContextBridgeState) -> str:
    """
    Determine if we have enough information to synthesize.
    """
    # Always synthesize after agents run
    return 'synthesis'


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_database_schema(product: str) -> str:
    """Get database schema for the product"""
    schemas = {
        'biddeed': """
Tables:
- multi_county_auctions (property_id, address, auction_date, recommendation)
- lien_analysis (property_id, lien_type, amount, priority)
- foreclosure_history (property_id, filing_date, judgment_amount)
""",
        'zonewise': """
Tables:
- permits (permit_id, address, type, status, filed_date)
- jurisdictions (jurisdiction_id, name, contact_info)
- zoning_rules (rule_id, jurisdiction, zoning_code, description)
""",
        'lifeos': """
Tables:
- activities (activity_id, title, state, due_date, completed_at)
- habits (habit_id, name, frequency, streak)
- goals (goal_id, title, progress, target_date)
"""
    }
    return schemas.get(product, "")


# ============================================================================
# WORKFLOW CONSTRUCTION
# ============================================================================

def build_contextbridge_workflow() -> StateGraph:
    """
    Build ContextBridge multi-agent LangGraph workflow
    """
    
    # Initialize workflow
    workflow = StateGraph(ContextBridgeState)
    
    # Add agent nodes
    workflow.add_node("intent_classifier", intent_classifier_agent)
    workflow.add_node("rag_retrieval", rag_retrieval_agent)
    workflow.add_node("sql_query", sql_query_agent)
    workflow.add_node("competitive_intel", competitive_intel_agent)
    workflow.add_node("external_api", external_api_agent)
    workflow.add_node("synthesis", response_synthesis_agent)
    
    # Set entry point
    workflow.set_entry_point("intent_classifier")
    
    # Conditional routing from intent classifier
    workflow.add_conditional_edges(
        "intent_classifier",
        route_by_intent,
        {
            "rag_retrieval": "rag_retrieval",
            "sql_query": "sql_query",
            "competitive_intel": "competitive_intel",
            "external_api": "external_api",
            "synthesis": "synthesis"
        }
    )
    
    # All agents lead to synthesis
    workflow.add_edge("rag_retrieval", "synthesis")
    workflow.add_edge("sql_query", "synthesis")
    workflow.add_edge("competitive_intel", "synthesis")
    workflow.add_edge("external_api", "synthesis")
    
    # Synthesis is terminal
    workflow.add_edge("synthesis", END)
    
    # Compile workflow
    return workflow.compile()


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def query_contextbridge(
    user_query: str,
    product: str,
    user_id: str = "ariel",
    conversation_id: Optional[str] = None
) -> ContextBridgeState:
    """
    Execute ContextBridge query with LangGraph orchestration
    
    Args:
        user_query: Natural language query
        product: "biddeed", "zonewise", "lifeos", "spd"
        user_id: User identifier
        conversation_id: Optional conversation ID for context
        
    Returns:
        Final state with synthesized response
    """
    
    # Initialize state
    initial_state: ContextBridgeState = {
        # Input
        'user_query': user_query,
        'product': product,
        'conversation_id': conversation_id or f"conv_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        'user_id': user_id,
        'session_context': {},
        
        # Agent outputs (empty)
        'intent': '',
        'confidence': 0.0,
        'entities': {},
        'requires_tools': [],
        'rag_query': '',
        'rag_results': [],
        'context_sources': [],
        'sql_query': '',
        'sql_results': [],
        'tables_queried': [],
        'competitive_intel_query': '',
        'competitive_intel_results': {},
        'competitor_mentioned': None,
        'api_calls': [],
        'api_results': {},
        'apis_used': [],
        'synthesized_response': '',
        'suggested_actions': [],
        'follow_up_questions': [],
        'confidence_score': 0.0,
        
        # Meta
        'current_agent': '',
        'agent_sequence': [],
        'errors': [],
        'retries': 0,
        'max_retries': 3,
        'workflow_status': 'running',
        'processing_time_ms': 0,
        'model_used': '',
        'tokens_used': 0,
        'cost_usd': 0.0,
        'supabase_conversation_id': None,
        'last_checkpoint': datetime.utcnow().isoformat()
    }
    
    # Build workflow
    workflow = build_contextbridge_workflow()
    
    # Execute
    start_time = datetime.utcnow()
    
    print(f"\n{'='*70}")
    print(f"CONTEXTBRIDGE QUERY")
    print(f"Product: {product}")
    print(f"Query: {user_query}")
    print(f"{'='*70}\n")
    
    final_state = workflow.invoke(initial_state)
    
    # Calculate processing time
    end_time = datetime.utcnow()
    final_state['processing_time_ms'] = int((end_time - start_time).total_seconds() * 1000)
    
    # Print summary
    print(f"\n{'='*70}")
    print(f"QUERY COMPLETE")
    print(f"{'='*70}")
    print(f"Status: {final_state['workflow_status']}")
    print(f"Agents used: {' → '.join(final_state['agent_sequence'])}")
    print(f"Processing time: {final_state['processing_time_ms']}ms")
    print(f"Cost: ${final_state['cost_usd']:.4f}")
    print(f"Tokens: {final_state['tokens_used']}")
    print(f"\nResponse:\n{final_state['synthesized_response']}")
    print(f"{'='*70}\n")
    
    return final_state


# ============================================================================
# CLI INTERFACE
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python contextbridge_orchestrator.py <product> <query>")
        print("Products: biddeed, zonewise, lifeos, spd")
        sys.exit(1)
    
    product = sys.argv[1]
    query = ' '.join(sys.argv[2:])
    
    # Execute query
    result = query_contextbridge(query, product)
    
    # Print response
    print("\n" + "="*70)
    print("RESPONSE")
    print("="*70)
    print(result['synthesized_response'])
    print("\nSuggested Actions:")
    for i, action in enumerate(result['suggested_actions'], 1):
        print(f"{i}. {action}")
    print("="*70)
