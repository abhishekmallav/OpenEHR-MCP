# 🧪 openEHR MCP Server - Claude Desktop Testing Guide

## 📋 Step 1: Claude Desktop Configuration

### Location of Config File

**macOS:**
```bash
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

**Linux:**
```bash
~/.config/Claude/claude_desktop_config.json
```

### Your Configuration (Update Paths)

**⚠️ IMPORTANT: Replace `/path/to/your/project` with your actual project location**

```json
{
  "mcpServers": {
    "openEHR": {
      "command": "/path/to/your/project/venv/bin/python",
      "args": [
        "/path/to/your/project/src/openehr_mcp_server.py"
      ],
      "env": {
        "EHRBASE_URL": "http://localhost:8080/ehrbase/rest",
        "EHRBASE_JSON_FORMAT": "wt_flat",
        "PYTHONPATH": "/path/to/your/project/src"
      }
    }
  }
}
```

**Example for different systems:**
- **Linux**: `/home/username/projects/openehr-mcp-server`
- **macOS**: `/Users/username/projects/openehr-mcp-server`
- **Windows**: `C:\\Users\\username\\projects\\openehr-mcp-server`

### Important Notes
- ✅ This uses your existing venv (no activation needed)
- ✅ All dependencies are already installed
- ✅ Medical coding features will work if Qdrant has ICD-10 data
- 🔄 **Restart Claude Desktop completely** after adding config

---

## 🚀 Step 2: Start Required Services

```bash
# Navigate to your project's docker-compose directory
cd /path/to/your/project/docker-compose
docker compose up -d
```

**Wait 10 seconds for services to start, then verify:**
```bash
# Check all services are running
docker compose ps

# Test EHRbase
curl http://localhost:8080/ehrbase/rest/openehr/v1/definition/template/adl1.4

# Test Qdrant
curl http://localhost:6333/healthz
```

---

## 🧪 Step 3: Progressive Test Sequence

### TEST 1: Connection Verification ✅

**In Claude Desktop, type:**
```
Can you see the openEHR MCP server? What tools are available?
```

**Expected Result:** 
- You should see 🔌 MCP icon in Claude
- Lists 15 tools including: openehr_template_list, openehr_ehr_create, openehr_composition_create, etc.

---

### TEST 2: List Templates 📋

```
List all available openEHR templates from the server.
```

**Expected Result:**
```json
[
  {
    "template_id": "vital_signs_basic",
    "created_timestamp": "..."
  }
]
```

---

### TEST 3: Get Template Example 🔍

```
Show me an example composition for the vital_signs_basic template.
```

**Expected Result:** 
- JSON structure showing blood pressure, heart rate, temperature fields
- Should indicate what data is required

---

### TEST 4: Create an EHR 🏥

```
Create a new EHR for test patient "TESTPATIENT001" in the "local" namespace.
```

**Expected Result:**
```json
{
  "ehr_id": "12345678-1234-1234-1234-123456789abc",
  "system_id": "...",
  "ehr_status": {...}
}
```

**⚠️ SAVE THE EHR_ID - You'll need it for next tests!**

---

### TEST 5: Interactive Vital Signs Capture 🩺

```
Use the vital_sign_capture prompt for EHR ID [paste-your-ehr-id-here]
```

**What happens:**
1. Claude will find the vital signs template
2. Ask you for required data:
   - Systolic blood pressure (e.g., 120)
   - Diastolic blood pressure (e.g., 80)
   - Heart rate (e.g., 72)
   - Body temperature (e.g., 36.8)
3. Creates the composition automatically

**Example interaction:**
```
You: Use the vital_sign_capture prompt for EHR ID abc123...

Claude: I found the vital_signs_basic template. Let me gather the required data.
        What is the systolic blood pressure (mmHg)?

You: 135

Claude: What is the diastolic blood pressure (mmHg)?

You: 85

Claude: What is the heart rate (bpm)?

You: 78

Claude: What is the body temperature (°C)?

You: 37.1

Claude: ✅ Created composition with UID: xyz789::local::1
```

---

### TEST 6: Manual Composition Creation 📝

```
Create a vital signs composition with the following data:
- Systolic: 120 mmHg
- Diastolic: 80 mmHg  
- Heart rate: 72 bpm
- Temperature: 36.8°C
- EHR ID: [your-ehr-id]
```

**Expected Result:**
- Returns composition UID
- No errors

---

### TEST 7: Query Compositions 🔍

```
Execute this AQL query to find all compositions:
SELECT c/uid/value AS uid, c/name/value AS name, c/context/start_time/value AS time
FROM EHR e CONTAINS COMPOSITION c
WHERE e/ehr_id/value = '[your-ehr-id]'
ORDER BY time DESC
```

**Expected Result:**
- Lists all compositions you created
- Shows UIDs, names, timestamps

---

### TEST 8: Retrieve Specific Composition 📄

```
Get the composition with UID [composition-uid] from EHR [ehr-id]
```

**Expected Result:**
- Full composition JSON
- Shows all vital signs data you entered

---

### TEST 9: Extract Blood Pressure 📊

```
Extract blood pressure measurements from composition [composition-uid] in EHR [ehr-id]
```

**Expected Result:**
```json
{
  "measurements": {
    "Systolic": 120,
    "Diastolic": 80,
    "Mean arterial pressure": 93.33
  },
  "clinical_interpretation": null,
  "comment": null
}
```

---

### TEST 10: Update Composition ✏️

```
Update composition [composition-uid] in EHR [ehr-id] with new blood pressure 125/82 mmHg
```

**Expected Result:**
- Returns new version UID (e.g., `xyz789::local::2`)
- Version number increments

---

### TEST 11: AI Medical Coding 🤖
*(Only if Qdrant has ICD-10 data loaded)*

```
Suggest ICD-10 codes for: "Patient presents with persistent dry cough, mild fever, and fatigue for 5 days"
```

**Expected Result:**
```json
{
  "query": "Patient presents with...",
  "suggested_codes": [
    {
      "code": "R05",
      "description": "Cough",
      "score": 0.89
    },
    {
      "code": "R50.9",
      "description": "Fever, unspecified",
      "score": 0.85
    }
  ]
}
```

---

### TEST 12: Complex Query 🔬

```
Find all EHRs with their latest vital signs composition. Run this AQL:

