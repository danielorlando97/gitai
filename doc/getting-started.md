# Guía de Inicio Rápido

Esta guía te ayudará a comenzar a usar GitClassifier en minutos.

## Instalación Rápida

```bash
# Clonar el repositorio (si aún no lo has hecho)
git clone <repo-url>
cd git-ai

# Instalar dependencias
./install.sh
```

El script de instalación:
- Instala todas las dependencias de Python
- Hace el script ejecutable
- Opcionalmente crea un alias global `git-split`

## Configuración Inicial

### Opción 1: Usar Ollama (Recomendado para empezar)

Ollama es gratuito y se ejecuta localmente. Solo necesitas:

1. **Instalar Ollama** (si no lo tienes):
   ```bash
   # macOS
   brew install ollama
   
   # Linux
   curl -fsSL https://ollama.com/install.sh | sh
   ```

2. **Iniciar Ollama**:
   ```bash
   ollama serve
   ```

3. **Descargar un modelo** (en otra terminal):
   ```bash
   ollama pull llama3.2:3b
   ```

4. **Verificar estado**:
   ```bash
   git-split ollama status
   ```

### Opción 2: Usar Gemini (Recomendado para producción)

1. **Obtener API key**:
   - Ve a [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Crea una nueva API key

2. **Añadir la key**:
   ```bash
   git-split api-key add gemini "Mi key principal"
   # Se te pedirá que ingreses la API key (se ocultará)
   ```

3. **Verificar**:
   ```bash
   git-split api-key list
   ```

### Opción 3: Usar OpenAI

1. **Obtener API key**:
   - Ve a [OpenAI Platform](https://platform.openai.com/api-keys)
   - Crea una nueva API key

2. **Añadir la key**:
   ```bash
   git-split api-key add openai "Mi key"
   ```

## Primer Uso

### Ejemplo Básico

1. **Haz algunos cambios** en tu repositorio:
   ```bash
   # Edita algunos archivos
   echo "nueva funcionalidad" >> archivo.py
   ```

2. **Ejecuta GitClassifier**:
   ```bash
   git-split
   ```

3. **Sigue las instrucciones interactivas**:
   - Selecciona la rama target (por defecto: `main`)
   - Elige si usar clasificación automática con LLM
   - Selecciona el proveedor (ollama/gemini/openai)
   - Revisa el plan generado
   - Confirma para ejecutar

### Ejemplo con Opciones

```bash
# Usar LLM automáticamente con Gemini
git-split --target main --use-llm --provider gemini

# Modo no interactivo completo
git-split --target main --use-llm --provider gemini \
  --mode normal --execute --generate-pr
```

## Casos de Uso Comunes

### 1. Dividir cambios en commits semánticos

```bash
# Después de hacer varios cambios
git-split --target main --use-llm --provider gemini
```

El LLM analizará tus cambios y los organizará en commits lógicos.

### 2. Analizar un diff desde archivo

```bash
# Guardar un diff
git diff main > cambios.patch

# Analizarlo
git-split --diff-file cambios.patch --use-llm --provider gemini
```

### 3. Modo paso a paso para revisión detallada

```bash
git-split --target main --use-llm --provider gemini --mode step-by-step
```

Este modo te permite revisar cada commit individualmente antes de confirmarlo.

### 4. Generar resumen de PR automáticamente

```bash
git-split --target main --use-llm --provider gemini \
  --generate-pr --execute
```

Después de crear los commits, se generará un resumen profesional en `PR_SUMMARY.md`.

## Comandos Útiles

```bash
# Ver ayuda
git-split help

# Gestionar API keys
git-split api-key list
git-split api-key add gemini "Nombre"
git-split api-key delete 1

# Verificar Ollama
git-split ollama status
```

## Próximos Pasos

- Lee la [Guía del Usuario](./user-guide.md) para conocer todas las funcionalidades
- Consulta la [Referencia de CLI](./cli-reference.md) para opciones avanzadas
- Revisa [Uso Avanzado](./advanced-usage.md) para flujos de trabajo complejos

## Solución Rápida de Problemas

**Error: "No estás en un repositorio Git"**
- Asegúrate de estar en un directorio con un repositorio Git inicializado

**Error: "No hay cambios para procesar"**
- Asegúrate de tener cambios sin commitear o diferencias con la rama target

**Error: "API key no válida"**
- Verifica que la API key esté correctamente configurada: `git-split api-key list`

**Ollama no funciona**
- Verifica que Ollama esté corriendo: `ollama serve`
- Verifica que tengas modelos descargados: `ollama list`

Para más ayuda, consulta la [Guía de Solución de Problemas](./troubleshooting.md).
