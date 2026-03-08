# Self-Critique Author — EHR Data Auditor with WhatsApp Verification

Mock EHR agent demo: corrupt a clean dataset, then use an auditor (Gemini) to find inconsistencies, verify with patients via WhatsApp, and correct data automatically.

---

## 🎯 **What's New in v2.0**

✅ **JSON Grievance Storage**: Complete grievance reports saved without truncation  
✅ **WhatsApp Message Files**: Messages and responses stored in separate fields  
✅ **Enhanced CoVE Format**: Chain of Verification for comprehensive auditing  
✅ **5-Second API Delays**: Faster processing (reduced from 60 seconds)  
✅ **Python 3.9 Compatible**: Full compatibility with older Python versions  

---

## Prerequisites

- **Python 3.8+**
- A **Gemini API key** (for auditor): [Get one here](https://aistudio.google.com/apikey)
- **WhatsApp Business API** (optional, for production): [WhatsApp Business API](https://developers.facebook.com/docs/whatsapp/business-management-api/)

---

## 1. Set up environment

Create a virtual environment in project folder:

```bash
cd /path/to/SelfCritiqueAuthor
python3 -m venv venv
```

---

## 2. Activate environment

**macOS / Linux:**

```bash
source venv/bin/activate
```

**Windows (Command Prompt):**

```cmd
venv\Scripts\activate.bat
```

**Windows (PowerShell):**

```powershell
venv\Scripts\Activate.ps1
```

When active, your prompt will show `(venv)`.

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Set up API keys

Create a `.env` file in project root:

```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

---

## 🚀 **Quick Start Guide**

### **Option 1: Full Pipeline (Demo Mode)**
```bash
# Run full pipeline with 5 records (demo)
python3 pipeline.py --demo 5

# Run full pipeline with all records
python3 pipeline.py
```

### **Option 2: JSON Auditor (Recommended)**
```bash
# Generate JSON grievance reports (no CSV truncation)
python3 run_auditor_json_complete.py --demo 5

# Then run verification
python3 pipeline.py --step verify
```

### **Option 3: Individual Steps**
```bash
# Step 1: Audit only
python3 pipeline.py --step audit --demo 5

# Step 2: Verify only
python3 pipeline.py --step verify

# Step 3: Resolve only  
python3 pipeline.py --step resolve
```

---

## 📁 **Simple Project Structure**

```
SelfCritiqueAuthor/
├── 📄 run_auditor_json_complete.py    # JSON auditor (no truncation)
├── 📄 pipeline.py                     # Main pipeline orchestrator
├── 📄 whatsapp_verifier.py            # WhatsApp verification system
├── 📄 doctor_verifier.py              # Doctor verification system
├── 📄 resolver.py                     # Data correction logic
├── 📄 auditor.prompt                  # LLM instructions
├── 📄 requirements.txt                # Dependencies
├── 📄 README.md                       # This file
├── 📄 .gitignore                      # Git ignore rules
├── 📄 .env.example                    # Environment variables template
├── 📁 grievance_reports/              # JSON grievance files (output)
├── 📁 whatsapp_messages/              # Message/response files (output)
├── 📄 ehr_messy.json                  # Input data
└── 📄 ehr_corrected.json              # Corrected output
```

---

## 📊 **Data Flow Architecture**

```
📥 EHR Data Input (ehr_messy.json)
   ↓
🔍 Auditor (Gemini + CoVE) → JSON grievance reports
   ↓
📱 WhatsApp Verification → Message files with responses
   ↓
📧 Doctor Verification → Clinical issue confirmation
   ↓
🔧 Data Resolution → Corrected EHR data
   ↓
📤 Clean Output (ehr_corrected.json)
```

---

## 🎯 **Key Features**

### **🔍 Enhanced Auditor**
- **Chain of Verification (CoVE)**: Lists ALL inconsistencies found
- **JSON Output**: Complete grievance reports (539+ chars vs truncated CSV)
- **Smart Categorization**: User data vs. clinical data issues
- **5-Second Delays**: Faster API retry logic

### **📱 WhatsApp Verification**
- **Message Storage**: All messages saved to `whatsapp_messages/`
- **Response Tracking**: Patient responses recorded in separate fields
- **Issue Display**: Shows specific inconsistencies instead of counts
- **Professional Format**: Healthcare-appropriate messaging

### **📧 Doctor Verification**
- **Clinical Review**: Automatic email to healthcare providers
- **HIPAA Compliant**: Privacy-focused verification process
- **Status Tracking**: Confirmation/Correction workflow

### **🔧 Data Resolution**
- **Auto-Correction**: Fixes identified inconsistencies
- **Preservation**: Maintains original data integrity
- **Validation**: Ensures corrected data consistency

---

## 📋 **File Formats**

### **JSON Grievance Reports**
```json
{
  "patient_info": { ... },
  "audit_results": {
    "status": "Not Consistent",
    "grievance_report": "TOTAL INCONSISTENCIES FOUND: 2\n\nCHAIN OF VERIFICATION (CoVE) PROCESS:\n1. Name capitalization inconsistency...\n2. Age-DOB mismatch...",
    "report_length": 539,
    "full_text_preserved": true
  },
  "metadata": {
    "auditor_version": "2.0",
    "output_format": "json",
    "truncation_prevented": true
  }
}
```

### **WhatsApp Message Files**
```json
{
  "messages": [
    {
      "patient_id": "PID-000000",
      "phone_number": "+1-630-440-3223",
      "message": "🏥 EHR Data Verification Required...",
      "sent_at": "2026-03-03 23:33:36",
      "status": "sent"
    }
  ],
  "responses": [
    {
      "response": "YES",
      "timestamp": 1772561023.663106,
      "received_at": "2026-03-03 23:33:43"
    }
  ],
  "patient_info": { ... }
}
```

---

## 🔧 **Configuration Options**

### **Pipeline Arguments**
```bash
python3 pipeline.py [OPTIONS]

Options:
  --demo N           Run with N records only (default: 0 = all)
  --step STEP        Run specific step: audit|verify|resolve
  --no-verification  Skip verification step
```

### **Auditor Arguments**
```bash
python3 run_auditor_json_complete.py [OPTIONS]

Options:
  --demo N           Run with N records only
  --output DIR       Custom grievance output directory
```

---

## 📊 **Performance Metrics**

| Feature | Old Version | New Version |
|---------|-------------|-------------|
| **Grievance Length** | ~50 chars (truncated) | 539+ chars (complete) |
| **API Delay** | 60 seconds | 5 seconds |
| **Storage Format** | CSV (limited) | JSON (structured) |
| **Message Tracking** | Console only | Files + Console |
| **Python Support** | 3.10+ | 3.8+ compatible |

---

## 🔍 **Troubleshooting**

### **Common Issues**

**❌ "TypeError: unsupported operand type(s) for |"**
- **Solution**: Use Python 3.9 compatible version (already fixed)

**❌ "Grievance reports are truncated"**
- **Solution**: Use `run_auditor_json_complete.py` instead of CSV

**❌ "No WhatsApp messages found"**
- **Solution**: Check `whatsapp_messages/` directory after running verification

**❌ "API key not found"**
- **Solution**: Set `GEMINI_API_KEY` in `.env` file

### **Getting Help**

1. Check the console output for detailed error messages
2. Verify all prerequisites are met
3. Ensure API keys are properly configured
4. Check file permissions for output directories

---

## 📞 **Support**

For questions or issues:
- Check the troubleshooting section above
- Review console output for detailed error messages
- Verify API key configuration and network connectivity

---

**🎉 Happy Auditing!** 

*Version 2.0 - Simple, clean, and functional EHR audit system*
