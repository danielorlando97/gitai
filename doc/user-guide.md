# Guía del Usuario

Esta guía completa cubre todas las funcionalidades de GitClassifier y cómo usarlas efectivamente.

## Tabla de Contenidos

1. [Conceptos Básicos](#conceptos-básicos)
2. [Modo Interactivo](#modo-interactivo)
3. [Modo de Línea de Comandos](#modo-de-línea-de-comandos)
4. [Análisis de Cambios](#análisis-de-cambios)
5. [Clasificación con LLM](#clasificación-con-llm)
6. [Git Plan](#git-plan)
7. [Modos de Ejecución](#modos-de-ejecución)
8. [Edición del Plan](#edición-del-plan)
9. [Generación de PR Summary](#generación-de-pr-summary)
10. [Gestión de API Keys](#gestión-de-api-keys)
11. [Manejo de Ramas](#manejo-de-ramas)
12. [Rollback y Seguridad](#rollback-y-seguridad)

## Conceptos Básicos

### ¿Qué hace GitClassifier?

GitClassifier analiza tus cambios de Git y los organiza automáticamente en commits semánticos usando modelos de lenguaje (LLM). El proceso incluye:

1. **Extracción**: Obtiene todos los bloques de cambios (hunks) del diff
2. **Análisis Global**: El LLM identifica objetivos funcionales en los cambios
3. **Clasificación**: Cada hunk se asigna a un objetivo funcional
4. **Planificación**: Se genera un plan de commits antes de ejecutar
5. **Ejecución**: Los commits se crean automáticamente

### Terminología

- **Hunk**: Un bloque de cambios en un archivo (añadido, modificado o eliminado)
- **Goal (Objetivo)**: Un objetivo funcional identificado por el LLM
- **Git Plan**: El plan de commits propuesto antes de ejecutar
- **Provider**: El proveedor LLM (Ollama, Gemini, OpenAI)
- **Target Branch**: La rama contra la cual se comparan los cambios

## Modo Interactivo

El modo interactivo es la forma más fácil de usar GitClassifier. Simplemente ejecuta:

```bash
git-split
```

### Flujo Interactivo

1. **Selección de fuente del diff**:
   ```
   ¿Usar diff desde archivo? (s/N): 
   ```
   - `N` (por defecto): Usar diff desde Git
   - `s`: Usar diff desde archivo

2. **Si eliges Git**:
   ```
   Introduce la rama target (ej. main): 
   ```
   - Por defecto: `main`

3. **Si eliges archivo**:
   ```
   Introduce la ruta del archivo de diff: 
   ```

4. **Clasificación automática**:
   ```
   ¿Usar clasificación automática con LLM? (s/N): 
   ```

5. **Selección de proveedor** (si usas LLM):
   ```
   Proveedor (ollama/gemini/openai) [ollama]: 
   ```

6. **Contexto del usuario** (opcional):
   ```
   📝 CONTEXTO PARA CLASIFICACIÓN
   ======================================================================
   Opcional: Explica de forma general todos los cambios...
   ```
   Presiona Enter dos veces para finalizar.

7. **Revisión del plan**:
   ```
   📋 GIT PLAN PROPUESTO
   ======================================================================
   [Commit 1]: Fix authentication bug
   [Commit 2]: Add user profile endpoint
   ======================================================================
   ```

8. **Acción**:
   ```
   ¿Qué deseas hacer? (e)jecutar, (ed)itar plan, (c)ancelar [e]: 
   ```

## Modo de Línea de Comandos

Para uso no interactivo o en scripts, usa argumentos de línea de comandos:

```bash
git-split --target main --use-llm --provider gemini --execute
```

### Argumentos Principales

- `--target`, `-t`: Rama target (default: `main`)
- `--diff-file`, `-f`: Ruta al archivo de diff
- `--use-llm`, `-l`: Usar clasificación automática
- `--provider`, `-p`: Proveedor LLM (`ollama`, `gemini`, `openai`)
- `--mode`, `-m`: Modo de ejecución (`normal`, `step-by-step`)
- `--execute`, `-e`: Ejecutar sin confirmación
- `--generate-pr`, `-g`: Generar resumen de PR
- `--test-cmd`: Comando para ejecutar tests

Ver [Referencia de CLI](./cli-reference.md) para la lista completa.

## Análisis de Cambios

### Diferencias desde Git

Por defecto, GitClassifier compara tu rama actual con la rama target:

```bash
git-split --target main
```

Esto obtiene todos los cambios entre `main` y tu rama actual.

### Diferencias desde Archivo

Puedes analizar un diff guardado en un archivo:

```bash
# Guardar un diff
git diff main > cambios.patch

# Analizarlo
git-split --diff-file cambios.patch
```

**Ventajas**:
- Analiza diffs guardados previamente
- Útil para revisar cambios de otros o de PRs
- Permite analizar diffs sin estar en el repositorio original

**Advertencias**:
- Los commits solo se aplicarán si el diff es compatible
- No hay rollback automático cuando el diff proviene de archivo
- El archivo debe contener un diff válido en formato estándar de git

### Manejo de Ramas Temporales

Si estás en la misma rama que el target, GitClassifier automáticamente:

1. Crea una rama temporal con ID único
2. Cambia a esa rama para analizar cambios
3. Al finalizar, vuelve a la rama original
4. Elimina la rama temporal automáticamente

Esto permite analizar cambios incluso cuando estás en la misma rama que el target.

## Clasificación con LLM

### Proceso de Clasificación

Cuando usas clasificación automática con LLM:

1. **Análisis Global**: El LLM analiza todos los cambios para identificar objetivos funcionales
2. **Clasificación Individual**: Cada hunk se asigna a un objetivo

### Contexto del Usuario

Puedes proporcionar contexto para mejorar la precisión:

```bash
git-split --user-context "Este PR refactoriza el sistema de autenticación para usar JWT tokens"
```

O en modo interactivo, se te pedirá después de seleccionar el proveedor.

**Ejemplo de contexto**:
```
Este PR refactoriza el sistema de autenticación para usar JWT tokens
y añade nuevas funcionalidades de perfil de usuario. También corrige
varios bugs en la validación de formularios.
```

### Desde Archivo

También puedes proporcionar contexto desde un archivo:

```bash
git-split --user-context contexto.txt
```

## Git Plan

El Git Plan es la vista previa del plan de commits antes de ejecutar.

### Visualización del Plan

```
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
```

### Información Mostrada

- **ID del commit**: Número secuencial
- **Mensaje**: Descripción del commit propuesta
- **Hunks**: Cantidad de bloques de cambios
- **Archivos**: Lista de archivos afectados

## Modos de Ejecución

### Modo Normal

Ejecuta todos los commits automáticamente:

```bash
git-split --mode normal
```

**Características**:
- Crea todos los commits de una vez
- Opción de ejecutar tests al final
- Rollback automático si algo falla

**Ejemplo con tests**:
```bash
git-split --mode normal --test-cmd "pytest"
```

Si los tests fallan, se hace rollback automático de todos los commits.

### Modo Paso a Paso (Step-by-Step)

Aísla visualmente cada commit antes de confirmarlo:

```bash
git-split --mode step-by-step
```

**Características**:
- **Aislamiento visual**: Usa `git stash --keep-index` para que solo veas los cambios del commit actual
- **Revisión individual**: Puedes probar, compilar o revisar cada commit aisladamente
- **Control total**: Para cada commit puedes:
  - `c` - Confirmar y continuar
  - `s` - Saltar este commit
  - `a` - Abortar todo y hacer rollback

**Ejemplo de flujo**:
```
🛠️  MODO PASO A PASO ACTIVADO
Tu código se filtrará para que veas solo el commit actual.

📦 Preparando Commit 1: Fix authentication bug
👉 Ahora puedes revisar/probar el código en tu editor.
Solo los cambios de 'Fix authentication bug' están presentes.

¿Confirmar commit 1? [c]onfirmar / [s]altar / [a]bortar todo: c
✅ [1] Commit realizado.

📦 Preparando Commit 2: Add user profile endpoint
...
```

**Ventajas**:
- Pruebas unitarias por commit
- Revisión visual limpia
- Detección temprana de dependencias

## Edición del Plan

Después de que el LLM genera el plan, puedes editarlo manualmente.

### Comandos de Edición

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

> r 2 Add user profile endpoint and fix login
✅ Commit 2 renombrado

> e
```

**Nota**: La edición del plan está disponible en modo interactivo. Para uso no interactivo, usa `--edit-plan`.

## Generación de PR Summary

Después de crear los commits, puedes generar automáticamente un resumen profesional para tu Pull Request.

### Uso Básico

```bash
git-split --generate-pr
```

O en modo interactivo, se te preguntará después de ejecutar los commits.

### Descripción del Usuario

Puedes proporcionar una descripción que se incluirá en el resumen:

```bash
git-split --user-description "Este PR mejora el sistema de autenticación..."
```

O desde archivo:

```bash
git-split --user-description descripcion.txt
```

### Salida

El resumen se guarda en `PR_SUMMARY.md` y se muestra en la terminal:

```
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

Este PR mejora el sistema de autenticación...
============================================================

📝 Resumen de PR guardado en: PR_SUMMARY.md
```

## Gestión de API Keys

### Añadir API Key

```bash
git-split api-key add gemini "Mi key principal"
```

Se te pedirá ingresar la API key (se ocultará la entrada).

### Listar API Keys

```bash
# Todas las keys
git-split api-key list

# Solo keys de un proveedor
git-split api-key list gemini
```

### Eliminar API Key

```bash
git-split api-key delete 1
```

### Rotación Automática

Cuando una API key alcanza su límite:

1. El sistema detecta el error automáticamente
2. Registra el error en la base de datos
3. Cambia a la siguiente key disponible
4. Reintenta la operación automáticamente
5. Evita usar keys con errores recientes (últimos 5 minutos)

### Espera Automática

Si todas las API keys han alcanzado su límite:

1. El sistema detecta que todas las keys han sido probadas
2. Espera automáticamente (por defecto 5 minutos)
3. Muestra un contador de tiempo restante
4. Reintenta con todas las keys después de la espera

Configuración:
```bash
export API_KEY_WAIT_MINUTES=5  # Minutos a esperar (default: 5)
```

## Manejo de Ramas

### Ramas Temporales

Si estás en la misma rama que el target:

```
⚠️  Estás en la misma rama que el target (main).
   Creando rama temporal para analizar cambios...
🌿 Creada rama temporal: git-split-draft-1234567890-a1b2c3d4
...
✅ Vuelto a rama: main
🗑️  Rama temporal eliminada: git-split-draft-1234567890-a1b2c3d4
```

La rama temporal se elimina automáticamente al finalizar, incluso si hay errores.

## Rollback y Seguridad

### Mecanismo de Rollback

GitClassifier incluye un sistema de seguridad automático:

- **Guardado del estado**: Antes de ejecutar, guarda el SHA del HEAD actual
- **Rollback con `--soft`**: Si un commit falla, deshace commits pero mantiene tus cambios intactos
- **Protección contra interrupciones**: Si presionas Ctrl+C, pregunta si deseas hacer rollback
- **Limpieza del index**: Antes de cada commit, limpia el staging area

### Rollback Automático

Se activa automáticamente si:
- Un commit falla durante la ejecución
- Los tests fallan (en modo normal con `--test-cmd`)
- El usuario aborta en modo paso a paso

### Rollback Manual

Si necesitas hacer rollback manualmente:

```bash
# Ver el punto de rollback guardado (si está disponible)
git log --oneline

# Hacer rollback
git reset --soft <SHA>
```

## Mejores Prácticas

1. **Revisa el plan antes de ejecutar**: Siempre revisa el Git Plan antes de confirmar
2. **Usa contexto del usuario**: Proporciona contexto para mejorar la precisión
3. **Prueba en modo paso a paso**: Para cambios complejos, usa modo paso a paso
4. **Ejecuta tests**: Usa `--test-cmd` para validar que todo funciona
5. **Múltiples API keys**: Añade múltiples keys para rotación automática
6. **Commits pequeños**: El LLM funciona mejor con cambios organizados

## Próximos Pasos

- Consulta la [Referencia de CLI](./cli-reference.md) para opciones avanzadas
- Lee [Uso Avanzado](./advanced-usage.md) para flujos de trabajo complejos
- Revisa [Solución de Problemas](./troubleshooting.md) si encuentras problemas
