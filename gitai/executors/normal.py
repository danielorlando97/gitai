"""Normal executor for Git plan execution."""

import os
import subprocess
from typing import Dict, Optional, Any
from .base import AbstractExecutor
from ..utils.git import rollback_to_commit


class NormalExecutor(AbstractExecutor):
    """Normal executor that executes all commits at once."""

    def _apply_and_commit(self, hunks: list, goal_name: str) -> bool:
        """Apply hunks and create commit."""
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
                    error_msg = (
                        f"Error aplicando parche: {result.stderr}"
                    )
                    raise Exception(error_msg)

            result = subprocess.run(
                ['git', 'commit', '-m', goal_name],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                raise Exception(f"Error creando commit: {result.stderr}")

            return True
        except Exception as e:
            print(f"❌ {e}")
            return False
        finally:
            if os.path.exists(patch_file):
                os.remove(patch_file)

    def _run_tests(self, test_command: str) -> bool:
        """Run test command."""
        print(f"\n🧪 Ejecutando tests: {test_command}")
        try:
            result = subprocess.run(
                test_command.split(),
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("✅ Todos los tests pasaron.")
                return True
            else:
                print("❌ Tests fallaron:")
                print(result.stdout)
                print(result.stderr)
                return False
        except Exception as e:
            print(f"❌ Error ejecutando tests: {e}")
            return False

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
        """Execute the Git plan."""
        if rollback_point:
            print(f"\n🛡️  Punto de restauración: {rollback_point[:8]}")

        print("\n--- Generando Commits ---")

        commits_realizados = 0
        commits_created = []

        try:
            for g_id in sorted(plan.keys()):
                data = plan[g_id]
                if not data.get("hunks"):
                    continue

                print(f"Creando commit {g_id}: {data['desc']}...")

                hunks = data["hunks"]
                if not self._apply_and_commit(hunks, data['desc']):
                    raise Exception(f"Error al crear commit '{data['desc']}'")

                commits_realizados += 1
                commits_created.append({"desc": data['desc']})
                print(f"✅ [{commits_realizados}] Commit: {data['desc']}")

            # Run tests if specified
            if test_command:
                if not self._run_tests(test_command):
                    raise Exception("Tests fallaron después de los commits")

            # Generate PR summary if requested
            if generate_pr and commits_created:
                print("\n📝 Generando resumen de Pull Request...")
                # PR generation would go here
                # For now, just print a message
                print("✅ Resumen de PR generado (implementación pendiente)")

            print("\n🎉 ¡Todos los cambios han sido organizados!")
            return True

        except Exception as e:
            print(f"\n❌ Error durante la ejecución: {e}")
            if rollback_point:
                print("\n🔄 Realizando rollback...")
                if rollback_to_commit(rollback_point):
                    print("✅ Rollback completado.")
                else:
                    print("⚠️  Error en rollback. Restaura manualmente.")
            return False
