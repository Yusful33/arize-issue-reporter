# Arize Bug Reporter CLI

A CLI tool to quickly create GitHub issues for bugs encountered in the Arize platform. Uses Claude AI to format your brief bug descriptions into well-structured GitHub issues.

## Setup

### Prerequisites

1. **GitHub CLI (`gh`)** - Must be installed and authenticated
   ```bash
   # Install (macOS)
   brew install gh
   
   # Authenticate
   gh auth login
   ```

2. **Anthropic API Key** - Required for AI-powered issue formatting
   ```bash
   export ANTHROPIC_API_KEY='your-api-key'
   ```

### Installation

```bash
# Navigate to the directory
cd /Users/yusufcattaneo/Projects/arize_bug_reporter

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Make the script executable
chmod +x arize_bug.py
```

### Add an Alias (Recommended)

Add this to your `~/.zshrc` for easy access:

```bash
alias arize-bug="source /Users/yusufcattaneo/Projects/arize_bug_reporter/.venv/bin/activate && python /Users/yusufcattaneo/Projects/arize_bug_reporter/arize_bug.py"
```

Then reload your shell:
```bash
source ~/.zshrc
```

## Usage

### Quick One-Liner

```bash
python arize_bug.py "Trace waterfall view doesn't show spans" \
  --url "https://app.arize.com/organizations/abc/spaces/xyz/projects/my-project/traces" \
  --space-id "xyz-123"
```

### With More Context

```bash
python arize_bug.py "Export to CSV is broken" \
  --url "https://app.arize.com/..." \
  --space-id "my-space-id" \
  --expected "CSV file downloads" \
  --actual "Nothing happens, no error shown"
```

### Interactive Mode

```bash
python arize_bug.py --interactive
```

### Dry Run (Preview Without Creating)

```bash
python arize_bug.py "Some bug description" \
  --url "https://app.arize.com/..." \
  --space-id "abc123" \
  --dry-run
```

### With Labels

```bash
python arize_bug.py "UI rendering issue" \
  --url "https://app.arize.com/..." \
  --space-id "abc123" \
  --labels bug \
  --labels ui
```

## Options

| Option | Short | Required | Description |
|--------|-------|----------|-------------|
| `--url` | `-u` | Yes | Arize platform URL where the bug occurred |
| `--space-id` | `-s` | Yes | Space ID where the bug occurred |
| `--expected` | `-e` | No | What you expected to happen |
| `--actual` | `-a` | No | What actually happened |
| `--labels` | `-l` | No | GitHub labels (can be used multiple times) |
| `--dry-run` | | No | Preview the issue without creating it |
| `--interactive` | `-i` | No | Interactive mode with prompts |

## Example Output

```
🤖 Generating issue with AI...
📤 Creating GitHub issue...

✅ Issue created successfully!
🔗 https://github.com/Arize-ai/arize/issues/1234
```
# arize-issue-reporter
