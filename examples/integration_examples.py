"""
ContextBridge Integration Example
Complete end-to-end demonstration of all agents working together

This example shows:
1. RAG Agent retrieving context from /CONTEXT/ folders
2. SQL Agent executing natural language queries
3. Competitive Intel Agent analyzing competitors
4. Response Synthesis combining all sources
"""

import os
import sys
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from rag_system import ContextBridgeRAG
from sql_agent import SQLAgent
from contextbridge_orchestrator import query_contextbridge, ContextBridgeState


def example_1_rag_only():
    """
    Example 1: RAG Agent Only
    Query: "How is the max bid formula calculated?"
    """
    print("\n" + "="*70)
    print("EXAMPLE 1: RAG AGENT - Documentation Query")
    print("="*70)
    
    rag = ContextBridgeRAG()
    
    results = rag.search(
        query="How is the max bid formula calculated?",
        product="biddeed",
        top_k=3
    )
    
    print("\n📚 RAG Results:")
    for result in results:
        print(f"\n[{result['rank']}] {result['filepath']}")
        print(f"Similarity: {result['similarity']:.3f}")
        print(f"Content: {result['content'][:200]}...")
    
    return results


def example_2_sql_only():
    """
    Example 2: SQL Agent Only
    Query: "What properties are BID recommendations in Brevard County?"
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: SQL AGENT - Data Query")
    print("="*70)
    
    sql_agent = SQLAgent()
    
    result = sql_agent.query(
        natural_language_query="What properties are BID recommendations in Brevard County?",
        product="biddeed",
        entities={'county': 'Brevard'}
    )
    
    print(f"\n🔍 SQL Query:")
    print(result['sql'])
    
    print(f"\n💡 Explanation:")
    print(result['explanation'])
    
    print(f"\n📊 Results: {result['result_count']} rows")
    if result['results']:
        for i, row in enumerate(result['results'][:3], 1):
            print(f"  [{i}] {row}")
    
    return result


def example_3_competitive_intel():
    """
    Example 3: Competitive Intelligence Agent
    Query: "How does PropertyOnion compare to BidDeed.AI?"
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: COMPETITIVE INTEL AGENT - Market Analysis")
    print("="*70)
    
    # This would call the competitive-intelligence orchestrator
    # For now, we'll simulate the result
    
    competitive_result = {
        'competitor': 'PropertyOnion',
        'executive_summary': """
PropertyOnion provides foreclosure data and analytics for 8 KPIs including
judgment amount, ARV, repairs, liens, tax certs, demographics, ownership, and
purchase probability. They serve similar market to BidDeed.AI.

Key Differences:
- PropertyOnion: Manual analysis, static reports
- BidDeed.AI: AI-powered ForecastEngine™, real-time recommendations

BidDeed.AI Advantages:
- ML-based predictions (64.4% accuracy)
- Automated lien discovery (no guesswork)
- Smart Router (90% FREE tier)
- Multi-county support (67 FL counties planned)

Recommendation: BUILD (BidDeed.AI superior technology, better UX)
""",
        'swot': {
            'strengths': ['Established brand', '8 KPI coverage'],
            'weaknesses': ['Manual process', 'No ML predictions'],
            'opportunities': ['Market validation', 'Customer feedback'],
            'threats': ['Direct competitor', 'Market awareness']
        }
    }
    
    print(f"\n🏆 Competitor: {competitive_result['competitor']}")
    print(f"\n📊 Analysis:")
    print(competitive_result['executive_summary'])
    
    return competitive_result


def example_4_full_orchestration():
    """
    Example 4: Full Multi-Agent Orchestration
    Query: "What are our BID properties and how do we calculate max bid?"
    
    This triggers:
    - Intent Classifier → identifies "data_query" + "documentation"
    - SQL Agent → retrieves BID properties
    - RAG Agent → retrieves max bid formula
    - Synthesis → combines both sources
    """
    print("\n" + "="*70)
    print("EXAMPLE 4: FULL ORCHESTRATION - Multi-Agent Query")
    print("="*70)
    
    result = query_contextbridge(
        user_query="What are our BID properties and how do we calculate max bid?",
        product="biddeed",
        user_id="ariel"
    )
    
    print(f"\n🎯 Intent: {result['intent']}")
    print(f"   Confidence: {result['confidence']}")
    
    print(f"\n🤖 Agents Used: {' → '.join(result['agent_sequence'])}")
    
    print(f"\n💬 Response:")
    print(result['synthesized_response'])
    
    print(f"\n⚡ Performance:")
    print(f"   Processing Time: {result['processing_time_ms']}ms")
    print(f"   Cost: ${result['cost_usd']:.4f}")
    print(f"   Tokens: {result['tokens_used']}")
    
    if result['suggested_actions']:
        print(f"\n✨ Suggested Actions:")
        for i, action in enumerate(result['suggested_actions'], 1):
            print(f"   {i}. {action}")
    
    return result


