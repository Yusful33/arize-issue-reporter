#!/usr/bin/env python3
"""
Arize Bug Reporter CLI

A CLI tool to quickly create GitHub issues for bugs encountered in the Arize platform.
Uses Claude AI to format bug reports into well-structured GitHub issues.
"""

import json
import mimetypes
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import anthropic
import click
import requests


def get_clipboard_image() -> str | None:
    """Get image from clipboard and save to a temp file. Returns the file path or None.
    
    Works on macOS using osascript (AppleScript) or pngpaste if available.
    """
    # Create a temp file for the clipboard image
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, "clipboard_screenshot.png")
    
    # Try pngpaste first (if installed via `brew install pngpaste`)
    try:
        result = subprocess.run(
            ["pngpaste", temp_path],
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and os.path.exists(temp_path):
            return temp_path
    except FileNotFoundError:
        # pngpaste not installed, fall through to AppleScript
        pass
    
    # Fallback: Use osascript to save clipboard image
    # This AppleScript saves the clipboard image to a file
    applescript = f'''
    set theFile to POSIX file "{temp_path}"
    try
        set imageData to the clipboard as «class PNGf»
        set fileRef to open for access theFile with write permission
        write imageData to fileRef
        close access fileRef
        return "success"
    on error errMsg
        try
            close access theFile
        end try
        return "error: " & errMsg
    end try
    '''
    
    result = subprocess.run(
        ["osascript", "-e", applescript],
        capture_output=True,
        text=True
    )
    
    if "success" in result.stdout and os.path.exists(temp_path):
        return temp_path
    
    return None


def upload_image_to_imgur(file_path: str, verbose: bool = False) -> str | None:
    """Upload an image to Imgur and return the markdown embed string.
    
    Uses Imgur's anonymous upload API (no account required).
    """
    import base64
    
    path = Path(file_path).expanduser().resolve()
    
    if not path.exists():
        if verbose:
            click.echo(f"      File not found: {path}")
        return None
    
    # Imgur anonymous upload client ID (public, for anonymous uploads)
    # This is a registered client ID for this tool
    CLIENT_ID = "546c25a59c58ad7"
    
    try:
        # Read and base64 encode the image
        with open(path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        # Upload to Imgur
        headers = {
            "Authorization": f"Client-ID {CLIENT_ID}",
        }
        
        resp = requests.post(
            "https://api.imgur.com/3/image",
            headers=headers,
            data={"image": image_data, "type": "base64"},
            timeout=60
        )
        
        if verbose:
            click.echo(f"      Imgur response: {resp.status_code}")
        
        if resp.status_code != 200:
            if verbose:
                click.echo(f"      Error: {resp.text[:200]}")
            return None
        
        data = resp.json()
        
        if data.get("success"):
            image_url = data["data"]["link"]
            return f"![Screenshot]({image_url})"
        
        return None
        
    except Exception as e:
        if verbose:
            click.echo(f"      Exception: {e}")
        return None


def save_screenshot_locally(file_path: str) -> str:
    """Copy screenshot to a persistent location and return the new path."""
    import shutil
    from datetime import datetime
    
    path = Path(file_path).expanduser().resolve()
    
    if not path.exists():
        raise click.ClickException(f"Screenshot file not found: {file_path}")
    
    # Save to ~/Desktop/arize-screenshots/
    screenshots_dir = Path.home() / "Desktop" / "arize-screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_path = screenshots_dir / f"screenshot_{timestamp}.png"
    
    shutil.copy2(path, new_path)
    return str(new_path)


def parse_space_id_from_url(url: str) -> str | None:
    """Extract the space ID from an Arize platform URL.
    
    Example URL:
    https://app.arize.com/organizations/.../spaces/U3BhY2U6MzY1NTU6aitIdg==/models/...
    
    Returns the space ID or None if not found.
    """
    # Pattern: /spaces/{space_id}/ where space_id is typically base64-encoded
    match = re.search(r'/spaces/([^/\?]+)', url)
    if match:
        return match.group(1)
    return None


GITHUB_REPO = "Arize-ai/arize"

# Issue type configurations
ISSUE_TYPES = {
    "bug": {
        "prefix": "[Bug]",
        "label": "bug",
        "prompt_context": "a bug report",
    },
    "feature": {
        "prefix": "[Internal Feature Request]",
        "label": "enhancement",
        "prompt_context": "an internal feature request",
    },
}

PROMPT_TEMPLATE = """You are helping create a GitHub issue for {issue_type_context} in the Arize observability platform.

User's description: {summary}
Platform URL: {url}
Space ID: {space_id}
{extra_context}
{customer_context}

Generate a well-structured GitHub issue with:
1. A clear, concise title (prefix with {title_prefix})
2. Description of the issue/request
3. Location context (include the URL and Space ID)
{type_specific_sections}

Output ONLY valid JSON in this exact format (no markdown, no extra text):
{{"title": "...", "body": "..."}}

The body should be formatted as GitHub-flavored markdown with appropriate headers (##) for each section."""

BUG_SECTIONS = """4. Steps to reproduce (if inferable from the description, otherwise use reasonable placeholders like "1. Navigate to [URL]", "2. Perform [action]", "3. Observe the issue")
5. Expected behavior
6. Actual behavior"""

FEATURE_SECTIONS = """4. Use case / motivation
5. Proposed solution or behavior
6. Any additional context"""


def get_extra_context(expected: str | None, actual: str | None) -> str:
    """Build extra context string from optional parameters."""
    parts = []
    if expected:
        parts.append(f"Expected behavior: {expected}")
    if actual:
        parts.append(f"Actual behavior: {actual}")
    return "\n".join(parts) if parts else ""


def format_issue_with_ai(
    summary: str,
    url: str,
    space_id: str,
    issue_type: str = "bug",
    customer: str | None = None,
    expected: str | None = None,
    actual: str | None = None,
) -> dict:
    """Use Claude to format the bug report into a structured GitHub issue."""
    client = anthropic.Anthropic()
    
    extra_context = get_extra_context(expected, actual)
    type_config = ISSUE_TYPES.get(issue_type, ISSUE_TYPES["bug"])
    
    customer_context = ""
    if customer:
        customer_context = f"Customer: {customer} (this is a customer-reported issue)"
    
    prompt = PROMPT_TEMPLATE.format(
        summary=summary,
        url=url,
        space_id=space_id,
        issue_type_context=type_config["prompt_context"],
        title_prefix=type_config["prefix"],
        extra_context=extra_context if extra_context else "(No additional context provided)",
        customer_context=customer_context,
        type_specific_sections=BUG_SECTIONS if issue_type == "bug" else FEATURE_SECTIONS,
    )
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ],
    )
    
    response_text = message.content[0].text.strip()
    
    # Parse the JSON response
    try:
        issue_data = json.loads(response_text)
    except json.JSONDecodeError:
        # Try to extract JSON from the response if it has extra text
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            issue_data = json.loads(json_match.group())
        else:
            raise click.ClickException(f"Failed to parse AI response as JSON: {response_text}")
    
    if "title" not in issue_data or "body" not in issue_data:
        raise click.ClickException(f"AI response missing required fields: {issue_data}")
    
    return issue_data


