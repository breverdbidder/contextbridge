"""
ContextBridge SQL Agent
Natural language → SQL with live Supabase execution

Features:
- Claude Sonnet for SQL generation
- Schema-aware query generation
- Safety validation (no DROP, DELETE without WHERE)
- Live execution against Supabase
- Result formatting
"""

import os
from typing import List, Dict, Optional, Tuple
from anthropic import Anthropic
from supabase import create_client, Client
import json


class SQLAgent:
    """
    SQL Agent for natural language database queries
    """
    
    # Product-specific database schemas
    SCHEMAS = {
        'biddeed': """
-- BidDeed.AI Database Schema

TABLE: multi_county_auctions
  - id: BIGSERIAL PRIMARY KEY
  - property_id: TEXT
  - address: TEXT
  - city: TEXT
  - zip_code: TEXT
  - county: TEXT
  - auction_date: DATE
  - judgment_amount: NUMERIC
  - max_bid: NUMERIC
  - recommendation: TEXT (BID, REVIEW, SKIP)
  - bid_judgment_ratio: NUMERIC
  - arv: NUMERIC
  - repairs: NUMERIC
  - created_at: TIMESTAMPTZ

TABLE: lien_analysis
  - id: BIGSERIAL PRIMARY KEY
  - property_id: TEXT
  - lien_type: TEXT (mortgage, hoa, tax, mechanic)
  - amount: NUMERIC
  - priority: INTEGER
  - survives_foreclosure: BOOLEAN
  - created_at: TIMESTAMPTZ

TABLE: foreclosure_history
  - id: BIGSERIAL PRIMARY KEY
  - property_id: TEXT
  - filing_date: DATE
  - judgment_date: DATE
  - judgment_amount: NUMERIC
  - plaintiff: TEXT
  - case_number: TEXT
  - status: TEXT
""",
        'zonewise': """
-- ZoneWise Database Schema

TABLE: permits
  - id: BIGSERIAL PRIMARY KEY
  - permit_id: TEXT
  - address: TEXT
  - city: TEXT
  - zip_code: TEXT
  - jurisdiction: TEXT
  - permit_type: TEXT
  - status: TEXT (filed, approved, rejected, pending)
  - filed_date: DATE
  - approved_date: DATE
  - description: TEXT
  - created_at: TIMESTAMPTZ

TABLE: jurisdictions
  - id: BIGSERIAL PRIMARY KEY
  - jurisdiction_id: TEXT
  - name: TEXT
  - contact_info: JSONB
  - website: TEXT
  - created_at: TIMESTAMPTZ

TABLE: zoning_rules
  - id: BIGSERIAL PRIMARY KEY
  - jurisdiction: TEXT
  - zoning_code: TEXT
  - description: TEXT
  - allowed_uses: TEXT[]
  - setbacks: JSONB
  - max_height: NUMERIC
  - created_at: TIMESTAMPTZ
""",
        'lifeos': """
-- Life OS Database Schema

TABLE: activities
  - id: BIGSERIAL PRIMARY KEY
  - activity_id: TEXT
  - title: TEXT
  - description: TEXT
  - state: TEXT (INITIATED, IN_PROGRESS, COMPLETED, ABANDONED, BLOCKED)
  - priority: TEXT (HIGH, MEDIUM, LOW)
  - due_date: DATE
  - completed_at: TIMESTAMPTZ
  - created_at: TIMESTAMPTZ

TABLE: habits
  - id: BIGSERIAL PRIMARY KEY
  - habit_id: TEXT
  - name: TEXT
  - frequency: TEXT (daily, weekly, monthly)
  - streak: INTEGER
  - last_completed: DATE
  - created_at: TIMESTAMPTZ

TABLE: goals
  - id: BIGSERIAL PRIMARY KEY
  - goal_id: TEXT
  - title: TEXT
  - progress: NUMERIC (0-100)
  - target_date: DATE
  - status: TEXT
  - created_at: TIMESTAMPTZ
""",
        'spd': """
-- SPD Database Schema

TABLE: projects
  - id: BIGSERIAL PRIMARY KEY
  - project_id: TEXT
  - name: TEXT
  - address: TEXT
  - city: TEXT
  - status: TEXT (DISCOVERY, DESIGN, APPROVAL, CONSTRUCTION)
  - created_at: TIMESTAMPTZ

TABLE: site_plans
  - id: BIGSERIAL PRIMARY KEY
  - project_id: TEXT
  - version: INTEGER
  - plan_type: TEXT
  - status: TEXT
  - file_url: TEXT
  - created_at: TIMESTAMPTZ

TABLE: approvals
  - id: BIGSERIAL PRIMARY KEY
  - project_id: TEXT
  - approval_type: TEXT
  - submitted_date: DATE
  - approved_date: DATE
  - status: TEXT
  - created_at: TIMESTAMPTZ
"""
        'michael': """
-- Michael D1 Swimming Database Schema

TABLE: swim_times
  - id: BIGSERIAL PRIMARY KEY
  - swimmer_id: TEXT
  - event: TEXT (50_free, 100_free, 100_fly, 100_back)
  - time_scy: TEXT
  - meet_name: TEXT
  - meet_date: DATE
  - is_personal_best: BOOLEAN
  - created_at: TIMESTAMPTZ

TABLE: target_schools
  - id: BIGSERIAL PRIMARY KEY
  - school_name: TEXT
  - conference: TEXT (SEC, Big Ten, ACC, etc.)
  - fit_score: INTEGER (0-100)
  - priority: INTEGER (1-27)
  - coach_name: TEXT
  - visit_date: DATE
  - created_at: TIMESTAMPTZ

TABLE: recruiting_outreach
  - id: BIGSERIAL PRIMARY KEY
  - school_name: TEXT
  - coach_name: TEXT
  - email_sent_date: DATE
  - response_received: BOOLEAN
  - created_at: TIMESTAMPTZ

TABLE: meet_schedule
  - id: BIGSERIAL PRIMARY KEY
  - meet_name: TEXT
  - meet_date: DATE
  - events_entered: TEXT[]
  - is_shabbat_conflict: BOOLEAN
  - created_at: TIMESTAMPTZ
""",
    }
    
    # Dangerous SQL patterns to block
    BLOCKED_PATTERNS = [
        'DROP ',
        'TRUNCATE ',
        'DELETE FROM',  # Unless has WHERE clause
        'UPDATE ',  # Unless has WHERE clause
        'INSERT INTO',
        'ALTER TABLE',
        'CREATE TABLE',
        'GRANT ',
        'REVOKE '
    ]
    
    def __init__(
        self,
        anthropic_api_key: Optional[str] = None,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None
    ):
        # Initialize Anthropic
        self.anthropic_api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=self.anthropic_api_key)
        
        # Initialize Supabase
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_SERVICE_KEY")
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        print("✅ SQL Agent initialized")
        print(f"   Supabase: {self.supabase_url}")
    
    def generate_sql(
        self,
        query: str,
        product: str,
        entities: Optional[Dict] = None
    ) -> Tuple[str, str]:
        """
        Generate SQL from natural language using Claude
        
        Args:
            query: Natural language query
            product: Product namespace
            entities: Extracted entities (addresses, dates, etc.)
            
        Returns:
            (sql_query, explanation)
        """
        print(f"\n🧠 Generating SQL for: {query}")
        print(f"   Product: {product}")
        
        # Get schema for product
        schema = self.SCHEMAS.get(product, "")
        
        if not schema:
            raise ValueError(f"Unknown product: {product}")
        
        # Prepare prompt
        prompt = f"""Convert this natural language query to PostgreSQL.

Product: {product}

Database Schema:
{schema}

User Query: {query}

Extracted Entities: {json.dumps(entities or {})}

Generate a valid PostgreSQL SELECT query.
- Use proper JOIN syntax if multiple tables needed
- Use WHERE clauses for filtering
- Use ORDER BY and LIMIT as appropriate
- Return ONLY valid SQL (no markdown, no explanations in the SQL)

Return JSON:
{{
    "sql": "SELECT ...",
    "explanation": "This query will...",
    "tables_used": ["table1", "table2"]
}}"""
        
        # Call Claude
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        # Parse response
        result = json.loads(response.content[0].text)
        
        sql = result['sql'].strip()
        explanation = result['explanation']
        tables = result.get('tables_used', [])
        
        print(f"✅ SQL generated")
        print(f"   Tables: {', '.join(tables)}")
        print(f"   SQL: {sql[:100]}...")
        
        return sql, explanation
    
    def validate_sql(self, sql: str) -> Tuple[bool, Optional[str]]:
        """
        Validate SQL for safety
        
        Args:
            sql: SQL query to validate
            
        Returns:
            (is_valid, error_message)
        """
        sql_upper = sql.upper()
        
        # Check for blocked patterns
        for pattern in self.BLOCKED_PATTERNS:
            if pattern in sql_upper:
                # Special cases
                if pattern == 'DELETE FROM' and 'WHERE' in sql_upper:
                    continue  # DELETE with WHERE is allowed
                if pattern == 'UPDATE ' and 'WHERE' in sql_upper:
                    continue  # UPDATE with WHERE is allowed
                
                return False, f"Blocked SQL pattern: {pattern}"
        
        # Must be SELECT query
        if not sql_upper.strip().startswith('SELECT'):
            return False, "Only SELECT queries are allowed"
        
        return True, None
    
    def execute_sql(
        self,
        sql: str,
        product: str
    ) -> Tuple[List[Dict], Optional[str]]:
        """
        Execute SQL against Supabase
        
        Args:
            sql: SQL query to execute
            product: Product namespace (for logging)
            
        Returns:
            (results, error_message)
        """
        print(f"\n⚡ Executing SQL...")
        
        # Validate SQL
        is_valid, error = self.validate_sql(sql)
        
        if not is_valid:
            print(f"❌ Validation failed: {error}")
            return [], error
        
        try:
            # Execute via Supabase RPC
            # Note: For production, this should use a stored procedure
            # For now, we'll execute directly
            
            # Extract table name from SELECT query
            # This is a simplified approach - production would use proper SQL parsing
            sql_lower = sql.lower()
            
            if 'from ' in sql_lower:
                # Simple extraction
                parts = sql_lower.split('from ')
                if len(parts) > 1:
                    table_part = parts[1].split()[0].strip()
                    table_name = table_part.split(',')[0].strip()
                    
                    # Execute using Supabase client
                    # This is limited but safe
                    print(f"   Table: {table_name}")
                    
                    # For complex queries, use RPC
                    result = self.supabase.rpc(
                        'execute_readonly_sql',
                        {'query': sql}
                    ).execute()
                    
                    if result.data:
                        print(f"✅ Query executed: {len(result.data)} rows")
                        return result.data, None
                    else:
                        print("⚠️ No results")
                        return [], None
            
            return [], "Could not parse SQL"
            
        except Exception as e:
            error_msg = f"Execution failed: {str(e)}"
            print(f"❌ {error_msg}")
            return [], error_msg
    
    def query(
        self,
        natural_language_query: str,
        product: str,
        entities: Optional[Dict] = None
    ) -> Dict:
        """
        Complete natural language to SQL pipeline
        
        Args:
            natural_language_query: User's question
            product: Product namespace
            entities: Extracted entities
            
        Returns:
            Complete result with SQL, explanation, and data
        """
        print(f"\n{'='*70}")
        print(f"SQL AGENT QUERY")
        print(f"{'='*70}")
        
        # Generate SQL
        sql, explanation = self.generate_sql(
            natural_language_query,
            product,
            entities
        )
        
        # Execute SQL
        results, error = self.execute_sql(sql, product)
        
        return {
            'query': natural_language_query,
            'sql': sql,
            'explanation': explanation,
            'results': results,
            'result_count': len(results),
            'error': error,
            'success': error is None
        }


