# Skills Integration for ContextBridge
## Add Skill Creator & Skill Mill to RAG System

**Time**: 10 minutes  
**Purpose**: Make skill creation queryable via ContextBridge

---

## 🎯 **WHAT TO INDEX**

### **Skill Creator Documentation:**
```
/mnt/skills/examples/skill-creator/SKILL.md
```

**Key Content** (358 lines):
- What skills are and when to create them
- Skill anatomy (SKILL.md + bundled resources)
- Progressive disclosure patterns
- 6-step creation process
- Validation and packaging

### **Public Skills** (Optional):
```
/mnt/skills/public/docx/SKILL.md
/mnt/skills/public/pdf/SKILL.md
/mnt/skills/public/pptx/SKILL.md
/mnt/skills/public/xlsx/SKILL.md
/mnt/skills/public/frontend-design/SKILL.md
/mnt/skills/public/product-self-knowledge/SKILL.md
```

---

## 📝 **INDEXING SCRIPT**

### **Quick Index (Command Line):**

```bash
# Index skill-creator documentation
python src/rag_system.py index contextbridge /mnt/skills/examples/skill-creator/

# This creates embeddings for:
# - SKILL.md (skill creation guide)
# - references/ (workflow patterns, output patterns)
```

### **Python Code (For Automation):**

```python
from src.rag_system import ContextBridgeRAG

rag = ContextBridgeRAG()

# Read skill-creator SKILL.md
with open('/mnt/skills/examples/skill-creator/SKILL.md', 'r') as f:
    skill_creator_content = f.read()

# Index to ContextBridge product
rag.index_document(
    filepath='/SKILLS/skill-creator.md',
    content=skill_creator_content,
    product='contextbridge',  # Available to all products
    metadata={'type': 'skill_guide', 'category': 'infrastructure'}
)

print("✅ Skill Creator indexed to ContextBridge RAG")
```

---

## 🔍 **EXAMPLE QUERIES**

### **After Indexing, You Can Ask:**

**Query 1: Skill Creation Basics**
```
Product: Any
Query: "How do I create a new skill?"

Expected Response:
"To create a skill, follow these steps:
1. Understand concrete examples of skill usage
2. Plan reusable contents (scripts/references/assets)
3. Initialize with init_skill.py script
4. Edit SKILL.md with frontmatter and instructions
5. Package with package_skill.py
6. Iterate based on usage..."

Source: /SKILLS/skill-creator.md
```

**Query 2: Skill Structure**
```
Product: Any
Query: "What goes in a skill folder?"

Expected Response:
"A skill consists of:
- SKILL.md (required): YAML frontmatter + markdown instructions
- scripts/ (optional): Executable code for deterministic tasks
- references/ (optional): Documentation loaded as needed
- assets/ (optional): Files used in output (templates, images)..."

Source: /SKILLS/skill-creator.md
```

**Query 3: When to Create Skill**
```
Product: Any
Query: "Should I create a skill for BidDeed.AI email templates?"

Expected Response:
"Yes, create a skill when you're repeatedly rewriting the same
patterns. For email templates:
- Create scripts/email_template.py for structure
- Add references/examples.md with sample emails
- Include assets/ if using branded templates
This saves tokens and ensures consistency..."

Source: /SKILLS/skill-creator.md
```

**Query 4: Progressive Disclosure**
```
Product: Any
Query: "How should I structure a large skill?"

Expected Response:
"Use progressive disclosure:
1. Keep SKILL.md under 500 lines
2. Move detailed info to references/ files
3. Reference them clearly in SKILL.md
4. Claude loads references only when needed
Example: Core workflow in SKILL.md, detailed patterns
in references/patterns.md..."

Source: /SKILLS/skill-creator.md
```

---

## 🚀 **INTEGRATION INTO CONTEXTBRIDGE**

### **Update SQL Agent Schema:**

Add to `sql_agent.py` SCHEMAS:

```python
'contextbridge': """
-- ContextBridge Infrastructure Schema

TABLE: context_embeddings
  - id: BIGSERIAL PRIMARY KEY
  - product: TEXT
  - filepath: TEXT  -- e.g., /SKILLS/skill-creator.md
  - content: TEXT
  - embedding: vector(1536)

-- Skills are indexed with product='contextbridge'
-- Available to all products via RAG search
"""
```

### **Update Orchestrator Intent:**

Skills queries trigger RAG agent:

```python
# In contextbridge_orchestrator.py

if 'skill' in query.lower() or 'create' in query.lower():
    intent = 'documentation'
    agents_to_use = ['rag']
    
    # RAG searches /SKILLS/ namespace
    # Returns skill creation guidance
```

