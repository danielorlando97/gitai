#!/usr/bin/env python3
"""
Prompts para GitClassifier - Clasificación semántica de cambios Git.
"""

from typing import Optional


def get_goals_identification_prompt(user_context: Optional[str] = None) -> str:
    """
    Genera el prompt para identificar objetivos funcionales globales.
    
    Args:
        user_context: Contexto adicional proporcionado por el usuario
        
    Returns:
        Template del prompt para identificar objetivos
    """
    context_section = ""
    if user_context:
        context_section = (
            f"\n\nContexto proporcionado por el usuario sobre los cambios:\n"
            f"{user_context}\n"
        )
    
    prompt = (
        "Eres un arquitecto de software experto en Git y organización de código. "
        "Analiza estos cambios de código y agrúpalos en objetivos funcionales "
        "lógicos y ATÓMICOS (commits pequeños y enfocados).\n"
        "\n"
        "REGLAS CRÍTICAS - LEE CON ATENCIÓN:\n"
        "1. Cada objetivo debe ser ATÓMICO: máximo 1-2 archivos relacionados o "
        "una funcionalidad específica y pequeña\n"
        "2. Si un cambio grande tiene múltiples partes independientes, "
        "DIVÍDELO OBLIGATORIAMENTE en objetivos separados\n"
        "3. Agrupa SOLO cambios que están directamente relacionados y "
        "dependen unos de otros (no solo porque son del mismo tipo)\n"
        "4. Prefiere SIEMPRE más objetivos pequeños que pocos objetivos grandes\n"
        "5. Cada objetivo debe poder ser entendido y revisado independientemente\n"
        "6. Si un objetivo tiene más de 3-4 archivos modificados, DIVÍDELO\n"
        "7. Si un objetivo combina múltiples comandos/features, DIVÍDELO\n"
        "\n"
        "Ejemplos de BUENOS objetivos (ATÓMICOS):\n"
        "- 'feat: Add authentication endpoint'\n"
        "- 'feat: Add rules command to optuna'\n"
        "- 'feat: Add trees command to optuna'\n"
        "- 'fix: Resolve memory leak in data processor'\n"
        "- 'refactor: Extract validation logic to separate module'\n"
        "\n"
        "Ejemplos de MALOS objetivos (demasiado grandes - NO HACER):\n"
        "- 'feat: Add multiple commands to optuna' (debe dividirse en uno por comando)\n"
        "- 'feat: Add multiple endpoints and refactor database' (demasiado amplio)\n"
        "- 'chore: Update all dependencies and fix all bugs' (múltiples cosas)\n"
        "- 'feat: Add commands and implement class imbalance detection' (dos cosas diferentes)\n"
        "\n"
        f"{context_section}"
        "\n"
        "Analiza los cambios y crea objetivos ATÓMICOS y bien definidos. "
        "Si dudas entre crear uno grande o varios pequeños, SIEMPRE elige varios pequeños.\n"
        "\n"
        "Cambios:\n"
        "{diff_summary}"
    )
    
    return prompt


def get_hunk_classification_prompt(user_context: Optional[str] = None) -> str:
    """
    Genera el prompt para clasificar un hunk individual en un objetivo.
    
    Args:
        user_context: Contexto adicional proporcionado por el usuario
        
    Returns:
        Template del prompt para clasificar hunks
    """
    context_section = ""
    if user_context:
        context_section = (
            f"\n\nContexto del usuario sobre los cambios: {user_context}\n"
        )
    
    prompt = (
        "Analiza el siguiente fragmento de código (hunk) y decide a qué ID de "
        "objetivo pertenece.{user_context}\n"
        "\n"
        "INSTRUCCIONES:\n"
        "1. El hunk debe pertenecer al objetivo que mejor describe su propósito\n"
        "2. Si el hunk tiene múltiples propósitos, elige el MÁS IMPORTANTE\n"
        "3. Si no encaja claramente en ningún objetivo, elige el más cercano\n"
        "\n"
        "Objetivos disponibles:\n"
        "{goals}\n"
        "\n"
        "Fragmento:\n"
        "{hunk}\n"
        "\n"
        "Responde SOLO con el número del ID."
    )
    
    return prompt


def get_pr_summary_prompt(user_description: Optional[str] = None) -> str:
    """
    Genera el prompt para crear un resumen de Pull Request.
    
    Args:
        user_description: Descripción adicional proporcionada por el usuario
        
    Returns:
        Template del prompt para generar resumen de PR
    """
    description_context = ""
    if user_description:
        description_context = (
            f"\n\nDescripción proporcionada por el usuario:\n"
            f"{user_description}"
        )
    
    prompt = (
        "Genera un resumen profesional para un Pull Request basado en estos "
        "commits. El resumen debe ser conciso, claro y destacar los cambios "
        "principales.{description_context}\n"
        "\n"
        "Commits:\n"
        "{commits}\n"
        "\n"
        "Resumen (máximo 200 palabras):"
    )
    
    return prompt

