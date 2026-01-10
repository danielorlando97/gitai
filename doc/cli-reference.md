# Referencia de CLI

Documentación completa de todos los comandos y opciones de GitClassifier.

## Índice

1. [Comando Principal](#comando-principal)
2. [Comando split](#comando-split)
3. [Comando api-key](#comando-api-key)
4. [Comando ollama](#comando-ollama)
5. [Comando help](#comando-help)

## Comando Principal

### Sintaxis

```bash
git-split [comando] [opciones]
```

### Sin Comando

Si no especificas un comando, se ejecuta el modo interactivo del comando `split`:

```bash
git-split
```

Equivale a:

```bash
git-split split
```

## Comando split

Clasifica y divide cambios de Git en commits semánticos.

### Sintaxis

```bash
git-split split [opciones]
git-split [opciones]  # Sin especificar 'split' explícitamente
```

### Opciones

#### Fuente del Diff

##### `--diff-file`, `-f`

Ruta al archivo de diff a analizar.

```bash
git-split --diff-file cambios.patch
```

**Mutualmente exclusivo con**: `--target`

**Nota**: Los commits solo se aplicarán si el diff es compatible con el estado actual del repositorio.

##### `--target`, `-t`

Rama target para comparar (default: `main`).

```bash
git-split --target develop
```

**Mutualmente exclusivo con**: `--diff-file`

#### Clasificación con LLM

##### `--use-llm`, `-l`

Usar clasificación automática con LLM.

```bash
git-split --use-llm
```

##### `--provider`, `-p`

Proveedor LLM: `ollama`, `gemini`, o `openai`.

```bash
git-split --provider gemini
```

**Default**: Auto-detectado (Ollama si está disponible, sino Gemini)

##### `--user-context`, `-c`

Contexto del usuario sobre los cambios. Puede ser texto directo o ruta a archivo.

```bash
# Texto directo
git-split --user-context "Este PR refactoriza el sistema de autenticación"

# Desde archivo
git-split --user-context contexto.txt
```

#### Descripción para PR

##### `--user-description`, `-d`

Descripción del usuario para el PR. Puede ser texto directo o ruta a archivo.

```bash
# Texto directo
git-split --user-description "Este PR mejora el sistema..."

# Desde archivo
git-split --user-description descripcion.txt
```

#### Modo de Ejecución

##### `--mode`, `-m`

Modo de ejecución: `normal` o `step-by-step`.

```bash
# Modo normal (default)
git-split --mode normal

# Modo paso a paso
git-split --mode step-by-step
```

**Default**: `normal`

##### `--execute`, `-e`

Ejecutar commits automáticamente sin confirmación.

```bash
git-split --execute
```

**Nota**: Útil para uso no interactivo o en scripts.

##### `--edit-plan`

Editar el plan antes de ejecutar.

```bash
git-split --edit-plan
```

#### Generación de PR

##### `--generate-pr`, `-g`

Generar resumen de Pull Request después de crear los commits.

```bash
git-split --generate-pr
```

El resumen se guarda en `PR_SUMMARY.md`.

#### Tests

##### `--test-cmd`

Comando para ejecutar tests después de los commits.

```bash
git-split --test-cmd "pytest"
git-split --test-cmd "npm test"
git-split --test-cmd "make test"
```

Si los tests fallan, se hace rollback automático de todos los commits.

#### Opciones Adicionales

##### `--skip-git-check`

Saltar verificación de repositorio Git.

```bash
git-split --diff-file cambios.patch --skip-git-check
```

**Útil para**: Analizar diffs sin estar en un repositorio Git.

**Advertencia**: No podrás aplicar commits sin un repo Git.

### Ejemplos

#### Ejemplo Básico

```bash
# Modo interactivo
git-split

# Con opciones básicas
git-split --target main --use-llm --provider gemini
```

#### Ejemplo Completo

```bash
git-split \
  --target main \
  --use-llm \
  --provider gemini \
  --user-context "Refactorización del sistema de autenticación" \
  --mode step-by-step \
  --generate-pr \
  --test-cmd "pytest"
```

#### Modo No Interactivo

```bash
git-split \
  --target main \
  --use-llm \
  --provider gemini \
  --execute \
  --generate-pr
```

#### Analizar Diff desde Archivo

```bash
git-split \
  --diff-file cambios.patch \
  --use-llm \
  --provider gemini \
  --skip-git-check
```

## Comando api-key

Gestiona API keys de LLMs.

### Sintaxis

```bash
git-split api-key <subcomando> [opciones]
```

### Subcomandos

#### add

Añadir una nueva API key.

```bash
git-split api-key add <provider> [nombre]
```

**Argumentos**:
- `provider`: `gemini`, `openai`, o `ollama`
- `nombre` (opcional): Nombre descriptivo para la key

**Ejemplos**:
```bash
git-split api-key add gemini "Mi key principal"
git-split api-key add gemini "Key de respaldo"
git-split api-key add openai "OpenAI key"
```

**Nota**: Se te pedirá ingresar la API key (se ocultará la entrada).

**Nota sobre Ollama**: Ollama no requiere API keys. Si intentas añadir una para Ollama, se mostrará un mensaje informativo.

#### list

Listar API keys.

```bash
git-split api-key list [provider]
```

**Argumentos**:
- `provider` (opcional): Filtrar por proveedor (`gemini`, `openai`, `ollama`)

**Ejemplos**:
```bash
# Todas las keys
git-split api-key list

# Solo keys de Gemini
git-split api-key list gemini
```

**Salida**:
```
📋 API Keys (gemini):
======================================================================

ID: 1
  Provider: gemini (Mi key principal)
  Creada: 2024-01-15 10:30:00
  Último uso: 2024-01-15 14:20:00
  Usos: 42

ID: 2
  Provider: gemini (Key de respaldo)
  Creada: 2024-01-15 11:00:00
  Último uso: Nunca
  Usos: 0

======================================================================
```

#### delete

Eliminar una API key.

```bash
git-split api-key delete <key_id>
```

**Argumentos**:
- `key_id`: ID de la API key a eliminar (ver `list` para obtener IDs)

**Ejemplo**:
```bash
git-split api-key delete 1
```

**Confirmación**: Se pedirá confirmación antes de eliminar.

### Ejemplos Completos

```bash
# Añadir múltiples keys para rotación
git-split api-key add gemini "Key principal"
git-split api-key add gemini "Key respaldo 1"
git-split api-key add gemini "Key respaldo 2"

# Ver todas las keys
git-split api-key list

# Eliminar una key
git-split api-key delete 2
```

## Comando ollama

Configura y gestiona Ollama.

### Sintaxis

```bash
git-split ollama <subcomando>
```

### Subcomandos

#### status

Verificar el estado de Ollama.

```bash
git-split ollama status
```

**Verifica**:
- Si Ollama está corriendo
- Si hay modelos disponibles
- Modelo recomendado

**Salida de ejemplo**:
```
✅ Ollama está corriendo
📦 Modelos disponibles:
  - llama3.2:3b (recomendado)
  - llama3.2
💡 Modelo recomendado: llama3.2:3b
```

### Ejemplos

```bash
# Verificar estado
git-split ollama status

# Usar Ollama con split
git-split --provider ollama --use-llm
```

## Comando help

Muestra la ayuda general.

### Sintaxis

```bash
git-split help
git-split --help
git-split -h
```

### Salida

Muestra información general sobre GitClassifier, comandos disponibles, y ejemplos de uso.

## Combinación de Opciones

### Orden de Precedencia

1. Argumentos de línea de comandos tienen prioridad sobre modo interactivo
2. API keys en base de datos tienen prioridad sobre variables de entorno
3. `--diff-file` y `--target` son mutuamente exclusivos

### Ejemplos de Combinaciones

#### Modo Paso a Paso con PR Summary

```bash
git-split \
  --target main \
  --use-llm \
  --provider gemini \
  --mode step-by-step \
  --generate-pr
```

#### Análisis desde Archivo con Contexto

```bash
git-split \
  --diff-file cambios.patch \
  --use-llm \
  --provider gemini \
  --user-context contexto.txt \
  --skip-git-check
```

#### Ejecución Automática Completa

```bash
git-split \
  --target main \
  --use-llm \
  --provider gemini \
  --user-context "Refactorización completa" \
  --user-description "Este PR refactoriza..." \
  --mode normal \
  --execute \
  --generate-pr \
  --test-cmd "pytest"
```

## Variables de Entorno

Aunque se recomienda usar la base de datos de API keys, también puedes usar variables de entorno:

### Gemini

```bash
export GOOGLE_API_KEY="tu-api-key"
export GEMINI_MODEL="gemini-1.5-flash"  # Opcional
```

### OpenAI

```bash
export OPENAI_API_KEY="tu-api-key"
export OPENAI_MODEL="gpt-4o-mini"  # Opcional
```

### Ollama

```bash
export OLLAMA_BASE_URL="http://localhost:11434/v1"  # Opcional
```

### Rotación de API Keys

```bash
export API_KEY_WAIT_MINUTES=5  # Minutos a esperar (default: 5)
```

**Nota**: Las API keys en la base de datos tienen prioridad sobre las variables de entorno.

## Códigos de Salida

- `0`: Éxito
- `1`: Error (ver mensaje de error para detalles)

## Ver También

- [Guía del Usuario](./user-guide.md) - Uso completo de funcionalidades
- [Guía de Configuración](./configuration.md) - Configuración detallada
- [Uso Avanzado](./advanced-usage.md) - Flujos de trabajo complejos
