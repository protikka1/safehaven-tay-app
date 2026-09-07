# IX1 Sentinel & SafeHaven: GitHub Collaboration & Contribution Guidelines

This document provides ready-to-use GitHub templates and contributor guidelines to structure and guide new developers, data scientists, and community advocates contributing to **`IX1 Sentinel`** and **`SafeHaven`**.

Save these templates in your local repository under the `.github/` folder to automate your repository's issue tracking and pull request workflows.

---

## Directory Setup for Templates
To implement these guidelines, create the following directory structure in your repository:
```text
your-repository/
├── .github/
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── CONTRIBUTING.md
│   └── ISSUE_TEMPLATE/
│       ├── bug_report.md
│       ├── feature_request.md
│       └── zoning_alert.md
```

---

# 1. Pull Request Template
**File Path:** `.github/PULL_REQUEST_TEMPLATE.md`

```markdown
## 🛡️ IX1 Sentinel / SafeHaven Pull Request

Thank you for contributing to the Skid Row civic-tech ecosystem! Please fill out the sections below to help maintain strict standards of data governance, security, and human-in-the-loop accountability.

### 1. Contribution Track
Please indicate which module or track this PR modifies:
- [ ] **Track A (GIS Zoning Engine)**: Core spatial containment calculations, API parsers, boundary modifications.
- [ ] **Track B (SRO Replacement Ledger)**: SQLite/PostgreSQL relational schemas, demolition audit checks, covenant locks.
- [ ] **Track C (Prosocial Forum / SoM)**: NLP mitigations, factual grounding rules, UI moderations.
- [ ] **SafeHaven App Core**: Streamlit views, database migrations, mobile/Termux optimization, APIs.
- [ ] **CI/CD / Documentation**: Deployment scripts, actions, tests.

### 2. Description & Justification
- **What change does this PR introduce?** (Include background on specific city planning cases or municipal ordinances, such as DTLA 2040, IX1 mandates, or SRO 1:1 rules).
- **How does this protect Skid Row residents?** (Explain how this change prevents speculative displacement, secures housing stability, or enhances low-barrier care coordination).

### 3. Verification & Compliance Checklist
Before requesting a review, you must verify that your code adheres to our robust data governance gates:

- [ ] **Lint & Format**: Code is formatted via `black` and syntax-checked via `flake8`.
- [ ] **Security Scan**: Local code has been scanned with `bandit` and contains no raw SQL injection vulnerabilities, hardcoded secrets, or exposed API tokens.
- [ ] **Unit Tests Passed**: The 12-case test suite (`test_watchdog.py` or app suite) runs with a 100% green status.
- [ ] **Termux Optimized**: Verified that execution remains stable inside mobile sandbox limits (where applicable).
- [ ] **Proactive Human-Led Control**: For administrative automation or client tracking, verify that final decision-making authority is preserved for human caseworkers/advocates (no fully automated client denials).

### 4. Code / Database Schema Changes
If this PR modifies database schemas (`recovery-app.db` or `sro-housing.db`):
- Have you updated `database/seed.py` and matching SQL schema files?
- Have you executed `run_all_simulations.sh` locally to ensure downstream simulations are uninterrupted?

---
*By submitting this PR, you agree to license your contributions under our open-source license.*
```

---

# 2. Bug Report Template
**File Path:** `.github/ISSUE_TEMPLATE/bug_report.md`

```markdown
---
name: 🐛 Bug Report
about: Report a technical bug or logical error within the watchdog or app engines
title: '[BUG] '
labels: bug, triage
assignees: ''
---

### 1. System Environment
Please let us know where this bug occurred:
- **Operating System**: [e.g., Android Termux, macOS, Linux]
- **Python Version**: [e.g., 3.10, 3.11, 3.12]
- **Platform Branch**: [e.g., main, dev, local-fork]

### 2. Describe the Bug
Provide a clear and concise description of what the issue is. (e.g., SRO replacement ledger fails to block a non-compliant permit; GIS engine fails to trigger warning on perimeter coordinates).

### 3. Step-by-Step Reproduction Guide
Steps to reproduce the behavior locally:
1. Run `./run_all_simulations.sh`
2. Perform action: '...'
3. See error traceback:
```text
Paste error traceback or console logs here
```

### 4. Expected Behavior
A clear and concise description of what should have happened in accordance with Skid Row spatial boundary limits or child-support pass-through rules.

### 5. Screenshots / Console Outputs
If applicable, add screenshots or paste diagnostic outputs (such as `database/query_services.py` logs or Streamlit UI errors) to help explain your problem.
```

