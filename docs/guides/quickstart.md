# SafeHaven & IX1 Sentinel Workspace: Technical Quick-Start Guide

Welcome to the development workspace for the **SafeHaven Transition-Age Youth (TAY) Care Coordination System** and the **Fourth & Central Community Watchdog (FCCW) / IX1 Sentinel** civic monitoring platform. 

This guide provides a single, unified reference for system installation, directory structure, and the entire registry of active Python scripts.

---

## 🛠️ 1. Installation & Environment Configuration

Follow these steps to configure your environment on **macOS** or **Android Termux**.

### Step 1.1: Install System-Level Prerequisites

*   **For macOS (via Homebrew):**
    ```bash
    # Install Homebrew if missing
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Install Python 3.12, SQLite3, and Git
    brew install python@3.12 sqlite git
    
    # Ensure C-compilers are active for spatial libraries
    xcode-select --install
    ```

*   **For Android (via Termux):**
    ```bash
    pkg update && pkg upgrade -y
    pkg install python sqlite git clang make libjpeg-turbo freetype -y
    ```

### Step 1.2: Build Local Virtual Environment

Run these commands inside your project root directory (`safehaven-fccw-workspace/`):

```bash
# Initialize the virtual environment
python3.12 -m venv .venv

# Activate the virtual environment
# macOS:
source .venv/bin/activate
# Termux:
source .venv/bin/activate
export MATHLIB="m"  # Required for Termux math compilation

# Upgrade package manager
pip install --upgrade pip
```

### Step 1.3: Install Dependencies
Install all required packages from your unified `requirements.txt`:
```bash
pip install -r requirements.txt
```

---

## 📂 2. Workspace Directory Structure

Maintain this structured hierarchy within your local repository to isolate configurations, databases, and core application modules:

```text
safehaven-fccw-workspace/
│
├── .github/                           # Automated Integration Pipelines
│   └── workflows/
│       └── ci.yml                     # GitHub Actions CI Workflow Configuration
│
├── database/                          # Relational SQLite Databases & Schemas
│   ├── seed.py                        # Database initializer and reference seed
│   ├── setup_sro_db.py                # SRO registry database initializer
│   ├── query_services.py              # Care dashboard query utility
│   ├── query_sro.py                   # SRO registry query utility
│   ├── simulate_intake.py             # Intake transaction simulation
│   ├── schema.sql                     # Complete SQL schema & DDL
│   ├── recovery_app.db                # SQLite care database (Gitignored - PII)
│   └── sro_housing.db                 # SQLite SRO database (Gitignored - registry)
│
├── docs/                              # Technical Runbooks & Design Guidelines
│   ├── guides/                         # Runbooks and project guides
│   ├── forms/                          # Intake and legal forms
│   └── assets/                         # Generated maps and images
│
├── tests/                             # Automated Test Verification Suites
│   ├── test_schema.py                 # Care database schema test cases
│   └── test_watchdog.py               # Boundary & rollback test cases
│
├── app.py                             # Streamlit Interactive Front-end App
├── fccw_watchdog.py                   # IX1 Zoning & Policy Watchdog Engine
├── fccw_api_monitor-v3.py             # Open Data API Auditor & Alert Dispatcher
├── fccw_spatial_map.py                # Cartographic GIS Map Generator
├── run_all_simulations.sh             # Master verification script
│
├── requirements.txt                   # Unified Python dependencies list
├── setup-mac-repo.sh                  # macOS developer setup automation script
│
└── .gitignore                         # Security wildcard filters (*.db, *.toml)
```

---

## 🐍 3. Core Python Scripts Registry

Below is a complete index of all active Python scripts within the workspace, detailing their operational purpose and exact terminal execution commands.

### 1. Database Initialization (`database/seed.py`)
*   **Purpose**: Compiles the **10 core relational tables** (tracking youth profiles, peer specialists, clinics, facilities, program placements, and MAT prescriptions) and seeds them with default Skid Row agencies and credentials.
*   **Execution**:
    ```bash
    python3 database/seed.py
    ```

### 2. SRO Registry Setup (`database/setup_sro_db.py`)
*   **Purpose**: Initializes the **SRO Watchdog Registry** (`sro-housing.db`) containing the historic inventory (884 registered units across 5 properties, including the Baltimore Hotel and King Edward Hotel) to enforce 1:1 replacement policies.
*   **Execution**:
    ```bash
    python3 database/setup_sro_db.py
    ```

### 3. Streamlit Front-End Web Portal (`app.py`)
*   **Purpose**: Launches the interactive, mobile-responsive dashboard for case managers. Displays active bed capacities, participant profiles, and coordinates clinical care pathways.
*   **Execution**:
    ```bash
    streamlit run app.py
    ```

### 4. Low-Barrier Intake Transaction Simulation (`database/simulate_intake.py`)
*   **Purpose**: Simulates an end-to-end, zero-barrier client intake for a street youth alias ("Sky"). In a single transaction, it books an active bed, assigns a Peer Support Specialist, and issues an M.D.-signed MAT prescription script.
*   **Execution**:
    ```bash
    python3 database/simulate_intake.py
    ```

### 5. Multi-Track Civic Watchdog Engine (`fccw_watchdog.py`)
*   **Purpose**: Evaluates spatial coordinate compliance, audits SRO replacement filings, and runs local Natural Language Processing (NLP) to screen out misleading information within public planning comments.
*   **Execution**:
    ```bash
    python3 fccw_watchdog.py
    ```

### 6. Real-Time GIS API Auditor & Alert Dispatcher (`fccw_api_monitor-v3.py`)
*   **Purpose**: Queries Los Angeles City Planning's Open Data API endpoints. Operates a mock interface locally to generate instant responsive emails and SMS alerts if developmental applications breach Skid Row boundaries.
*   **Execution**:
    ```bash
    python3 fccw_api_monitor-v3.py
    ```

### 7. Cartographic GIS Boundary Mapper (`fccw_spatial_map.py`)
*   **Purpose**: Computes geometric boundaries and uses Matplotlib to plot checked projects against Skid Row’s containment buffer zones, exporting a publication-quality map (`fccw_zoning_audit_map.png`).
*   **Execution**:
    ```bash
    python3 fccw_spatial_map.py
    ```

### 8. Relational Active Placements Reporter (`database/query_services.py`)
*   **Purpose**: Runs join-queries across SQLite tables to output a comprehensive administrative diagnostic report of currently enrolled participants, assigned caseworkers, and clinical adherence statuses.
*   **Execution**:
    ```bash
    python3 database/query_services.py
    ```

### 9. Unified Verification Suite (`run_all_simulations.sh`)
*   **Purpose**: Automates testing. Installs dependencies, sets up fresh databases, runs the 12-case unit tests, and conducts active command-line mock simulations.
*   **Execution**:
    ```bash
    python3 run_all_simulations.sh
    ```

---

## 🔒 4. Key Security Directives
1.  **PII Quarantine**: Never commit `.db` files. Ensure they are in the `.gitignore` list.
2.  **API Verification**: Always validate that medical practitioners listed in `clinicians` have a valid 10-digit National Provider Identifier (NPI) to satisfy federal care compliance.
3.  **Human-in-the-Loop**: Case managers retain absolute discretionary override capacity over any system-recommended placement queues.
