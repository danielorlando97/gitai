# Solución de Problemas

Esta guía cubre problemas comunes y sus soluciones.

## Tabla de Contenidos

1. [Problemas de Instalación](#problemas-de-instalación)
2. [Problemas de Configuración](#problemas-de-configuración)
3. [Problemas de Ejecución](#problemas-de-ejecución)
4. [Problemas con LLMs](#problemas-con-llms)
5. [Problemas con Git](#problemas-con-git)
6. [Problemas de Performance](#problemas-de-performance)
7. [Errores Comunes](#errores-comunes)

## Problemas de Instalación

### Error: "Python 3.8+ requerido"

**Síntomas**:
```
Error: Python 3.8 o superior es requerido
```

**Solución**:
```bash
# Verificar versión actual
python3 --version

# Actualizar Python
# macOS:
brew install python3

# Linux (Ubuntu/Debian):
sudo apt update
sudo apt install python3.8

# Verificar nueva versión
python3 --version
```

### Error: "pip no encontrado"

**Síntomas**:
```
pip: command not found
```

**Solución**:
```bash
# Instalar pip
python3 -m ensurepip --upgrade

# O usar pip3
pip3 install -r requirements.txt
```

### Error: "Permission denied" al ejecutar

**Síntomas**:
```
Permission denied: src/main.py
```

**Solución**:
```bash
chmod +x src/main.py
chmod +x install.sh
```

### Error: "Module not found" después de instalar

**Síntomas**:
```
ModuleNotFoundError: No module named 'langchain'
```

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

**Síntomas**:
```
ImportError: cannot import name 'X' from 'langchain'
```

**Solución**:
```bash
# Actualizar LangChain y dependencias
pip install --upgrade langchain langchain-google-genai langchain-openai

# Verificar versión
python3 -c "import langchain; print(langchain.__version__)"
```

## Problemas de Configuración

### API Key No Funciona

**Síntomas**:
```
Error: Invalid API key
Error: API key authentication failed
```

**Soluciones**:

1. **Verificar que la key esté correcta**:
   ```bash
   git-split api-key list
   ```

2. **Probar la key manualmente**:
   ```bash
   # Para Gemini
   curl "https://generativelanguage.googleapis.com/v1/models?key=TU_API_KEY"
   
   # Para OpenAI
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer TU_API_KEY"
   ```

3. **Verificar que no haya alcanzado su límite**:
   - Revisa el dashboard del proveedor
   - Verifica errores recientes: `git-split api-key list`

4. **Eliminar y volver a añadir**:
   ```bash
   git-split api-key delete <key_id>
   git-split api-key add gemini "Nueva key"
   ```

### Variables de Entorno No Se Usan

**Síntomas**:
- Las variables están definidas pero no se usan
- El sistema pide API keys aunque están en variables de entorno

**Solución**:

1. **Verificar que las variables estén exportadas**:
   ```bash
   env | grep -E "(GOOGLE_API_KEY|OPENAI_API_KEY)"
   ```

2. **Recargar la shell**:
   ```bash
   # Cerrar y abrir nueva terminal
   # O recargar configuración
   source ~/.zshrc  # o ~/.bashrc
   ```

3. **Verificar que no haya keys en la base de datos** (tienen prioridad):
   ```bash
   git-split api-key list
   # Si hay keys, elimínalas o úsalas en su lugar
   ```

### Ollama No Se Detecta

**Síntomas**:
```
Error: Ollama no está disponible
Error: No se pudo conectar a Ollama
```

**Soluciones**:

1. **Verificar que Ollama esté corriendo**:
   ```bash
   # Verificar proceso
   ps aux | grep ollama
   
   # Iniciar Ollama
   ollama serve
   ```

2. **Verificar que tengas modelos**:
   ```bash
   ollama list
   
   # Si no hay modelos, descargar uno
   ollama pull llama3.2:3b
   ```

3. **Verificar conexión**:
   ```bash
   curl http://localhost:11434/api/tags
   ```

4. **Verificar estado con git-split**:
   ```bash
   git-split ollama status
   ```

5. **Verificar URL base** (si usas URL personalizada):
   ```bash
   export OLLAMA_BASE_URL="http://localhost:11434/v1"
   ```

## Problemas de Ejecución

### Error: "No estás en un repositorio Git"

**Síntomas**:
```
Error: No estás en un repositorio Git.
```

**Solución**:
```bash
# Verificar que estás en un repo Git
git status

# Si no estás en un repo, inicializar uno
git init

# O navegar a un repo existente
cd /ruta/a/repo
```

**Nota**: Si quieres analizar un diff sin estar en un repo:
```bash
git-split --diff-file cambios.patch --skip-git-check
```

### Error: "No hay cambios para procesar"

**Síntomas**:
```
No hay cambios para procesar.
```

**Soluciones**:

1. **Verificar que hay cambios**:
   ```bash
   git status
   git diff main
   ```

2. **Verificar la rama target**:
   ```bash
   # Asegúrate de que la rama target existe
   git branch -a | grep main
   
   # Si no existe, crear o usar otra rama
   git-split --target develop
   ```

3. **Verificar que los cambios no estén ya commiteados**:
   ```bash
   # Ver commits no en main
   git log main..HEAD
   ```

### Error: "No se encontraron hunks para procesar"

**Síntomas**:
```
No se encontraron hunks para procesar.
```

**Solución**:
- Verifica que el diff contenga cambios válidos
- Si usas `--diff-file`, verifica que el archivo tenga formato válido:
  ```bash
  # Verificar formato del diff
  head -20 cambios.patch
  ```

## Problemas con LLMs

### Error: "Rate limit exceeded"

**Síntomas**:
```
Error: Rate limit exceeded
Error: Quota exceeded
```

**Soluciones**:

1. **El sistema debería rotar automáticamente** si tienes múltiples keys:
   ```bash
   # Añadir más keys
   git-split api-key add gemini "Key 2"
   git-split api-key add gemini "Key 3"
   ```

2. **Esperar automáticamente**: El sistema espera 5 minutos y reintenta

3. **Configurar tiempo de espera**:
   ```bash
   export API_KEY_WAIT_MINUTES=10
   ```

4. **Usar otro proveedor temporalmente**:
   ```bash
   git-split --provider ollama  # Local, sin límites
   ```

### Error: "Model not found"

**Síntomas**:
```
Error: Model 'gemini-xxx' not found
```

**Solución**:
```bash
# Verificar modelo disponible
# Para Gemini: usar gemini-1.5-flash o gemini-1.5-pro
export GEMINI_MODEL="gemini-1.5-flash"

# Para Ollama: verificar modelos instalados
ollama list
```

### Error: "Timeout" o "Request timeout"

**Síntomas**:
```
Error: Request timeout
Error: Connection timeout
```

**Soluciones**:

1. **Verificar conexión a internet**:
   ```bash
   ping google.com
   ```

2. **Probar con otro proveedor**:
   ```bash
   git-split --provider ollama  # Local, sin timeout de red
   ```

3. **Usar modelo más rápido**:
   ```bash
   export GEMINI_MODEL="gemini-1.5-flash"  # Más rápido
   ```

### Clasificación Incorrecta

**Síntomas**:
- Los commits no están bien organizados
- Hunks asignados incorrectamente

**Soluciones**:

1. **Añadir más contexto**:
   ```bash
   git-split --user-context "Descripción muy detallada de los cambios"
   ```

2. **Usar modelo más potente**:
   ```bash
   export GEMINI_MODEL="gemini-1.5-pro"
   git-split --provider gemini
   ```

3. **Revisar y editar el plan manualmente**:
   ```bash
   git-split --edit-plan
   ```

4. **Usar modo paso a paso para revisar**:
   ```bash
   git-split --mode step-by-step
   ```

## Problemas con Git

### Error: "Cannot apply diff"

**Síntomas**:
```
Error: Cannot apply diff
Error: Patch does not apply
```

**Soluciones**:

1. **Verificar que el diff sea compatible**:
   ```bash
   # Probar aplicar manualmente
   git apply --check cambios.patch
   ```

2. **Si el diff es de un archivo, verificar compatibilidad**:
   - El diff debe ser compatible con el estado actual del repo
   - Considera usar `git apply` manualmente primero

3. **Si estás en la misma rama que target**:
   - El sistema crea una rama temporal automáticamente
   - Si hay problemas, verifica que no haya conflictos

### Error: "Merge conflict" durante ejecución

**Síntomas**:
```
Error: Merge conflict
Auto-merging failed
```

**Solución**:
```bash
# Resolver conflictos manualmente
git status
# Editar archivos con conflictos
# Luego continuar con git-split o hacer commit manualmente
```

### Error: "Branch already exists"

**Síntomas**:
```
Error: Branch 'git-split-draft-xxx' already exists
```

**Solución**:
```bash
# Eliminar rama temporal manualmente
git branch -D git-split-draft-*

# O cambiar a otra rama primero
git checkout main
```

### Rollback No Funciona

**Síntomas**:
- Los commits no se revierten correctamente
- Cambios se pierden después del rollback

**Solución**:
```bash
# El rollback usa --soft, los cambios deberían estar en staging
git status

# Si no están, recuperar desde reflog
git reflog
git reset --soft <commit-sha>
```

## Problemas de Performance

### Ejecución Muy Lenta

**Síntomas**:
- El proceso tarda mucho tiempo
- Timeouts frecuentes

**Soluciones**:

1. **Usar modelo más rápido**:
   ```bash
   export GEMINI_MODEL="gemini-1.5-flash"  # Más rápido
   ```

2. **Usar Ollama local**:
   ```bash
   git-split --provider ollama
   ```

3. **Reducir número de hunks**:
   - Divide cambios grandes en múltiples ejecuciones
   - Usa `git add -p` para seleccionar cambios específicos primero

4. **Verificar conexión**:
   ```bash
   # Para servicios en la nube
   ping api.openai.com
   ping generativelanguage.googleapis.com
   ```

### Alto Uso de Memoria

**Síntomas**:
- El proceso consume mucha memoria
- Sistema se vuelve lento

**Soluciones**:

1. **Procesar cambios en lotes más pequeños**
2. **Cerrar otras aplicaciones**
3. **Usar modelo más pequeño** (para Ollama):
   ```bash
   ollama pull llama3.2:3b  # Modelo más pequeño
   ```

## Errores Comunes

### Error: "Command not found: git-split"

**Solución**:
```bash
# Verificar que el alias esté configurado
which git-split

# Si no existe, crear alias o usar ruta completa
python3 /ruta/a/git-ai/src/main.py

# O añadir al PATH
export PATH="$PATH:/ruta/a/git-ai"
```

### Error: "Database locked"

**Síntomas**:
```
Error: database is locked
```

**Solución**:
```bash
# Cerrar otras instancias de git-split
# O esperar unos segundos y reintentar
```

### Error: "Invalid diff format"

**Síntomas**:
```
Error: Invalid diff format
```

**Solución**:
```bash
# Verificar formato del diff
head -20 diff.patch

# Asegúrate de que sea un diff válido de git
git diff main > valid-diff.patch
```

### Error: "No se pudo identificar objetivos"

**Síntomas**:
```
No se pudieron identificar objetivos. Abortando.
```

**Soluciones**:

1. **Añadir contexto más detallado**:
   ```bash
   git-split --user-context "Descripción detallada..."
   ```

2. **Verificar que hay cambios suficientes**:
   ```bash
   git diff main | wc -l
   ```

3. **Probar con otro proveedor**:
   ```bash
   git-split --provider openai
   ```

## Obtener Ayuda Adicional

### Logs y Debugging

Para obtener más información sobre errores:

1. **Ejecutar con verbose** (si está disponible):
   ```bash
   git-split --verbose
   ```

2. **Revisar mensajes de error completos**:
   - Los mensajes de error suelen incluir detalles útiles
   - Copia el mensaje completo para debugging

3. **Verificar estado del sistema**:
   ```bash
   git-split api-key list
   git-split ollama status
   git status
   ```

### Reportar Problemas

Si encuentras un bug:

1. **Recopilar información**:
   - Versión de Python: `python3 --version`
   - Versión de Git: `git --version`
   - Mensaje de error completo
   - Pasos para reproducir

2. **Verificar issues existentes** en el repositorio

3. **Crear nuevo issue** con toda la información

## Próximos Pasos

- Consulta la [Guía del Usuario](./user-guide.md) para uso correcto
- Lee [Uso Avanzado](./advanced-usage.md) para optimizaciones
- Revisa [Configuración](./configuration.md) para ajustes
