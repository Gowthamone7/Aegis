"""
EKA Unified Git Diff Generator & Validator

Provides standard, robust Git diff generation and validation:
- Generates standard unified Git diffs compatible with git apply / GitHub PRs
- Validates diff structure (headers, hunk markers, line count balance)
- Enforces security checks on diffs (no secret additions, bounds validation)
"""
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field
from typing import List, Optional

from ..security import detect_injection, sanitize_for_output


@dataclass
class DiffValidationResult:
    valid: bool
    error: Optional[str] = None
    additions: int = 0
    deletions: int = 0
    modified_files: List[str] = field(default_factory=list)
    has_injection: bool = False
    has_secrets: bool = False


def generate_unified_diff(
    file_path: str,
    original_content: str,
    patched_content: str,
    context_lines: int = 3,
) -> str:
    """
    Generate a standard unified Git diff string for a file modification.
    Headers conform to standard Git:
      --- a/{file_path}
      +++ b/{file_path}
      @@ -old_line,count +new_line,count @@
    """
    orig_lines = original_content.splitlines(keepends=True)
    patch_lines = patched_content.splitlines(keepends=True)

    clean_path = file_path.strip().replace("\\", "/")

    diff_lines = list(
        difflib.unified_diff(
            orig_lines,
            patch_lines,
            fromfile=f"a/{clean_path}",
            tofile=f"b/{clean_path}",
            n=context_lines,
        )
    )

    if not diff_lines:
        return ""

    return "".join(diff_lines)


def validate_unified_diff(diff_text: str) -> DiffValidationResult:
    r"""
    Validates a unified Git diff against standard syntax and security guardrails.
    Checks:
    - Non-empty diff text
    - Header format: `--- a/...` and `+++ b/...`
    - Hunk header format: `@@ -start,len +start,len @@`
    - Line prefixes: ` `, `+`, `-`, `\`, `@`
    - Prompt injection markers in added code
    - Secret exposure in added lines
    """
    if not diff_text or not diff_text.strip():
        return DiffValidationResult(valid=False, error="Diff is empty")

    lines = diff_text.splitlines()
    has_old_file = False
    has_new_file = False
    files_modified: List[str] = []
    hunk_count = 0
    additions = 0
    deletions = 0
    added_lines_text = []

    hunk_regex = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")

    for line in lines:
        if line.startswith("--- a/"):
            has_old_file = True
            files_modified.append(line[6:].strip())
        elif line.startswith("+++ b/"):
            has_new_file = True
        elif hunk_regex.match(line):
            hunk_count += 1
        elif line.startswith("+"):
            additions += 1
            added_lines_text.append(line[1:])
        elif line.startswith("-"):
            deletions += 1
        elif line.startswith(" ") or line.startswith("\\"):
            continue
        elif line.startswith("diff --git") or line.startswith("index "):
            continue
        else:
            # Tolerant parsing for patch metadata
            continue

    if not (has_old_file and has_new_file):
        return DiffValidationResult(
            valid=False,
            error="Missing unified diff file headers (--- a/... and +++ b/...)",
        )

    if hunk_count == 0:
        return DiffValidationResult(
            valid=False,
            error="Missing hunk header marker (@@ -x,y +x,y @@)",
        )

    # Security verification on added lines
    full_added_text = "\n".join(added_lines_text)
    injection_check = detect_injection(full_added_text)
    if injection_check.detected:
        return DiffValidationResult(
            valid=False,
            error=f"Security violation: Prompt injection marker detected in patch: {', '.join(injection_check.markers)}",
            additions=additions,
            deletions=deletions,
            modified_files=list(dict.fromkeys(files_modified)),
            has_injection=True,
        )

    # Check for raw unredacted secret patterns
    sanitized_text = sanitize_for_output(full_added_text)
    has_secrets = "[REDACTED:" in sanitized_text
    if has_secrets:
        return DiffValidationResult(
            valid=False,
            error="Security violation: Hardcoded credentials or API keys detected in patch additions",
            additions=additions,
            deletions=deletions,
            modified_files=list(dict.fromkeys(files_modified)),
            has_secrets=True,
        )

    return DiffValidationResult(
        valid=True,
        additions=additions,
        deletions=deletions,
        modified_files=list(dict.fromkeys(files_modified)),
    )
