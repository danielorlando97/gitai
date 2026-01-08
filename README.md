# GitClassifier

Herramienta inteligente para clasificar y dividir cambios de Git en commits semánticos usando LLM.

**CLI integral** con gestión de API keys, rotación automática y múltiples modos de ejecución.

## Características

- 🔍 **Análisis Global**: El LLM analiza todos los cambios para identificar objetivos funcionales
- 🏷️ **Clasificación Automática**: Cada bloque de cambios se asigna automáticamente a un objetivo
- 📋 **Git Plan**: Vista previa del plan de commits antes de ejecutar
- 🔄 **Modo Manual**: Opción para clasificar manualmente si prefieres control total
- 🛠️ **LangChain Integration**: Usa LangChain con Pydantic para estructuración robusta de datos
- ⚡ **Gemini 1.5 Flash**: Modelo rápido y económico por defecto
- 📝 **Generación de PR Summary**: Crea automáticamente un resumen profesional para Pull Requests
- 🔑 **CLI Integral**: Gestión de API keys integrada con comandos `api-key` y `help`
- 🔄 **Rotación Automática**: Cambia automáticamente de API key cuando se alcanzan límites

## Instalación

### Instalación Rápida

```bash
./install.sh
```

Este script:
- Instala todas las dependencias
- Hace el script ejecutable
- Opcionalmente crea un alias `git-split` global

### Instalación Manual

```bash
pip install -r requirements.txt
chmod +x src/main.py
```

## Configuración

### Gestión de API Keys con SQLite (Recomendado)

La herramienta incluye un sistema de gestión de API keys con SQLite que permite:

- ✅ **Múltiples API keys**: Añade varias keys para el mismo provider
- ✅ **Rotación automática**: Cambia automáticamente cuando se alcanza el rate limit
- ✅ **Gestión centralizada**: Todas las keys en una base de datos local
- ✅ **Historial de errores**: Registra errores para evitar keys problemáticas

#### Comandos de gestión de API keys:

```bash
# Añadir una API key
git-split api-key add gemini "Mi key principal"
git-split api-key add gemini "Key de respaldo"

# Listar todas las keys
git-split api-key list
git-split api-key list gemini  # Solo keys de Gemini

# Eliminar una key
git-split api-key delete 1

# Ver ayuda
git-split help
```

#### Rotación automática:

Cuando una API key alcanza su límite de rate/quota:
1. El sistema detecta el error automáticamente
2. Registra el error en la base de datos
3. Cambia a la siguiente key disponible
4. Reintenta la operación automáticamente
5. Evita usar keys con errores recientes (últimos 5 minutos)

#### Espera automática cuando todas las keys fallan:

Si todas las API keys han alcanzado su límite para una misma operación:
1. El sistema detecta que todas las keys han sido probadas
2. Espera automáticamente (por defecto 5 minutos, configurable)
3. Muestra un contador de tiempo restante
4. Reintenta con todas las keys después de la espera

Configuración:
```bash
export API_KEY_WAIT_MINUTES=5  # Minutos a esperar (por defecto: 5)
```

### Configuración tradicional (Variables de entorno)

Si prefieres usar variables de entorno en lugar de la base de datos:

#### Gemini (Recomendado - Usa LangChain)

```bash
export GOOGLE_API_KEY="tu-api-key-aqui"
export GEMINI_MODEL="gemini-1.5-flash"  # Opcional
```

**Ventajas de Gemini con LangChain:**
- ✅ Estructuración automática con Pydantic (sin errores de parseo JSON)
- ✅ Más económico y rápido (Gemini 1.5 Flash)
- ✅ Fácil cambio de modelos
- ✅ Encadenamiento de operaciones simplificado

#### OpenAI (Alternativa)

```bash
export OPENAI_API_KEY="tu-api-key-aqui"
export OPENAI_MODEL="gpt-4o-mini"  # Opcional
```

#### Ollama (Local)

```bash
export OLLAMA_BASE_URL="http://localhost:11434/v1"  # Opcional
```

Asegúrate de tener Ollama corriendo localmente.

**Nota**: Si hay API keys en la base de datos, estas tienen prioridad sobre las variables de entorno.

## Uso

### Modo Interactivo (Por defecto)

```bash
git-split
# O
python src/main.py
```

