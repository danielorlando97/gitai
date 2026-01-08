"""Ollama management command."""

import sys
import subprocess
import argparse
from .base import BaseCommand
from ...detectors import (
    SystemResourceDetector,
    detect_resource_scale,
    get_recommended_model,
    print_system_info
)


class OllamaCommand(BaseCommand):
    """Command for managing Ollama."""

    name = "ollama"
    description = "Configura y gestiona Ollama"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add command-specific arguments."""
        subparsers = parser.add_subparsers(
            dest='subcommand',
            help='Subcomandos disponibles',
            required=True
        )

        subparsers.add_parser('setup', help='Instalar y configurar Ollama')
        subparsers.add_parser('status', help='Verificar estado de Ollama')
        subparsers.add_parser('list', help='Listar modelos disponibles')

        pull_parser = subparsers.add_parser(
            'pull',
            help='Descargar un modelo'
        )
        pull_parser.add_argument(
            'model',
            help='Nombre del modelo a descargar'
        )

        subparsers.add_parser('info', help='Mostrar información del sistema')

    def execute(self, args: argparse.Namespace) -> int:
        """Execute the command."""
        if args.subcommand == 'setup':
            return self._handle_setup()
        elif args.subcommand == 'status':
            return self._handle_status()
        elif args.subcommand == 'pull':
            return self._handle_pull(args.model)
        elif args.subcommand == 'list':
            return self._handle_list()
        elif args.subcommand == 'info':
            return self._handle_info()
        else:
            print(f"❌ Subcomando desconocido: {args.subcommand}")
            return 1

    def _handle_setup(self) -> int:
        """Handle setup subcommand."""
        print("🔧 Configurando Ollama...")
        print()

        if not self._check_installation():
            return 1

        if not self._check_service():
            return 1

        self._check_models()

        print()
        print("📚 Verificando dependencias de Python...")
        try:
            import langchain_ollama
            print("✅ langchain-ollama está instalado")
        except ImportError:
            print("⚠️  langchain-ollama no está instalado")
            print("   Instala con: pip install langchain-ollama")

        try:
            import openai
            print("✅ openai está instalado (fallback disponible)")
        except ImportError:
            print("⚠️  openai no está instalado (recomendado para fallback)")
            print("   Instala con: pip install openai")

        print()
        print("✅ Configuración completada")
        print()
        print_system_info()
        return 0

    def _handle_status(self) -> int:
        """Handle status subcommand."""
        print("🔍 Verificando estado de Ollama...")
        print()

        if not self._check_installation():
            return 1

        if not self._check_service():
            return 1

        self._check_models()
        return 0

    def _handle_pull(self, model_name: str) -> int:
        """Handle pull subcommand."""
        print(f"📥 Descargando modelo: {model_name}")
        print("   Esto puede tomar varios minutos...")
        print()

        try:
            result = subprocess.run(
                ['ollama', 'pull', model_name],
                text=True
            )
            if result.returncode == 0:
                print(f"\n✅ Modelo {model_name} descargado exitosamente")
                return 0
            else:
                print(f"\n❌ Error al descargar modelo {model_name}")
                return 1
        except KeyboardInterrupt:
            print("\n⚠️  Descarga cancelada por el usuario")
            return 1
        except Exception as e:
            print(f"\n❌ Error: {e}")
            return 1

    def _handle_list(self) -> int:
        """Handle list subcommand."""
        try:
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print("📦 Modelos instalados:")
                print(result.stdout.strip() or "   (ninguno)")
                return 0
            else:
                print("❌ Error al obtener lista de modelos")
                return 1
        except Exception as e:
            print(f"❌ Error: {e}")
            return 1

    def _handle_info(self) -> int:
        """Handle info subcommand."""
        print_system_info()
        return 0

    def _check_installation(self) -> bool:
        """Check if Ollama is installed."""
        try:
            result = subprocess.run(
                ['ollama', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"✅ Ollama instalado: {result.stdout.strip()}")
                return True
            else:
                print("❌ Ollama no está instalado")
                self._print_install_instructions()
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("❌ Ollama no está instalado o no está en PATH")
            self._print_install_instructions()
            return False

    def _check_service(self) -> bool:
        """Check if Ollama service is running."""
        try:
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print("✅ Servicio de Ollama está corriendo")
                return True
            else:
                print("❌ Servicio de Ollama no está corriendo")
                print("   Inicia el servicio con: ollama serve")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("❌ No se pudo conectar al servicio de Ollama")
            print("   Asegúrate de que Ollama esté corriendo:")
            print("   - En macOS/Linux: ollama serve")
            print("   - O inicia la aplicación Ollama")
            return False

    def _check_models(self) -> None:
        """Check installed models."""
        print()
        print("📦 Modelos instalados:")
        try:
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                models = result.stdout.strip()
                if models:
                    print(models)
                else:
                    print("   (ninguno)")
                    print()
                    scale = detect_resource_scale()
                    recommended = get_recommended_model("ollama", scale=scale)
                    if recommended:
                        print(
                            f"💡 Modelo recomendado para tu sistema: "
                            f"{recommended}"
                        )
                        print(
                            f"   Descarga con: git-split ollama pull "
                            f"{recommended}"
                        )
            else:
                print("   (no se pudo obtener la lista)")
        except Exception as e:
            print(f"   Error: {e}")

    def _print_install_instructions(self) -> None:
        """Print installation instructions."""
        print()
        print("Para instalar Ollama:")
        print("  macOS:   brew install ollama")
        print("  Linux:  curl -fsSL https://ollama.com/install.sh | sh")
        print("  Windows: Descarga desde https://ollama.com/download")