# ============================================================================
# SUPABASE RPC FUNCTION (Execute this in Supabase SQL Editor)
# ============================================================================

SQL_AGENT_RPC_FUNCTION = """
-- Create function to execute read-only SQL safely
CREATE OR REPLACE FUNCTION execute_readonly_sql(query text)
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    result json;
BEGIN
    -- Validate query is SELECT only
    IF UPPER(TRIM(query)) NOT LIKE 'SELECT%' THEN
        RAISE EXCEPTION 'Only SELECT queries are allowed';
    END IF;
    
    -- Execute and return results as JSON
    EXECUTE 'SELECT json_agg(row_to_json(t)) FROM (' || query || ') t'
        INTO result;
    
    RETURN COALESCE(result, '[]'::json);
END;
$$;

-- Grant execute to service role
GRANT EXECUTE ON FUNCTION execute_readonly_sql(text) TO service_role;
"""


# ============================================================================
# CLI INTERFACE
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python sql_agent.py <product> <query>")
        print("Products: biddeed, zonewise, lifeos, spd")
        print("\nExample:")
        print('  python sql_agent.py biddeed "What properties are BID recommendations?"')
        sys.exit(1)
    
    product = sys.argv[1]
    query = ' '.join(sys.argv[2:])
    
    # Initialize agent
    agent = SQLAgent()
    
    # Execute query
    result = agent.query(query, product)
    
    # Print results
    print(f"\n{'='*70}")
    print("RESULTS")
    print(f"{'='*70}")
    print(f"\nSQL:\n{result['sql']}\n")
    print(f"Explanation: {result['explanation']}\n")
    
    if result['error']:
        print(f"❌ Error: {result['error']}")
    else:
        print(f"✅ {result['result_count']} rows returned\n")
        
        if result['results']:
            # Print first 5 rows
            for i, row in enumerate(result['results'][:5], 1):
                print(f"[{i}] {row}")
            
            if result['result_count'] > 5:
                print(f"\n... and {result['result_count'] - 5} more rows")
    
    print(f"\n{'='*70}")
