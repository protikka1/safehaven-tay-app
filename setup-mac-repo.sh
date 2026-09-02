#!/bin/bash
# ==============================================================================
# SafeHaven TAY Mobile Recovery App - macOS Repository Setup Automation
# ==============================================================================
# This script initializes the project directory structure, configures Git,
# generates robust security/contribution files, sets up a local virtual env,
# and creates a GitHub Actions CI pipeline with schema integrity validation.

# Exit immediately if a command exits with a non-zero status
set -e

echo "================================================================================"
echo "Initializing SafeHaven Repository & Developer Environment on macOS"
echo "================================================================================"

# 1. Project Directory Structure
echo "Creating project directory structure..."
mkdir -p .github/workflows
mkdir -p database
mkdir -p tests
mkdir -p docs
mkdir -p .streamlit

# 2. Generate .gitignore
echo "Generating .gitignore..."
cat << 'EOF' > .gitignore
# Virtual Environment
.venv/
venv/
ENV/
env/

# Python caching
**/__pycache__/
*.py[cod]
*$py.class
.ipynb_checkpoints/

# Database Files (CRITICAL: Never commit active patient databases to GitHub!)
*.db
*.sqlite3
*.sqlite

# Streamlit Local Configuration & Secrets
.streamlit/config.toml
.streamlit/secrets.toml

# macOS System Files
.DS_Store
.AppleDouble
.LSOverride
Icon?
._*
EOF

# 3. Generate SECURITY.md
echo "Generating SECURITY.md..."
cat << 'EOF' > SECURITY.md
# Security Policy: SafeHaven TAY Mobile App

Because the SafeHaven mobile application coordinates healthcare delivery—including Medications for Addiction Treatment (MAT)—and links unhoused youth aliases to official social welfare cases (CalWORKs/DPSS), protecting patient privacy and maintaining data integrity is our highest priority.

## Supported Versions

Only the active main development branch and tagged production releases are supported for security patches.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Critical Compliance Standards (HIPAA & DPSS)

To remain compliant with health confidentiality and state records standards:
1. **Zero Database Commits**: Active databases (`*.db`, `*.sqlite3`) must **never** be committed to Git. They are explicitly blocked in `.gitignore`.
2. **PII and HIPAA Safeguarding**: High-risk fields matching street aliases to legal names (for CalWORKs) must only be queried/displayed through encrypted, authenticated channels.
3. **No Code Secrets**: All API keys, tokens, database credentials, and clinician authorization signing keys must reside in `.streamlit/secrets.toml` locally, or be loaded as environment variables. They must never be hardcoded.

## Reporting a Vulnerability

If you discover a security vulnerability, please do **not** open a public GitHub issue. 

Please report vulnerabilities confidentially by emailing the Lead Security Coordinator at **security@safehaven-recovery.org**. 

### What to Include in Your Report:
* A detailed description of the vulnerability.
* Steps to reproduce or a proof of concept (PoC).
* Potential impact (e.g., unauthorized access to patient profiles or MAT scripts).

We will acknowledge receipt of your report within **24 hours** and provide a timeline for remediation.
EOF

# 4. Generate CONTRIBUTING.md
echo "Generating CONTRIBUTING.md..."
cat << 'EOF' > CONTRIBUTING.md
# Contributing to SafeHaven TAY Mobile App

Welcome! By contributing to SafeHaven, you are directly helping connect transition-age youth in Skid Row to life-saving clinical care, harm reduction services, and stable housing.

## Code of Conduct & Ethical Guardrails
* **Protect Anonymity First**: Our "Low-Barrier Identity Management" model allows youth to register using only a street alias (e.g., "Sky"). Never write code that mandates government IDs or formal legal names during the initial street triage phase.
* **Clinician NPI Verification**: When writing clinical modules, ensure that any Medications for Addiction Treatment (MAT) prescriptions are strictly linked to a clinician with a validated 10-digit National Provider Identifier (NPI) to maintain regulatory compliance.

## Quickstart macOS Local Developer Setup

1. **Clone the Repository**:
   ```bash
   git clone <your-fork-url>
   cd safehaven-tay-app
   ```

2. **Configure Virtual Environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Initialize Database**:
   ```bash
   python3 database/seed.py
   ```

4. **Run the App**:
   ```bash
   streamlit run app.py
   ```

## Git Branching & Pull Request (PR) Workflow

We follow a strict PR workflow to protect the main branch from regression:

1. **Branch Naming Conventions**:
   * Features: `feature/short-description` (e.g., `feature/one-click-booking`)
   * Bug Fixes: `bugfix/short-description` (e.g., `bugfix/npi-validation-error`)
   * Hotfixes: `hotfix/short-description`

