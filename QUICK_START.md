# 🚀 ContextBridge Quick Start Guide
## Get Your NLP Chatbot Running in 10 Minutes

**Last Updated**: January 12, 2026  
**Time Required**: 10 minutes  
**Prerequisites**: Python 3.10+, Supabase account

---

## 📋 **CHECKLIST**

- [ ] Step 1: Execute Supabase schema (2 min)
- [ ] Step 2: Set environment variables (2 min)
- [ ] Step 3: Install dependencies (3 min)
- [ ] Step 4: Run API server (1 min)
- [ ] Step 5: Open chatbot (1 min)
- [ ] Step 6: Test queries (1 min)

**Total: ~10 minutes to working chatbot**

---

## **STEP 1: Execute Supabase Schema** ⏱️ 2 minutes

### **1.1 Open Supabase SQL Editor**
```
https://supabase.com/dashboard/project/mocerqjnksmhcjzxrewo/sql
```

### **1.2 Create New Query**
- Click "New query" button

### **1.3 Copy & Paste Schema**
- Open file: `migrations/002_complete_schema.sql`
- Copy entire contents
- Paste into SQL Editor

### **1.4 Execute**
- Click "Run" button
- Wait for completion (~30 seconds)

### **1.5 Verify Success**
You should see:
```
✅ ContextBridge schema created successfully!
   Tables: 7
   Functions: 2
   Views: 3
   Seed data: 27 target schools
```

### **1.6 Verify Tables Created**
Run this query:
```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND (table_name LIKE '%context%' OR table_name LIKE '%swim%')
ORDER BY table_name;
```

Expected output (7 tables):
- context_embeddings
- contextbridge_analytics
- contextbridge_conversations
- meet_schedule
- recruiting_outreach
- swim_times
- target_schools

### **1.7 Verify Seed Data**
```sql
SELECT COUNT(*) FROM target_schools;
```

