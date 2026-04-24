# Security Policy

## Supported Versions

The latest tagged release is supported. Older releases may receive fixes when the issue is small and low-risk.

## Privacy Model

`scripts/life_stats.py` stores data locally in:

```text
~/.openclaw/skills/memento-mori/state.json
```

The script does not make network requests. OpenClaw itself may deliver messages through configured channels when the user schedules a cron job; that behavior is controlled by the user's OpenClaw setup, not by this script.

## Sensitive Data

Journal entries may contain private reflections. Do not commit:

- `state.json`
- exported journals
- `.env` files
- channel identifiers, tokens, phone numbers, or chat IDs

The repository `.gitignore` excludes common local state and export files, but users should still review commits before publishing.

## Reporting A Vulnerability

Please open a private security advisory on GitHub if available, or contact the repository owner through GitHub. Include:

- affected version or commit
- reproduction steps
- expected and actual behavior
- whether local journal data can be exposed or modified

## Safety Boundary

This skill discusses mortality. If a user expresses self-harm intent, suicidal thoughts, immediate danger, or severe hopelessness, the skill instructions require the agent to stop countdown framing and respond with supportive crisis-safe guidance.

