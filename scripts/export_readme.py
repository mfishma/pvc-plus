#!/usr/bin/env python3
"""
Exports README.md for external hosting (Modrinth, CurseForge, etc.)
by converting relative asset and image paths into absolute raw GitHub URLs.
"""

import os
import re
import sys
import argparse
import subprocess
from pathlib import Path

DEFAULT_REPO_RAW_URL = "https://raw.githubusercontent.com/mfishma/pvc-plus/main"
DEFAULT_REPO_BLOB_URL = "https://github.com/mfishma/pvc-plus/blob/main"

RESPACKOPTS_MODRINTH_URL = "https://modrinth.com/mod/respackopts"
RESPACKOPTS_CURSEFORGE_URL = "https://www.curseforge.com/minecraft/mc-mods/respackopts"

def resolve_repo_root() -> Path:
    """Finds repository root based on the script location or current directory."""
    script_dir = Path(__file__).resolve().parent
    if (script_dir.parent / "README.md").exists():
        return script_dir.parent
    cwd = Path.cwd()
    if (cwd / "README.md").exists():
        return cwd
    return script_dir.parent

def convert_readme(
    content: str,
    raw_base_url: str,
    blob_base_url: str,
    platform: str = "modrinth"
) -> tuple[str, int]:
    """
    Replaces relative image and link paths with absolute GitHub URLs.
    Returns the converted content and count of replacements made.
    """
    count = 0
    raw_base = raw_base_url.rstrip("/")
    blob_base = blob_base_url.rstrip("/")

    # 1. HTML <img src="..."> tags
    # Matches src="path" where path does not start with http://, https://, or //
    def replace_html_img(match):
        nonlocal count
        pre = match.group(1)
        src = match.group(2)
        post = match.group(3)
        if src.startswith(("http://", "https://", "//")):
            return match.group(0)
        clean_src = re.sub(r"^\.?/", "", src)
        count += 1
        return f'{pre}{raw_base}/{clean_src}{post}'

    html_img_pattern = re.compile(r'(<img\b[^>]*?\bsrc=["\'])([^"\']+)(["\'])', re.IGNORECASE)
    content = html_img_pattern.sub(replace_html_img, content)

    # 2. Markdown image tags ![alt](path)
    def replace_md_img(match):
        nonlocal count
        prefix = match.group(1)
        src = match.group(2)
        suffix = match.group(3)
        if src.startswith(("http://", "https://", "//")):
            return match.group(0)
        clean_src = re.sub(r"^\.?/", "", src)
        count += 1
        return f'{prefix}{raw_base}/{clean_src}{suffix}'

    md_img_pattern = re.compile(r'(!\[[^\]]*\]\()([^\s\)]+)(\))')
    content = md_img_pattern.sub(replace_md_img, content)

    # 3. Markdown links [text](path) for internal assets/files (excluding anchors # and external urls)
    def replace_md_link(match):
        nonlocal count
        prefix = match.group(1)
        href = match.group(2)
        suffix = match.group(3)
        if href.startswith(("http://", "https://", "//", "#", "mailto:")):
            return match.group(0)
        clean_href = re.sub(r"^\.?/", "", href)
        count += 1
        return f'{prefix}{blob_base}/{clean_href}{suffix}'

    md_link_pattern = re.compile(r'((?<!\!)\[[^\]]+\]\()([^\s\)]+)(\))')
    content = md_link_pattern.sub(replace_md_link, content)

    # 4. Target host platform link overrides
    if platform.lower() in ("curseforge", "cf"):
        content = content.replace(RESPACKOPTS_MODRINTH_URL, RESPACKOPTS_CURSEFORGE_URL)
    else:
        content = content.replace(RESPACKOPTS_CURSEFORGE_URL, RESPACKOPTS_MODRINTH_URL)

    return content, count

def copy_to_clipboard(text: str) -> bool:
    """Copies text to system clipboard across Windows, macOS, or Linux."""
    try:
        if sys.platform == "win32":
            subprocess.run(["clip"], input=text.encode("utf-16le"), check=True)
            return True
        elif sys.platform == "darwin":
            subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)
            return True
        else:
            # Linux: try xclip or xsel
            for cmd in [["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]]:
                try:
                    subprocess.run(cmd, input=text.encode("utf-8"), check=True)
                    return True
                except FileNotFoundError:
                    continue
    except Exception as e:
        print(f"Warning: Failed to copy to clipboard: {e}", file=sys.stderr)
    return False

def main():
    repo_root = resolve_repo_root()
    default_input = repo_root / "README.md"
    default_output = repo_root / "README_EXTERNAL.md"

    parser = argparse.ArgumentParser(
        description="Convert README.md relative paths to absolute raw GitHub URLs for Modrinth/CurseForge."
    )
    parser.add_argument(
        "-i", "--input",
        type=Path,
        default=default_input,
        help=f"Input markdown file (default: {default_input})"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=default_output,
        help=f"Output markdown file (default: {default_output})"
    )
    parser.add_argument(
        "--raw-url",
        default=DEFAULT_REPO_RAW_URL,
        help=f"Base raw GitHub URL for images (default: {DEFAULT_REPO_RAW_URL})"
    )
    parser.add_argument(
        "--blob-url",
        default=DEFAULT_REPO_BLOB_URL,
        help=f"Base GitHub URL for documents/links (default: {DEFAULT_REPO_BLOB_URL})"
    )
    parser.add_argument(
        "-c", "--clipboard",
        action="store_true",
        help="Also copy the converted markdown directly to system clipboard."
    )
    parser.add_argument(
        "-p", "--platform",
        choices=["modrinth", "curseforge", "cf"],
        default="modrinth",
        help="Target platform (default: modrinth). Switches Respackopts link to CurseForge when targeting CF."
    )
    parser.add_argument(
        "--curseforge",
        action="store_true",
        help="Convenience alias: equivalent to --platform curseforge."
    )

    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: Input file '{args.input}' not found.", file=sys.stderr)
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        original_text = f.read()

    target_platform = "curseforge" if args.curseforge else args.platform
    converted_text, count = convert_readme(
        original_text,
        args.raw_url,
        args.blob_url,
        platform=target_platform
    )

    with open(args.output, "w", encoding="utf-8", newline="\n") as f:
        f.write(converted_text)

    print(f"Successfully converted {count} relative paths.")
    print(f"Output saved to: {args.output}")

    if args.clipboard:
        if copy_to_clipboard(converted_text):
            print("Copied converted content directly to system clipboard!")
        else:
            print("Note: Could not access system clipboard.", file=sys.stderr)

if __name__ == "__main__":
    main()
