"""
Self-Critique Author - EHR Data Auditor with WhatsApp Verification

A production-ready, modular system for auditing Electronic Health Records,
verifying inconsistencies with patients, and correcting data automatically.
"""

__version__ = "2.0.0"
__author__ = "Self-Critique Author Team"
__description__ = "EHR Data Auditor with WhatsApp Verification"

from .core.pipeline import EHRPipeline
from .core.auditor import EHRAuditor
from .core.resolver import EHRResolver

__all__ = [
    "EHRPipeline",
    "EHRAuditor", 
    "EHRResolver",
]
