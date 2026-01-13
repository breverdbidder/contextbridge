# ContextBridge - One-Command Setup

## 🚀 Quick Start (3 Minutes)

```bash
git clone https://github.com/breverdbidder/contextbridge
cd contextbridge
python setup_and_deploy.py
```

That's it! The script will:
1. Ask for your Supabase database password (one-time)
2. Add it to GitHub secrets
3. Execute the schema automatically
4. Verify deployment

## 📋 Get Database Password

### Option A: From Dashboard
1. Go to: https://supabase.com/dashboard/project/mocerqjnksmhcjzxrewo/settings/database
2. Scroll to "Connection string"
3. Click "URI" tab  
4. Copy password (between `postgres:` and `@`)

### Option B: Reset Password
1. Go to same URL above
2. Click "Reset database password"
3. Copy the new password

## ✅ What Gets Deployed

- 7 database tables (embeddings, conversations, analytics, swim data)
- 27 target D1 schools for Michael Shapira
- 2 functions (vector search, SQL execution)
- 3 views (stats, metrics, progress tracking)

## 🎯 After Setup

Start using ContextBridge:

```bash
# Set environment variables
export ANTHROPIC_API_KEY=your_key
export OPENAI_API_KEY=your_key

# Install dependencies
pip install -r requirements-api.txt

# Start server
python src/api.py

# Open chatbot
open widget/contextbridge_live.html
```

## 💡 Troubleshooting

**Script asks for password**: Get it from Supabase dashboard (see above)

**Workflow fails**: Check logs at https://github.com/breverdbidder/contextbridge/actions

**Tables already exist**: Schema was already executed - you're ready to use it!

## 📚 Full Documentation

- Quick Start: QUICK_START.md
- Architecture: README.md (main)
- Skills Integration: docs/SKILLS_INTEGRATION.md
- Week 2 Progress: docs/WEEK_2_COMPLETE.md

---

**Total setup time**: 3 minutes  
**Manual actions**: 1 (provide password)  
**After setup**: Zero-loop autonomous chatbot