def create_github_issue(title: str, body: str, labels: tuple[str, ...]) -> str:
    """Create a GitHub issue using the gh CLI and return the issue URL."""
    cmd = [
        "gh", "issue", "create",
        "--repo", GITHUB_REPO,
        "--title", title,
        "--body", body,
    ]
    
    for label in labels:
        cmd.extend(["--label", label])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise click.ClickException(f"Failed to create GitHub issue: {result.stderr}")
    
    # gh issue create outputs the issue URL
    return result.stdout.strip()


def interactive_mode() -> dict:
    """Gather issue details interactively."""
    click.echo("\n📝 Arize Issue Reporter - Interactive Mode\n")
    
    # Issue type selection
    click.echo("Issue type:")
    click.echo("  1. Bug report (default)")
    click.echo("  2. Feature request")
    type_choice = click.prompt("Select type", type=click.Choice(["1", "2"]), default="1", show_default=False)
    issue_type = "bug" if type_choice == "1" else "feature"
    
    summary = click.prompt(f"Describe the {'bug' if issue_type == 'bug' else 'feature request'}")
    url = click.prompt("Arize platform URL")
    
    # Try to parse space ID from URL
    space_id = parse_space_id_from_url(url)
    if space_id:
        click.echo(f"   (Space ID auto-detected: {space_id})")
    else:
        space_id = click.prompt("Space ID (could not auto-detect from URL)")
    
    # Customer prompt
    has_customer = click.confirm("Is this related to a specific customer?", default=False)
    customer = None
    if has_customer:
        customer = click.prompt("Customer name/identifier (for tagging)")
    
    expected = None
    actual = None
    if issue_type == "bug":
        expected = click.prompt("What did you expect to happen?", default="", show_default=False)
        actual = click.prompt("What actually happened?", default="", show_default=False)
    
    # Screenshots - simple clipboard paste flow
    screenshots = []
    clipboard = False
    
    if click.confirm("Do you have a screenshot to attach?", default=False):
        click.echo("   Paste your screenshot (Cmd+V), then press Enter: ", nl=False)
        input()  # Wait for paste + Enter
        clipboard = True
        click.echo("   ✓ Screenshot captured")
    
    # Recordings
    recordings = []
    if click.confirm("Do you have any video recordings (Loom/Zoom)?", default=False):
        click.echo("   (Paste URLs, empty line to finish)")
        while True:
            rec_url = click.prompt("Recording URL", default="", show_default=False)
            if not rec_url:
                break
            recordings.append(rec_url.strip())
    
    return {
        "summary": summary,
        "url": url,
        "space_id": space_id,
        "issue_type": issue_type,
        "customer": customer,
        "expected": expected or None,
        "actual": actual or None,
        "screenshots": screenshots,
        "clipboard": clipboard,
        "recordings": recordings,
    }