El script te pedirá:
1. **Fuente del diff**: Usar diff desde archivo o desde git (rama target)
2. Si eliges archivo: La ruta al archivo de diff
3. Si eliges git: La rama target (por defecto: `main`)
4. Si quieres usar clasificación automática con LLM
5. El proveedor (Gemini por defecto, OpenAI u Ollama)
6. Confirmación del Git Plan antes de ejecutar

### Usar Diff desde Archivo

Puedes analizar un diff guardado en un archivo en lugar de usar comandos de git:

```bash
git-split
# ¿Usar diff desde archivo? (s/N): s
# Introduce la ruta del archivo de diff: /ruta/a/mi/diff.patch
```

**Ventajas:**
- Analiza diffs guardados previamente
- Útil para revisar cambios de otros o de PRs
- Permite analizar diffs sin estar en el repositorio original

**Advertencias:**
- Los commits solo se aplicarán si el diff es compatible con el estado actual del repositorio
- No se puede hacer rollback automático cuando el diff proviene de un archivo (no hay punto de referencia en git)
- El archivo debe contener un diff válido en formato estándar de git

### Comandos CLI

```bash
# Ver ayuda
git-split help

# Gestionar API keys
git-split api-key add gemini "Mi key"
git-split api-key list
git-split api-key delete 1
```

## Flujo de Trabajo

1. **Extracción**: Obtiene todos los hunks del diff
2. **Análisis Global (LLM)**: Identifica objetivos funcionales
3. **Clasificación (LLM)**: Asigna cada hunk a un objetivo
4. **Revisión Humana**: Muestra el Git Plan para confirmar
5. **Edición Opcional**: Permite mover hunks entre commits
6. **Ejecución**: Crea los commits automáticamente

## Edición del Plan

Después de que el LLM genera el plan, puedes editarlo manualmente:

- `m [id_origen] [id_destino] [archivo]` - Mover archivo entre commits
- `r [id] [nuevo mensaje]` - Renombrar commit
- `d [id]` - Descartar commit del plan
- `n [mensaje]` - Crear nuevo commit vacío
- `e` - Ejecutar commits (salir del editor)
- `q` - Salir sin hacer nada

### Ejemplo de Edición

```
ID [1] 📝 Mensaje: Fix authentication bug
   • auth.py (3 hunk(s))
   • login.py (2 hunk(s))

ID [2] 📝 Mensaje: Add user profile endpoint
   • api.py (5 hunk(s))
   • models.py (2 hunk(s))

> m 1 2 login.py
✅ Movido login.py del commit 1 al 2
```

## Mecanismo de Rollback

La herramienta incluye un sistema de seguridad automático:

- **Guardado del estado**: Antes de ejecutar, guarda el SHA del HEAD actual
- **Rollback con `--soft`**: Si un commit falla, deshace commits pero **mantiene tus cambios intactos** en los archivos
- **Protección contra interrupciones**: Si presionas Ctrl+C, pregunta si deseas hacer rollback
- **Limpieza del index**: Antes de cada commit, limpia el staging area para evitar conflictos

Esto garantiza que tu repositorio siempre quede en un estado consistente, incluso si algo sale mal durante la ejecución. Tus cambios nunca se perderán gracias al uso de `git reset --soft`.

## Modos de Ejecución

### Modo Normal

Ejecuta todos los commits automáticamente:

- Crea todos los commits de una vez
- Opción de ejecutar tests al final
- Rollback automático si algo falla

### Modo Paso a Paso (Isolation Mode)

Aísla visualmente cada commit antes de confirmarlo:

- **Aislamiento visual**: Usa `git stash --keep-index` para que solo veas los cambios del commit actual en tu editor
- **Revisión individual**: Puedes probar, compilar o revisar cada commit aisladamente
- **Control total**: Para cada commit puedes:
  - `c` - Confirmar y continuar
  - `s` - Saltar este commit
  - `a` - Abortar todo y hacer rollback

**Ventajas del modo paso a paso:**
- Pruebas unitarias por commit: Ejecuta tests específicos para cada cambio
- Revisión visual limpia: Sin el "ruido" de otros cambios en el editor
- Detección temprana de dependencias: Si un commit no compila, lo detectas antes de confirmarlo

