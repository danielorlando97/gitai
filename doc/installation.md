# Guía de Instalación

Esta guía detallada cubre todos los aspectos de la instalación de GitClassifier.

## Requisitos del Sistema

### Requisitos Mínimos

- **Python**: 3.8 o superior
- **Git**: 2.0 o superior
- **Sistema Operativo**: macOS, Linux, o Windows (con WSL)

### Dependencias de Python

Las siguientes dependencias se instalan automáticamente:

- `langchain` - Framework para trabajar con LLMs
- `langchain-google-genai` - Integración con Gemini
- `langchain-openai` - Integración con OpenAI
- `pydantic` - Validación de datos
- `sqlite3` - Base de datos para API keys (incluida en Python)

## Instalación

### Método 1: Script de Instalación Automática (Recomendado)

```bash
# Dar permisos de ejecución
chmod +x install.sh

# Ejecutar instalación
./install.sh
```

El script:
1. Verifica que Python 3.8+ esté instalado
2. Crea un entorno virtual (opcional)
3. Instala todas las dependencias de `requirements.txt`
4. Hace el script principal ejecutable
5. Opcionalmente crea un alias global `git-split`

**Opciones del script**:
- `--no-alias`: No crear alias global
- `--venv`: Crear y usar entorno virtual

### Método 2: Instalación Manual

#### Paso 1: Clonar el Repositorio

```bash
git clone <repo-url>
cd git-ai
```

#### Paso 2: Crear Entorno Virtual (Recomendado)

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

#### Paso 3: Instalar Dependencias

```bash
pip install -r requirements.txt
```

#### Paso 4: Hacer Ejecutable

```bash
chmod +x src/main.py
```

#### Paso 5: Crear Alias (Opcional)

**macOS/Linux** (añadir a `~/.zshrc` o `~/.bashrc`):

```bash
alias git-split="python3 /ruta/completa/a/git-ai/src/main.py"
```

**Windows** (PowerShell):

```powershell
function git-split {
    python C:\ruta\completa\a\git-ai\src\main.py $args
}
```

## Verificación de Instalación

### Verificar Instalación Básica

```bash
# Verificar que el script es ejecutable
python3 src/main.py help

# O si creaste el alias
git-split help
```

Deberías ver la ayuda del comando.

### Verificar Dependencias

```bash
python3 -c "import langchain; print('LangChain OK')"
python3 -c "import langchain_google_genai; print('Gemini OK')"
python3 -c "import langchain_openai; print('OpenAI OK')"
python3 -c "import pydantic; print('Pydantic OK')"
```

## Configuración de Proveedores LLM

### Configurar Ollama (Local, Gratuito)

1. **Instalar Ollama**:

   **macOS**:
   ```bash
   brew install ollama
   ```

   **Linux**:
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```

   **Windows**: Descargar desde [ollama.com](https://ollama.com)

2. **Iniciar Ollama**:
   ```bash
   ollama serve
   ```

3. **Descargar un modelo**:
   ```bash
   # Modelo pequeño y rápido (recomendado para empezar)
   ollama pull llama3.2:3b
   
   # Modelo más potente
   ollama pull llama3.2
   ```

4. **Verificar**:
   ```bash
   git-split ollama status
   ollama list
   ```

### Configurar Gemini (Recomendado para Producción)

1. **Obtener API Key**:
   - Visita [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Crea una cuenta o inicia sesión
   - Crea una nueva API key

2. **Añadir API Key**:
   ```bash
   git-split api-key add gemini "Mi key principal"
   ```
   Se te pedirá ingresar la API key (se ocultará la entrada).

3. **Verificar**:
   ```bash
   git-split api-key list
   ```

**Nota**: Gemini es económico y rápido. El modelo por defecto es `gemini-1.5-flash`.

### Configurar OpenAI

1. **Obtener API Key**:
   - Visita [OpenAI Platform](https://platform.openai.com/api-keys)
   - Crea una cuenta o inicia sesión
   - Crea una nueva API key

2. **Añadir API Key**:
   ```bash
   git-split api-key add openai "Mi key"
   ```

3. **Verificar**:
   ```bash
   git-split api-key list
   ```

**Nota**: OpenAI es más costoso pero puede ofrecer mejor calidad en algunos casos.

## Configuración Alternativa: Variables de Entorno

Si prefieres usar variables de entorno en lugar de la base de datos:

### Gemini

```bash
export GOOGLE_API_KEY="tu-api-key-aqui"
export GEMINI_MODEL="gemini-1.5-flash"  # Opcional
```

### OpenAI

```bash
export OPENAI_API_KEY="tu-api-key-aqui"
export OPENAI_MODEL="gpt-4o-mini"  # Opcional
```

### Ollama

```bash
export OLLAMA_BASE_URL="http://localhost:11434/v1"  # Opcional
```

**Nota**: Las API keys en la base de datos tienen prioridad sobre las variables de entorno.

## Actualización

### Actualizar GitClassifier

```bash
# Si clonaste el repositorio
cd git-ai
git pull origin main

# Reinstalar dependencias si hay cambios
pip install -r requirements.txt --upgrade
```

### Actualizar Dependencias

```bash
pip install -r requirements.txt --upgrade
```

## Desinstalación

### Eliminar Instalación

1. **Eliminar alias** (si lo creaste):
   - Edita `~/.zshrc` o `~/.bashrc` y elimina la línea del alias

2. **Eliminar base de datos de API keys** (opcional):
   ```bash
   rm ~/.git-split/api_keys.db
   ```

3. **Eliminar directorio del proyecto**:
   ```bash
   rm -rf /ruta/a/git-ai
   ```

### Eliminar Entorno Virtual

```bash
deactivate  # Si está activo
rm -rf venv
```

## Solución de Problemas de Instalación

### Error: "Python 3.8+ requerido"

**Solución**:
```bash
# Verificar versión de Python
python3 --version

# Si es menor a 3.8, actualizar Python
# macOS:
brew install python3

# Linux (Ubuntu/Debian):
sudo apt update
sudo apt install python3.8
```

### Error: "pip no encontrado"

**Solución**:
```bash
# Instalar pip
python3 -m ensurepip --upgrade

# O usar pip3
pip3 install -r requirements.txt
```

### Error: "Permission denied" al ejecutar

**Solución**:
```bash
chmod +x src/main.py
chmod +x install.sh
```

### Error: "Module not found" después de instalar

**Solución**:
```bash
# Asegúrate de estar en el directorio correcto
cd git-ai

# Reinstalar dependencias
pip install -r requirements.txt --force-reinstall

# Verificar que estás usando el Python correcto
which python3
python3 --version
```

### Error con LangChain

**Solución**:
```bash
# Actualizar LangChain
pip install --upgrade langchain langchain-google-genai langchain-openai
```

## Próximos Pasos

Después de la instalación:

1. Lee la [Guía de Inicio Rápido](./getting-started.md) para tu primer uso
2. Configura al menos un proveedor LLM (Ollama es el más fácil)
3. Prueba con un repositorio de ejemplo

## Soporte

Si encuentras problemas durante la instalación:

1. Consulta la [Guía de Solución de Problemas](./troubleshooting.md)
2. Verifica que cumplas todos los requisitos
3. Revisa los logs de error para más detalles