---

## 📊 **USAGE EXAMPLES**

### **Scenario 1: Creating Email Template Skill**
```
User: "I keep writing BidDeed.AI outreach emails. Should I make a skill?"

ContextBridge Query:
Product: biddeed
Query: "Should I create a skill for email templates?"

Response:
"Yes! Create a skill when repeatedly rewriting the same patterns.
For BidDeed.AI emails:
1. Create scripts/outreach_template.py
2. Add references/examples.md with successful emails
3. Include competitor positioning from competitive intel
This ensures consistency and saves time."

Agents: Intent → RAG → Synthesis
Cost: $0.01
Time: 300ms
```

### **Scenario 2: Creating Michael D1 Recruiting Skill**
```
User: "How do I make a skill for Michael's recruiting emails?"

ContextBridge Query:
Product: michael
Query: "Create skill for D1 recruiting email templates"

Response:
"Create a recruiting-emails skill:
1. Initialize: python scripts/init_skill.py recruiting-emails
2. Add scripts/draft_email.py for email structure
3. Add references/coach_info.md with 27 schools data
4. Add assets/email_templates/ for each school tier
5. Package: python scripts/package_skill.py recruiting-emails
Then Claude can draft emails using the skill automatically."

Agents: Intent → RAG → Synthesis
Cost: $0.02
Time: 500ms
```

### **Scenario 3: Skill Mill Automation**
```
User: "How does skill-mill-deployer work?"

ContextBridge Query:
Product: contextbridge
Query: "Explain skill mill deployment"

Response:
"skill-mill-deployer automates skill creation:
1. Alias 'newrepo' triggers Python script
2. Uses GitHub API to create repository
3. Scaffolds skill structure automatically
4. Deploys SKILL.md template
5. Configures for immediate use

For manual deployment:
python skill-mill-deployer/deploy.py <skill-name> <repo-name>"

Agents: Intent → RAG → Synthesis
Cost: $0.01
Time: 400ms
```

---

## 🔧 **IMPLEMENTATION (10 Minutes)**

### **Step 1: Index Skill Creator** (5 min)

```bash
cd contextbridge

# Run indexing
python src/rag_system.py index contextbridge /mnt/skills/examples/skill-creator/

# Verify
python src/rag_system.py search contextbridge "how to create a skill"

# Should return relevant chunks from SKILL.md
```

### **Step 2: Test Queries** (3 min)

```bash
# Start API server (if not running)
python src/api.py

# Open chatbot
open widget/contextbridge_live.html

# Test query
Product: Any (e.g., BidDeed.AI)
Query: "How do I create a new skill?"

# Should return skill creation guidance
```

### **Step 3: Verify Results** (2 min)

Expected response should include:
- ✅ 6-step process (Understand → Plan → Initialize → Edit → Package → Iterate)
- ✅ Skill anatomy (SKILL.md + scripts/references/assets)
- ✅ Progressive disclosure guidance
- ✅ When to create skills

---

## 📋 **VALIDATION**

**Skills integration is successful if:**

- [ ] Can query "How do I create a skill?" → Gets 6-step process
- [ ] Can query "What goes in a skill?" → Gets structure
- [ ] Can query "Should I create a skill for X?" → Gets guidance
- [ ] Responses cite /SKILLS/skill-creator.md
- [ ] Works from any product (biddeed, michael, zonewise, etc.)

---

## 💰 **COST IMPACT**

**Indexing:**
- One-time: ~$0.10 (skill-creator is ~10K tokens)
- Storage: FREE (Supabase)

**Queries:**
- Per query: ~$0.01 (RAG retrieval)
- Monthly: ~$3 (assuming 10 skill queries/week)

**Total monthly**: +$3 to ContextBridge operating cost

---

## 🎯 **BENEFITS**

**Before:**
- Had to remember skill creation process
- Manually reference documentation
- Inconsistent skill structure

**After:**
- Query ContextBridge for guidance
- Get step-by-step instructions
- Consistent skill creation process
- Available across all 5 products

---

## ✅ **COMPLETION CHECKLIST**

- [ ] Index /mnt/skills/examples/skill-creator/
- [ ] Test query: "How do I create a skill?"
- [ ] Verify response quality
- [ ] Document as infrastructure capability
- [ ] Use when creating new skills

**Time**: 10 minutes  
**Cost**: ~$3/month  
**Value**: Consistent skill creation across all projects

---

**This completes Skills integration into ContextBridge.** ✅

**Skills are now queryable infrastructure supporting all 5 projects.**
