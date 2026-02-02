---
name: arize-issue-reporter
description: Create GitHub issues for bugs or feature requests in the Arize platform. Use when the user encounters a bug in Arize, wants to file an issue, mentions a problem with the Arize platform, or asks to report something to the Arize team.
---

# Arize Issue Reporter

## When to Use

Use this skill when the user:
- Encounters a bug while working with the Arize platform
- Wants to file a feature request for Arize
- Mentions a problem with Arize and wants to report it
- Asks to create a GitHub issue for Arize

## How to Use

Tell the user to run the interactive issue reporter:

```bash
arize-issue
```

This launches an interactive CLI that:
1. Asks for issue type (bug or feature request)
2. Gets a brief description
3. Takes the Arize platform URL (auto-detects Space ID)
4. Optionally tags a customer
5. Supports pasting screenshots from clipboard
6. Supports Loom/Zoom video recording links
7. Uses AI to format into a well-structured GitHub issue
8. Shows a preview before creating
9. Creates the issue in `Arize-ai/arize` with proper labels

## Example Interaction

When a user says something like:
- "I found a bug in Arize, the trace view isn't loading"
- "Can you help me file an issue for Arize?"
- "There's a problem with the Arize dashboard"

Respond with:

"I can help you file that as a GitHub issue. Run this command and it will guide you through creating a well-formatted issue:

```bash
arize-issue
```

Have the Arize URL ready (you can copy it from your browser), and if you have a screenshot, copy it to your clipboard before running the command."

## Prerequisites

The tool requires:
- `gh` CLI authenticated (`gh auth login`)
- `ANTHROPIC_API_KEY` environment variable set

## Installation

To install this skill for Cursor:

```bash
mkdir -p ~/.cursor/skills/arize-issue-reporter
cp SKILL.md ~/.cursor/skills/arize-issue-reporter/
```