Ejemplo:
```
Modo de ejecución: (n)ormal / (p)aso a paso [n]: p

🛠️  MODO PASO A PASO ACTIVADO
Tu código se filtrará para que veas solo el commit actual.

📦 Preparando Commit 1: Fix authentication bug
👉 Ahora puedes revisar/probar el código en tu editor.
Solo los cambios de 'Fix authentication bug' están presentes.

¿Confirmar commit 1? [c]onfirmar / [s]altar / [a]bortar todo: c
✅ [1] Commit realizado.
```

## Ejecución de Tests

En modo normal, después de crear todos los commits puedes ejecutar tests:

- Si los tests fallan, se hace rollback automático de todos los commits
- Soporta cualquier comando de tests (pytest, npm test, make test, etc.)
- Opcional: puedes omitir los tests si no los necesitas

Ejemplo:
```
¿Ejecutar tests después de los commits? (deja vacío para omitir, ej: 'pytest' o 'npm test'): pytest

🧪 Ejecutando tests: pytest
✅ Todos los tests pasaron.
```

## Contexto para Clasificación

Cuando eliges usar clasificación automática con LLM, puedes proporcionar un contexto general de todos los cambios:

- **Antes de la clasificación**: Se solicita justo después de elegir usar LLM, antes de que el modelo analice los cambios
- **Mejora la precisión**: El LLM usa este contexto para entender mejor el propósito general de los cambios
- **Opcional**: Puedes escribir un contexto detallado o dejarlo vacío
- **Multilínea**: Soporta contextos de múltiples líneas

Para finalizar el contexto, presiona Enter dos veces o deja la primera línea vacía.

**Ejemplo:**
```
¿Usar clasificación automática con LLM? (s/N): s
Proveedor (gemini/openai/ollama) [gemini]: 

📝 CONTEXTO PARA CLASIFICACIÓN
======================================================================
Opcional: Explica de forma general todos los cambios que están 
actualmente en el diff.
Este contexto ayudará al LLM a clasificar mejor los cambios. 
Presiona Enter dos veces para finalizar o dejar vacío.
======================================================================
Este PR refactoriza el sistema de autenticación para usar JWT tokens
y añade nuevas funcionalidades de perfil de usuario. También corrige
varios bugs en la validación de formularios.

[Enter dos veces para finalizar]

🚀 Analizando cambios globalmente...
```

## Descripción de Cambios (para PR)

Después de mostrar el Git Plan, puedes añadir una descripción general de todos los cambios que se incluirá en el resumen de PR:

- **Opcional**: Puedes escribir una descripción detallada o dejarla vacía
- **Multilínea**: Soporta descripciones de múltiples líneas
- **Integrada en PR**: Se incluye automáticamente en el resumen de PR si se genera

Para finalizar la descripción, presiona Enter dos veces o deja la primera línea vacía.

## Generación de Resumen de Pull Request

Después de crear los commits, puedes generar automáticamente un resumen profesional para tu Pull Request:

- **Generación Inteligente**: Usa el LLM para crear un resumen conciso y profesional
- **Incluye tu descripción**: Si proporcionaste una descripción, se añade al resumen
- **Guardado Automático**: Se guarda en `PR_SUMMARY.md` para copiar y pegar
- **Visualización**: Muestra el resumen en la terminal antes de guardarlo
- **Opcional**: Puedes omitir la generación si no la necesitas

Ejemplo:
```
📋 GIT PLAN PROPUESTO
======================================================================
[Commit 1]: Fix authentication bug in login flow
[Commit 2]: Add user profile endpoint
======================================================================

📝 DESCRIPCIÓN DE CAMBIOS
======================================================================
Opcional: Escribe una descripción general de todos los cambios 
realizados.
Presiona Enter dos veces para finalizar o dejar vacío.
======================================================================
Este PR mejora el sistema de autenticación y añade funcionalidades
de perfil de usuario. Los cambios incluyen mejoras de seguridad
y nuevas APIs para gestión de perfiles.

[Enter dos veces para finalizar]

¿Qué deseas hacer? (e)jecutar, (ed)itar plan, (c)ancelar [e]: e
¿Generar resumen de Pull Request? (s/N): s

📝 Generando resumen de Pull Request...

============================================================
RESUMEN DE PR GENERADO:
============================================================
## Resumen

Este PR implementa mejoras significativas en el sistema de 
autenticación y añade nuevas funcionalidades de perfil de usuario.

### Cambios Principales

- Refactorización del flujo de login para mejorar la seguridad
- Corrección de bugs en la validación de tokens
- Implementación de endpoint de perfil de usuario

## Descripción del Usuario

Este PR mejora el sistema de autenticación y añade funcionalidades
de perfil de usuario. Los cambios incluyen mejoras de seguridad
y nuevas APIs para gestión de perfiles.
============================================================

📝 Resumen de PR guardado en: PR_SUMMARY.md
```

