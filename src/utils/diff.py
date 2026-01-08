"""Diff parsing utility functions."""

import os
import re
from typing import List, Dict, Optional


def read_diff_from_file(file_path: str) -> Optional[str]:
    """Read diff from file."""
    try:
        expanded_path = os.path.expanduser(os.path.expandvars(file_path))

        if not os.path.exists(expanded_path):
            print(f"❌ Error: El archivo '{expanded_path}' no existe.")
            return None

        if not os.path.isfile(expanded_path):
            print(f"❌ Error: '{expanded_path}' no es un archivo.")
            return None

        with open(expanded_path, 'r', encoding='utf-8') as f:
            diff_content = f.read()

        if not diff_content.strip():
            print(f"⚠️  El archivo '{expanded_path}' está vacío.")
            return None

        print(f"✓ Diff leído desde: {expanded_path}")
        return diff_content

    except PermissionError:
        print(f"❌ Error: No tienes permisos para leer '{file_path}'.")
        return None
    except Exception as e:
        print(f"❌ Error leyendo archivo: {e}")
        return None


def get_git_diff(target_branch: str,
                 use_working_dir: bool = False) -> Optional[str]:
    """Get complete diff against target branch."""
    import subprocess
    try:
        if use_working_dir:
            unstaged_result = subprocess.run(
                ['git', 'diff', 'HEAD'],
                capture_output=True,
                text=True
            )
            staged_result = subprocess.run(
                ['git', 'diff', '--cached', 'HEAD'],
                capture_output=True,
                text=True
            )
            combined = ""
            if unstaged_result.stdout:
                combined += unstaged_result.stdout
            if staged_result.stdout:
                combined += staged_result.stdout
            return combined if combined.strip() else None
        else:
            result = subprocess.check_output(
                ['git', 'diff', f'{target_branch}...HEAD'],
                stderr=subprocess.STDOUT
            ).decode('utf-8')
            return result if result.strip() else None
    except subprocess.CalledProcessError as e:
        output = e.output.decode() if e.output else ""
        if not output:
            return None
        print(f"Error al obtener diff: {output}")
        return None
    except FileNotFoundError:
        print("Error: Git no está instalado o no está en el PATH.")
        return None


def parse_hunks(diff_text: str) -> List[Dict[str, str]]:
    """Split diff into files and then into individual hunks."""
    if not diff_text:
        return []

    hunks_found = []
    file_sections = re.split(r'diff --git', diff_text)

    for file_section in file_sections[1:]:
        if not file_section.strip():
            continue

        file_match = re.search(r'b/(.+?)(?:\n|$)', file_section)
        if not file_match:
            continue

        file_name = file_match.group(1).strip()
        file_header = file_section.split('@@')[0]

        parts = re.split(
            r'(@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@)',
            file_section
        )

        for i in range(1, len(parts), 2):
            if i + 1 < len(parts):
                hunk_header = parts[i]
                hunk_body = parts[i + 1]
                next_hunk = hunk_body.find('@@')
                if next_hunk != -1:
                    hunk_body = hunk_body[:next_hunk]

                hunk_content = (
                    f"diff --git a/{file_name} b/{file_name}\n"
                    f"{file_header}{hunk_header}{hunk_body}"
                )

                hunks_found.append({
                    'file': file_name,
                    'content': hunk_content
                })

    return hunks_found


def create_summary_for_llm(hunks: List[Dict[str, str]],
                          max_chars: int = 8000) -> str:
    """Create summary of hunks for LLM analysis."""
    summary_parts = []
    total_chars = 0

    for hunk in hunks:
        file_name = hunk['file']
        content = hunk['content']

        # Extract only the changed lines (lines starting with + or -)
        lines = content.split('\n')
        changed_lines = [
            line for line in lines
            if line.startswith('+') or line.startswith('-')
        ]
        changed_content = '\n'.join(changed_lines[:50])

        hunk_summary = f"File: {file_name}\n{changed_content}\n"
        hunk_chars = len(hunk_summary)

        if total_chars + hunk_chars > max_chars:
            remaining = max_chars - total_chars
            if remaining > 100:
                summary_parts.append(hunk_summary[:remaining])
            break

        summary_parts.append(hunk_summary)
        total_chars += hunk_chars

    return '\n'.join(summary_parts)
