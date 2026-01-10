# Documentación de GitClassifier

Bienvenido a la documentación completa de **GitClassifier**, una herramienta inteligente para clasificar y dividir cambios de Git en commits semánticos usando modelos de lenguaje (LLM).

## Índice de Documentación

### 📚 Guías Principales

1. **[Guía de Inicio Rápido](./getting-started.md)**
   - Comienza a usar GitClassifier en minutos
   - Ejemplos básicos y casos de uso comunes

2. **[Guía de Instalación](./installation.md)**
   - Requisitos del sistema
   - Instalación paso a paso
   - Configuración inicial

3. **[Guía del Usuario](./user-guide.md)**
   - Uso completo de todas las funcionalidades
   - Modos de ejecución
   - Gestión de commits y planes
   - Generación de resúmenes de PR

4. **[Referencia de CLI](./cli-reference.md)**
   - Documentación completa de todos los comandos
   - Opciones y argumentos
   - Ejemplos de uso

5. **[Guía de Configuración](./configuration.md)**
   - Gestión de API keys
   - Configuración de proveedores LLM
   - Variables de entorno
   - Personalización avanzada

6. **[Uso Avanzado](./advanced-usage.md)**
   - Flujos de trabajo complejos
   - Integración con otros sistemas
   - Automatización y scripting
   - Mejores prácticas

7. **[Solución de Problemas](./troubleshooting.md)**
   - Problemas comunes y soluciones
   - Errores frecuentes
   - Debugging y diagnóstico

## ¿Qué es GitClassifier?

GitClassifier es una herramienta CLI que utiliza modelos de lenguaje (LLM) para:

- **Analizar cambios de Git** de forma inteligente
- **Identificar objetivos funcionales** en tus cambios
- **Clasificar automáticamente** bloques de código (hunks) en commits semánticos
- **Generar planes de commits** antes de ejecutarlos
- **Crear resúmenes profesionales** para Pull Requests

## Características Principales

### 🔍 Análisis Inteligente
- Análisis global de todos los cambios para identificar objetivos funcionales
- Clasificación automática de cada bloque de cambios
- Soporte para contexto del usuario para mejorar la precisión

### 🏷️ Clasificación Automática
- Usa LLMs (Gemini, OpenAI, Ollama) para clasificar cambios
- Identifica objetivos funcionales automáticamente
- Asigna hunks a commits semánticos

### 📋 Git Plan
- Vista previa del plan de commits antes de ejecutar
- Edición manual del plan si es necesario
- Revisión y confirmación antes de aplicar cambios

### 🔄 Múltiples Modos de Ejecución
- **Modo Normal**: Ejecuta todos los commits automáticamente
- **Modo Paso a Paso**: Revisa cada commit individualmente antes de confirmarlo

### 🛠️ Gestión de API Keys
- Sistema integrado de gestión de API keys con SQLite
- Rotación automática cuando se alcanzan límites
- Soporte para múltiples keys por proveedor

### 📝 Generación de PR Summary
- Crea automáticamente resúmenes profesionales para Pull Requests
- Incluye descripción del usuario si se proporciona
- Guardado automático en archivo

## Flujo de Trabajo Típico

```
1. Hacer cambios en tu código
2. Ejecutar git-split
3. El LLM analiza los cambios y genera un plan
4. Revisar y editar el plan si es necesario
5. Confirmar y ejecutar los commits
6. (Opcional) Generar resumen de PR
```

## Próximos Pasos

- Si eres nuevo, comienza con la [Guía de Inicio Rápido](./getting-started.md)
- Para instalación detallada, consulta la [Guía de Instalación](./installation.md)
- Para uso completo, lee la [Guía del Usuario](./user-guide.md)

## Recursos Adicionales

- [Architecture.md](../ARCHITECTURE.md) - Arquitectura del proyecto
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Guía para contribuir
- [README.md](../README.md) - Documentación general del proyecto
