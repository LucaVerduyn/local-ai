# Security Policy

## Supported versions

Security fixes are applied to the latest release on `main`.

## Reporting a vulnerability

Please **do not** open a public issue for security vulnerabilities.

Email the maintainer privately or use GitHub’s private vulnerability reporting if enabled on the repository.

Include:

- A description of the issue
- Steps to reproduce
- Impact assessment
- Any suggested fix

You should receive an acknowledgement within a reasonable time. We will coordinate a fix and disclosure timeline.

## Scope notes

Local AI is designed to keep data on-device. Still report issues involving:

- Path traversal or unsafe file handling
- SQLite injection / unsafe query construction
- Insecure deserialization
- Unexpected network exfiltration

Model quality issues and Ollama upstream bugs are generally out of scope unless Local AI mishandles them.
