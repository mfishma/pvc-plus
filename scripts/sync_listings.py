#!/usr/bin/env python3
"""
sync_listings.py - Pre-publish sync and asset path resolver for pvc-plus.

1. Rewrites relative asset/image paths in README.md to raw GitHub URLs.
2. Updates Modrinth project description via API (PATCH /v2/project/{id}).
3. Exports a CurseForge-sanitized overview (strips inline style tags).
4. Resolves the version changelog (expanding relative image paths for graphics).
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path

DEFAULT_REPO = "mfishma/pvc-plus"
DEFAULT_BRANCH = "main"

def rewrite_relative_urls(text: str, repo: str = DEFAULT_REPO, branch: str = DEFAULT_BRANCH) -> str:
    """
    Expands relative asset and image references to raw GitHub permalinks.
    Handles HTML src="..." and Markdown ![alt](...) / [text](...).
    """
    raw_base = f"https://raw.githubusercontent.com/{repo}/{branch}/"

    # HTML attributes: src="assets/..." or src=".github/..."
    def replace_html_src(match):
        prefix = match.group(1) # e.g. 'src="'
        path = match.group(2)   # e.g. 'assets/...' or '.github/...'
        suffix = match.group(3) # e.g. '"'
        return f"{prefix}{raw_base}{path}{suffix}"

    html_pattern = re.compile(r'(src=["\'])((?:assets|\.github)/[^"\']+)(["\'])', re.IGNORECASE)
    text = html_pattern.sub(replace_html_src, text)

    # Markdown links: ![alt](assets/...) or [alt](assets/...)
    def replace_md_link(match):
        prefix = match.group(1) # e.g. '![' or '['
        label = match.group(2)  # link text
        path = match.group(3)   # relative path
        return f"{prefix}{label}]({raw_base}{path})"

    md_pattern = re.compile(r'(!?\[)([^\]]*)\]\(((?:assets|\.github)/[^\)]+)\)', re.IGNORECASE)
    text = md_pattern.sub(replace_md_link, text)

    return text

def sanitize_for_curseforge(text: str) -> str:
    """
    Strips inline CSS attributes (such as style="image-rendering: pixelated;")
    that CurseForge's rich-text sanitizer corrupts or escapes.
    """
    return re.sub(r'\s*style=["\'][^"\']*["\']', '', text, flags=re.IGNORECASE)

def update_modrinth_project_body(project_id: str, token: str, body_content: str) -> bool:
    """
    Sends a PATCH request to Modrinth API to update the project overview body.
    """
    url = f"https://api.modrinth.com/v2/project/{project_id}"
    payload = json.dumps({"body": body_content}).encode("utf-8")
    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
        "User-Agent": "mfishma/pvc-plus-publisher (via GitHub Actions)"
    }

    req = urllib.request.Request(url, data=payload, headers=headers, method="PATCH")
    try:
        with urllib.request.urlopen(req) as resp:
            if resp.status in (200, 204):
                print(f"[OK] Successfully updated Modrinth project description for '{project_id}'")
                return True
            print(f"[WARN] Modrinth returned status {resp.status}")
            return False
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        print(f"[ERROR] Failed to update Modrinth project body (HTTP {e.code}): {error_body}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error updating Modrinth project body: {e}", file=sys.stderr)
        return False

def resolve_changelog(input_text: str | None, file_path: Path, repo: str, branch: str) -> str:
    """
    Determines changelog content (input text takes precedence, fallback to file).
    Expands relative image links so embedded graphics load on Modrinth & CurseForge.
    """
    raw_changelog = ""
    if input_text and input_text.strip():
        print("[INFO] Using changelog provided via workflow input/event.")
        raw_changelog = input_text.strip()
    elif file_path.exists():
        print(f"[INFO] Reading changelog from '{file_path}'.")
        raw_changelog = file_path.read_text(encoding="utf-8").strip()
    else:
        print("[INFO] No changelog input or file found; using default stub.")
        raw_changelog = "Routine updates and improvements."

    # Expand any relative image/asset links in the changelog
    resolved = rewrite_relative_urls(raw_changelog, repo=repo, branch=branch)
    return resolved

def main():
    parser = argparse.ArgumentParser(description="Sync listing descriptions and resolve changelogs.")
    parser.add_argument("--version", required=True, help="Target release version (e.g. 2026.10.16)")
    parser.add_argument("--modrinth-id", default=os.getenv("MODRINTH_PROJECT_ID", "oKsOeGEg"), help="Modrinth project ID or slug")
    parser.add_argument("--repo", default=DEFAULT_REPO, help="GitHub repository slug (owner/repo)")
    parser.add_argument("--branch", default=DEFAULT_BRANCH, help="Git branch for raw asset URLs")
    parser.add_argument("--readme", type=Path, default=Path("README.md"), help="Path to input README.md")
    parser.add_argument("--changelog-file", type=Path, default=Path("changelogs/latest.md"), help="Path to staging changelog")
    parser.add_argument("--output-dir", type=Path, default=Path("build"), help="Directory for generated files")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Process Project README (Description)
    if args.readme.exists():
        readme_raw = args.readme.read_text(encoding="utf-8")
        modrinth_overview = rewrite_relative_urls(readme_raw, repo=args.repo, branch=args.branch)
        curseforge_overview = sanitize_for_curseforge(modrinth_overview)

        # Write generated overviews
        (args.output_dir / "MODRINTH_OVERVIEW.md").write_text(modrinth_overview, encoding="utf-8")
        (args.output_dir / "CURSEFORGE_OVERVIEW.md").write_text(curseforge_overview, encoding="utf-8")
        print(f"[OK] Wrote processed overviews to '{args.output_dir}'")

        # Update Modrinth project description via API if token is available
        modrinth_token = os.getenv("MODRINTH_TOKEN")
        if modrinth_token and args.modrinth_id:
            update_modrinth_project_body(args.modrinth_id, modrinth_token, modrinth_overview)
        else:
            print("[INFO] MODRINTH_TOKEN not set; skipping automated Modrinth body update.")

        # If running in GitHub Actions, append CurseForge overview snippet to Step Summary
        summary_file = os.getenv("GITHUB_STEP_SUMMARY")
        if summary_file:
            with open(summary_file, "a", encoding="utf-8") as f:
                f.write("### 📋 CurseForge Project Description Ready\n")
                f.write("The sanitized CurseForge overview has been prepared. You can copy it from `build/CURSEFORGE_OVERVIEW.md` if needed.\n\n")
    else:
        print(f"[WARN] Readme file '{args.readme}' not found; skipping description generation.")

    # 2. Process Changelog (with Graphic Link Expansion)
    changelog_input = os.getenv("CHANGELOG_INPUT")
    resolved_changelog = resolve_changelog(changelog_input, args.changelog_file, repo=args.repo, branch=args.branch)
    changelog_output_path = args.output_dir / "CHANGELOG_RESOLVED.md"
    changelog_output_path.write_text(resolved_changelog, encoding="utf-8")
    print(f"[OK] Wrote resolved changelog to '{changelog_output_path}'")

    # If running in GitHub Actions, preview changelog in Step Summary
    summary_file = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "a", encoding="utf-8") as f:
            f.write(f"### 🚀 Release Changelog (`{args.version}`)\n\n")
            f.write(resolved_changelog + "\n\n")

if __name__ == "__main__":
    main()
