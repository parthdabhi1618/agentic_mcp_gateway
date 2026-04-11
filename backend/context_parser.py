# backend/context_parser.py — V6
# Parses @folder/file.json patterns from the user prompt.
# Used by /plan endpoint to auto-extract context references
# from the Spotlight bar input before sending to the planner.

import re


def extract_context_refs(prompt: str) -> tuple[str, list[str]]:
    """
    Parses @folder/file patterns from the prompt.
    Returns (cleaned_prompt, list_of_context_refs).

    Example:
      Input:  "Create a PR for @github_context/recent_branches.json"
      Output: ("Create a PR for ", ["@github_context/recent_branches.json"])
    """
    pattern = r'@[\w./-]+'
    refs = re.findall(pattern, prompt)
    cleaned = re.sub(pattern, '', prompt).strip()
    # Collapse multiple spaces left after stripping refs
    cleaned = re.sub(r'\s{2,}', ' ', cleaned)
    return cleaned, refs