@click.command()
@click.argument("summary", required=False)
@click.option("--url", "-u", help="Arize platform URL where issue occurred")
@click.option("--space-id", "-s", help="Space ID where issue occurred")
@click.option("--type", "-t", "issue_type", type=click.Choice(["bug", "feature"]), default="bug", help="Issue type: bug or feature request")
@click.option("--customer", "-c", help="Customer name/identifier if customer-related")
@click.option("--expected", "-e", help="What you expected to happen (for bugs)")
@click.option("--actual", "-a", help="What actually happened (for bugs)")
@click.option("--screenshot", "--image", "screenshots", multiple=True, help="Path to screenshot image (can be used multiple times)")
@click.option("--clipboard", "-p", is_flag=True, help="Paste screenshot from clipboard")
@click.option("--recording", "--video", "recordings", multiple=True, help="URL to Loom/Zoom recording (can be used multiple times)")
@click.option("--labels", "-l", multiple=True, help="Additional GitHub labels")
@click.option("--dry-run", is_flag=True, help="Preview the issue without creating it")
@click.option("--interactive", "-i", is_flag=True, help="Interactive mode with prompts")
def main(
    summary: str | None,
    url: str | None,
    space_id: str | None,
    issue_type: str,
    customer: str | None,
    expected: str | None,
    actual: str | None,
    screenshots: tuple[str, ...],
    clipboard: bool,
    recordings: tuple[str, ...],
    labels: tuple[str, ...],
    dry_run: bool,
    interactive: bool,
):
    """
    Create a GitHub issue for the Arize platform.
    
    SUMMARY is a brief description of the bug or feature request.
    
    Examples:
    
        arize-bug "Traces don't load" --url "https://app.arize.com/..." --space-id "abc123"
        
        arize-bug "Add export to PDF" --type feature --url "..." --space-id "..."
        
        arize-bug "Dashboard broken" --url "..." --space-id "..." --customer "acme-corp"
        
        arize-bug --interactive
    """
    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise click.ClickException(
            "ANTHROPIC_API_KEY environment variable is required. "
            "Set it with: export ANTHROPIC_API_KEY='your-key'"
        )
    
    # Interactive mode
    if interactive:
        data = interactive_mode()
        summary = data["summary"]
        url = data["url"]
        space_id = data["space_id"]
        issue_type = data["issue_type"]
        customer = data["customer"]
        expected = data["expected"]
        actual = data["actual"]
        screenshots = tuple(data.get("screenshots", []))
        clipboard = data.get("clipboard", False)
        recordings = tuple(data.get("recordings", []))
    
    # Validate required fields
    if not summary:
        raise click.ClickException("Summary is required. Provide it as an argument or use --interactive")
    if not url:
        raise click.ClickException("--url is required. Provide the Arize platform URL.")
    
    # Try to auto-detect space ID from URL if not provided
    if not space_id and url:
        space_id = parse_space_id_from_url(url)
        if space_id:
            click.echo(f"📍 Space ID auto-detected: {space_id}")
    
    if not space_id:
        raise click.ClickException("--space-id is required (could not auto-detect from URL).")
    
    # Format with AI
    click.echo("🤖 Generating issue with AI...")
    issue_data = format_issue_with_ai(summary, url, space_id, issue_type, customer, expected, actual)
    
    title = issue_data["title"]
    body = issue_data["body"]
    
    # Process attachments
    attachment_sections = []
    
    # Combine file screenshots with clipboard screenshot
    all_screenshots = list(screenshots)
    
    if clipboard:
        click.echo("📋 Getting image from clipboard...")
        clipboard_path = get_clipboard_image()
        if clipboard_path:
            all_screenshots.append(clipboard_path)
            click.echo("   ✓ Found image in clipboard")
        else:
            click.echo("   ⚠ No image found in clipboard (copy a screenshot first)")
    
    # Process screenshots - try to upload to GitHub, fall back to local save
    saved_screenshots = []  # Local paths for fallback
    uploaded_screenshots = []  # Markdown embeds for successful uploads
    
    if all_screenshots:
        click.echo("📸 Uploading screenshots...")
        for i, screenshot_path in enumerate(all_screenshots, 1):
            click.echo(f"   Uploading screenshot {i}...")
            
            # Upload to Imgur for reliable image hosting
            img_markdown = upload_image_to_imgur(screenshot_path, verbose=True)
            
            if img_markdown:
                uploaded_screenshots.append(img_markdown)
                click.echo(f"   ✓ Screenshot {i} uploaded successfully")
            else:
                # Fall back to local save
                try:
                    saved_path = save_screenshot_locally(screenshot_path)
                    saved_screenshots.append(saved_path)
                    click.echo(f"   ⚠ Upload failed, saved locally: {saved_path}")
                except Exception as e:
                    click.echo(f"   ✗ Screenshot {i} failed: {e}")
        
        # Add uploaded screenshots to issue body
        if uploaded_screenshots:
            attachment_sections.append("## Screenshots\n\n" + "\n\n".join(uploaded_screenshots))
        elif saved_screenshots:
            attachment_sections.append("## Screenshots\n\n*Screenshots to be attached manually after issue creation*")
    
    # Add recording links
    if recordings:
        recording_items = []
        for i, rec_url in enumerate(recordings, 1):
            # Detect if it's Loom or Zoom for nice labeling
            if "loom.com" in rec_url.lower():
                recording_items.append(f"- [Loom Recording {i}]({rec_url})")
            elif "zoom" in rec_url.lower():
                recording_items.append(f"- [Zoom Recording {i}]({rec_url})")
            else:
                recording_items.append(f"- [Video Recording {i}]({rec_url})")
        
        attachment_sections.append("## Video Recordings\n\n" + "\n".join(recording_items))
    
    # Append attachments to body
    if attachment_sections:
        body = body + "\n\n" + "\n\n".join(attachment_sections)
    
    # Build labels automatically
    type_config = ISSUE_TYPES.get(issue_type, ISSUE_TYPES["bug"])
    all_labels = [type_config["label"]]  # bug or enhancement
    
    if customer:
        # Add customer-related labels
        customer_tag = customer.lower().replace(" ", "-")
        all_labels.append(f"customer-{customer_tag}")
        all_labels.append("Customer Request")
    
    # Add any additional user-specified labels
    all_labels.extend(labels)
    
    # Show preview
    click.echo("\n" + "=" * 60)
    click.echo("ISSUE PREVIEW")
    click.echo("=" * 60)
    click.echo(f"\n📌 Title: {title}\n")
    click.echo("📄 Body:\n")
    click.echo(body)
    click.echo("\n" + "=" * 60)
    click.echo(f"🏷️  Labels: {', '.join(all_labels)}")
    
    # Dry run - exit after preview
    if dry_run:
        click.echo("\n(dry run - issue not created)")
        return
    
    # Ask for confirmation before creating
    click.echo()
    if not click.confirm("Create this issue?", default=True):
        click.echo("❌ Issue creation cancelled.")
        return
    
    # Create the issue
    click.echo("\n📤 Creating GitHub issue...")
    issue_url = create_github_issue(title, body, tuple(all_labels))
    
    click.echo(f"\n✅ Issue created successfully!")
    click.echo(f"🔗 {issue_url}")
    
    # If there are screenshots that failed to upload, open browser for manual attachment
    if saved_screenshots:
        click.echo(f"\n📎 Screenshots that need manual attachment:")
        for path in saved_screenshots:
            click.echo(f"   {path}")
        click.echo(f"\n🌐 Opening issue in browser - edit the issue and drag screenshots in...")
        subprocess.run(["open", issue_url], capture_output=True)


if __name__ == "__main__":
    main()