2. **Local Schema Verification**:
   Before pushing, run our database validation test suite locally:
   ```bash
   python3 -m unittest discover tests/
   ```

3. **Submit a Pull Request**:
   * Target the `main` branch.
   * Fill out the Pull Request Template completely.
   * Ensure that the Automated CI Pipeline passes successfully.
   * Solicit a review from at least one core maintainer before merging.
EOF

# 5. Generate PULL_REQUEST_TEMPLATE.md
echo "Generating .github/PULL_REQUEST_TEMPLATE.md..."
cat << 'EOF' > .github/PULL_REQUEST_TEMPLATE.md
## Description
Provide a concise summary of the changes introduced in this PR and the specific problem they solve.

## Linked Issues
Fixes # (issue number)

## Type of Change
- [ ] Feature (non-breaking change which adds new app functionality)
- [ ] Bug Fix (non-breaking change which fixes an active issue)
- [ ] Refactor (code quality, styling, or structural improvements)
- [ ] Database Schema Change (requires data migration validation)

## Security & Compliance Checklist
- [ ] I have verified that no private active database files (`*.db`) are included in this commit.
- [ ] No API keys, credentials, or clinician secrets are hardcoded in the codebase.
- [ ] Clinical prescription routines securely link to validated National Provider Identifier (NPI) fields.
- [ ] All inputs are properly sanitized to prevent SQL Injection against the SQLite3 engine.

## Database & Local Testing Checklist
- [ ] I have run local unit tests using `python3 -m unittest discover tests/` and they passed.
- [ ] The schema seeding script (`database/seed.py`) executes without errors on a fresh SQLite3 install.
- [ ] Streamlit interface boots locally via `streamlit run app.py` and renders without console errors.
EOF

# 6. Generate Schema Integrity Unit Test
echo "Generating tests/test_schema.py..."
cat << 'EOF' > tests/test_schema.py
import unittest
import sqlite3
import os

class TestDatabaseSchema(unittest.TestCase):
    def setUp(self):
        # Locate the database (checks workspace/scratch or current folder)
        self.db_path = "recovery-app.db"
        if not os.path.exists(self.db_path):
            # If not in root, try fallback location
            self.db_path = "../recovery-app.db"
            
    def test_database_exists(self):
        """Verify the database file exists."""
        self.assertTrue(os.path.exists(self.db_path), f"Database file not found at {self.db_path}")

    def test_core_tables_exist(self):
        """Verify that all core tables are present in the schema."""
        expected_tables = {
            "youth_profiles",
            "caseworkers",
            "clinicians",
            "assessments",
            "care_assignments",
            "mat_prescriptions",
            "facilities"
        }
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()
        
        for table in expected_tables:
            self.assertIn(table, tables, f"Mandatory table '{table}' is missing from the database schema.")

    def test_clinician_npi_constraint(self):
        """Verify that clinicians table contains the NPI column."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(clinicians);")
        columns = [row[1] for row in cursor.fetchall()]
        conn.close()
        self.assertIn("npi_number", columns, "The 'npi_number' column is missing from the clinicians table.")

if __name__ == '__main__':
    unittest.main()
EOF

# 7. Generate GitHub Actions CI Workflow
echo "Generating .github/workflows/ci.yml..."
cat << 'EOF' > .github/workflows/ci.yml
name: SafeHaven TAY App CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build-and-test:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout Repository
      uses: actions/checkout@v4

    - name: Set up Python 3.12
      uses: actions/setup-python@v5
      with:
        python-python-version: '3.12'

    - name: Install Dependencies
      run: |
        python -m pip install --upgrade pip
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

    - name: Initialize Test Database Schema
      run: |
        # Set up a fresh testing database using the seed script
        if [ -f database/seed.py ]; then
          python database/seed.py
        elif [ -f setup-and-seed-db.py ]; then
          mkdir -p database
          cp setup-and-seed-db.py database/seed.py
          python database/seed.py
        fi

    - name: Run Schema Integrity & Unit Tests
      run: |
        python -m unittest discover tests/
EOF

# 8. Create baseline requirements.txt
echo "Generating requirements.txt..."
echo "streamlit" > requirements.txt

# 9. Initialize Git Locally
echo "Initializing local Git repository..."
git init
git add .
git commit -m "chore: automated repo initialization with security, contributing, and GitHub Actions CI pipelines"

echo "================================================================================"
echo "macOS Repository Setup Complete!"
echo "--------------------------------------------------------------------------------"
echo "Next Steps:"
echo "1. Create a remote repository on GitHub (do NOT initialize with README/license)."
echo "2. Link and push to remote:"
echo "   git branch -M main"
echo "   git remote add origin https://github.com/YOUR-USERNAME/safehaven-tay-app.git"
echo "   git push -u origin main"
echo "================================================================================"
