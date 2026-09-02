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
