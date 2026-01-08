"""Git utility functions."""

import subprocess
import time
import uuid
from typing import Optional


def get_current_branch() -> Optional[str]:
    """Get current branch name."""
    try:
        result = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()
        return result
    except subprocess.CalledProcessError:
        return None


def get_current_head() -> Optional[str]:
    """Get current HEAD SHA for rollback."""
    try:
        result = subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'],
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()
        return result
    except subprocess.CalledProcessError:
        return None


def create_temp_branch() -> Optional[str]:
    """Create temporary branch with unique ID."""
    timestamp = int(time.time())
    unique_id = str(uuid.uuid4())[:8]
    branch_name = f"git-split-draft-{timestamp}-{unique_id}"

    try:
        subprocess.run(
            ['git', 'checkout', '-b', branch_name],
            check=True,
            capture_output=True
        )
        print(f"🌿 Creada rama temporal: {branch_name}")
        return branch_name
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        print(f"❌ Error creando rama temporal: {error_msg}")
        return None


def cleanup_temp_branch(branch_name: str, original_branch: str) -> bool:
    """Return to original branch and delete temporary branch."""
    try:
        subprocess.run(
            ['git', 'checkout', original_branch],
            check=True,
            capture_output=True
        )
        print(f"✅ Vuelto a rama: {original_branch}")

        subprocess.run(
            ['git', 'branch', '-D', branch_name],
            check=True,
            capture_output=True
        )
        print(f"🗑️  Rama temporal eliminada: {branch_name}")
        return True
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        print(f"⚠️  Error limpiando rama temporal: {error_msg}")
        print(f"   Elimina manualmente con: git branch -D {branch_name}")
        return False


def rollback_to_commit(commit_sha: str) -> bool:
    """Rollback commits using --soft (keeps changes in files)."""
    try:
        print(f"\n⚠️  Realizando rollback a {commit_sha[:8]}...")
        subprocess.run(
            ['git', 'reset', '--soft', commit_sha],
            check=True,
            capture_output=True
        )
        subprocess.run(
            ['git', 'reset'],
            check=True,
            capture_output=True
        )
        print("✅ Rollback completado. Tu código está intacto.")
        print("   Los commits parciales se han deshecho.")
        return True
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        print(f"❌ Error en rollback: {error_msg}")
        print("⚠️  Restaura manualmente con:")
        print(f"   git reset --soft {commit_sha}")
        print("   git reset")
        return False


def is_git_repo() -> bool:
    """Check if current directory is a git repository."""
    try:
        subprocess.run(
            ['git', 'rev-parse', '--git-dir'],
            check=True,
            capture_output=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
