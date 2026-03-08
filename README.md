# Self-Critique Author — EHR Data Auditor with WhatsApp Verification

Mock EHR agent demo: corrupt a clean dataset, then use an auditor (Gemini) to find inconsistencies, verify with patients via WhatsApp, and correct data automatically.

---

## 🎯 **What's New in v2.0**

✅ **JSON Grievance Storage**: Complete grievance reports saved without truncation  
✅ **WhatsApp Message Files**: Messages and responses stored in separate fields  
✅ **Enhanced CoVE Format**: Chain of Verification for comprehensive auditing  
✅ **5-Second API Delays**: Faster processing (reduced from 60 seconds)  
✅ **Python 3.9 Compatible**: Full compatibility with older Python versions  
✅ **Production-Ready Architecture**: Modular, extensible, team-friendly structure  

---

## 🏗️ **Production-Ready Architecture**

This project follows a modular, production-ready structure that can be easily extended and maintained by multiple developers.

### **📁 Project Structure**

```
self_critique_author/
├── 📁 src/self_critique_author/          # Main package
│   ├── 📁 core/                          # Core business logic
│   │   ├── auditor.py                    # LLM-based auditing
│   │   ├── resolver.py                   # Data correction
│   │   └── pipeline.py                    # Main orchestrator
│   ├── 📁 verification/                  # Verification systems
│   │   ├── whatsapp_verifier.py          # WhatsApp messaging
│   │   └── doctor_verifier.py            # Doctor verification
│   ├── 📁 storage/                       # Data persistence
│   │   └── json_storage.py               # JSON file storage
│   ├── 📁 models/                        # Data models
│   │   ├── patient.py                    # Patient record model
│   │   ├── grievance.py                  # Grievance report model
│   │   └── message.py                    # Message model
│   ├── 📁 utils/                         # Utilities
│   │   ├── config.py                     # Configuration management
│   │   ├── logger.py                     # Structured logging
│   │   └── validators.py                 # Data validation
│   └── __init__.py                       # Package initialization
├── 📁 config/                            # Configuration files
│   ├── settings.yaml                     # Application settings
│   └── auditor.prompt                    # LLM instructions
├── 📁 data/                              # Data directories
│   ├── raw/                              # Input data
│   └── processed/                        # Output data
├── 📁 scripts/                           # Entry points
│   └── run_pipeline.py                   # Main script
├── 📄 requirements.txt                    # Dependencies
├── 📄 requirements-dev.txt                # Development dependencies
├── 📄 setup.py                           # Package setup
├── 📄 Makefile                           # Common commands
└── 📄 .gitignore                         # Git ignore rules
```

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
# Install package in development mode
pip install -e .

# Or install dependencies directly
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
make demo
# OR
python scripts/run_pipeline.py --demo 5

# Run full pipeline with all records
python scripts/run_pipeline.py
```

### **Option 2: Individual Steps**
```bash
# Step 1: Audit only
make audit
# OR
python scripts/run_pipeline.py --step audit --demo 5

# Step 2: Verify only
make verify
# OR
python scripts/run_pipeline.py --step verify

# Step 3: Resolve only  
make resolve
# OR
python scripts/run_pipeline.py --step resolve --demo 5
```

### **Option 3: Legacy Scripts**
```bash
# Use original auditor (JSON output)
python3 run_auditor_json_complete.py --demo 5

# Use original pipeline
python3 pipeline.py --demo 5
```

---

## 📊 **Data Flow Architecture**

```
📥 EHR Data Input 
   ↓
🔍 Auditor (Gemini + CoVE)
   ↓
📄 JSON Grievance Reports (NEW - No Truncation!)
   ↓
📱 WhatsApp Verification (Messages + Responses Saved)
   ↓
📧 Doctor Verification (Clinical Issues)
   ↓
🔧 Data Resolution
   ↓
📤 Clean EHR Output
```

---

## 🎯 **Key Features**

### **🔍 Enhanced Auditor**
- **Chain of Verification (CoVE)**: Lists ALL inconsistencies found
- **JSON Output**: Complete grievance reports (539+ chars vs truncated CSV)
- **Smart Categorization**: User data vs. clinical data issues
- **5-Second Delays**: Faster API retry logic

### **📱 WhatsApp Verification**
- **Message Storage**: All messages saved to `data/processed/messages/`
- **Response Tracking**: Patient responses recorded in separate fields
- **Issue Display**: Shows specific inconsistencies instead of counts
- **Professional Format**: Healthcare-appropriate messaging

### **📧 Data Resolution**
- **Auto-Correction**: Fixes identified inconsistencies
- **Preservation**: Maintains original data integrity
- **Validation**: Ensures corrected data consistency

### **🏗️ Production Architecture**
- **Modular Design**: Clear separation of concerns
- **Configuration-Driven**: YAML-based settings with environment overrides
- **Type Safety**: Pydantic models with full type hints
- **Structured Logging**: JSON logs with context tracking
- **Extensible**: Easy to add new verifiers, storage, or processors
- **Testable**: pytest framework ready

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
python scripts/run_pipeline.py [OPTIONS]

Options:
  --demo N           Run with N records only (default: 0 = all)
  --step STEP        Run specific step: audit|verify|resolve
  --no-verification  Skip verification step
  --output DIR       Custom output directory
  --config FILE       Custom configuration file
  --log-level LEVEL   Logging level (DEBUG|INFO|WARNING|ERROR)
  --verbose          Enable verbose logging
```

