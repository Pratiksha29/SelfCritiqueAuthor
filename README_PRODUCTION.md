# Self-Critique Author — EHR Data Auditor with WhatsApp Verification

Mock EHR agent demo: corrupt a clean dataset, then use an auditor (Gemini) to find inconsistencies, verify with patients via WhatsApp, and correct data automatically.

---

## 🏗️ **Production-Ready Architecture**

This project follows a modular, production-ready structure that can be easily extended and maintained by multiple developers.

---

## 📁 **Project Structure**

```
self_critique_author/
├── 📁 src/
│   ├── 📁 self_critique_author/
│   │   ├── 📁 core/
│   │   │   ├── __init__.py
│   │   │   ├── auditor.py              # Core auditing logic
│   │   │   ├── resolver.py             # Data resolution
│   │   │   └── pipeline.py             # Main orchestrator
│   │   ├── 📁 verification/
│   │   │   ├── __init__.py
│   │   │   ├── whatsapp_verifier.py   # WhatsApp verification
│   │   │   └── doctor_verifier.py     # Doctor verification
│   │   ├── 📁 storage/
│   │   │   ├── __init__.py
│   │   │   ├── json_storage.py         # JSON file storage
│   │   │   └── csv_storage.py          # CSV file storage
│   │   ├── 📁 models/
│   │   │   ├── __init__.py
│   │   │   ├── patient.py              # Patient data models
│   │   │   ├── grievance.py            # Grievance data models
│   │   │   └── message.py              # Message data models
│   │   ├── 📁 utils/
│   │   │   ├── __init__.py
│   │   │   ├── config.py               # Configuration management
│   │   │   ├── logger.py               # Logging utilities
│   │   │   └── validators.py           # Data validation
│   │   └── __init__.py
├── 📁 config/
│   ├── auditor.prompt                  # LLM instructions
│   ├── settings.yaml                   # Application settings
│   └── logging.yaml                    # Logging configuration
├── 📁 data/
│   ├── raw/                           # Raw input data
│   ├── processed/                     # Processed output data
│   └── temp/                          # Temporary files
├── 📁 scripts/
│   ├── run_pipeline.py                # Main entry point
│   ├── run_auditor.py                 # Auditor-only script
│   └── utils/                         # Utility scripts
├── 📁 tests/
│   ├── unit/                          # Unit tests
│   ├── integration/                   # Integration tests
│   └── fixtures/                      # Test data
├── 📁 docs/                           # Documentation
├── 📄 requirements.txt               # Dependencies
├── 📄 requirements-dev.txt           # Development dependencies
├── 📄 setup.py                       # Package setup
├── 📄 pyproject.toml                 # Modern Python packaging
├── 📄 README.md                      # Project documentation
├── 📄 .gitignore                     # Git ignore rules
├── 📄 .env.example                   # Environment variables template
└── 📄 Makefile                       # Common commands
```

---

## 🚀 **Quick Start**

### **Installation**
```bash
# Clone and setup
git clone <repository-url>
cd self_critique_author
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Or install dependencies
pip install -r requirements.txt
```

### **Configuration**
```bash
# Copy environment template
cp .env.example .env

# Edit with your API keys
nano .env
```

### **Run the Application**
```bash
# Full pipeline
python scripts/run_pipeline.py --demo 5

# Individual components
python scripts/run_auditor.py --demo 5
python -m self_critique_author.core.pipeline --step verify
```

---

## 🏛️ **Architecture Overview**

### **Core Principles**

1. **Separation of Concerns**: Each module has a single responsibility
2. **Dependency Injection**: Components are loosely coupled
3. **Configuration-Driven**: Behavior controlled via config files
4. **Extensibility**: Easy to add new verifiers, storage, or processors
5. **Testability**: All components are unit-testable

### **Module Responsibilities**

#### **📁 core/**
- **auditor.py**: Core auditing logic using LLM
- **resolver.py**: Data correction and resolution
- **pipeline.py**: Main workflow orchestration

#### **📁 verification/**
- **whatsapp_verifier.py**: Patient communication via WhatsApp
- **doctor_verifier.py**: Healthcare provider verification

