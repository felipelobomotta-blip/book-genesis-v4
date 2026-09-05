# Security Policy

## Supported versions

Book Genesis uses semantic versioning. Imagination Edition is released as `5.0.0b1` in Python packaging and `v5.0.0-beta.1` on GitHub. The beta is actively maintained alongside the existing version support policy below.

| Version | Supported |
|---------|-----------|
| V5.0.0 beta | Active beta; report reproducible security issues |
| V4.2.x  | ✅ current |
| V4.1.x  | ⚠️ critical fixes only |
| V4.0.x  | ⚠️ critical fixes only |
| < V4.0  | ❌ end of life |

## Reporting a vulnerability

**Do not open a public issue for security reports.**

If you find a vulnerability — in the agent prompts, the install scripts, the file I/O contracts, or anywhere else in the pipeline that could compromise a user's system, credentials, or work — please report it privately:

1. Open a private [GitHub Security Advisory](https://github.com/felipelobomotta-blip/book-genesis-v4/security/advisories/new), OR
2. Message the maintainer through the email on the GitHub profile.

**What to include:**
- Version affected
- Steps to reproduce (agent config, input brief, observed behavior)
- Impact assessment (data leak, remote code, credential exposure, etc.)
- Suggested fix if you have one

## Response timeline

- **Acknowledgement:** within 72 hours
- **Initial assessment:** within 7 days
- **Fix or mitigation:** within 30 days for high/critical severity; scheduled for the next minor release for medium/low
- **Public disclosure:** coordinated with the reporter after the fix ships

## What is in scope

- Agent instructions that could be prompt-injected into performing destructive filesystem or shell actions
- Install scripts (`install.sh`, `install.ps1`) that could compromise a user's system
- File I/O contracts that could leak the user's OS-level secrets or credentials
- Third-party dependencies (Remotion demo, video tools) if they introduce supply-chain risk

## What is out of scope

- Model behavior of Claude/Codex/Kimi/Antigravity itself (report to the respective vendor)
- User-reported "the book was bad" — that is a quality issue, not security
- Cost overruns from long generation loops (mitigated by the 8.5 gate exit criteria, not a security bug)

## Hall of fame

Contributors who report valid vulnerabilities are credited by name in the release notes of the fixing version, unless they request anonymity.
