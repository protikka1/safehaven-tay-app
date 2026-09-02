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
