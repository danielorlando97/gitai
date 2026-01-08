"""API key management command."""

import sys
import getpass
import argparse
from typing import Optional
from .base import BaseCommand
from ...storage import APIKeyRepository


class APIKeyCommand(BaseCommand):
    """Command for managing API keys."""

    name = "api-key"
    description = "Gestiona API keys de LLMs"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add command-specific arguments."""
        subparsers = parser.add_subparsers(
            dest='subcommand',
            help='Subcomandos disponibles',
            required=True
        )

        add_parser = subparsers.add_parser(
            'add',
            help='Añadir API key'
        )
        add_parser.add_argument(
            'provider',
            choices=['gemini', 'openai', 'ollama'],
            help='Proveedor LLM'
        )
        add_parser.add_argument(
            'name',
            nargs='?',
            help='Nombre opcional para la API key'
        )

        list_parser = subparsers.add_parser(
            'list',
            help='Listar API keys'
        )
        list_parser.add_argument(
            'provider',
            nargs='?',
            choices=['gemini', 'openai', 'ollama'],
            help='Filtrar por proveedor'
        )

        delete_parser = subparsers.add_parser(
            'delete',
            help='Eliminar API key'
        )
        delete_parser.add_argument(
            'key_id',
            type=int,
            help='ID de la API key a eliminar'
        )

    def execute(self, args: argparse.Namespace) -> int:
        """Execute the command."""
        try:
            repository = APIKeyRepository()
        except Exception as e:
            print(f"❌ Error: No se pudo inicializar el repositorio: {e}")
            return 1

        if args.subcommand == 'add':
            return self._handle_add(repository, args.provider, args.name)
        elif args.subcommand == 'list':
            return self._handle_list(repository, args.provider)
        elif args.subcommand == 'delete':
            return self._handle_delete(repository, args.key_id)
        else:
            print(f"❌ Subcomando desconocido: {args.subcommand}")
            return 1

    def _handle_add(
        self,
        repository: APIKeyRepository,
        provider: str,
        name: Optional[str]
    ) -> int:
        """Handle add subcommand."""
        if provider == "ollama":
            print("ℹ️  Ollama no requiere API keys.")
            print("   Ollama es un servicio local que se ejecuta en tu máquina.")
            print("   Solo necesitas tener Ollama instalado y corriendo.")
            print("   Verifica el estado con: git-split ollama status")
            return 0

        print(f"\nAñadiendo API key para {provider}")
        if name:
            print(f"Nombre: {name}")

        api_key = getpass.getpass("API Key (se ocultará): ")
        if not api_key:
            print("❌ API key vacía. Operación cancelada.")
            return 1

        if repository.create({
            'provider': provider,
            'api_key': api_key,
            'name': name
        }):
            print(f"✅ API key añadida exitosamente para {provider}")
            return 0
        else:
            print(f"❌ Error: La API key ya existe para {provider}")
            return 1

    def _handle_list(
        self,
        repository: APIKeyRepository,
        provider: Optional[str]
    ) -> int:
        """Handle list subcommand."""
        filters = {'provider': provider} if provider else None
        keys = repository.list_all(filters)

        if not keys:
            provider_msg = f" para {provider}" if provider else ""
            print(f"\n📭 No hay API keys activas{provider_msg}.")
            return 0

        provider_suffix = f" ({provider})" if provider else ""
        print(f"\n📋 API Keys{provider_suffix}:")
        print("=" * 70)

        for key in keys:
            name_str = f" ({key['name']})" if key['name'] else ""
            last_used = key['last_used'] or "Nunca"
            print(f"\nID: {key['id']}")
            print(f"  Provider: {key['provider']}{name_str}")
            print(f"  Creada: {key['created_at']}")
            print(f"  Último uso: {last_used}")
            print(f"  Usos: {key['use_count']}")

        print("\n" + "=" * 70)
        return 0

    def _handle_delete(
        self,
        repository: APIKeyRepository,
        key_id: int
    ) -> int:
        """Handle delete subcommand."""
        key = repository.read(key_id)
        if not key:
            print(f"❌ No se encontró API key con ID {key_id}")
            return 1

        if not key['is_active']:
            print(f"⚠️  La API key {key_id} ya está desactivada.")
            return 0

        name_str = f" - {key['name']}" if key['name'] else ""
        confirm = input(
            f"\n¿Eliminar API key {key_id} "
            f"({key['provider']}{name_str})? (s/N): "
        ).strip().lower()

        if confirm == 's':
            if repository.delete(key_id):
                print(f"✅ API key {key_id} eliminada.")
                return 0
            else:
                print(f"❌ Error al eliminar API key {key_id}")
                return 1
        else:
            print("Operación cancelada.")
            return 0