### **YAML Configuration**
```yaml
# config/settings.yaml
app:
  name: "Self-Critique Author"
  version: "2.0.0"
  debug: false

llm:
  provider: "gemini"
  model: "gemini-1.5-flash"
  max_retries: 3
  delay_seconds: 5

storage:
  default_format: "json"
  output_directory: "data/processed"
  grievance_directory: "data/processed/grievances"
  message_directory: "data/processed/messages"

verification:
  whatsapp:
    enabled: true
    message_format: "professional"
  doctor:
    enabled: true
    email_template: "clinical_verification"

logging:
  level: "INFO"
  format: "structured"
  file: "logs/app.log"
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
| **Architecture** | Monolithic | Modular & Extensible |

---

## 🧪 **Testing & Development**

### **Development Setup**
```bash
# Setup development environment
make dev-setup

# Run tests
make test

# Code quality checks
make lint
make format

# Clean build artifacts
make clean
```

### **Available Commands**
```bash
make help           # Show all available commands
make demo           # Run pipeline in demo mode (5 records)
make audit          # Run audit step only
make verify         # Run verification step only
make resolve        # Run resolution step only
make test           # Run all tests
make lint           # Run linting checks
make format         # Format code with black and isort
make clean          # Clean temporary files
```

---

## 🔍 **Troubleshooting**

### **Common Issues**

**❌ "TypeError: unsupported operand type(s) for |"**
- **Solution**: Use Python 3.9 compatible version (already fixed)

**❌ "Grievance reports are truncated"**
- **Solution**: Use `run_auditor_json_complete.py` or new modular system

**❌ "No WhatsApp messages found"**
- **Solution**: Check `data/processed/messages/` directory after running verification

**❌ "API key not found"**
- **Solution**: Set `GEMINI_API_KEY` in `.env` file

**❌ "Module not found"**
- **Solution**: Install package in development mode: `pip install -e .`

### **Getting Help**

1. Check the structured logs in `logs/app.log`
2. Verify all prerequisites are met
3. Ensure API keys are properly configured
4. Check file permissions for output directories
5. Use `--verbose` flag for detailed debugging

---

## 🚀 **Extending the System**

### **Adding a New Verifier**
```python
# src/self_critique_author/verification/email_verifier.py
from ..core.interfaces import VerifierInterface
from ..models.message import VerificationMessage

class EmailVerifier(VerifierInterface):
    def send_verification(self, grievance):
        # Implementation
        pass
```

### **Adding New Storage**
```python
# src/self_critique_author/storage/database_storage.py
from ..core.interfaces import StorageInterface
from ..models.grievance import GrievanceReport

class DatabaseStorage(StorageInterface):
    def save_grievance(self, grievance: GrievanceReport) -> str:
        # Database implementation
        pass
```

### **Configuration for New Components**
```yaml
# config/settings.yaml
verification:
  email:
    enabled: true
    smtp_server: "smtp.example.com"
    template: "verification_email"

storage:
  database:
    enabled: true
    connection_string: "postgresql://..."
```

---

## 📈 **Production Deployment**

### **Environment Setup**
```bash
# Production environment
export APP_ENV=production
export LOG_LEVEL=INFO
export STORAGE_TYPE=database
export VERIFICATION_WHATSAPP_ENABLED=false
export GEMINI_API_KEY=your_production_key
```

### **Docker Support**
```bash
# Build and run with Docker
make docker-build
make docker-run
```

### **Monitoring**
- Monitor `data/processed/grievances/` for audit results
- Check `data/processed/messages/` for communication logs
- Track `data/processed/ehr_corrected.json` for final output
- Review structured logs in `logs/app.log`

---

## 🤝 **Contributing Guidelines**

1. **Follow existing code structure** and module boundaries
2. **Add tests for new features** using pytest framework
3. **Update documentation** and configuration examples
4. **Use type hints** and Pydantic models
5. **Follow PEP 8 style guide**
6. **Add configuration options** for new features in YAML
7. **Test with `make test`** before submitting

---

## 📄 **License**

This project is for demonstration purposes. Please ensure compliance with healthcare data regulations (HIPAA, GDPR) in production use.

---

## 📞 **Support**

For questions or issues:
- Check troubleshooting section above
- Review structured logs in `logs/app.log`
- Verify API key configuration and network connectivity
- Check Makefile commands for common tasks

---

**🎉 Happy Auditing!** 

*Version 2.0 - Production-ready modular architecture with complete JSON grievance storage and WhatsApp message tracking*
