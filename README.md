# Arize Issue Reporter

A CLI tool to quickly create GitHub issues for bugs and feature requests in the Arize platform.

## Quick Start

```bash
arize-issue
```

That's it! The tool guides you through everything interactively.

## What It Does

1. **Asks for issue type** - Bug report or feature request
2. **Gets your description** - Brief summary of the issue
3. **Takes the Arize URL** - Auto-detects Space ID
4. **Customer tagging** - Optional, for customer-related issues
5. **Screenshot support** - Paste from clipboard (Cmd+V)
6. **Video recordings** - Paste Loom/Zoom URLs
7. **AI formatting** - Generates a well-structured issue
8. **Preview & confirm** - Review before creating
9. **Creates the issue** - In Arize-ai/arize with proper labels

## Setup

### Prerequisites

```bash
# Install GitHub CLI
brew install gh
gh auth login

# Set Anthropic API key
export ANTHROPIC_API_KEY='your-api-key'
```

### Installation

```bash
cd /Users/yusufcattaneo/Projects/arize-issue-reporter
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Add to Shell

Add to `~/.zshrc`:

```bash
arize-issue() {
    source /Users/yusufcattaneo/Projects/arize-issue-reporter/.venv/bin/activate
    python /Users/yusufcattaneo/Projects/arize-issue-reporter/arize_bug.py "$@"
}
```

Then: `source ~/.zshrc`

### Install Cursor Skill (Optional)

To let Claude Code help you file issues, copy the skill:

```bash
mkdir -p ~/.cursor/skills/arize-issue-reporter
cp SKILL.md ~/.cursor/skills/arize-issue-reporter/
```

Now when you tell Claude about an Arize bug, it will suggest using this tool.

## Example Session

```
$ arize-issue

📝 Arize Issue Reporter - Interactive Mode

Issue type:
  1. Bug report (default)
  2. Feature request
Select type (1, 2): 1
Describe the bug: Trace waterfall view shows empty when clicking from search
Arize platform URL: https://app.arize.com/organizations/.../spaces/U3BhY2U6.../...
   (Space ID auto-detected: U3BhY2U6...)
Is this related to a specific customer? [y/N]: n
Do you have a screenshot to attach? [y/N]: y
   Paste your screenshot (Cmd+V), then press Enter: 
   ✓ Screenshot captured
Do you have any video recordings (Loom/Zoom)? [y/N]: n

🤖 Generating issue with AI...
📸 Uploading screenshots...
   ✓ Screenshot 1 uploaded successfully

============================================================
ISSUE PREVIEW
============================================================

📌 Title: [Bug] Trace waterfall view displays empty when selecting trace from search results
...

Create this issue? [Y/n]: y

✅ Issue created successfully!
🔗 https://github.com/Arize-ai/arize/issues/12345
```
