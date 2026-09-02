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
