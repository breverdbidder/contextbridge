#!/usr/bin/env python3
"""
Index Skills Documentation into ContextBridge RAG
Quick script to make skill creation queryable

Usage:
    python index_skills.py
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from rag_system import ContextBridgeRAG

def main():
    print("\n" + "="*70)
    print("INDEXING SKILLS DOCUMENTATION")
    print("="*70)
    
    # Initialize RAG
    rag = ContextBridgeRAG()
    
    # Skill Creator documentation
    skill_creator_path = '/mnt/skills/examples/skill-creator/SKILL.md'
    
    if not os.path.exists(skill_creator_path):
        print(f"❌ Skill creator not found at: {skill_creator_path}")
        print("   Make sure you're running in Claude environment")
        return
    
    print(f"\n📚 Reading skill-creator documentation...")
    with open(skill_creator_path, 'r') as f:
        skill_creator_content = f.read()
    
    print(f"   Length: {len(skill_creator_content):,} characters")
    print(f"   Tokens: ~{len(skill_creator_content) // 4:,}")
    
    # Index to ContextBridge (available to all products)
    print(f"\n🔄 Indexing to ContextBridge RAG...")
    indexed = rag.index_document(
        filepath='/SKILLS/skill-creator.md',
        content=skill_creator_content,
        product='contextbridge',
        metadata={
            'type': 'skill_guide',
            'category': 'infrastructure',
            'original_path': skill_creator_path
        }
    )
    
    print(f"✅ Indexed {indexed} chunks")
    
    # Test search
    print(f"\n🔍 Testing search...")
    results = rag.search(
        query="How do I create a new skill?",
        product='contextbridge',
        top_k=3
    )
    
    print(f"✅ Search successful - {len(results)} results")
    
    if results:
        print(f"\nTop result:")
        print(f"  Similarity: {results[0]['similarity']:.3f}")
        print(f"  Preview: {results[0]['content'][:200]}...")
    
    print("\n" + "="*70)
    print("✅ SKILLS INTEGRATION COMPLETE")
    print("="*70)
    print("\nNow you can query:")
    print('  - "How do I create a skill?"')
    print('  - "What goes in a skill folder?"')
    print('  - "Should I create a skill for X?"')
    print("\nFrom any product in ContextBridge!")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