---

# 3. Zoning / SRO Alert Template
**File Path:** `.github/ISSUE_TEMPLATE/zoning_alert.md`

```markdown
---
name: 🚨 Zoning or SRO Replacement Alert
about: Report a newly filed LA City Planning case or potential SRO demolition requiring tracking
title: '[WATCHDOG ALERT] Case: '
labels: zoning-audit, sro-ledger
assignees: ''
---

### 📡 New Municipal Development / Covenant Alert

Please use this template to register newly filed LA Planning cases, alcohol permits (CUB), or SRO demolition warnings requiring community-led technical audit tracking.

### 1. Planning Case Metadata
- **Planning Case Number**: [e.g., CPC-2025-1600-GPA-VZC-HD-MCUP-SPR]
- **Project / Property Name**: [e.g., Fourth & Central, Baltimore Hotel]
- **Street Address**: [e.g., 1110 E 4th St]
- **GPS Coordinates**: (Latitude: `XX.XXXX`, Longitude: `-118.XXXX`)

### 2. Affected Protections
Indicate which protective measures are impacted:
- [ ] **IX1 Zone Encroachment**: Proposal falls within 3rd to 7th Streets, and Main to Alameda.
- [ ] **Perimeter Buffer Zone (Within 3 Blocks)**: Speculative luxury tower proposed near boundary.
- [ ] **SRO Demolition/Conversion**: SRO units are threatened with loss or conversion.
- [ ] **Compatible Use Violation**: CUB alcohol or dispensary proposed near recovery centers.

### 3. Case Details & Developer Request
- What does the developer propose to build vs. the covenanted affordable housing ratio?
- If an SRO is affected, what is the covenanted 1:1 replacement address proposed?
- Developer Notes / Link to LA Planning Portal:
```

---

# 4. Contributing Guidelines
**File Path:** `.github/CONTRIBUTING.md`

```markdown
# Contributing to IX1 Sentinel & SafeHaven

Thank you for choosing to commit your skills to protecting Skid Row's housing stability and low-barrier care networks! 

This project is built around the principles of **Robust Data Governance** and **Proactive Human-Led Oversight**. All software must serve to empower community advocates and frontline caseworkers, not to replace their judgment or automate administrative barriers.

---

## 🚀 Setting Up Your Local Environment

Before pushing code, configure your local environment using our unified bootstrappers:

### For Android Developers (Termux):
Run our automated mobile environment script:
```bash
python3 database/seed.py
```
*Note: This script configures prebuilt NumPy and Pandas binaries through Termux's `tur-repo` to bypass mobile processor compile crashes.*

### For Desktop Developers (macOS / Linux):
Initialize your local Git repository and python virtual environment:
```bash
chmod +x setup-mac-repo.sh
./setup-mac-repo.sh
```

---

## 🧪 Testing and Integration Checklist

To maintain code security and avoid regressions that could result in erroneous care coordination, all contributions must pass through our three continuous integration (CI) gates:

1. **Linting and Formatting**:
   Ensure your scripts conform to standard python formatting rules:
   ```bash
   black your_modified_script.py
   flake8 your_modified_script.py
   ```
2. **Security Audits**:
   Ensure your code contains no exposed API secrets or SQL injection hazards:
   ```bash
   bandit -r .
   safety check
   ```
3. **Run the Master Integration Suite**:
   Execute the master orchestrator to verify that the database schema seeds cleanly, unit tests pass green, GIS boundaries parse, and alerts dispatch:
   ```bash
   chmod +x run_all_simulations.sh
   ./run_all_simulations.sh
   ```

---

## 💬 Code of Conduct & Communication Norms

Our community is dedicated to constructive, factual, and prosocial interaction. 
* To prevent the **"Sense of Misinformation" (SoM)** from escalating into local divisions, we focus our discussions on **factual policy structures** (such as specific zoning codes, SRO counts, and legal mandates) rather than attacking individual motives.
* Keep communications civil, actionable, and empathetic. 

Let's write code that makes a tangible, human impact!
```
