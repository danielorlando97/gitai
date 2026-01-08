#!/usr/bin/env python3
"""
GitClassifier: Herramienta para clasificar y dividir cambios de Git
en commits semánticos basados en objetivos usando LLM.
"""

import subprocess
import re
import os
import sys
import json
import time
import uuid
import getpass
import argparse
from typing import List, Dict, Optional, Tuple

try:
    from db_manager import APIKeyManager
    HAS_DB = True
except ImportError:
    HAS_DB = False

try:
    from prompts import (
        get_goals_identification_prompt,
        get_hunk_classification_prompt,
        get_pr_summary_prompt
    )
    HAS_PROMPTS = True
except ImportError:
    HAS_PROMPTS = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import PydanticOutputParser
    from pydantic import BaseModel, Field
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False
    # Placeholder para type checking cuando LangChain no está disponible
    ChatGoogleGenerativeAI = None

try:
    from langchain_ollama import ChatOllama
    HAS_OLLAMA_LANGCHAIN = True
except ImportError:
    HAS_OLLAMA_LANGCHAIN = False
    ChatOllama = None

try:
    from resource_detector import (
        detect_resource_scale,
        get_recommended_model,
        get_provider_priority,
        get_default_provider,
        print_system_info
    )
    HAS_RESOURCE_DETECTOR = True
except ImportError:
    HAS_RESOURCE_DETECTOR = False


# Modelos Pydantic para estructuración de datos
class Goal(BaseModel):
    """Modelo para un objetivo funcional."""
    id: int = Field(description="ID único del objetivo")
    description: str = Field(description="Mensaje de commit sugerido")


class GitPlan(BaseModel):
    """Modelo para el plan completo de Git."""
    goals: List[Goal] = Field(description="Lista de objetivos funcionales")


def get_llm_client(provider: str = None, 
                  key_manager: Optional[APIKeyManager] = None,
                  current_key_id: Optional[int] = None,
                  model_name: Optional[str] = None) -> Optional[object]:
    """
    Inicializa el cliente LLM según el proveedor con rotación de keys.
    
    Args:
        provider: Proveedor LLM (ollama, gemini, openai). Si None, usa default.
        key_manager: Manager de API keys
        current_key_id: ID de la key actual
        model_name: Nombre del modelo a usar (si None, se detecta automáticamente)
    """
    # Si no se especifica proveedor, usar el default del config
    if provider is None:
        if HAS_RESOURCE_DETECTOR:
            provider = get_default_provider()
        else:
            provider = "ollama"  # Default a Ollama
    
    # Detectar modelo recomendado si no se especifica
    if model_name is None and HAS_RESOURCE_DETECTOR:
        model_name = get_recommended_model(provider)
    
    if provider == "ollama":
        # Priorizar LangChain si está disponible
        if HAS_OLLAMA_LANGCHAIN and ChatOllama:
            if model_name is None:
                model_name = "llama3.2:3b"  # Default para Ollama
            
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            client = ChatOllama(
                model=model_name,
                base_url=base_url,
                temperature=0
            )
            return client
        elif HAS_OPENAI:
            # Fallback a OpenAI client compatible
            if model_name is None:
                model_name = "llama3.2:3b"
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
            client = OpenAI(base_url=base_url, api_key="ollama")
            return client
        else:
            print("Error: Ollama requiere langchain-ollama o openai.")
            print("Instala con: pip install langchain-ollama")
            return None
    
    elif provider == "gemini":
        if not HAS_LANGCHAIN:
            return None
        
        api_key = None
        key_id = None
        
        # Intentar obtener key de la base de datos primero
        if HAS_DB and key_manager:
            key_data = key_manager.get_next_key(provider)
            if key_data:
                api_key = key_data['api_key']
                key_id = key_data['id']
        
        # Fallback a variable de entorno
        if not api_key:
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                if HAS_DB:
                    print("⚠️  No hay API keys en la base de datos.")
                    print("   Usa: python api_key_cli.py add gemini")
                else:
                    print("Error: GOOGLE_API_KEY no está configurada.")
                return None
        
        if model_name is None:
            model_name = os.getenv("GEMINI_MODEL")
            if not model_name and HAS_RESOURCE_DETECTOR:
                model_name = get_recommended_model("gemini")
            if not model_name:
                model_name = "models/gemini-2.5-flash-lite"
        
        client = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0,
            google_api_key=api_key
        )
        
        # Guardar key_id en el cliente para rotación
        if key_id:
            client._key_id = key_id
            client._key_manager = key_manager
        
        return client
    
    elif provider == "openai":
        if not HAS_OPENAI:
            return None
        
        api_key = None
        key_id = None
        
        if HAS_DB and key_manager:
            key_data = key_manager.get_next_key(provider)
            if key_data:
                api_key = key_data['api_key']
                key_id = key_data['id']
        
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                if HAS_DB:
                    print("⚠️  No hay API keys en la base de datos.")
                    print("   Usa: python api_key_cli.py add openai")
                else:
                    print("Error: OPENAI_API_KEY no está configurada.")
                return None
        
        client = OpenAI(api_key=api_key)
        if key_id:
            client._key_id = key_id
            client._key_manager = key_manager
        
        return client
    
    return None


def read_diff_from_file(file_path: str) -> Optional[str]:
    """Lee el diff desde un archivo."""
    try:
        # Expandir ~ y variables de entorno
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
    """Obtiene el diff completo contra una rama objetivo."""
    try:
        if use_working_dir:
            # Obtener diff del working directory (staged + unstaged)
            # Primero cambios unstaged
            unstaged_result = subprocess.run(
                ['git', 'diff', 'HEAD'],
                capture_output=True,
                text=True
            )
            # Luego cambios staged
            staged_result = subprocess.run(
                ['git', 'diff', '--cached', 'HEAD'],
                capture_output=True,
                text=True
            )
            # Combinar ambos diffs
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
    """Divide el diff en archivos y luego en hunks individuales."""
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
    """Crea un resumen de los hunks para el análisis global."""
    summary_parts = []
    total_chars = 0
    
    for hunk in hunks:
        file_name = hunk['file']
        content_preview = hunk['content'][:300]
        entry = f"File: {file_name}\n{content_preview}...\n"
        
        if total_chars + len(entry) > max_chars:
            break
        summary_parts.append(entry)
        total_chars += len(entry)
    
    return "\n".join(summary_parts)


def handle_llm_error(error: Exception, client: object, 
                    provider: str, key_manager: Optional[APIKeyManager]) -> bool:
    """Maneja errores de LLM y rota API keys si es necesario."""
    error_str = str(error)
    
    # Detectar errores de rate limit/quota
    is_rate_limit = (
        "RESOURCE_EXHAUSTED" in error_str or
        "429" in error_str or
        "rate limit" in error_str.lower() or
        "quota" in error_str.lower()
    )
    
    if is_rate_limit and HAS_DB and key_manager:
        # Registrar error en la base de datos
        if hasattr(client, '_key_id') and client._key_id:
            key_manager.record_error(
                client._key_id,
                "RATE_LIMIT",
                error_str[:500]  # Limitar longitud
            )
            print(f"\n⚠️  Rate limit alcanzado. Cambiando a siguiente API key...")
            return True  # Indica que se debe rotar
    
    return False  # No se puede rotar automáticamente