SELECT 
  e/ehr_id/value AS ehr_id,
  c/uid/value AS composition_uid,
  c/context/start_time/value AS recorded_time
FROM EHR e 
CONTAINS COMPOSITION c
WHERE c/archetype_details/template_id/value = 'vital_signs_basic'
ORDER BY recorded_time DESC
LIMIT 10
```

**Expected Result:**
- Table of recent vital signs records
- Multiple EHR IDs if you created multiple patients

---

### TEST 13: List All EHRs 📋

```
List all EHRs in the system.
```

**Expected Result:**
```json
{
  "ehr_ids": [
    "abc-123...",
    "def-456..."
  ],
  "total": 2
}
```

---

### TEST 14: Error Handling ⚠️

```
Try to get composition with UID "invalid-uid-12345" from EHR [your-ehr-id]
```

**Expected Result:**
- Graceful error message
- No crash
- Explains composition not found

---

### TEST 15: Delete Composition 🗑️

```
Delete the composition with version UID [composition-version-uid] from EHR [ehr-id]
```

**Expected Result:**
- Success confirmation
- Composition marked as deleted (soft delete in openEHR)

---

## 🎯 Quick 5-Minute Test Script

Copy-paste these commands in sequence to Claude Desktop:

```
1. Can you see the openEHR MCP server? List available tools.

2. List all openEHR templates.

3. Create a new EHR for patient "QUICK_TEST_001" in namespace "local".

4. Using the EHR ID from step 3, create a vital signs composition with: Systolic 120, Diastolic 80, Heart rate 72, Temperature 36.8°C.

5. List all compositions for that EHR.

6. Extract blood pressure from the composition you just created.
```

---

## ✅ Success Checklist

After running all tests, you should have:

- [ ] Seen 15 MCP tools listed
- [ ] Retrieved template list successfully
- [ ] Created at least 1 EHR
- [ ] Created at least 1 composition
- [ ] Executed AQL queries successfully
- [ ] Retrieved and extracted data from compositions
- [ ] Updated a composition (version incremented)
- [ ] Tested error handling (invalid UID)
- [ ] No Python errors or crashes

---

## 🐛 Troubleshooting

### "Cannot connect to server"
```bash
# Check services
cd /media/D-Drive/VS-Code/openehr-mcp-server/docker-compose
docker compose ps

# Restart if needed
docker compose restart
```

### "Module not found" errors
```bash
# Verify venv has packages
/media/D-Drive/VS-Code/openehr-mcp-server/venv/bin/python -c "import fastmcp; print('OK')"

# Reinstall if needed
cd /media/D-Drive/VS-Code/openehr-mcp-server
source venv/bin/activate
pip install -r requirements.txt
```

### "MCP tools not showing in Claude"
1. Completely quit Claude Desktop (not just close window)
2. Verify config file location and syntax (must be valid JSON)
3. Restart Claude Desktop
4. Look for 🔌 icon in chat interface

### "EHRbase connection refused"
```bash
# Check EHRbase is running
curl http://localhost:8080/ehrbase/rest/openehr/v1/definition/template/adl1.4

# Check logs
docker logs ehrbase
```

---

## 📊 Expected Performance

- Template list: < 1 second
- EHR creation: < 1 second
- Composition creation: 1-2 seconds
- AQL queries: 1-3 seconds
- Medical coding: 2-5 seconds (with Qdrant)

---

## 🎓 Learning Path

1. **Beginner:** Tests 1-6 (basic CRUD operations)
2. **Intermediate:** Tests 7-10 (queries and updates)
3. **Advanced:** Tests 11-15 (AI features, complex queries, deletions)

---

## 📝 Notes

- All data is stored in Docker volumes (persists across restarts)
- EHR IDs are UUIDs generated by EHRbase
- Composition UIDs include version numbers (e.g., `::1`, `::2`)
- Use `wt_flat` format for easier AI interaction
- Medical coding requires ICD-10 embeddings loaded in Qdrant

---

**Ready to test? Start with TEST 1! 🚀**
