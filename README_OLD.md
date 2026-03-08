# Self-Critique Author — EHR Data Auditor with WhatsApp Verification

Mock EHR agent demo: corrupt a clean dataset, then use an auditor (Gemini) to find inconsistencies, verify with patients via WhatsApp, and correct data automatically.

---

## Prerequisites

- **Python 3.8+**
- A **Gemini API key** (for auditor): [Get one here](https://aistudio.google.com/apikey)
- **WhatsApp Business API** (optional, for production): [WhatsApp Business API](https://developers.facebook.com/docs/whatsapp/business-management-api/)

---

## 1. Set up the environment

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

With virtual environment activated:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This installs:

- `pandas` — data handling
- `numpy` — numerical operations  
- `google-generativeai` — Gemini API for auditor
- `python-dotenv` — environment variable management

Optional (for loading API key from `.env`):

```bash
pip install python-dotenv
```

---

## 4. Configure API key (for the auditor)

Create a `.env` file from example:

```bash
cp .env.example .env
```

Edit `.env` and set your Gemini API key:

```bash
GEMINI_API_KEY=your_actual_api_key_here
```

Or set it in the shell before running the auditor:

```bash
export GEMINI_API_KEY=your_actual_api_key_here
```

---

## 5. WhatsApp Verification Setup (Optional)

The system includes WhatsApp verification for patient outreach:

### For Demo/Testing:
- WhatsApp functionality is simulated (prints messages to console)
- No API key required

### For Production:
1. Get WhatsApp Business API access
2. Configure in `whatsapp_verifier.py`:
   ```python
   verifier = WhatsAppVerifier(api_key="your_whatsapp_api_key")
   ```

---

## 6. Pipeline Commands

The system now supports a **4-step pipeline** with individual step execution:

### **A. Run Complete Pipeline (Recommended)**
```bash
# Full pipeline with demo (first 5 records)
python3 pipeline.py --demo 5

# Full pipeline with all records  
python3 pipeline.py

# Full pipeline without verification step
python3 pipeline.py --no-verification
```

### **B. Run Individual Steps**

#### **1. Load CSV to JSON**
```bash
python3 pipeline.py --step load
```

#### **2. Run Auditor (Find Inconsistencies)**
```bash
# Demo mode (first 5 records)
python3 pipeline.py --step audit --demo 5

# Full audit (all records)
python3 pipeline.py --step audit
```

#### **3. Run WhatsApp Verification** ⭐ **NEW**
```bash
# Send WhatsApp messages to patients with inconsistencies
python3 pipeline.py --step verify

# Includes demo responses for testing
python3 pipeline.py --step verify
```

#### **4. Run Resolver (Fix Data)**
```bash
python3 pipeline.py --step resolve
```

### **C. Custom CSV Input**
```bash
python3 pipeline.py --csv your_custom_file.csv --demo 10
```

---

## 7. WhatsApp Verification Features

### **Smart Grievance Categorization**
- **User Data Issues**: Name, DOB, contact, demographics
  - WhatsApp response options: YES/NO/DETAILS
- **Clinical Data Issues**: Diagnosis, treatment, medications, test results  
  - WhatsApp response options: CONFIRM/DECLINE/DETAILS
  - Doctor verification emails sent automatically

### **Message Examples**

**User Data Verification:**
```
🏥 EHR Data Verification Required

Dear Patient Name,

We found some inconsistencies in your medical records that need verification:

📋 Issues found:
1. Temporal inconsistency between "Age" and "Date_of_Birth" relative to "Date of Admission"
2. Structural inconsistency in capitalization of "Name" field
3. Clinical contradiction regarding "Test Results" for a patient diagnosed with
... and 2 more issues

❓ Please confirm:
Is this correct: Temporal inconsistency between "Age" and "Date_of_Birth" relative to "Date of Admission"?

Reply with:
• YES - If the information is correct
• NO - If the information is incorrect  
• DETAILS - To provide additional information
```

**Clinical Data Verification:**
```
🏥 Clinical Record Verification Required

Dear Patient Name,

Our audit system found potential issues in your diagnosis/treatment records that require verification from your healthcare provider.

📋 Clinical Issue: 3 clinical inconsistencies found in your diagnosis/treatment records

⚠️ This requires verification from your doctor/hospital.

Reply with:
• CONFIRM - To authorize us to contact your healthcare provider
• DECLINE - If you prefer not to proceed with verification
• DETAILS - To provide additional context

Your privacy is our priority. No information will be shared without your consent.
```

### **Response Handling**
- Tracks all patient responses with timestamps
- Generates verification summaries
- HIPAA-compliant workflows with patient consent

---

## 8. End-to-End Workflow

```bash
# 1. Activate venv
source venv/bin/activate   # or Windows equivalent

# 2. Install deps
pip install -r requirements.txt

# 3. Set API key (e.g. in .env or export GEMINI_API_KEY=...)

# 4. Generate messy data (if you have smaller_set.csv)
python corrupt_ehr_dataset.py

# 5. Export to JSON
python main.py

# 6. Add phone numbers (automatically done)
python add_phone_numbers.py

# 7. Run auditor (demo first, e.g. 5 records)
python3 pipeline.py --step audit --demo 5

# 8. Run WhatsApp verification
python3 pipeline.py --step verify

# 9. Run resolver to fix issues
python3 pipeline.py --step resolve

# OR run everything at once:
python3 pipeline.py --demo 5
```

---

## 9. Project Files (Reference)

| File | Purpose |
|------|---------|
| `smaller_set.csv` | Clean 2000-record EHR subset (input to corruption) |
| `corrupt_ehr_dataset.py` | Injects inconsistencies → `ehr_messy.csv` |
| `add_phone_numbers.py` | Adds `cell_number` column with phone numbers |
| `main.py` | Converts `ehr_messy.csv` → `ehr_messy.json` |
| `auditor.prompt` | System prompt for medical data auditor (CoVE format) |
| `run_auditor.py` | Calls Gemini to audit each record in `ehr_messy.json` → `audit_report.csv` |
| `whatsapp_verifier.py` | WhatsApp verification system for patient outreach |
| `doctor_verifier.py` | Doctor/hospital verification for clinical issues |
| `pipeline.py` | Complete 4-step pipeline orchestrator |
| `audit_report.csv` | All original columns + Consistent_or_Not + Grievance_Report |
| `ehr_corrected.csv/json` | Final corrected data (without audit columns) |

---

## 10. Output Files

### **Audit Report (`audit_report.csv`)**
- Contains all original EHR data
- **Consistent_or_Not**: "Consistent" or "Not Consistent"  
- **Grievance_Report**: Detailed CoVE format grievances with:
  - Total inconsistencies count
  - Chain of Verification process
  - Numbered issue details
  - Required corrections

### **Corrected Data (`ehr_corrected.csv/json`)**
- Original data with inconsistencies resolved
- Rule-based corrections applied
- Audit columns removed for clean dataset

---

## 11. Troubleshooting

### **Common Issues**

**Python 3.9 Compatibility:**
```bash
# If you see "unsupported operand type(s) for |" errors:
# The system includes Union imports for Python 3.9 compatibility
```

**Missing API Key:**
```bash
# Set environment variable:
export GEMINI_API_KEY=your_key_here

# Or create .env file:
echo "GEMINI_API_KEY=your_key_here" > .env
```

**WhatsApp Verification Not Working:**
- Demo mode: Messages print to console (normal behavior)
- Production: Requires WhatsApp Business API setup
- Check phone numbers in `cell_number` column

**Empty Grievance Reports:**
- Check auditor.prompt formatting
- Verify Gemini API key is valid
- Review `ehr_messy.json` structure

---

## 12. Advanced Usage

### **Custom Verification Workflows**
```python
from whatsapp_verifier import WhatsAppVerifier
from doctor_verifier import DoctorVerifier

# Initialize verifiers
whatsapp = WhatsAppVerifier()
doctor = DoctorVerifier()

# Send custom messages
messages = whatsapp.send_verification_messages("audit_report.csv")
summary = whatsapp.get_verification_summary()
```

### **Pipeline Integration**
```python
from pipeline import run_full_pipeline

# Run with custom settings
json_path, audit_csv, corrected_csv, verification_summary = run_full_pipeline(
    csv_path="custom_data.csv",
    demo_n=10,
    include_verification=True
)
```

---

## 🎯 **Quick Start Summary**

```bash
# 1. Setup
git clone <repository>
cd SelfCritiqueAuthor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configure
export GEMINI_API_KEY=your_key_here

# 3. Run demo (5 records with WhatsApp verification)
python3 pipeline.py --demo 5
```

This will:
1. ✅ Load CSV → JSON
2. 🔍 Audit 5 records with CoVE process  
3. 📱 Send WhatsApp messages for verification
4. 🔧 Generate corrected data

**Result**: Complete audit trail with patient verification and corrected EHR data.
