# Smart Returns AI

A smart return management system that uses AI to automatically process return requests.

## URLs to demo live



## v1.1.0 Additions
- **Reviewer Override Screen**: Override AI decisions with notes at `/returns/{id}` and manage the **Review Queue** at `/review`.
- **Tunable Thresholds**: Use `AUTO_APPROVE_THRESHOLD` and `AUTO_REJECT_THRESHOLD` env vars.
- **Metrics Page**: `/metrics` shows totals and average risk.

## Features
- Automated return processing using AI
- Image analysis for product condition
- Customer history tracking
- Risk scoring system
- Manual review queue
- Decision override capability
- Performance metrics dashboard