#### **📁 storage/**
- **json_storage.py**: JSON file operations
- **csv_storage.py**: CSV file operations
- **Extensible**: Add database storage, cloud storage, etc.

#### **📁 models/**
- **patient.py**: Patient data structures
- **grievance.py**: Grievance report structures
- **message.py**: Communication message structures

#### **📁 utils/**
- **config.py**: Configuration management
- **logger.py**: Structured logging
- **validators.py**: Data validation utilities

---

## 🔧 **Configuration System**

### **settings.yaml**
```yaml
# Application settings
app:
  name: "Self-Critique Author"
  version: "2.0.0"
  debug: false

# LLM Configuration
llm:
  provider: "gemini"
  model: "gemini-1.5-flash"
  max_retries: 3
  delay_seconds: 5

# Storage Configuration
storage:
  default_format: "json"
  output_directory: "data/processed"
  grievance_directory: "data/processed/grievances"
  message_directory: "data/processed/messages"

# Verification Configuration
verification:
  whatsapp:
    enabled: true
    message_format: "professional"
  doctor:
    enabled: true
    email_template: "clinical_verification"

# Logging Configuration
logging:
  level: "INFO"
  format: "structured"
  file: "logs/app.log"
```

---

## 🧪 **Testing Strategy**

### **Unit Tests**
```bash
# Run all tests
pytest

# Run specific module tests
pytest tests/unit/core/test_auditor.py

# Run with coverage
pytest --cov=self_critique_author
```

### **Integration Tests**
```bash
# Test full pipeline
pytest tests/integration/test_pipeline.py

# Test with real data
pytest tests/integration/test_with_real_data.py
```

---

## 📦 **Package Management**

### **Development Dependencies**
```bash
# Install development tools
pip install -r requirements-dev.txt

# Pre-commit hooks
pre-commit install

# Code formatting
black src/
isort src/

# Type checking
mypy src/
```

### **Building for Distribution**
```bash
# Build package
python -m build

# Upload to PyPI
python -m twine upload dist/*
```

---

## 🔌 **Extending the System**

### **Adding a New Verifier**
```python
# src/self_critique_author/verification/email_verifier.py
from ..core.interfaces import VerifierInterface
from ..models.message import VerificationMessage

class EmailVerifier(VerifierInterface):
    def send_message(self, message: VerificationMessage) -> bool:
        # Implementation
        pass
    
    def record_response(self, response: str) -> bool:
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
    
    def load_grievance(self, grievance_id: str) -> GrievanceReport:
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

## 🚀 **Deployment**

### **Docker Support**
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
COPY config/ ./config/

CMD ["python", "scripts/run_pipeline.py"]
```

### **Environment Configuration**
```bash
# Production environment variables
export APP_ENV=production
export LOG_LEVEL=INFO
export STORAGE_TYPE=database
export VERIFICATION_WHATSAPP_ENABLED=false
```

---

## 📊 **Monitoring & Observability**

### **Structured Logging**
```python
# Automatic structured logging with context
logger.info("Processing patient record", 
            patient_id=patient.id, 
            step="auditing",
            duration_ms=processing_time)
```

### **Metrics Collection**
```python
# Built-in metrics
from ..utils.metrics import Metrics

metrics.counter("records_processed").increment()
metrics.histogram("processing_time").record(duration)
```

---

## 🤝 **Contributing Guidelines**

1. **Follow the existing code structure**
2. **Add tests for new features**
3. **Update documentation**
4. **Use type hints**
5. **Follow PEP 8 style guide**
6. **Add configuration options for new features**

---

## 📝 **API Documentation**

### **Core Pipeline API**
```python
from self_critique_author.core.pipeline import EHRPipeline

pipeline = EHRPipeline(config_path="config/settings.yaml")
results = pipeline.run(input_data_path="data/raw/patients.json")
```

### **Auditor API**
```python
from self_critique_author.core.auditor import EHRAuditor

auditor = EHRAuditor(config=config)
grievance = auditor.audit_patient_record(patient_data)
```

---

**🎉 Production-ready, modular, and extensible architecture for team development!**