def get_goals_from_llm(client: object, 
                       hunks: List[Dict[str, str]],
                       provider: str = "gemini",
                       key_manager: Optional[APIKeyManager] = None,
                       user_context: Optional[str] = None) -> List[Dict]:
    """Paso 1: Identificar objetivos funcionales globales."""
    summary = create_summary_for_llm(hunks)
    
    # Calcular max_retries basado en número de keys disponibles
    if HAS_DB and key_manager:
        all_keys = key_manager.list_keys(provider)
        max_retries = max(len(all_keys) * 2, 10) if all_keys else 1
    else:
        max_retries = 1
    
    current_client = client
    used_key_ids = set()
    
    if hasattr(client, '_key_id') and client._key_id:
        used_key_ids.add(client._key_id)
    
    for attempt in range(max_retries):
        # Usar LangChain si está disponible y es compatible
        is_langchain_client = (
            (HAS_LANGCHAIN and ChatGoogleGenerativeAI and 
             isinstance(current_client, ChatGoogleGenerativeAI)) or
            (HAS_OLLAMA_LANGCHAIN and ChatOllama and 
             isinstance(current_client, ChatOllama))
        )
        
        if is_langchain_client:
            try:
                parser = PydanticOutputParser(pydantic_object=GitPlan)
                
                # Usar prompt desde archivo separado
                if HAS_PROMPTS:
                    prompt_template = get_goals_identification_prompt(user_context)
                else:
                    # Fallback si no se puede importar prompts
                    context_section = ""
                    if user_context:
                        context_section = (
                            f"\n\nContexto proporcionado por el usuario sobre "
                            f"los cambios:\n{user_context}\n"
                        )
                    prompt_template = (
                        "Eres un arquitecto de software experto en Git. "
                        "Analiza estos cambios de código y agrúpalos en objetivos "
                        "funcionales lógicos (commits).{user_context}\n"
                        "{format_instructions}\n\n"
                        "Cambios:\n{diff_summary}"
                    )
                
                prompt = ChatPromptTemplate.from_template(prompt_template)
                
                chain = prompt | current_client | parser
                result = chain.invoke({
                    "diff_summary": summary,
                    "format_instructions": parser.get_format_instructions()
                })
                
                return [{"id": g.id, "description": g.description} 
                       for g in result.goals]
            except Exception as e:
                if handle_llm_error(e, current_client, provider, key_manager):
                    # Verificar si hemos usado todas las keys disponibles
                    should_wait = False
                    if HAS_DB and key_manager:
                        all_keys = key_manager.list_keys(provider)
                        all_key_ids = {k['id'] for k in all_keys}
                        
                        if (used_key_ids.issuperset(all_key_ids) and 
                            all_key_ids and len(used_key_ids) >= len(all_key_ids)):
                            should_wait = True
                    
                    if should_wait:
                        # Todas las keys han sido probadas
                        wait_minutes = int(
                            os.getenv("API_KEY_WAIT_MINUTES", "5")
                        )
                        print(
                            f"\n⚠️  Todas las API keys han alcanzado el límite."
                        )
                        print(
                            f"⏳ Esperando {wait_minutes} minutos antes de "
                            f"reintentar..."
                        )
                        
                        total_seconds = wait_minutes * 60
                        for remaining in range(total_seconds, 0, -30):
                            mins = remaining // 60
                            secs = remaining % 60
                            print(
                                f"   Tiempo restante: {mins:02d}:{secs:02d}",
                                end='\r'
                            )
                            time.sleep(min(30, remaining))
                        
                        print("\n🔄 Reintentando con todas las keys...")
                        used_key_ids.clear()  # Reset para reintentar todas
                    
                    # Rotar a siguiente key
                    current_client = get_llm_client(provider, key_manager)
                    if not current_client:
                        print("❌ No hay más API keys disponibles.")
                        break
                    
                    # Registrar key usada
                    if hasattr(current_client, '_key_id') and current_client._key_id:
                        used_key_ids.add(current_client._key_id)
                    
                    msg = (
                        f"🔄 Reintentando con nueva API key "
                        f"(intento {attempt + 2}/{max_retries})..."
                    )
                    print(msg)
                    continue
                else:
                    print(f"Error con LangChain: {e}")
                    if attempt < max_retries - 1:
                        continue
                    break
    
    # Fallback para OpenAI/Ollama (solo si el provider es openai/ollama)
    if provider in ["openai", "ollama"] and HAS_OPENAI:
        prompt = f"""
Analiza estos cambios de código y define una lista de objetivos 
funcionales (commits). Agrúpalos por lógica (ej: Refactorización, 
Corrección de Bug X, Nueva Feature Y).

Responde ÚNICAMENTE en formato JSON válido:
{{"goals": [{{"id": 1, "description": "Mensaje de commit corto"}}, ...]}}

Cambios:
{summary}
"""
        
        # Obtener modelo del cliente actual si está disponible
        model_to_use = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        if hasattr(current_client, 'model'):
            model_to_use = current_client.model
        elif hasattr(current_client, '_model'):
            model_to_use = current_client._model
        elif provider == "ollama":
            # Para Ollama, usar modelo recomendado o default
            if HAS_RESOURCE_DETECTOR:
                model_to_use = get_recommended_model("ollama") or "llama3.2:3b"
            else:
                model_to_use = "llama3.2:3b"
        
        # Intentar con rotación de keys
        for fallback_attempt in range(max_retries):
            try:
                fallback_client = current_client
                if not isinstance(fallback_client, OpenAI):
                    # Obtener nuevo cliente OpenAI
                    fallback_client = get_llm_client(provider, key_manager)
                    if not fallback_client:
                        break
                    # Actualizar modelo si el cliente tiene uno
                    if hasattr(fallback_client, 'model'):
                        model_to_use = fallback_client.model
                    elif hasattr(fallback_client, '_model'):
                        model_to_use = fallback_client._model
                
                response = fallback_client.chat.completions.create(
                    model=model_to_use,
                    messages=[
                        {
                            "role": "system",
                            "content": "Eres un experto en Git y arquitectura."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3
                )
                
                content = response.choices[0].message.content.strip()
                if content.startswith("```"):
                    content = re.sub(r'^```(?:json)?\n?', '', content)
                    content = re.sub(r'\n?```$', '', content)
                
                parsed = json.loads(content)
                return parsed.get("goals", [])
            except Exception as e:
                if handle_llm_error(e, fallback_client, provider, key_manager):
                    fallback_client = get_llm_client(provider, key_manager)
                    if not fallback_client:
                        break
                    continue
                else:
                    if fallback_attempt < max_retries - 1:
                        continue
                    print(f"Error consultando LLM: {e}")
                    break
    
    print("❌ No se pudieron obtener objetivos funcionales.")
    return []


def classify_hunk_with_llm(client: object, hunk: Dict[str, str],
                           goals: List[Dict],
                           provider: str = "gemini",
                           key_manager: Optional[APIKeyManager] = None,
                           used_key_ids: Optional[set] = None,
                           user_context: Optional[str] = None) -> Optional[int]:
    """Paso 2: Clasificar un hunk individual en un objetivo."""
    if used_key_ids is None:
        used_key_ids = set()
    
    goals_text = "\n".join(
        [f"{g['id']}: {g['description']}" for g in goals]
    )
    
    # Calcular max_retries basado en número de keys disponibles
    if HAS_DB and key_manager:
        all_keys = key_manager.list_keys(provider)
        max_retries = max(len(all_keys) * 2, 10) if all_keys else 1
    else:
        max_retries = 1
    
    current_client = client
    
    if hasattr(client, '_key_id') and client._key_id:
        used_key_ids.add(client._key_id)
    
    for attempt in range(max_retries):
        is_langchain_client = (
            (HAS_LANGCHAIN and ChatGoogleGenerativeAI and 
             isinstance(current_client, ChatGoogleGenerativeAI)) or
            (HAS_OLLAMA_LANGCHAIN and ChatOllama and 
             isinstance(current_client, ChatOllama))
        )
        
        if is_langchain_client:
            try:
                # Usar prompt desde archivo separado
                if HAS_PROMPTS:
                    prompt_template = get_hunk_classification_prompt(user_context)
                else:
                    # Fallback si no se puede importar prompts
                    context_section = ""
                    if user_context:
                        context_section = (
                            f"\n\nContexto del usuario sobre los cambios: "
                            f"{user_context}\n"
                        )
                    prompt_template = (
                        "Analiza el siguiente fragmento de código (hunk) y decide "
                        "a qué ID de objetivo pertenece.{user_context}\n"
                        "Objetivos disponibles:\n{goals}\n\n"
                        "Fragmento:\n{hunk}\n\n"
                        "Responde SOLO con el número del ID."
                    )
                
                prompt = ChatPromptTemplate.from_template(prompt_template)
                
                chain = prompt | current_client
                response = chain.invoke({
                    "goals": goals_text,
                    "hunk": hunk['content'][:2000]
                })
                
                content = response.content.strip()
                goal_id = int(re.sub(r'\D', '', content))
                return goal_id if goal_id in [g['id'] for g in goals] else None
            except Exception as e:
                if handle_llm_error(e, current_client, provider, key_manager):
                    # Verificar si hemos usado todas las keys disponibles
                    should_wait = False
                    if HAS_DB and key_manager:
                        all_keys = key_manager.list_keys(provider)
                        all_key_ids = {k['id'] for k in all_keys}
                        
                        if (used_key_ids.issuperset(all_key_ids) and 
                            all_key_ids and len(used_key_ids) >= len(all_key_ids)):
                            should_wait = True
                    
                    if should_wait:
                        # Todas las keys han sido probadas
                        wait_minutes = int(
                            os.getenv("API_KEY_WAIT_MINUTES", "5")
                        )
                        print(
                            f"\n⚠️  Todas las API keys han alcanzado el límite."
                        )
                        print(
                            f"⏳ Esperando {wait_minutes} minutos antes de "
                            f"reintentar..."
                        )
                        
                        total_seconds = wait_minutes * 60
                        for remaining in range(total_seconds, 0, -30):
                            mins = remaining // 60
                            secs = remaining % 60
                            print(
                                f"   Tiempo restante: {mins:02d}:{secs:02d}",
                                end='\r'
                            )
                            time.sleep(min(30, remaining))
                        
                        print("\n🔄 Reintentando con todas las keys...")
                        used_key_ids.clear()  # Reset para reintentar todas
                    
                    # Rotar a siguiente key
                    current_client = get_llm_client(provider, key_manager)
                    if not current_client:
                        break
                    
                    # Registrar key usada
                    if hasattr(current_client, '_key_id') and current_client._key_id:
                        used_key_ids.add(current_client._key_id)
                    
                    continue
                else:
                    if attempt < max_retries - 1:
                        continue
                    if attempt < max_retries - 1:
                        continue
                    break
    
    # Fallback para OpenAI/Ollama (solo si el provider es openai/ollama)
    if provider in ["openai", "ollama"] and HAS_OPENAI:
        context_section = ""
        if user_context:
            context_section = (
                f"\n\nContexto del usuario sobre los cambios: {user_context}\n"
            )
        
        prompt = f"""
¿A qué objetivo pertenece este cambio?{context_section}
Objetivos disponibles:
{goals_text}

Cambio:
{hunk['content'][:2000]}

Responde SOLO el ID numérico del objetivo.
"""
        
        # Intentar con rotación de keys
        for fallback_attempt in range(max_retries):
            try:
                fallback_client = current_client
                if not isinstance(fallback_client, OpenAI):
                    # Obtener nuevo cliente OpenAI
                    fallback_client = get_llm_client(provider, key_manager)
                    if not fallback_client:
                        break
                
                # Obtener modelo del cliente si está disponible
                model_to_use = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
                if hasattr(current_client, 'model'):
                    model_to_use = current_client.model
                elif hasattr(current_client, '_model'):
                    model_to_use = current_client._model
                elif provider == "ollama":
                    # Para Ollama, usar modelo recomendado o default
                    if HAS_RESOURCE_DETECTOR:
                        model_to_use = get_recommended_model("ollama") or "llama3.2:3b"
                    else:
                        model_to_use = "llama3.2:3b"
                
                # Actualizar modelo si el fallback_client tiene uno
                if hasattr(fallback_client, 'model'):
                    model_to_use = fallback_client.model
                elif hasattr(fallback_client, '_model'):
                    model_to_use = fallback_client._model
                
                response = fallback_client.chat.completions.create(
                    model=model_to_use,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1
                )
                
                content = response.choices[0].message.content.strip()
                goal_id = int(re.sub(r'\D', '', content))
                return goal_id if goal_id in [g['id'] for g in goals] else None
            except Exception as e:
                if handle_llm_error(e, fallback_client, provider, key_manager):
                    fallback_client = get_llm_client(provider, key_manager)
                    if not fallback_client:
                        break
                    continue
                else:
                    if fallback_attempt < max_retries - 1:
                        continue
                    print(f"Error clasificando hunk: {e}")
                    break
    
    return None


def classify_hunks_with_llm(
    client: object, 
    hunks: List[Dict[str, str]],
    goals: List[Dict],
    provider: str = "gemini",
    key_manager: Optional[APIKeyManager] = None,
    user_context: Optional[str] = None
) -> Dict[int, Dict]:
    """Clasifica todos los hunks usando LLM con rotación de keys."""
    classified_plan = {
        goal['id']: {
            "desc": goal['description'],
            "hunks": []
        } for goal in goals
    }
    
    print("Clasificando cambios...")
    current_client = client
    
    for i, hunk in enumerate(hunks):
        print(f"  [{i+1}/{len(hunks)}] {hunk['file']}...", end='\r')
        
        # Cada hunk tiene su propio conjunto de keys usadas
        hunk_used_keys = set()
        if hasattr(current_client, '_key_id') and current_client._key_id:
            hunk_used_keys.add(current_client._key_id)
        
        goal_id = classify_hunk_with_llm(
            current_client, hunk, goals, provider, key_manager, 
            hunk_used_keys, user_context
        )
        
        # Si hay error y se rotó, actualizar current_client
        if not goal_id and HAS_DB and key_manager:
            # Intentar obtener nuevo cliente si el anterior falló
            new_client = get_llm_client(provider, key_manager)
            if new_client:
                current_client = new_client
                if hasattr(new_client, '_key_id') and new_client._key_id:
                    hunk_used_keys.add(new_client._key_id)
                # Reintentar con nueva key
                goal_id = classify_hunk_with_llm(
                    current_client, hunk, goals, provider, 
                    key_manager, hunk_used_keys, user_context
                )
        
        if goal_id and goal_id in classified_plan:
            classified_plan[goal_id]["hunks"].append(hunk)
    
    print()  # Nueva línea después del progreso
    return classified_plan


def display_git_plan(plan: Dict[int, Dict]) -> None:
    """Muestra el Git Plan propuesto."""
    print("\n" + "="*70)
    print("📋 GIT PLAN PROPUESTO")
    print("="*70)
    
    for g_id in sorted(plan.keys()):
        data = plan[g_id]
        if not data["hunks"]:
            continue
        
        files = set(h['file'] for h in data["hunks"])
        print(f"\n[Commit {g_id}]: {data['desc']}")
        print(f"  Hunks: {len(data['hunks'])} | Archivos: {len(files)}")
        print(f"  Archivos: {', '.join(sorted(files)[:5])}")
        if len(files) > 5:
            print(f"  ... y {len(files) - 5} más")
    
    print("\n" + "="*70)


def show_plan_detailed(plan: Dict[int, Dict]) -> None:
    """Muestra el plan con detalles por archivo."""
    print("\n" + "="*60)
    print("📋 ESTADO ACTUAL DEL GIT PLAN")
    print("="*60)
    
    for g_id in sorted(plan.keys()):
        data = plan[g_id]
        hunk_count = len(data["hunks"])
        if hunk_count > 0:
            print(f"\nID [{g_id}] 📝 Mensaje: {data['desc']}")
            files = set(h['file'] for h in data["hunks"])
            for f in sorted(files):
                file_hunks = [h for h in data["hunks"] if h['file'] == f]
                print(f"   • {f} ({len(file_hunks)} hunk(s))")
    
    print("\n" + "="*60)


def apply_and_commit(hunks: List[Dict[str, str]], 
                     goal_name: str) -> bool:
    """Aplica una lista de hunks al stage y hace el commit."""
    patch_file = "temp.patch"
    
    try:
        # Limpiar el index antes de aplicar hunks
        subprocess.run(
            ['git', 'reset'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        for hunk in hunks:
            with open(patch_file, "w", encoding='utf-8') as f:
                f.write(hunk['content'])
            
            result = subprocess.run(
                ['git', 'apply', '--cached', patch_file],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                error_msg = (
                    f"Error aplicando parche en {hunk['file']}: "
                    f"{result.stderr}"
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


def get_all_hunks_from_plan(plan: Dict[int, Dict]) -> List[Tuple[int, int, Dict]]:
    """Extrae todos los hunks del plan con sus índices."""
    all_hunks = []
    for g_id, data in plan.items():
        for idx, hunk in enumerate(data["hunks"]):
            all_hunks.append((g_id, idx, hunk))
    return all_hunks


def edit_plan_interactive(plan: Dict[int, Dict]) -> Optional[Dict[int, Dict]]:
    """Editor interactivo mejorado para el plan."""
    while True:
        show_plan_detailed(plan)
        print("\nComandos disponibles:")
        print("  m [id_origen] [id_destino] [archivo]  -> Mover archivo")
        print("  r [id] [nuevo mensaje]                -> Renombrar commit")
        print("  d [id]                                 -> Descartar commit")
        print("  n [mensaje]                            -> Nuevo commit")
        print("  e                                      -> EJECUTAR COMMITS")
        print("  q                                      -> Salir sin hacer nada")
        
        cmd = input("\n> ").strip().split()
        if not cmd:
            continue
        
        action = cmd[0].lower()
        
        if action == 'e':
            return plan
        elif action == 'q':
            return None
        
        try:
            if action == 'm' and len(cmd) >= 4:
                src_id = int(cmd[1])
                dst_id = int(cmd[2])
                file_name = ' '.join(cmd[3:])
                
                if src_id not in plan:
                    print(f"❌ Commit {src_id} no existe.")
                    continue
                if dst_id not in plan:
                    print(f"❌ Commit {dst_id} no existe.")
                    continue
                
                hunks_to_move = [
                    h for h in plan[src_id]["hunks"]
                    if h["file"] == file_name
                ]
                
                if not hunks_to_move:
                    print(f"❌ Archivo '{file_name}' no encontrado en commit {src_id}")
                    continue
                
                plan[src_id]["hunks"] = [
                    h for h in plan[src_id]["hunks"]
                    if h["file"] != file_name
                ]
                plan[dst_id]["hunks"].extend(hunks_to_move)
                print(f"✅ Movido {file_name} del commit {src_id} al {dst_id}")
            
            elif action == 'r' and len(cmd) >= 3:
                target_id = int(cmd[1])
                new_desc = ' '.join(cmd[2:])
                
                if target_id not in plan:
                    print(f"❌ Commit {target_id} no existe.")
                    continue
                
                plan[target_id]["desc"] = new_desc
                print(f"✅ Commit {target_id} renombrado.")
            
            elif action == 'd' and len(cmd) >= 2:
                target_id = int(cmd[1])
                
                if target_id not in plan:
                    print(f"❌ Commit {target_id} no existe.")
                    continue
                
                if plan[target_id]["hunks"]:
                    confirm = input(
                        f"¿Descartar commit {target_id} y sus hunks? (s/N): "
                    ).strip().lower()
                    if confirm != 's':
                        continue
                
                plan[target_id]["hunks"] = []
                print(f"✅ Commit {target_id} descartado.")
            
            elif action == 'n' and len(cmd) >= 2:
                desc = ' '.join(cmd[1:])
                new_id = max(plan.keys()) + 1 if plan else 1
                plan[new_id] = {"desc": desc, "hunks": []}
                print(f"✅ Nuevo commit {new_id} creado: {desc}")
            
            else:
                print("❌ Comando no reconocido o parámetros incorrectos.")
        
        except (ValueError, KeyError) as e:
            print(f"❌ Error en el comando: {e}")
        except Exception as e:
            print(f"❌ Error inesperado: {e}")


def get_current_branch() -> Optional[str]:
    """Obtiene el nombre de la rama actual."""
    try:
        result = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()
        return result
    except subprocess.CalledProcessError:
        return None


def get_current_head() -> Optional[str]:
    """Obtiene el SHA del HEAD actual para rollback."""
    try:
        result = subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'],
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()
        return result
    except subprocess.CalledProcessError:
        return None


def create_temp_branch() -> Optional[str]:
    """Crea una rama temporal con ID único."""
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
        print(f"❌ Error creando rama temporal: {e.stderr.decode()}")
        return None


def cleanup_temp_branch(branch_name: str, original_branch: str) -> bool:
    """Vuelve a la rama original y elimina la rama temporal."""
    try:
        # Volver a la rama original
        subprocess.run(
            ['git', 'checkout', original_branch],
            check=True,
            capture_output=True
        )
        print(f"✅ Vuelto a rama: {original_branch}")
        
        # Eliminar rama temporal
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
    """Deshace commits usando --soft (mantiene cambios en archivos)."""
    try:
        print(f"\n⚠️  Realizando rollback a {commit_sha[:8]}...")
        # --soft deshace commits pero mantiene cambios en archivos
        subprocess.run(
            ['git', 'reset', '--soft', commit_sha],
            check=True,
            capture_output=True
        )
        # Limpiar el staging area para que todo vuelva a 'modified'
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


def cleanup_temp_stashes() -> None:
    """Limpia stashes temporales creados por el script."""
    try:
        result = subprocess.run(
            ['git', 'stash', 'list'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'dev_splitter_temp' in line:
                    stash_ref = line.split(':')[0]
                    subprocess.run(
                        ['git', 'stash', 'drop', stash_ref],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
    except Exception:
        pass


def step_by_step_execution(plan: Dict[int, Dict],
                          rollback_point: Optional[str] = None,
                          generate_pr: bool = False,
                          llm_client: Optional[object] = None,
                          user_description: Optional[str] = None,
                          provider: str = "gemini",
                          key_manager: Optional[APIKeyManager] = None) -> bool:
    """Ejecuta el plan commit por commit con aislamiento visual."""
    print("\n" + "!"*60)
    print("🛠️  MODO PASO A PASO ACTIVADO")
    print("Tu código se filtrará para que veas solo el commit actual.")
    print("!"*60)
    
    if rollback_point:
        print(f"\n🛡️  Punto de restauración: {rollback_point[:8]}")
    
    patch_file = "temp.patch"
    commits_realizados = 0
    commits_created = []
    
    try:
        for g_id in sorted(plan.keys()):
            data = plan[g_id]
            if not data["hunks"]:
                continue
            
            try:
                # 1. Limpiar stage y aplicar solo lo de este commit
                subprocess.run(
                    ['git', 'reset'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                
                for hunk in data["hunks"]:
                    with open(patch_file, "w", encoding='utf-8') as f:
                        f.write(hunk['content'])
                    
                    result = subprocess.run(
                        ['git', 'apply', '--cached', patch_file],
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode != 0:
                        raise Exception(
                            f"Error aplicando parche en {hunk['file']}: "
                            f"{result.stderr}"
                        )
                
                # 2. Aislar cambios: guardar todo lo demás
                print(f"\n📦 Preparando Commit {g_id}: {data['desc']}")
                
                # Verificar si hay archivos untracked
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
                    print("⚠️  Nota: Hay archivos nuevos (untracked).")
                
                stash_result = subprocess.run(
                    stash_cmd,
                    capture_output=True,
                    text=True
                )
                
                if stash_result.returncode != 0:
                    if 'No local changes' in stash_result.stderr:
                        print("ℹ️  No hay cambios adicionales para aislar.")
                    else:
                        raise Exception(
                            f"Error al crear stash: {stash_result.stderr}"
                        )
                
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
                        commit_result = subprocess.run(
                            ['git', 'commit', '-m', data['desc']],
                            capture_output=True,
                            text=True
                        )
                        
                        if commit_result.returncode != 0:
                            print(f"❌ Error: {commit_result.stderr}")
                            # Restaurar stash antes de continuar
                            subprocess.run(
                                ['git', 'stash', 'pop'],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL
                            )
                            raise Exception("Error al crear commit")
                        
                        commits_realizados += 1
                        commits_created.append({"desc": data['desc']})
                        print(f"✅ [{commits_realizados}] Commit realizado.")
                        
                        # Recuperar el resto de los cambios
                        pop_result = subprocess.run(
                            ['git', 'stash', 'pop'],
                            capture_output=True,
                            text=True
                        )
                        
                        if pop_result.returncode != 0:
                            if 'CONFLICT' in pop_result.stderr:
                                print("⚠️  Conflicto al restaurar cambios.")
                                print("   Resuelve manualmente con:")
                                print("   git stash pop")
                                return False
                            elif 'No stash entries' in pop_result.stderr:
                                pass  # No había stash, está bien
                        
                        break
                    
                    elif action == 's':
                        print(f"⏩ Saltando commit {g_id}...")
                        subprocess.run(
                            ['git', 'reset'],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                        
                        pop_result = subprocess.run(
                            ['git', 'stash', 'pop'],
                            capture_output=True,
                            text=True
                        )
                        
                        if pop_result.returncode != 0:
                            if 'No stash entries' not in pop_result.stderr:
                                print("⚠️  Error restaurando cambios.")
                        
                        break
                    
                    elif action == 'a':
                        print("⚠️  Abortando y restaurando estado original...")
                        subprocess.run(
                            ['git', 'reset'],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                        
                        pop_result = subprocess.run(
                            ['git', 'stash', 'pop'],
                            capture_output=True,
                            text=True
                        )
                        
                        if rollback_point:
                            print("\n🔄 Haciendo rollback completo...")
                            rollback_to_commit(rollback_point)
                        
                        cleanup_temp_stashes()
                        return False
                    
                    else:
                        print("❌ Opción no válida. Usa 'c', 's' o 'a'.")
            
            except Exception as e:
                print(f"❌ Error en el paso {g_id}: {e}")
                # Intentar restaurar stash si existe
                subprocess.run(
                    ['git', 'stash', 'pop'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                
                if rollback_point:
                    print("\n🔄 Haciendo rollback...")
                    rollback_to_commit(rollback_point)
                
                cleanup_temp_stashes()
                return False
        
        cleanup_temp_stashes()
        
        # Generar resumen de PR si se solicita
        if generate_pr and commits_created:
            print("\n📝 Generando resumen de Pull Request...")
            summary = generate_pr_summary(
                commits_created, llm_client, user_description, 
                provider, key_manager
            )
            save_pr_summary(summary)
            print("\n" + "="*60)
            print("RESUMEN DE PR GENERADO:")
            print("="*60)
            print(summary)
            print("="*60)
        
        print("\n🎉 Proceso paso a paso terminado.")
        return True
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupción detectada.")
        # Intentar restaurar stash
        subprocess.run(
            ['git', 'stash', 'pop'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        if rollback_point:
            confirm = input(
                "¿Deseas hacer rollback de los commits creados? (s/N): "
            ).strip().lower()
            if confirm == 's':
                rollback_to_commit(rollback_point)
        
        cleanup_temp_stashes()
        return False
    
    finally:
        if os.path.exists(patch_file):
            os.remove(patch_file)


def get_ollama_model_selection(recommended_model: Optional[str] = None) -> str:
    """
    Permite al usuario seleccionar un modelo de Ollama.
    
    Args:
        recommended_model: Modelo recomendado según recursos del sistema
        
    Returns:
        str: Nombre del modelo seleccionado
    """
    import subprocess
    
    # Intentar listar modelos disponibles
    available_models = []
    try:
        result = subprocess.run(
            ['ollama', 'list'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            # Parsear output de ollama list
            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:  # Saltar header
                if line.strip():
                    # Formato: NAME    SIZE    MODIFIED
                    parts = line.split()
                    if parts:
                        available_models.append(parts[0])
    except Exception:
        pass
    
    if available_models:
        print(f"\n📦 Modelos de Ollama disponibles:")
        for i, model in enumerate(available_models, 1):
            marker = " (recomendado)" if model == recommended_model else ""
            print(f"  {i}. {model}{marker}")
        print()
        
        if recommended_model:
            prompt = f"Selecciona un modelo (1-{len(available_models)}) [{recommended_model}]: "
        else:
            prompt = f"Selecciona un modelo (1-{len(available_models)}): "
        
        try:
            selection = input(prompt).strip()
            if selection:
                try:
                    idx = int(selection) - 1
                    if 0 <= idx < len(available_models):
                        return available_models[idx]
                except ValueError:
                    # Si no es un número, asumir que es el nombre del modelo
                    if selection in available_models:
                        return selection
                    print(f"⚠️  Modelo '{selection}' no encontrado. Usando recomendado.")
            # Si no hay selección, usar recomendado o el primero
            return recommended_model or available_models[0]
        except (EOFError, KeyboardInterrupt):
            return recommended_model or available_models[0] if available_models else "llama3.2:3b"
    else:
        # No hay modelos disponibles, usar recomendado o default
        if recommended_model:
            print(f"\n💡 Usando modelo recomendado: {recommended_model}")
            print("   (No se encontraron modelos instalados. Descarga con: git-split ollama pull <modelo>)")
            return recommended_model
        else:
            print("\n⚠️  No se encontraron modelos de Ollama instalados.")
            print("   Usa: git-split ollama pull llama3.2:3b")
            model_input = input("Ingresa el nombre del modelo [llama3.2:3b]: ").strip()
            return model_input or "llama3.2:3b"


def get_user_context(provider: Optional[str] = None, 
                     model_name: Optional[str] = None) -> Optional[str]:
    """
    Solicita al usuario un contexto general de los cambios para el LLM.
    
    Args:
        provider: Proveedor LLM que se usará
        model_name: Nombre del modelo que se usará
    """
    print("\n" + "="*70)
    print("📝 CONTEXTO PARA CLASIFICACIÓN")
    print("="*70)
    if provider and model_name:
        print(f"🤖 Usando: {provider.upper()} - {model_name}")
    elif provider:
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
                if empty_lines >= 2 or (empty_lines == 1 and not context_lines):
                    break
            else:
                empty_lines = 0
                context_lines.append(line)
        except (EOFError, KeyboardInterrupt):
            break
    
    context = "\n".join(context_lines).strip()
    return context if context else None


def get_user_description() -> Optional[str]:
    """Solicita al usuario una descripción general de los cambios."""
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
                if empty_lines >= 2 or (empty_lines == 1 and not description_lines):
                    break
            else:
                empty_lines = 0
                description_lines.append(line)
        except (EOFError, KeyboardInterrupt):
            break
    
    description = "\n".join(description_lines).strip()
    return description if description else None


def generate_pr_summary(commits: List[Dict[str, str]], 
                        client: Optional[object] = None,
                        user_description: Optional[str] = None,
                        provider: str = "gemini",
                        key_manager: Optional[APIKeyManager] = None) -> str:
    """Genera un resumen automático para Pull Request con rotación de keys."""
    if not commits:
        return ""
    
    commits_text = "\n".join([
        f"- {c['desc']}" for c in commits
    ])
    
    # Calcular max_retries basado en número de keys disponibles
    if HAS_DB and key_manager:
        all_keys = key_manager.list_keys(provider)
        max_retries = max(len(all_keys) * 2, 10) if all_keys else 1
    else:
        max_retries = 1
    
    current_client = client
    used_key_ids = set()
    
    if client and hasattr(client, '_key_id') and client._key_id:
        used_key_ids.add(client._key_id)
    
    # Si tenemos LangChain disponible, usarlo
    is_langchain_client = (
        (HAS_LANGCHAIN and current_client and 
         isinstance(current_client, ChatGoogleGenerativeAI)) or
        (HAS_OLLAMA_LANGCHAIN and current_client and 
         isinstance(current_client, ChatOllama))
    )
    
    if is_langchain_client:
        for attempt in range(max_retries):
            try:
                # Usar prompt desde archivo separado
                if HAS_PROMPTS:
                    prompt_template = get_pr_summary_prompt(user_description)
                else:
                    # Fallback si no se puede importar prompts
                    description_context = ""
                    if user_description:
                        description_context = (
                            f"\n\nDescripción proporcionada por el usuario:\n"
                            f"{user_description}"
                        )
                    prompt_template = (
                        "Genera un resumen profesional para un Pull Request basado "
                        "en estos commits. El resumen debe ser conciso, claro y "
                        "destacar los cambios principales.{description_context}\n\n"
                        "Commits:\n{commits}\n\n"
                        "Resumen (máximo 200 palabras):"
                    )
                
                prompt = ChatPromptTemplate.from_template(prompt_template)
                
                chain = prompt | current_client
                response = chain.invoke({
                    "commits": commits_text
                })
                
                summary = response.content.strip()
                
                # Añadir descripción del usuario si existe
                if user_description:
                    summary = (
                        f"{summary}\n\n## Descripción del Usuario\n\n"
                        f"{user_description}"
                    )
                
                return summary
            except Exception as e:
                if handle_llm_error(e, current_client, provider, key_manager):
                    # Verificar si hemos usado todas las keys disponibles
                    should_wait = False
                    if HAS_DB and key_manager:
                        all_keys = key_manager.list_keys(provider)
                        all_key_ids = {k['id'] for k in all_keys}
                        
                        if (used_key_ids.issuperset(all_key_ids) and 
                            all_key_ids and len(used_key_ids) >= len(all_key_ids)):
                            should_wait = True
                    
                    if should_wait:
                        wait_minutes = int(
                            os.getenv("API_KEY_WAIT_MINUTES", "5")
                        )
                        print(
                            f"\n⚠️  Todas las API keys han alcanzado el límite."
                        )
                        print(
                            f"⏳ Esperando {wait_minutes} minutos antes de "
                            f"reintentar..."
                        )
                        
                        total_seconds = wait_minutes * 60
                        for remaining in range(total_seconds, 0, -30):
                            mins = remaining // 60
                            secs = remaining % 60
                            print(
                                f"   Tiempo restante: {mins:02d}:{secs:02d}",
                                end='\r'
                            )
                            time.sleep(min(30, remaining))
                        
                        print("\n🔄 Reintentando con todas las keys...")
                        used_key_ids.clear()
                    
                    # Rotar a siguiente key
                    current_client = get_llm_client(provider, key_manager)
                    if not current_client:
                        print("❌ No hay más API keys disponibles.")
                        break
                    
                    # Registrar key usada
                    if hasattr(current_client, '_key_id') and current_client._key_id:
                        used_key_ids.add(current_client._key_id)
                    
                    if attempt < max_retries - 1:
                        print(
                            f"🔄 Reintentando con nueva API key "
                            f"(intento {attempt + 2}/{max_retries})..."
                        )
                        continue
                else:
                    print(f"⚠️  Error generando resumen con LLM: {e}")
                    if attempt < max_retries - 1:
                        continue
                    break
    
    # Fallback a resumen simple
    summary = (
        f"## Resumen\n\nEste PR incluye los siguientes cambios:\n\n"
        f"{commits_text}"
    )
    if user_description:
        summary += f"\n\n## Descripción del Usuario\n\n{user_description}"
    return summary
    
    # Resumen simple si no hay LLM
    summary = (
        f"## Resumen\n\nEste PR incluye los siguientes cambios:\n\n"
        f"{commits_text}"
    )
    if user_description:
        summary += f"\n\n## Descripción del Usuario\n\n{user_description}"
    return summary


def save_pr_summary(summary: str, filename: str = "PR_SUMMARY.md") -> None:
    """Guarda el resumen de PR en un archivo."""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(summary)
        print(f"\n📝 Resumen de PR guardado en: {filename}")
    except Exception as e:
        print(f"⚠️  Error guardando resumen: {e}")


def run_tests(test_command: str) -> bool:
    """Ejecuta los tests automáticos del proyecto."""
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
            if result.stderr:
                print(result.stderr)
            return False
    except FileNotFoundError:
        print(f"❌ Comando no encontrado: {test_command}")
        return False
    except Exception as e:
        print(f"❌ Error ejecutando tests: {e}")
        return False


def execute_plan(plan: Dict[int, Dict], 
                 rollback_point: Optional[str] = None,
                 test_command: Optional[str] = None,
                 generate_pr: bool = False,
                 llm_client: Optional[object] = None,
                 user_description: Optional[str] = None,
                 provider: str = "gemini",
                 key_manager: Optional[APIKeyManager] = None) -> bool:
    """Ejecuta el Git Plan con soporte de rollback, tests y PR summary."""
    if rollback_point:
        print(f"\n🛡️  Punto de restauración: {rollback_point[:8]}")
    
    print("\n--- Generando Commits ---")
    
    commits_realizados = 0
    commits_created = []
    
    try:
        for g_id in sorted(plan.keys()):
            data = plan[g_id]
            if not data["hunks"]:
                continue
            
            print(f"Creando commit {g_id}: {data['desc']}...")
            
            if not apply_and_commit(data["hunks"], data['desc']):
                raise Exception(
                    f"Error al crear commit '{data['desc']}'"
                )
            
            commits_realizados += 1
            commits_created.append({"desc": data['desc']})
            print(f"✅ [{commits_realizados}] Commit: {data['desc']}")
        
        # Ejecutar tests si se especificó un comando
        if test_command:
            if not run_tests(test_command):
                raise Exception("Tests fallaron después de los commits")
        
        # Generar resumen de PR si se solicita
        if generate_pr and commits_created:
            print("\n📝 Generando resumen de Pull Request...")
            summary = generate_pr_summary(
                commits_created, llm_client, user_description,
                provider, key_manager
            )
            save_pr_summary(summary)
            print("\n" + "="*60)
            print("RESUMEN DE PR GENERADO:")
            print("="*60)
            print(summary)
            print("="*60)
        
        print("\n🎉 ¡Proceso finalizado con éxito!")
        return True
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupción detectada.")
        if rollback_point:
            confirm = input(
                "¿Deseas hacer rollback de los commits creados? (s/N): "
            ).strip().lower()
            if confirm == 's':
                rollback_to_commit(rollback_point)
        return False
    
    except Exception as e:
        print("\n" + "!"*60)
        print(f"❌ ERROR CRÍTICO: {e}")
        print("!"*60)
        
        if rollback_point:
            print(f"\n🔄 Iniciando rollback a {rollback_point[:8]}...")
            rollback_to_commit(rollback_point)
            print("\n✅ Puedes corregir el problema y volver a ejecutar.")
        else:
            print("\n⚠️  No se pudo hacer rollback automático.")
            print("   Revisa el estado del repositorio manualmente.")
        
        return False


def parse_args():
    """Parsea los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description='GitClassifier: Clasifica y divide cambios de Git en commits semánticos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Usar diff desde archivo con LLM
  python3 git_splitter.py --diff-file diff.patch --use-llm --provider gemini

  # Usar git diff con configuración completa
  python3 git_splitter.py --target main --use-llm --provider gemini --mode step-by-step --generate-pr

  # Modo no interactivo completo
  python3 git_splitter.py --diff-file diff.patch --use-llm --provider gemini \\
    --mode normal --generate-pr --test-cmd "pytest" --execute
        """
    )
    
    # Fuente del diff
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
    
    # Configuración LLM
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
        help='Proveedor LLM (default: auto-detectado desde config)'
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
    
    # Modo de ejecución
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
    
    # Opciones adicionales
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
        help='Saltar verificación de repositorio Git (solo con --diff-file)'
    )
    
    return parser.parse_args()


def read_file_or_text(input_str: str) -> Optional[str]:
    """Lee contenido de un archivo o retorna el texto directamente."""
    if not input_str:
        return None
    
    # Si parece una ruta de archivo y existe, leerlo
    if os.path.exists(input_str) and os.path.isfile(input_str):
        try:
            with open(input_str, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            print(f"⚠️  Error leyendo archivo {input_str}: {e}")
            return input_str  # Fallback al texto directo
    
    return input_str


def main(args: Optional[argparse.Namespace] = None):
    """Función principal del script."""
    temp_branch = None
    original_branch = None
    diff_from_file = False
    
    # Si no se pasan args, usar modo interactivo
    interactive = args is None
    
    # Verificar repositorio Git
    # Si se usa --diff-file con --skip-git-check, no se requiere repo Git
    skip_git_check = args and args.diff_file and args.skip_git_check
    
    if not skip_git_check:
        try:
            subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                check=True,
                capture_output=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            if args and args.diff_file:
                print("⚠️  No estás en un repositorio Git.")
                print("   Usa --skip-git-check para analizar sin repo Git")
                print("   (Nota: no podrás aplicar commits sin un repo Git)")
                sys.exit(1)
            else:
                print("Error: No estás en un repositorio Git.")
                sys.exit(1)
    
    try:
        # Determinar fuente del diff
        if args and args.diff_file:
            use_file = True
            diff_file = args.diff_file
        elif args and args.target:
            use_file = False
            target = args.target
        else:
            # Modo interactivo
            use_file = input(
                "\n¿Usar diff desde archivo? (s/N): "
            ).strip().lower() == 's'
        
        if use_file:
            if interactive:
                diff_file = input(
                    "Introduce la ruta del archivo de diff: "
                ).strip()
            else:
                diff_file = args.diff_file
            
            if not diff_file:
                print("❌ No se especificó un archivo. Abortando.")
                return
            
            diff = read_diff_from_file(diff_file)
            if not diff:
                return
            
            diff_from_file = True
            print(
                "\n⚠️  Modo: Análisis desde archivo. "
                "Los commits solo se aplicarán si el diff es compatible."
            )
        else:
            if interactive:
                target = input(
                    "Introduce la rama target (ej. main): "
                ).strip() or "main"
            else:
                target = args.target
            
            # Verificar si estamos en la misma rama que el target
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
                    return
                # Actualizar current_branch para el resto del proceso
                current_branch = temp_branch
                # Usar diff del working directory ya que la rama temporal
                # apunta al mismo commit que el target
                use_working_dir_diff = True
            
            diff = get_git_diff(target, use_working_dir_diff)
            if not diff:
                print("No hay cambios para procesar.")
                return
        
        hunks = parse_hunks(diff)
        if not hunks:
            print("No se encontraron hunks para procesar.")
            return
        
        print(f"\n📦 Se encontraron {len(hunks)} bloques de cambios.")
        
        # Elegir modo: LLM o manual
        if args and args.use_llm:
            use_llm = True
            # Si no se especifica proveedor, preguntar o usar el default
            if args.provider:
                provider = args.provider
            else:
                # Preguntar por el proveedor incluso en modo no interactivo
                if HAS_RESOURCE_DETECTOR:
                    default_provider = get_default_provider()
                    print(f"\n🤖 Proveedor LLM no especificado.")
                    provider_input = input(
                        f"Proveedor (ollama/gemini/openai) [{default_provider}]: "
                    ).strip().lower()
                    provider = provider_input or default_provider
                else:
                    provider_input = input(
                        "Proveedor (ollama/gemini/openai) [ollama]: "
                    ).strip().lower()
                    provider = provider_input or "ollama"
        elif interactive:
            use_llm = input(
                "\n¿Usar clasificación automática con LLM? (s/N): "
            ).strip().lower() == 's'
            if use_llm:
                # Mostrar proveedor recomendado
                if HAS_RESOURCE_DETECTOR:
                    default_provider = get_default_provider()
                    provider_input = input(
                        f"Proveedor (ollama/gemini/openai) [{default_provider}]: "
                    ).strip().lower()
                    provider = provider_input or default_provider
                else:
                    provider = input(
                        "Proveedor (ollama/gemini/openai) [ollama]: "
                    ).strip().lower() or "ollama"
            else:
                provider = None
        else:
            use_llm = False
            provider = None
        
        if use_llm:
            # Verificar dependencias según el proveedor
            if provider == "ollama":
                if not HAS_OLLAMA_LANGCHAIN and not HAS_OPENAI:
                    print("Error: Ollama requiere langchain-ollama o openai.")
                    print("Instala con: pip install langchain-ollama")
                    print("O instala Ollama con: git-split ollama setup")
                    return
            elif provider == "gemini":
                if not HAS_LANGCHAIN:
                    print("Error: langchain-google-genai no está instalado.")
                    print("Instala con: pip install langchain-google-genai")
                    return
            elif provider == "openai":
                if not HAS_OPENAI:
                    print("Error: openai no está instalado.")
                    print("Instala con: pip install openai")
                    return
            
            # Inicializar key manager si está disponible
            # Nota: Ollama no requiere API keys (es local)
            key_manager = None
            if HAS_DB and provider != "ollama":
                key_manager = APIKeyManager()
                keys = key_manager.list_keys(provider)
                if keys:
                    print(f"📋 Encontradas {len(keys)} API keys para {provider}")
                else:
                    print(f"ℹ️  No hay API keys en BD para {provider}")
                    print(f"   Usa: git-split api-key add {provider}")
            
            # Obtener modelo recomendado antes de mostrar contexto
            model_name = None
            if HAS_RESOURCE_DETECTOR:
                model_name = get_recommended_model(provider)
            
            # Si es Ollama, preguntar por el modelo o listar disponibles
            if provider == "ollama":
                model_name = get_ollama_model_selection(model_name)
            
            # Inicializar cliente LLM temporalmente para obtener el modelo real
            temp_client = get_llm_client(provider, key_manager, model_name=model_name)
            if not temp_client:
                print("Error: No se pudo inicializar el cliente LLM.")
                if provider == "gemini":
                    if not HAS_DB or not key_manager or not keys:
                        print("Asegúrate de tener GOOGLE_API_KEY configurada")
                        print("o añade keys con: python api_key_cli.py add gemini")
                return
            
            # Obtener el modelo real del cliente
            actual_model = model_name
            if hasattr(temp_client, 'model'):
                actual_model = temp_client.model
            elif hasattr(temp_client, '_model'):
                actual_model = temp_client._model
            
            # Obtener contexto del usuario
            # Si se pasa como flag, usarlo; si no, preguntar interactivamente
            if args and args.user_context:
                user_context = read_file_or_text(args.user_context)
            else:
                # Siempre permitir agregar contexto, incluso en modo no interactivo
                user_context = get_user_context(provider, actual_model)
            
            # Usar el cliente ya inicializado
            client = temp_client
            
            print("\n🚀 Analizando cambios globalmente...")
            goals = get_goals_from_llm(
                client, hunks, provider, key_manager, user_context
            )
            
            if not goals:
                print("No se pudieron identificar objetivos. Abortando.")
                return
            
            print(f"✓ Se identificaron {len(goals)} objetivos funcionales.")
            for goal in goals:
                print(f"  {goal['id']}: {goal['description']}")
            print("\n🏷️ Clasificando cambios individualmente...")
            plan = classify_hunks_with_llm(
                client, hunks, goals, provider, key_manager, user_context
            )
            
            display_git_plan(plan)
            
            # Obtener descripción del usuario
            if args and args.user_description:
                user_description = read_file_or_text(args.user_description)
            elif interactive:
                user_description = get_user_description()
            else:
                user_description = None
            
            # Determinar acción
            if args and args.execute:
                action = 'e'
            elif args and args.edit_plan:
                action = 'ed'
            elif interactive:
                action = input(
                    "\n¿Qué deseas hacer? "
                    "(e)jecutar, (ed)itar plan, (c)ancelar [e]: "
                ).strip().lower() or 'e'
            else:
                action = 'c'  # Cancelar si no hay flags
            
            if action == 'e':
                if diff_from_file:
                    print(
                        "\n⚠️  ADVERTENCIA: El diff proviene de un archivo."
                    )
                    print(
                        "   Los commits solo se aplicarán si el diff es "
                        "compatible con el estado actual del repositorio."
                    )
                    confirm_apply = input(
                        "¿Continuar con la aplicación de commits? (s/N): "
                    ).strip().lower() == 's'
                    if not confirm_apply:
                        print("Operación cancelada.")
                        return
                    # No podemos hacer rollback si el diff viene de archivo
                    # porque no hay un punto de referencia válido
                    rollback_point = None
                else:
                    rollback_point = get_current_head()
                
                if args:
                    execution_mode = args.mode  # 'normal' o 'step-by-step'
                    generate_pr_summary = args.generate_pr
                else:
                    mode_input = input(
                        "\nModo de ejecución: "
                        "(n)ormal / (p)aso a paso [n]: "
                    ).strip().lower() or 'n'
                    execution_mode = 'step-by-step' if mode_input == 'p' else 'normal'
                    
                    generate_pr_summary = input(
                        "\n¿Generar resumen de Pull Request? (s/N): "
                    ).strip().lower() == 's'
                
                if execution_mode == 'step-by-step':
                    if step_by_step_execution(
                        plan, rollback_point, generate_pr_summary, 
                        client, user_description, provider, key_manager
                    ):
                        print("\n🎉 ¡Todos los cambios han sido organizados!")
                else:
                    if args and args.test_cmd:
                        test_cmd = args.test_cmd
                    elif interactive:
                        test_cmd = input(
                            "\n¿Ejecutar tests después de los commits? "
                            "(deja vacío para omitir, ej: 'pytest' o 'npm test'): "
                        ).strip() or None
                    else:
                        test_cmd = None
                    
                    if execute_plan(
                        plan, rollback_point, test_cmd, 
                        generate_pr_summary, client, user_description,
                        provider, key_manager
                    ):
                        print("\n🎉 ¡Todos los cambios han sido organizados!")
            elif action == 'ed':
                edited_plan = edit_plan_interactive(plan)
                if edited_plan:
                    display_git_plan(edited_plan)
                    
                    # Solicitar descripción si no se había pedido antes
                    if not user_description:
                        user_description = get_user_description()
                    
                    confirm = input(
                        "\n¿Ejecutar plan editado? (s/N): "
                    ).strip().lower()
                    if confirm == 's':
                        if diff_from_file:
                            print(
                                "\n⚠️  ADVERTENCIA: El diff proviene de un "
                                "archivo."
                            )
                            print(
                                "   Los commits solo se aplicarán si el diff "
                                "es compatible con el estado actual del "
                                "repositorio."
                            )
                            confirm_apply = input(
                                "¿Continuar con la aplicación de commits? "
                                "(s/N): "
                            ).strip().lower() == 's'
                            if not confirm_apply:
                                print("Operación cancelada.")
                                return
                            rollback_point = None
                        else:
                            rollback_point = get_current_head()
                        
                        if args:
                            execution_mode = args.mode
                            generate_pr_summary = args.generate_pr
                        else:
                            mode_input = input(
                                "\nModo de ejecución: "
                                "(n)ormal / (p)aso a paso [n]: "
                            ).strip().lower() or 'n'
                            execution_mode = 'step-by-step' if mode_input == 'p' else 'normal'
                            
                            generate_pr_summary = input(
                                "\n¿Generar resumen de Pull Request? (s/N): "
                            ).strip().lower() == 's'
                        
                        if execution_mode == 'step-by-step':
                            if step_by_step_execution(
                                edited_plan, rollback_point, 
                                generate_pr_summary, client, user_description,
                                provider, key_manager
                            ):
                                print("\n🎉 ¡Todos los cambios han sido organizados!")
                        else:
                            if args and args.test_cmd:
                                test_cmd = args.test_cmd
                            elif interactive:
                                test_cmd = input(
                                    "\n¿Ejecutar tests después de los commits? "
                                    "(deja vacío para omitir): "
                                ).strip() or None
                            else:
                                test_cmd = None
                            
                            if execute_plan(
                                edited_plan, rollback_point, test_cmd,
                                generate_pr_summary, client, user_description,
                                provider, key_manager
                            ):
                                print("\n🎉 ¡Todos los cambios han sido organizados!")
                    else:
                        print("Operación cancelada.")
                else:
                    print("Operación cancelada.")
            else:
                print("Operación cancelada.")
        else:
            # Modo manual (código original simplificado)
            goals: Dict[str, List[Dict[str, str]]] = {}
            
            print("\nModo manual: clasifica cada bloque.")
            for i, hunk in enumerate(hunks):
                print(f"\n[{i+1}/{len(hunks)}] {hunk['file']}")
                goal = input("Objetivo (Enter para omitir): ").strip()
                
                if goal:
                    if goal not in goals:
                        goals[goal] = []
                    goals[goal].append(hunk)
            
            if goals:
                print("\n--- Resumen ---")
                for goal_name, goal_hunks in goals.items():
                    files = set(h['file'] for h in goal_hunks)
                    print(f"{goal_name}: {len(goal_hunks)} hunks, "
                          f"{len(files)} archivos")
                
                confirm = input(
                    "\n¿Proceder con commits? (s/N): "
                ).strip().lower()
                
                if confirm == 's':
                    for goal_name, goal_hunks in goals.items():
                        apply_and_commit(goal_hunks, goal_name)
                    print("\n🎉 ¡Completado!")
            else:
                print("No se seleccionó ningún cambio.")
    
    finally:
        # Limpiar rama temporal si se creó
        if temp_branch and original_branch:
            cleanup_temp_branch(temp_branch, original_branch)


def show_help() -> None:
    """Muestra la ayuda de la herramienta."""
    help_text = """
GitClassifier - Herramienta inteligente para organizar commits

USO:
    git-split [comando] [opciones]

COMANDOS:
    (sin comando)     Ejecuta el clasificador interactivo
    help              Muestra esta ayuda
    api-key           Gestiona API keys de LLMs
    ollama            Configura y gestiona Ollama
                      Subcomandos:
                        add <provider> [name]    Añadir API key
                        list [provider]          Listar API keys
                        delete <id>              Eliminar API key

EJEMPLOS:
    git-split                    # Modo interactivo
    git-split help               # Mostrar ayuda
    git-split api-key add gemini "Mi key"
    git-split api-key list
    git-split api-key delete 1

PROVEEDORES SOPORTADOS:
    ollama    Ollama local (recomendado, por defecto)
    gemini    Google Gemini
    openai    OpenAI

Para más información, visita: https://github.com/tu-repo/git-ai
"""
    print(help_text)


def handle_ollama_command(args: List[str]) -> None:
    """Maneja los comandos de configuración de Ollama."""
    if len(args) < 2:
        print("Uso: git-split ollama <subcomando>")
        print("\nSubcomandos:")
        print("  setup       - Instalar y configurar Ollama")
        print("  status      - Verificar estado de Ollama")
        print("  pull <model> - Descargar un modelo")
        print("  list        - Listar modelos disponibles")
        print("  info        - Mostrar información del sistema y modelos recomendados")
        sys.exit(1)
    
    subcommand = args[1].lower()
    
    if subcommand == 'setup':
        print("🔧 Configurando Ollama...")
        print()
        
        # Verificar si Ollama está instalado
        try:
            result = subprocess.run(
                ['ollama', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print("✅ Ollama ya está instalado")
                print(f"   Versión: {result.stdout.strip()}")
            else:
                print("⚠️  Ollama no está instalado o no está en PATH")
                print()
                print("Para instalar Ollama:")
                print("  macOS:   brew install ollama")
                print("  Linux:  curl -fsSL https://ollama.com/install.sh | sh")
                print("  Windows: Descarga desde https://ollama.com/download")
                sys.exit(1)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("⚠️  Ollama no está instalado o no está en PATH")
            print()
            print("Para instalar Ollama:")
            print("  macOS:   brew install ollama")
            print("  Linux:  curl -fsSL https://ollama.com/install.sh | sh")
            print("  Windows: Descarga desde https://ollama.com/download")
            sys.exit(1)
        
        # Verificar si el servicio está corriendo
        try:
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print("✅ Servicio de Ollama está corriendo")
            else:
                print("⚠️  El servicio de Ollama no está corriendo")
                print("   Inicia el servicio con: ollama serve")
                sys.exit(1)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("⚠️  No se pudo conectar al servicio de Ollama")
            print("   Asegúrate de que Ollama esté corriendo:")
            print("   - En macOS/Linux: ollama serve")
            print("   - O inicia la aplicación Ollama")
            sys.exit(1)
        
        # Verificar modelos instalados
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
                    if HAS_RESOURCE_DETECTOR:
                        scale = detect_resource_scale()
                        recommended = get_recommended_model("ollama", scale=scale)
                        if recommended:
                            print(f"💡 Modelo recomendado para tu sistema: {recommended}")
                            print(f"   Descarga con: git-split ollama pull {recommended}")
            else:
                print("   (no se pudo obtener la lista)")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Verificar dependencias de Python
        print()
        print("📚 Verificando dependencias de Python...")
        if HAS_OLLAMA_LANGCHAIN:
            print("✅ langchain-ollama está instalado")
        else:
            print("⚠️  langchain-ollama no está instalado")
            print("   Instala con: pip install langchain-ollama")
        
        if HAS_OPENAI:
            print("✅ openai está instalado (fallback disponible)")
        else:
            print("⚠️  openai no está instalado (recomendado para fallback)")
            print("   Instala con: pip install openai")
        
        print()
        print("✅ Configuración completada")
        if HAS_RESOURCE_DETECTOR:
            print()
            print_system_info()
    
    elif subcommand == 'status':
        print("🔍 Verificando estado de Ollama...")
        print()
        
        # Verificar instalación
        try:
            result = subprocess.run(
                ['ollama', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"✅ Ollama instalado: {result.stdout.strip()}")
            else:
                print("❌ Ollama no está instalado")
                return
        except Exception:
            print("❌ Ollama no está instalado")
            return
        
        # Verificar servicio
        try:
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print("✅ Servicio de Ollama está corriendo")
            else:
                print("❌ Servicio de Ollama no está corriendo")
                return
        except Exception:
            print("❌ No se pudo conectar al servicio de Ollama")
            return
        
        # Listar modelos
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
                print(result.stdout.strip() or "   (ninguno)")
            else:
                print("   (error al obtener lista)")
        except Exception as e:
            print(f"   Error: {e}")
    
    elif subcommand == 'pull':
        if len(args) < 3:
            print("❌ Error: Especifica el nombre del modelo")
            print("   Ejemplo: git-split ollama pull llama3.2:3b")
            sys.exit(1)
        
        model_name = args[2]
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
            else:
                print(f"\n❌ Error al descargar modelo {model_name}")
                sys.exit(1)
        except KeyboardInterrupt:
            print("\n⚠️  Descarga cancelada por el usuario")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Error: {e}")
            sys.exit(1)
    
    elif subcommand == 'list':
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
            else:
                print("❌ Error al obtener lista de modelos")
                sys.exit(1)
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)
    
    elif subcommand == 'info':
        if HAS_RESOURCE_DETECTOR:
            print_system_info()
        else:
            print("⚠️  resource_detector no está disponible")
            print("   Asegúrate de que resource_detector.py esté en el mismo directorio")
    
    else:
        print(f"❌ Subcomando desconocido: {subcommand}")
        print("   Usa: setup, status, pull, list o info")
        sys.exit(1)


def handle_api_key_command(args: List[str]) -> None:
    """Maneja los comandos de gestión de API keys."""
    if not HAS_DB:
        print("❌ Error: db_manager no está disponible.")
        print("   Asegúrate de que db_manager.py esté en el mismo directorio.")
        sys.exit(1)
    
    manager = APIKeyManager()
    
    if len(args) < 2:
        print("Uso: git-split api-key <subcomando> [opciones]")
        print("\nSubcomandos:")
        print("  add <provider> [name]    - Añadir API key")
        print("  list [provider]           - Listar API keys")
        print("  delete <id>               - Eliminar API key")
        sys.exit(1)
    
    subcommand = args[1].lower()
    
    if subcommand == 'add':
        if len(args) < 3:
            print("❌ Error: Especifica el provider (gemini/openai/ollama)")
            sys.exit(1)
        provider = args[2]
        name = args[3] if len(args) > 3 else None
        
        print(f"\nAñadiendo API key para {provider}")
        if name:
            print(f"Nombre: {name}")
        
        api_key = getpass.getpass("API Key (se ocultará): ")
        if not api_key:
            print("❌ API key vacía. Operación cancelada.")
            sys.exit(1)
        
        if manager.add_key(provider, api_key, name):
            print(f"✅ API key añadida exitosamente para {provider}")
        else:
            print(f"❌ Error: La API key ya existe para {provider}")
            sys.exit(1)
    
    elif subcommand == 'list':
        provider = args[2] if len(args) > 2 else None
        keys = manager.list_keys(provider)
        
        if not keys:
            provider_msg = f" para {provider}" if provider else ""
            print(f"\n📭 No hay API keys activas{provider_msg}.")
            return
        
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
    
    elif subcommand == 'delete':
        if len(args) < 3:
            print("❌ Error: Especifica el ID de la API key")
            sys.exit(1)
        
        try:
            key_id = int(args[2])
            key = manager.get_key_by_id(key_id)
            
            if not key:
                print(f"❌ No se encontró API key con ID {key_id}")
                sys.exit(1)
            
            if not key['is_active']:
                print(f"⚠️  La API key {key_id} ya está desactivada.")
                return
            
            name_str = f" - {key['name']}" if key['name'] else ""
            confirm = input(
                f"\n¿Eliminar API key {key_id} "
                f"({key['provider']}{name_str})? (s/N): "
            ).strip().lower()
            
            if confirm == 's':
                if manager.delete_key(key_id):
                    print(f"✅ API key {key_id} eliminada.")
                else:
                    print(f"❌ Error al eliminar API key {key_id}")
                    sys.exit(1)
            else:
                print("Operación cancelada.")
        
        except ValueError:
            print("❌ Error: El ID debe ser un número")
            sys.exit(1)
    
    else:
        print(f"❌ Subcomando desconocido: {subcommand}")
        print("   Usa: add, list o delete")
        sys.exit(1)


def main_cli() -> None:
    """Punto de entrada principal de la CLI."""
    # Manejar comandos especiales (help, api-key) antes de parsear
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'help':
            show_help()
            return
        elif command == 'api-key':
            handle_api_key_command(sys.argv[1:])
            return
        elif command == 'ollama':
            handle_ollama_command(sys.argv[1:])
            return
    
    # Parsear argumentos (argparse maneja --help y -h automáticamente)
    try:
        args = parse_args()
    except SystemExit:
        # argparse ya mostró el mensaje de ayuda o error
        return
    
    # Si hay argumentos de configuración, usar modo no interactivo
    # Si no hay argumentos, usar modo interactivo
    has_config_args = any(
        arg.startswith('--') and arg not in ['--help', '-h']
        for arg in sys.argv[1:]
    ) or any(
        arg in ['-f', '-t', '-l', '-p', '-c', '-d', '-m', '-e', '-g']
        for arg in sys.argv[1:]
    )
    
    if has_config_args:
        main(args)
    else:
        main(None)  # Modo interactivo


if __name__ == "__main__":
    main_cli()
