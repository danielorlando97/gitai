"""Split command for GitClassifier."""

import sys
import os
import subprocess
import argparse
from typing import Optional, Dict, List
from .base import BaseCommand
from ...utils.git import (
    get_current_branch, get_current_head, create_temp_branch,
    cleanup_temp_branch, is_git_repo
)
from ...utils.diff import (
    read_diff_from_file, get_git_diff, parse_hunks
)
from ...models.hunk import Hunk
from ...classifiers import SemanticClassifier
from ...executors import NormalExecutor, StepByStepExecutor
from ...storage import APIKeyRepository
from ...detectors import (
    get_default_provider, get_recommended_model, detect_resource_scale
)


class SplitCommand(BaseCommand):
    """Command for splitting git changes into semantic commits."""

    name = "split"
    description = "Clasifica y divide cambios de Git en commits semánticos"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add command-specific arguments."""
        diff_group = parser.add_mutually_exclusive_group()
        diff_group.add_argument(
            '--diff-file', '-f',
            type=str,
            help='Ruta al archivo de diff a analizar'
        )
        diff_group.add_argument(
            '--target', '-t',
            type=str,
            default='main',
            help='Rama target para comparar (default: main)'
        )

        parser.add_argument(
            '--use-llm', '-l',
            action='store_true',
            help='Usar clasificación automática con LLM'
        )
        parser.add_argument(
            '--provider', '-p',
            type=str,
            choices=['ollama', 'gemini', 'openai'],
            default=None,
            help='Proveedor LLM (default: auto-detectado)'
        )
        parser.add_argument(
            '--user-context', '-c',
            type=str,
            help='Contexto del usuario sobre los cambios (archivo o texto)'
        )
        parser.add_argument(
            '--user-description', '-d',
            type=str,
            help='Descripción del usuario para el PR (archivo o texto)'
        )

        parser.add_argument(
            '--mode', '-m',
            type=str,
            choices=['normal', 'step-by-step'],
            default='normal',
            help='Modo de ejecución (default: normal)'
        )
        parser.add_argument(
            '--execute', '-e',
            action='store_true',
            help='Ejecutar commits automáticamente sin confirmación'
        )
        parser.add_argument(
            '--edit-plan',
            action='store_true',
            help='Editar el plan antes de ejecutar'
        )

        parser.add_argument(
            '--generate-pr', '-g',
            action='store_true',
            help='Generar resumen de Pull Request'
        )
        parser.add_argument(
            '--test-cmd',
            type=str,
            help='Comando para ejecutar tests después de los commits'
        )
        parser.add_argument(
            '--skip-git-check',
            action='store_true',
            help='Saltar verificación de repositorio Git'
        )

    def execute(self, args: argparse.Namespace) -> int:
        """Execute the command."""
        temp_branch = None
        original_branch = None
        diff_from_file = False

        interactive = not any([
            args.diff_file, args.target != 'main', args.use_llm,
            args.provider, args.user_context, args.user_description,
            args.mode != 'normal', args.execute, args.edit_plan,
            args.generate_pr, args.test_cmd
        ])

        skip_git_check = args.diff_file and args.skip_git_check

        if not skip_git_check:
            if not is_git_repo():
                if args.diff_file:
                    print("⚠️  No estás en un repositorio Git.")
                    print("   Usa --skip-git-check para analizar sin repo Git")
                    print("   (Nota: no podrás aplicar commits sin un repo Git)")
                    return 1
                else:
                    print("Error: No estás en un repositorio Git.")
                    return 1

        try:
            diff, diff_from_file = self._get_diff(args, interactive)
            if not diff:
                return 1

            hunks_dict = parse_hunks(diff)
            if not hunks_dict:
                print("No se encontraron hunks para procesar.")
                return 1

            hunks = [
                Hunk(file=h['file'], content=h['content'])
                for h in hunks_dict
            ]

            print(f"\n📦 Se encontraron {len(hunks)} bloques de cambios.")

            if args.use_llm or (interactive and self._ask_use_llm()):
                provider = args.provider or self._get_provider(interactive)
                if not provider:
                    return 1

                key_manager = None
                if provider != "ollama":
                    try:
                        key_manager = APIKeyRepository()
                    except Exception:
                        pass

                model_name = self._get_model_name(provider, key_manager)
                if not model_name:
                    return 1

                user_context = self._get_user_context(
                    args.user_context, provider, model_name, interactive
                )

                classifier = SemanticClassifier(
                    provider=provider,
                    key_manager=key_manager,
                    model_name=model_name
                )

                print("\n🚀 Analizando cambios globalmente...")
                goals = classifier.identify_goals(hunks, user_context)

                if not goals:
                    print("No se pudieron identificar objetivos. Abortando.")
                    return 1

                print(f"✓ Se identificaron {len(goals)} objetivos funcionales.")
                for goal in goals:
                    print(f"  {goal.id}: {goal.description}")

                print("\n🏷️ Clasificando cambios individualmente...")
                plan = classifier.classify_hunks(hunks, goals, user_context)

                self._display_plan(plan)

                user_description = self._get_user_description(
                    args.user_description, interactive
                )

                action = self._get_action(args, interactive)
                if action == 'e':
                    return self._execute_plan(
                        plan, diff_from_file, args, provider,
                        key_manager, user_description
                    )
                elif action == 'ed':
                    print("⚠️  Edición de plan no implementada aún.")
                    return 1
                else:
                    print("Operación cancelada.")
                    return 0
            else:
                print("⚠️  Modo manual no implementado aún.")
                return 1

        except KeyboardInterrupt:
            print("\n\n⚠️  Operación cancelada por el usuario.")
            return 1
        except Exception as e:
            print(f"\n❌ Error: {e}")
            return 1
        finally:
            if temp_branch and original_branch:
                cleanup_temp_branch(temp_branch, original_branch)

    def _get_diff(self, args, interactive: bool):
        """Get diff from file or git."""
        if args.diff_file:
            diff = read_diff_from_file(args.diff_file)
            if not diff:
                return None, True
            print(
                "\n⚠️  Modo: Análisis desde archivo. "
                "Los commits solo se aplicarán si el diff es compatible."
            )
            return diff, True
        else:
            target = args.target
            if interactive:
                target = input(
                    "Introduce la rama target (ej. main): "
                ).strip() or "main"

            current_branch = get_current_branch()
            original_branch = current_branch
            use_working_dir_diff = False

            if current_branch and current_branch == target:
                print(
                    f"\n⚠️  Estás en la misma rama que el target ({target})."
                )
                print("   Creando rama temporal para analizar cambios...")
                temp_branch = create_temp_branch()
                if not temp_branch:
                    print("❌ No se pudo crear la rama temporal. Abortando.")
                    return None, False
                current_branch = temp_branch
                use_working_dir_diff = True

            diff = get_git_diff(target, use_working_dir_diff)
            if not diff:
                print("No hay cambios para procesar.")
                return None, False
            return diff, False

    def _ask_use_llm(self) -> bool:
        """Ask user if they want to use LLM."""
        response = input(
            "\n¿Usar clasificación automática con LLM? (s/N): "
        ).strip().lower()
        return response == 's'

    def _get_provider(self, interactive: bool) -> Optional[str]:
        """Get provider selection."""
        default_provider = get_default_provider()
        if interactive:
            provider_input = input(
                f"Proveedor (ollama/gemini/openai) [{default_provider}]: "
            ).strip().lower()
            return provider_input or default_provider
        return default_provider

    def _get_model_name(
        self,
        provider: str,
        key_manager: Optional[APIKeyRepository]
    ) -> Optional[str]:
        """Get model name for provider."""
        scale = detect_resource_scale()
        recommended = get_recommended_model(provider, scale=scale)

        if provider == "ollama":
            return self._get_ollama_model(recommended)
        return recommended

    def _get_ollama_model(
        self,
        recommended: Optional[str]
    ) -> Optional[str]:
        """Get Ollama model selection."""
        try:
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                models = []
                for line in lines[1:]:
                    if line.strip():
                        parts = line.split()
                        if parts:
                            models.append(parts[0])

                if models:
                    print(f"\n📦 Modelos de Ollama disponibles:")
                    for i, model in enumerate(models, 1):
                        marker = " (recomendado)" if model == recommended else ""
                        print(f"  {i}. {model}{marker}")
                    print()

                    if recommended:
                        prompt = (
                            f"Selecciona un modelo "
                            f"(1-{len(models)}) [{recommended}]: "
                        )
                    else:
                        prompt = f"Selecciona un modelo (1-{len(models)}): "

                    selection = input(prompt).strip()
                    if selection:
                        try:
                            idx = int(selection) - 1
                            if 0 <= idx < len(models):
                                return models[idx]
                        except ValueError:
                            if selection in models:
                                return selection
                    return recommended or models[0]
                else:
                    if recommended:
                        print(f"\n💡 Usando modelo recomendado: {recommended}")
                        return recommended
                    else:
                        model_input = input(
                            "Ingresa el nombre del modelo [llama3.2:3b]: "
                        ).strip()
                        return model_input or "llama3.2:3b"
        except Exception:
            pass

        return recommended or "llama3.2:3b"

    def _get_user_context(
        self,
        user_context_arg: Optional[str],
        provider: str,
        model_name: Optional[str],
        interactive: bool
    ) -> Optional[str]:
        """Get user context."""
        if user_context_arg:
            return self._read_file_or_text(user_context_arg)

        if not interactive:
            return None

        print("\n" + "="*70)
        print("📝 CONTEXTO PARA CLASIFICACIÓN")
        print("="*70)
        if model_name:
            print(f"🤖 Usando: {provider.upper()} - {model_name}")
        else:
            print(f"🤖 Usando: {provider.upper()}")
        print(
            "Opcional: Explica de forma general todos los cambios que están "
            "actualmente en el diff."
        )
        print(
            "Este contexto ayudará al LLM a clasificar mejor los cambios. "
            "Presiona Enter dos veces para finalizar o dejar vacío."
        )
        print("="*70)

        context_lines = []
        empty_lines = 0

        while True:
            try:
                line = input()
                if not line.strip():
                    empty_lines += 1
                    if empty_lines >= 2 or (
                        empty_lines == 1 and not context_lines
                    ):
                        break
                else:
                    empty_lines = 0
                    context_lines.append(line)
            except (EOFError, KeyboardInterrupt):
                break

        context = "\n".join(context_lines).strip()
        return context if context else None

    def _get_user_description(
        self,
        user_description_arg: Optional[str],
        interactive: bool
    ) -> Optional[str]:
        """Get user description."""
        if user_description_arg:
            return self._read_file_or_text(user_description_arg)

        if not interactive:
            return None

        print("\n" + "="*70)
        print("📝 DESCRIPCIÓN DE CAMBIOS")
        print("="*70)
        print(
            "Opcional: Escribe una descripción general de todos los cambios "
            "realizados."
        )
        print("Presiona Enter dos veces para finalizar o dejar vacío.")
        print("="*70)

        description_lines = []
        empty_lines = 0

        while True:
            try:
                line = input()
                if not line.strip():
                    empty_lines += 1
                    if empty_lines >= 2 or (
                        empty_lines == 1 and not description_lines
                    ):
                        break
                else:
                    empty_lines = 0
                    description_lines.append(line)
            except (EOFError, KeyboardInterrupt):
                break

        description = "\n".join(description_lines).strip()
        return description if description else None

    def _read_file_or_text(self, input_str: str) -> Optional[str]:
        """Read content from file or return text directly."""
        if not input_str:
            return None

        if os.path.exists(input_str):
            try:
                with open(input_str, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                print(f"❌ Error leyendo archivo: {e}")
                return None
        return input_str

    def _display_plan(self, plan: Dict[int, Dict]) -> None:
        """Display git plan."""
        print("\n" + "="*70)
        print("📋 GIT PLAN PROPUESTO")
        print("="*70)

        for g_id in sorted(plan.keys()):
            data = plan[g_id]
            if not data["hunks"]:
                continue

            files = set(
                h.file if hasattr(h, 'file') else h['file']
                for h in data["hunks"]
            )
            print(f"\n[Commit {g_id}]: {data['desc']}")
            print(f"  Hunks: {len(data['hunks'])} | Archivos: {len(files)}")
            print(f"  Archivos: {', '.join(sorted(files)[:5])}")
            if len(files) > 5:
                print(f"  ... y {len(files) - 5} más")

        print("\n" + "="*70)

    def _get_action(self, args, interactive: bool) -> str:
        """Get user action."""
        if args.execute:
            return 'e'
        elif args.edit_plan:
            return 'ed'
        elif interactive:
            action = input(
                "\n¿Qué deseas hacer? "
                "(e)jecutar, (ed)itar plan, (c)ancelar [e]: "
            ).strip().lower()
            return action or 'e'
        else:
            return 'c'

    def _execute_plan(
        self,
        plan: Dict[int, Dict],
        diff_from_file: bool,
        args: argparse.Namespace,
        provider: str,
        key_manager: Optional[APIKeyRepository],
        user_description: Optional[str]
    ) -> int:
        """Execute the plan."""
        if diff_from_file:
            print(
                "\n⚠️  ADVERTENCIA: El diff proviene de un archivo."
            )
            print(
                "   Los commits solo se aplicarán si el diff es compatible "
                "con el estado actual del repositorio."
            )
            confirm_apply = input(
                "¿Continuar con la aplicación de commits? (s/N): "
            ).strip().lower() == 's'
            if not confirm_apply:
                print("Operación cancelada.")
                return 0
            rollback_point = None
        else:
            rollback_point = get_current_head()

        execution_mode = args.mode
        generate_pr_summary = args.generate_pr
        test_cmd = args.test_cmd

        if execution_mode == 'step-by-step':
            executor = StepByStepExecutor()
        else:
            executor = NormalExecutor()

        provider_instance = None
        llm_client = None
        if generate_pr_summary:
            try:
                from ...providers import ProviderFactory
                provider_instance = ProviderFactory.create(
                    provider,
                    model_name=None,
                    key_manager=key_manager
                )
                if provider_instance:
                    llm_client = provider_instance.get_client()
            except Exception:
                pass

        success = executor.execute(
            plan=plan,
            rollback_point=rollback_point,
            test_command=test_cmd,
            generate_pr=generate_pr_summary,
            llm_client=llm_client,
            user_description=user_description,
            provider=provider,
            key_manager=key_manager
        )

        return 0 if success else 1
