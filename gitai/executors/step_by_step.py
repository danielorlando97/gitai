"""Step-by-step executor for Git plan execution."""

import os
import subprocess
from typing import Dict, Optional, Any
from .base import AbstractExecutor
from ..utils.git import rollback_to_commit


class StepByStepExecutor(AbstractExecutor):
    """Step-by-step executor with visual isolation."""

    def _apply_hunks(self, hunks: list) -> bool:
        """Apply hunks to staging area."""
        patch_file = "temp.patch"

        try:
            subprocess.run(
                ['git', 'reset'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            for hunk in hunks:
                hunk_content = hunk.content if hasattr(hunk, 'content') else hunk['content']

                with open(patch_file, "w", encoding='utf-8') as f:
                    f.write(hunk_content)

                result = subprocess.run(
                    ['git', 'apply', '--cached', patch_file],
                    capture_output=True,
                    text=True
                )

                if result.returncode != 0:
                    raise Exception(
                        f"Error aplicando parche: {result.stderr}"
                    )

            return True
        except Exception as e:
            print(f"❌ {e}")
            return False
        finally:
            if os.path.exists(patch_file):
                os.remove(patch_file)

    def _isolate_changes(self) -> bool:
        """Isolate current changes using git stash."""
        untracked_result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True
        )
        has_untracked = any(
            line.startswith('??')
            for line in untracked_result.stdout.split('\n')
        )

        stash_cmd = ['git', 'stash', 'push', '--keep-index', '-m',
                     'dev_splitter_temp']
        if has_untracked:
            stash_cmd.append('-u')

        stash_result = subprocess.run(
            stash_cmd,
            capture_output=True,
            text=True
        )

        if stash_result.returncode != 0:
            if 'No local changes' in stash_result.stderr:
                return True  # No changes to stash
            return False

        return True

    def _restore_changes(self) -> bool:
        """Restore stashed changes."""
        result = subprocess.run(
            ['git', 'stash', 'pop'],
            capture_output=True,
            text=True
        )
        return result.returncode == 0

    def execute(
        self,
        plan: Dict[int, Dict],
        rollback_point: Optional[str] = None,
        test_command: Optional[str] = None,
        generate_pr: bool = False,
        llm_client: Optional[Any] = None,
        user_description: Optional[str] = None,
        provider: str = "gemini",
        key_manager: Optional[Any] = None
    ) -> bool:
        """Execute plan step by step with visual isolation."""
        print("\n" + "!"*60)
        print("🛠️  MODO PASO A PASO ACTIVADO")
        print("Tu código se filtrará para que veas solo el commit actual.")
        print("!"*60)

        if rollback_point:
            print(f"\n🛡️  Punto de restauración: {rollback_point[:8]}")

        commits_realizados = 0
        commits_created = []

        try:
            for g_id in sorted(plan.keys()):
                data = plan[g_id]
                if not data.get("hunks"):
                    continue

                # Apply hunks for this commit
                if not self._apply_hunks(data["hunks"]):
                    raise Exception(f"Error aplicando cambios para commit {g_id}")

                # Isolate changes
                print(f"\n📦 Preparando Commit {g_id}: {data['desc']}")
                if not self._isolate_changes():
                    print("⚠️  No se pudieron aislar cambios adicionales.")

                print("-" * 60)
                print(f"👉 Ahora puedes revisar/probar el código en tu editor.")
                print(f"Solo los cambios de '{data['desc']}' están presentes.")
                print("-" * 60)

                while True:
                    action = input(
                        f"\n¿Confirmar commit {g_id}? "
                        "[c]onfirmar / [s]altar / [a]bortar todo: "
                    ).strip().lower()

                    if action == 'c':
                        # Restore changes first
                        self._restore_changes()

                        # Create commit
                        result = subprocess.run(
                            ['git', 'commit', '-m', data['desc']],
                            capture_output=True,
                            text=True
                        )

                        if result.returncode != 0:
                            print(f"❌ Error creando commit: {result.stderr}")
                            continue

                        commits_realizados += 1
                        commits_created.append({"desc": data['desc']})
                        print(f"✅ [{commits_realizados}] Commit realizado.")
                        break

                    elif action == 's':
                        # Restore changes and skip
                        self._restore_changes()
                        subprocess.run(['git', 'reset'], capture_output=True)
                        print(f"⏭️  Commit {g_id} saltado.")
                        break

                    elif action == 'a':
                        # Abort everything
                        self._restore_changes()
                        subprocess.run(['git', 'reset'], capture_output=True)
                        if rollback_point:
                            print("\n🔄 Realizando rollback...")
                            rollback_to_commit(rollback_point)
                        return False

            # Generate PR summary if requested
            if generate_pr and commits_created:
                print("\n📝 Generando resumen de Pull Request...")
                print("✅ Resumen de PR generado (implementación pendiente)")

            print("\n🎉 ¡Todos los cambios han sido organizados!")
            return True

        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupción detectada.")
            if rollback_point:
                confirm = input("¿Hacer rollback? (s/N): ").strip().lower()
                if confirm == 's':
                    rollback_to_commit(rollback_point)
            return False

        except Exception as e:
            print(f"\n❌ Error durante la ejecución: {e}")
            if rollback_point:
                print("\n🔄 Realizando rollback...")
                rollback_to_commit(rollback_point)
            return False