Expected: **27** (Michael's target D1 schools)

---

## **STEP 2: Set Environment Variables** ⏱️ 2 minutes

### **2.1 Create .env File**
In the `contextbridge` repository root, create `.env`:

```bash
# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here

# OpenAI (for embeddings)
OPENAI_API_KEY=sk-your-key-here

# Supabase
SUPABASE_URL=https://mocerqjnksmhcjzxrewo.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1vY2VycWpua3NtaGNqenhyZXdvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NDUzMjUyNiwiZXhwIjoyMDgwMTA4NTI2fQ.KqF65YsQVBE_kBRsOlDo7bMIYGpPVXaQ9SBAtfL255mO0V8
```

### **2.2 Export Variables (Optional)**
Or export directly in terminal:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-...
export SUPABASE_URL=https://mocerqjnksmhcjzxrewo.supabase.co
export SUPABASE_SERVICE_KEY=eyJhbGc...
```

---

## **STEP 3: Install Dependencies** ⏱️ 3 minutes

### **3.1 Install API Dependencies**
```bash
cd contextbridge
pip install -r requirements-api.txt
```

Expected output:
```
Installing fastapi, uvicorn, anthropic, openai, supabase...
Successfully installed 15 packages
```

### **3.2 Verify Installation**
```bash
python -c "import fastapi, anthropic, openai; print('✅ All dependencies installed')"
```

---

## **STEP 4: Run API Server** ⏱️ 1 minute

### **4.1 Start Server**
```bash
cd src
python api.py
```

Or using uvicorn directly:
```bash
uvicorn src.api:app --reload --port 8000
```

### **4.2 Verify Server Running**
You should see:
```
======================================================================
ContextBridge API Starting...
======================================================================
Time: 2026-01-12T21:25:00.000000
Environment:
  ANTHROPIC_API_KEY: ✅ Set
  OPENAI_API_KEY: ✅ Set
  SUPABASE_URL: ✅ Set
  SUPABASE_SERVICE_KEY: ✅ Set

Endpoints:
  GET  /         - API info
  GET  /health   - Health check
  GET  /products - List products
  POST /query    - Main chat endpoint

Ready! 🚀
======================================================================

INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### **4.3 Test Health Endpoint**
Open in browser:
```
http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-12T21:25:30.123456",
  "version": "1.0.0"
}
```

### **4.4 View Interactive Docs**
```
http://localhost:8000/docs
```

You'll see FastAPI auto-generated documentation with all endpoints.

---

## **STEP 5: Open Chatbot** ⏱️ 1 minute

### **5.1 Open Widget in Browser**
```bash
open widget/contextbridge_live_chatbot.html
```

Or navigate manually:
```
file:///path/to/contextbridge/widget/contextbridge_live_chatbot.html
```

### **5.2 Verify Connection**
Top status bar should show:
```
🟢 API Connected
```

If it shows offline:
- Check that API server is running on port 8000
- Check browser console for errors (F12)

---

## **STEP 6: Test Queries** ⏱️ 1 minute

### **6.1 Test Each Product**

**BidDeed.AI:**
```
Query: "What properties are BID recommendations?"
Expected: Response about foreclosure properties
```

**Michael D1:**
```
Query: "What are my target schools?"
Expected: List of 27 D1 schools
```

**ZoneWise:**
```
Query: "What permits were filed?"
Expected: Permit information
```

**Life OS:**
```
Query: "Show my tasks"
Expected: Task information
```

**SPD:**
```
Query: "What's the project status?"
Expected: Project information
```

### **6.2 Verify Response Structure**

Each response should show:
- ✅ AI response text
- ✅ Intent classification
- ✅ Agents used (e.g., "Intent → SQL → Synthesis")
- ✅ Processing time (ms)
- ✅ Cost ($0.00XX)

---

## 🎉 **SUCCESS!**

**If you got here, you have:**
- ✅ Working database (7 tables, 27 schools)
- ✅ Running API server
- ✅ Live chatbot interface
- ✅ All 5 products queryable

---

## 🧪 **TESTING EXAMPLES**

### **Example 1: Michael's Target Schools**
```
Product: Michael D1
Query: "What are my target schools?"

Expected Response:
"You have 27 target D1 schools. Top priorities:
1. University of Florida (SEC) - Coach Anthony Nesty
2. University of Texas (Big 12) - Coach Bob Bowman
3. NC State (ACC) - Coach Braden Holloway
..."

Metadata:
- Intent: data_query
- Agents: Intent → SQL → Synthesis
- Time: ~500ms
- Cost: $0.03
```

### **Example 2: Max Bid Formula**
```
Product: BidDeed.AI
Query: "How is max bid calculated?"

Expected Response:
"The max bid formula is: (ARV × 70%) - Repairs - $10K - MIN($25K, 15% ARV)
This ensures you maintain a 30% equity cushion..."

Metadata:
- Intent: documentation
- Agents: Intent → RAG → Synthesis
- Time: ~300ms
- Cost: $0.01
```

### **Example 3: UF Time Gap**
```
Product: Michael D1
Query: "What's my gap to UF walk-on times?"

Expected Response:
"UF walk-on standards: 21.5 (50 Free), 46.5 (100 Free)
Your current times: [needs SwimCloud scraping]
Gap analysis: [calculated based on current times]"

Metadata:
- Intent: data_query + documentation
- Agents: Intent → SQL + RAG → Synthesis
- Time: ~800ms
- Cost: $0.05
```

---

## 🐛 **TROUBLESHOOTING**

### **Problem: API won't start**
```
Error: ModuleNotFoundError: No module named 'fastapi'

Solution:
pip install -r requirements-api.txt
```

### **Problem: Database connection failed**
```
Error: Could not connect to Supabase

Solution:
1. Verify SUPABASE_URL in .env
2. Verify SUPABASE_SERVICE_KEY in .env
3. Check schema was executed
```

### **Problem: Chatbot shows "API Offline"**
```
Solution:
1. Verify API server is running: http://localhost:8000/health
2. Check CORS is enabled in api.py
3. Check browser console (F12) for errors
```

### **Problem: Empty responses**
```
Error: Response is empty or null

Solution:
1. Check that orchestrator is returning data
2. Verify database tables have data
3. Check API logs for errors
```

---

## 📊 **PERFORMANCE EXPECTATIONS**

| Query Type | Time | Cost | Agents Used |
|------------|------|------|-------------|
| **Simple lookup** | 200-500ms | $0.01 | Intent → SQL |
| **Documentation** | 300-600ms | $0.02 | Intent → RAG |
| **Complex query** | 800-1500ms | $0.05 | Intent → SQL + RAG + Synthesis |
| **Competitive intel** | 2000-3000ms | $0.10 | Intent → Competitive → Synthesis |

**Average**: ~500ms, $0.02 per query

---

## 🎯 **NEXT STEPS**

**Now that ContextBridge is running:**

1. **Use it daily** for 7 consecutive days
2. **Track which queries save you time**
3. **Note any errors or issues**
4. **Improve blockers only** (≤30 min each)

**Focus on projects:**
- BidDeed.AI: Use ContextBridge to research competitors, draft emails
- Michael D1: Use ContextBridge to track schools, draft outreach
- ZoneWise: Use ContextBridge to query permits
- Life OS: Use ContextBridge to track tasks
- SPD: Use ContextBridge to check project status

**Do NOT:**
- Build new features "because it would be nice"
- Polish UI/UX beyond functional
- Add capabilities not needed for projects
- Spend >30 minutes on any improvement

---

## 📝 **USAGE LOG TEMPLATE**

Track your usage to validate dogfooding:

```
Date: _______________
Product: _____________
Query: ______________________________________________
Result: ☐ Helpful  ☐ Not helpful
Time saved: _____ minutes
Notes: ______________________________________________
```

**Goal**: 35+ queries over 7 days, 80%+ helpful

---

## ✅ **VALIDATION CRITERIA**

After 7 days, ContextBridge passes if:
- ☐ Used 5+ times per day
- ☐ 80%+ queries were helpful
- ☐ Saved 10+ minutes per day
- ☐ No major bugs or blockers
- ☐ Cost stayed under $15/month

**If criteria met**: Keep as permanent infrastructure

**If criteria NOT met**: Deprecate, use manual methods

---

**ContextBridge Quick Start: COMPLETE** ✅

**Time to first query: ~10 minutes**

**Now go test it!** 🚀