## Ejemplo

```
📦 Se encontraron 15 bloques de cambios.
¿Usar clasificación automática con LLM? (s/N): s
Proveedor (gemini/openai/ollama) [gemini]: gemini

🚀 Analizando cambios globalmente...
✓ Se identificaron 3 objetivos funcionales.

🏷️ Clasificando cambios individualmente...
Clasificando cambios...

📋 GIT PLAN PROPUESTO
======================================================================
[Commit 1]: Fix authentication bug in login flow
  Hunks: 5 | Archivos: 2
  Archivos: auth.py, login.py

[Commit 2]: Add user profile endpoint
  Hunks: 7 | Archivos: 3
  Archivos: api.py, models.py, routes.py

[Commit 3]: Refactor database connection handling
  Hunks: 3 | Archivos: 1
  Archivos: db.py
======================================================================

¿Qué deseas hacer? (e)jecutar, (ed)itar plan, (c)ancelar [e]: ed

📋 ESTADO ACTUAL DEL GIT PLAN
============================================================

ID [1] 📝 Mensaje: Fix authentication bug in login flow
   • auth.py (3 hunk(s))
   • login.py (2 hunk(s))

ID [2] 📝 Mensaje: Add user profile endpoint
   • api.py (5 hunk(s))
   • models.py (2 hunk(s))

Comandos disponibles:
  m [id_origen] [id_destino] [archivo]  -> Mover archivo
  r [id] [nuevo mensaje]                -> Renombrar commit
  d [id]                                 -> Descartar commit
  n [mensaje]                            -> Nuevo commit
  e                                      -> EJECUTAR COMMITS
  q                                      -> Salir sin hacer nada

> m 1 2 login.py
✅ Movido login.py del commit 1 al 2

> e

--- Generando Commits ---
Creando commit 1: Fix authentication bug in login flow...
✓ Commit 'Fix authentication bug in login flow' creado.
Creando commit 2: Add user profile endpoint...
✓ Commit 'Add user profile endpoint' creado.

🎉 ¡Todos los cambios han sido organizados!
```

## ¿Por qué LangChain?

La herramienta usa **LangChain** con **Pydantic** para:

1. **Estructuración Robusta**: `PydanticOutputParser` garantiza que el LLM devuelva JSON válido según el esquema definido, eliminando errores de parseo
2. **Facilidad de Cambio**: Cambiar de Gemini a otro modelo es solo una línea de código
3. **Encadenamiento Limpio**: La sintaxis `prompt | llm | parser` hace el código más legible y mantenible
4. **Few-shot Learning**: En el futuro, puedes añadir ejemplos para mejorar la clasificación

## Manejo de Ramas

Si estás en la misma rama que el target, el script automáticamente:

1. **Crea una rama temporal** con un ID único (formato: `git-split-draft-{timestamp}-{uuid}`)
2. **Cambia a esa rama** para analizar los cambios
3. **Al finalizar**, vuelve a la rama original
4. **Elimina la rama temporal** automáticamente

Esto permite analizar cambios incluso cuando estás en la misma rama que el target, sin afectar tu rama de trabajo.

Ejemplo:
```
⚠️  Estás en la misma rama que el target (main).
   Creando rama temporal para analizar cambios...
🌿 Creada rama temporal: git-split-draft-1234567890-a1b2c3d4
...
✅ Vuelto a rama: main
🗑️  Rama temporal eliminada: git-split-draft-1234567890-a1b2c3d4
```

## Notas

- El script usa `git apply --cached` para aplicar cambios sin modificar archivos físicos
- Los hunks no clasificados se omiten automáticamente
- Puedes cancelar en cualquier momento antes de la ejecución
- El modo paso a paso maneja automáticamente archivos nuevos (untracked) con `git stash -u`
- Si hay conflictos al restaurar cambios en modo paso a paso, el script te avisará para resolverlos manualmente
- Si LangChain no está disponible, el script hace fallback a OpenAI/Ollama con el método tradicional
- Si se crea una rama temporal, se limpia automáticamente al finalizar (incluso si hay errores)

