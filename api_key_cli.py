#!/usr/bin/env python3
"""
CLI para gestionar API keys de LLMs.
"""

import sys
import getpass
from typing import Optional
from db_manager import APIKeyManager


def add_key(manager: APIKeyManager, provider: str, 
            name: Optional[str] = None) -> None:
    """
    Agrega una API key para un proveedor.
    
    Nota: Ollama no requiere API keys ya que es un servicio local.
    """
    if provider == "ollama":
        print("ℹ️  Ollama no requiere API keys.")
        print("   Ollama es un servicio local que se ejecuta en tu máquina.")
        print("   Solo necesitas tener Ollama instalado y corriendo.")
        print("   Verifica el estado con: git-split ollama status")
        return
    """Añade una nueva API key."""
    print(f"\nAñadiendo API key para {provider}")
    if name:
        print(f"Nombre: {name}")
    
    api_key = getpass.getpass("API Key (se ocultará al escribir): ")
    if not api_key:
        print("❌ API key vacía. Operación cancelada.")
        return
    
    if manager.add_key(provider, api_key, name):
        print(f"✅ API key añadida exitosamente para {provider}")
    else:
        print(f"❌ Error: La API key ya existe para {provider}")


def list_keys(manager: APIKeyManager, provider: Optional[str] = None) -> None:
    """Lista todas las API keys."""
    keys = manager.list_keys(provider)
    
    if not keys:
        provider_msg = f" para {provider}" if provider else ""
        print(f"\n📭 No hay API keys activas{provider_msg}.")
        return
    
    print(f"\n📋 API Keys{' (' + provider + ')' if provider else '')}:")
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


def delete_key(manager: APIKeyManager, key_id: int) -> None:
    """Elimina una API key."""
    key = manager.get_key_by_id(key_id)
    if not key:
        print(f"❌ No se encontró API key con ID {key_id}")
        return
    
    if not key['is_active']:
        print(f"⚠️  La API key {key_id} ya está desactivada.")
        return
    
    confirm = input(
        f"\n¿Eliminar API key {key_id} "
        f"({key['provider']}{' - ' + key['name'] if key['name'] else ''})? "
        "(s/N): "
    ).strip().lower()
    
    if confirm == 's':
        if manager.delete_key(key_id):
            print(f"✅ API key {key_id} eliminada.")
        else:
            print(f"❌ Error al eliminar API key {key_id}")
    else:
        print("Operación cancelada.")


def main():
    """Función principal del CLI."""
    manager = APIKeyManager()
    
    if len(sys.argv) < 2:
        print("Uso: python api_key_cli.py <comando> [opciones]")
        print("\nComandos:")
        print("  add <provider> [name]    - Añadir API key")
        print("  list [provider]          - Listar API keys")
        print("  delete <id>              - Eliminar API key")
        print("\nEjemplos:")
        print("  python api_key_cli.py add gemini 'Mi key principal'")
        print("  python api_key_cli.py list gemini")
        print("  python api_key_cli.py delete 1")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'add':
        if len(sys.argv) < 3:
            print("❌ Error: Especifica el provider (gemini/openai/ollama)")
            sys.exit(1)
        provider = sys.argv[2]
        name = sys.argv[3] if len(sys.argv) > 3 else None
        add_key(manager, provider, name)
    
    elif command == 'list':
        provider = sys.argv[2] if len(sys.argv) > 2 else None
        list_keys(manager, provider)
    
    elif command == 'delete':
        if len(sys.argv) < 3:
            print("❌ Error: Especifica el ID de la API key")
            sys.exit(1)
        try:
            key_id = int(sys.argv[2])
            delete_key(manager, key_id)
        except ValueError:
            print("❌ Error: El ID debe ser un número")
            sys.exit(1)
    
    else:
        print(f"❌ Comando desconocido: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()

