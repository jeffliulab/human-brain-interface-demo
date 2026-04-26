# Security Policy

## This project is a research prototype

**`anima-intention-action` is NOT a medical device.** It is an open-source research prototype for a cognitive framework that could, in the future and after appropriate regulatory validation, be used in assistive-technology products. Do not deploy it in clinical settings.

## Reporting a vulnerability

If you believe you have found a security issue or a defect with **clinical-safety implications** (for example: a way to bypass Test-and-Check gates, defeat the Safety Watchdog, inject malicious TaskSpecs, or cause the framework to emit unsafe motor commands), please **do not open a public GitHub issue**.

Instead, email the maintainer privately:

- **Contact**: the email address listed under `project.authors` in [`python/pyproject.toml`](./python/pyproject.toml)
- **Subject line**: `[SECURITY] anima-intention-action: <short summary>`
- **PGP**: not yet available; an encrypted channel can be arranged on request

You should receive an acknowledgement within **72 hours**. A triage and remediation plan will follow within **7 days**.

## What to include

- Description of the issue and its impact
- Steps to reproduce (a minimal test case is very helpful)
- Affected version / commit SHA
- Whether you believe the issue has patient-safety implications, and why

## Disclosure policy

- We follow **coordinated disclosure**: we ask reporters to withhold public disclosure until we have a fix available or 90 days have elapsed, whichever comes first.
- We will credit reporters in the CHANGELOG unless they request anonymity.
- For issues with patient-safety implications, we may extend the disclosure window if a downstream integrator needs time to patch.

## Scope

Security reports welcomed for:

- The framework source code in `python/src/anima_intention_action/`
- LLM provider abstractions and tool-calling paths
- Test-and-Check validation logic
- Safety Watchdog and E-stop handling
- Audit-trail integrity
- Dependencies declared in `pyproject.toml`

Out of scope:

- Issues in third-party dependencies that are already publicly known and awaiting upstream patch
- Social engineering or physical-security scenarios
- Performance / denial-of-service on demo deployments (not safety-critical)

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.0.x (pre-alpha) | ✅ main branch |
| < 0.0.x | ❌ |

Once we tag `0.1.0`, a full support matrix will be published here.