def example_5_zonewise_chatbot():
    """
    Example 5: ZoneWise Chatbot
    Query: "What permits were filed in Melbourne last month?"
    """
    print("\n" + "="*70)
    print("EXAMPLE 5: ZONEWISE CHATBOT - Permit Search")
    print("="*70)
    
    result = query_contextbridge(
        user_query="What permits were filed in Melbourne last month?",
        product="zonewise",
        user_id="ariel"
    )
    
    print(f"\n💬 Response:")
    print(result['synthesized_response'])
    
    print(f"\n📊 SQL Query:")
    print(result.get('sql_query', 'N/A'))
    
    print(f"\n📈 Results: {len(result.get('sql_results', []))} permits found")
    
    return result


def example_6_lifeos_productivity():
    """
    Example 6: Life OS Chatbot
    Query: "How many tasks did I complete this week?"
    """
    print("\n" + "="*70)
    print("EXAMPLE 6: LIFE OS CHATBOT - Productivity Analytics")
    print("="*70)
    
    result = query_contextbridge(
        user_query="How many tasks did I complete this week?",
        product="lifeos",
        user_id="ariel"
    )
    
    print(f"\n💬 Response:")
    print(result['synthesized_response'])
    
    if result.get('sql_results'):
        print(f"\n✅ Completed Tasks: {len(result['sql_results'])}")
    
    return result


def run_all_examples():
    """
    Run all integration examples
    """
    print("\n" + "="*70)
    print("CONTEXTBRIDGE INTEGRATION EXAMPLES")
    print("Complete Multi-Agent System Demonstration")
    print("="*70)
    print(f"\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Products: BidDeed.AI, ZoneWise, Life OS, SPD")
    print(f"Agents: RAG, SQL, Competitive Intel, Synthesis")
    
    examples = [
        ("RAG Only", example_1_rag_only),
        ("SQL Only", example_2_sql_only),
        ("Competitive Intel", example_3_competitive_intel),
        ("Full Orchestration", example_4_full_orchestration),
        ("ZoneWise Chatbot", example_5_zonewise_chatbot),
        ("Life OS Chatbot", example_6_lifeos_productivity)
    ]
    
    results = {}
    
    for name, example_func in examples:
        try:
            print(f"\n\n{'='*70}")
            print(f"Running: {name}")
            print(f"{'='*70}")
            
            result = example_func()
            results[name] = {'success': True, 'result': result}
            
            print(f"\n✅ {name} completed successfully")
            
        except Exception as e:
            print(f"\n❌ {name} failed: {e}")
            results[name] = {'success': False, 'error': str(e)}
    
    # Summary
    print(f"\n\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    
    success_count = sum(1 for r in results.values() if r['success'])
    total_count = len(results)
    
    print(f"\nExamples Run: {total_count}")
    print(f"Successful: {success_count}")
    print(f"Failed: {total_count - success_count}")
    
    for name, result in results.items():
        status = "✅" if result['success'] else "❌"
        print(f"  {status} {name}")
    
    print(f"\n{'='*70}")
    print("Integration testing complete!")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    # Check if specific example requested
    if len(sys.argv) > 1:
        example_num = int(sys.argv[1])
        
        examples = {
            1: example_1_rag_only,
            2: example_2_sql_only,
            3: example_3_competitive_intel,
            4: example_4_full_orchestration,
            5: example_5_zonewise_chatbot,
            6: example_6_lifeos_productivity
        }
        
        if example_num in examples:
            examples[example_num]()
        else:
            print(f"Invalid example number. Choose 1-6.")
    else:
        # Run all examples
        run_all_examples()
