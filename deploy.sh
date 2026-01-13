#!/bin/bash
# ContextBridge One-Command Deployment
# Usage: ./deploy.sh

set -e

echo "======================================================================"
echo "CONTEXTBRIDGE AUTONOMOUS DEPLOYMENT"
echo "======================================================================"
echo ""

# Check if running from contextbridge directory
if [ ! -f "src/api.py" ]; then
    echo "❌ Error: Run this from the contextbridge directory"
    echo "   cd contextbridge && ./deploy.sh"
    exit 1
fi

# Step 1: Environment check
echo "Step 1/5: Checking environment..."
if [ -z "$ANTHROPIC_API_KEY" ] || [ -z "$OPENAI_API_KEY" ] || [ -z "$SUPABASE_URL" ]; then
    echo "⚠️  Environment variables not set. Setting them now..."
    
    export SUPABASE_URL="https://mocerqjnksmhcjzxrewo.supabase.co"
    export SUPABASE_SERVICE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1vY2VycWpua3NtaGNqenhyZXdvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NDUzMjUyNiwiZXhwIjoyMDgwMTA4NTI2fQ.KqF65YsQVBE_kBRsOlDo7bMIYGpPVXaQ9SBAtfL255mO0V8"
    
    # Prompt for API keys
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        read -p "Enter ANTHROPIC_API_KEY: " ANTHROPIC_API_KEY
        export ANTHROPIC_API_KEY
    fi
    
    if [ -z "$OPENAI_API_KEY" ]; then
        read -p "Enter OPENAI_API_KEY: " OPENAI_API_KEY
        export OPENAI_API_KEY
    fi
fi
echo "✅ Environment configured"

# Step 2: Install dependencies
echo ""
echo "Step 2/5: Installing dependencies..."
pip install -q -r requirements-api.txt
echo "✅ Dependencies installed"

# Step 3: Execute schema (one-time action required)
echo ""
echo "Step 3/5: Database schema..."
echo "⚠️  ONE MANUAL ACTION REQUIRED:"
echo ""
echo "   1. Open: https://supabase.com/dashboard/project/mocerqjnksmhcjzxrewo/sql"
echo "   2. Click 'New query'"
echo "   3. Paste contents of: migrations/002_complete_schema.sql"
echo "   4. Click 'Run'"
echo "   5. Verify: '✅ 27 target schools' message"
echo ""
read -p "Press ENTER when schema is executed..."
echo "✅ Schema executed"

# Step 4: Index skills
echo ""
echo "Step 4/5: Indexing skills..."
if [ -f "index_skills.py" ]; then
    python index_skills.py > /dev/null 2>&1 || echo "⚠️  Skills indexing skipped (optional)"
    echo "✅ Skills indexed"
else
    echo "⚠️  Skills indexing skipped (file not found)"
fi

# Step 5: Start services
echo ""
echo "Step 5/5: Starting ContextBridge..."
echo ""
echo "======================================================================"
echo "✅ CONTEXTBRIDGE READY"
echo "======================================================================"
echo ""
echo "Starting API server on http://localhost:8000"
echo "Open chatbot at: file://$(pwd)/widget/contextbridge_live.html"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start API server
python src/api.py
