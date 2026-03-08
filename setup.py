"""Setup script for the Self-Critique Author package."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent.parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent.parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    requirements = requirements_path.read_text(encoding="utf-8").strip().split('\n')
    requirements = [req.strip() for req in requirements if req.strip() and not req.startswith('#')]

setup(
    name="self-critique-author",
    version="2.0.0",
    description="EHR Data Auditor with WhatsApp Verification",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Self-Critique Author Team",
    author_email="team@selfcritiqueauthor.com",
    url="https://github.com/your-org/self-critique-author",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    package_data={
        "self_critique_author": [
            "config/*.yaml",
            "config/*.prompt",
        ]
    },
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "mypy>=0.991",
            "pre-commit>=2.20.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.8.0",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Healthcare Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="EHR, healthcare, audit, verification, whatsapp, data-quality",
    entry_points={
        "console_scripts": [
            "ehr-audit=self_critique_author.cli:main",
            "ehr-pipeline=self_critique_author.cli:main",
        ],
    },
    zip_safe=False,
)
