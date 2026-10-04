# Meta Buyer Intelligence engineering brief

Build a commercial-minded Windows desktop app that combines official Meta Ads data with first-party order outcomes.

Rules:
- Use official APIs only; never scrape private Facebook data or bypass permissions.
- Never infer individual wealth. Use segment-level Purchase Propensity / Buyer Score.
- Keep Meta insight breakdown grains separate to avoid double counting.
- Orders are the source of truth for conversion quality.
- Never execute Meta write actions without explicit user approval.
- Never hard-code tokens, payment details, or PII.
- Demo Mode must always work.
- Target artifact: MetaBuyerIntelligence.exe first; installer packaging can follow.
- If Meta API fields/permissions are uncertain, isolate them behind adapters and mark VERIFY_WITH_CURRENT_META_DOCS.

Next priorities:
1. Complete GUI and Demo Mode.
2. Complete real Meta provider and paging.
3. Add order CRUD and CSV import/export.
4. Add Buyer Score, COD analytics, hourly analysis and recommendations.
5. Add secure token storage.
6. Add approval queue for future Meta write actions.
7. Keep GitHub Actions Windows build green.
