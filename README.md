# Meta Buyer Intelligence

Windows desktop MVP for combining Meta/Facebook Ads performance with real order outcomes.

Current repository already contains:
- SQLite local data layer
- Demo Mode data generator
- Buyer Score / Purchase Propensity scoring
- Order and COD analytics foundations
- Recommendation engine
- Secure-secret helper
- GitHub Actions Windows build workflow

## Goal
Build a user-installable Windows application that analyzes which audience/time/ad segments actually produce orders, not merely clicks or chats.

## Safety and platform rules
- Official Meta APIs only
- No scraping or bypassing permissions
- No individual wealth estimation
- No automatic Meta changes without explicit approval
- Never hard-code access tokens, PII or payment credentials

## Default retail configuration
- 1 dozen: 180 THB prepaid / 190 THB COD
- 2 dozen: 360 THB prepaid / 375 THB COD
- 3 dozen: 540 THB prepaid / 560 THB COD

## Development
```bash
pip install -r requirements-dev.txt
pytest -q
python app.py
```

## Windows build
GitHub Actions workflow: **Build Windows Installer**

Target artifact for current MVP:
`MetaBuyerIntelligence.exe`

The next engineering instructions are in `AGENTS.md`.
