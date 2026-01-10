# Guía de Configuración

Esta guía cubre todas las opciones de configuración de GitClassifier.

## Tabla de Contenidos

1. [Gestión de API Keys](#gestión-de-api-keys)
2. [Configuración de Proveedores](#configuración-de-proveedores)
3. [Variables de Entorno](#variables-de-entorno)
4. [Configuración de Modelos](#configuración-de-modelos)
5. [Personalización Avanzada](#personalización-avanzada)

## Gestión de API Keys

GitClassifier incluye un sistema integrado de gestión de API keys usando SQLite.

### Base de Datos

Las API keys se almacenan en:
```
~/.git-split/api_keys.db
```

Esta base de datos se crea automáticamente la primera vez que usas el comando `api-key`.

### Añadir API Keys

#### Método 1: CLI (Recomendado)

```bash
git-split api-key add gemini "Mi key principal"
```

Se te pedirá ingresar la API key (se ocultará la entrada).

#### Múltiples Keys

Puedes añadir múltiples keys para el mismo proveedor:

```bash
git-split api-key add gemini "Key principal"
git-split api-key add gemini "Key respaldo 1"
git-split api-key add gemini "Key respaldo 2"
```

Esto permite rotación automática cuando se alcanzan límites.

### Listar API Keys

```bash
# Todas las keys
git-split api-key list

# Solo keys de un proveedor
git-split api-key list gemini
```

### Eliminar API Keys

```bash
git-split api-key delete <key_id>
```

Obtén el `key_id` de la salida de `list`.

### Rotación Automática

El sistema automáticamente:

1. **Detecta errores de límite**: Cuando una key alcanza su rate limit o quota
2. **Registra el error**: Guarda el error en la base de datos
3. **Cambia de key**: Usa la siguiente key disponible
4. **Reintenta**: Reintenta la operación automáticamente
5. **Evita keys problemáticas**: No usa keys con errores recientes (últimos 5 minutos)

### Espera Automática

Si todas las API keys han alcanzado su límite:

1. **Detecta el problema**: Identifica que todas las keys han sido probadas
2. **Espera automáticamente**: Por defecto 5 minutos (configurable)
3. **Muestra contador**: Indica el tiempo restante
4. **Reintenta**: Después de la espera, reintenta con todas las keys

**Configuración**:
```bash
export API_KEY_WAIT_MINUTES=10  # Esperar 10 minutos (default: 5)
```

### Estructura de la Base de Datos

La base de datos almacena:

- `id`: ID único de la key
- `provider`: Proveedor (`gemini`, `openai`, `ollama`)
- `api_key`: La API key (encriptada)
- `name`: Nombre descriptivo (opcional)
- `created_at`: Fecha de creación
- `last_used`: Última vez que se usó
- `use_count`: Número de veces usada
- `is_active`: Si está activa
- `error_count`: Número de errores
- `last_error`: Último error registrado
- `last_error_at`: Fecha del último error

## Configuración de Proveedores

### Ollama (Local, Gratuito)

Ollama no requiere API keys. Solo necesitas:

1. **Instalar Ollama**:
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

3. **Descargar modelos**:
   ```bash
   ollama pull llama3.2:3b  # Modelo pequeño y rápido
   ollama pull llama3.2     # Modelo más potente
   ```

4. **Verificar**:
   ```bash
   git-split ollama status
   ```

**Ventajas**:
- ✅ Gratuito
- ✅ Se ejecuta localmente (privacidad)
- ✅ Sin límites de rate

**Desventajas**:
- ⚠️ Requiere recursos locales
- ⚠️ Puede ser más lento que servicios en la nube

### Gemini (Recomendado para Producción)

#### Obtener API Key

1. Visita [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Crea una cuenta o inicia sesión
3. Crea una nueva API key

#### Configurar

```bash
git-split api-key add gemini "Mi key principal"
```

#### Modelos Disponibles

- `gemini-1.5-flash` (default, recomendado): Rápido y económico
- `gemini-1.5-pro`: Más potente pero más costoso
- `gemini-2.0-flash-exp`: Experimental

**Configuración de modelo**:
```bash
export GEMINI_MODEL="gemini-1.5-pro"
```

**Ventajas**:
- ✅ Económico (especialmente Flash)
- ✅ Rápido
- ✅ Buena calidad
- ✅ Generoso rate limit

### OpenAI

#### Obtener API Key

1. Visita [OpenAI Platform](https://platform.openai.com/api-keys)
2. Crea una cuenta o inicia sesión
3. Crea una nueva API key

#### Configurar

```bash
git-split api-key add openai "Mi key"
```

#### Modelos Disponibles

- `gpt-4o-mini` (default, recomendado): Económico y rápido
- `gpt-4o`: Más potente pero más costoso
- `gpt-4-turbo`: Alternativa potente

**Configuración de modelo**:
```bash
export OPENAI_MODEL="gpt-4o"
```

**Ventajas**:
- ✅ Excelente calidad
- ✅ Muy confiable

**Desventajas**:
- ⚠️ Más costoso que Gemini
- ⚠️ Rate limits más estrictos

## Variables de Entorno

Aunque se recomienda usar la base de datos de API keys, también puedes usar variables de entorno.

### Prioridad

1. **API keys en base de datos** (más alta prioridad)
2. Variables de entorno
3. Fallback a valores por defecto

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

**Nota**: Si no se especifica, usa `http://localhost:11434/v1` por defecto.

### Rotación de API Keys

```bash
export API_KEY_WAIT_MINUTES=5  # Minutos a esperar (default: 5)
```

## Configuración de Modelos

### Detección Automática

GitClassifier detecta automáticamente:

- **Escala de recursos**: Basado en el número de hunks
- **Modelo recomendado**: Según la escala y el proveedor

### Escalas de Recursos

- **Pequeña** (< 10 hunks): Modelo rápido y económico
- **Mediana** (10-50 hunks): Modelo balanceado
- **Grande** (> 50 hunks): Modelo más potente

### Modelos Recomendados por Escala

#### Gemini

- **Pequeña**: `gemini-1.5-flash`
- **Mediana**: `gemini-1.5-flash`
- **Grande**: `gemini-1.5-pro`

#### OpenAI

- **Pequeña**: `gpt-4o-mini`
- **Mediana**: `gpt-4o-mini`
- **Grande**: `gpt-4o`

#### Ollama

- **Pequeña**: `llama3.2:3b`
- **Mediana**: `llama3.2:3b` o `llama3.2`
- **Grande**: `llama3.2`

### Forzar Modelo Específico

Aunque no hay una opción directa en CLI, puedes modificar el código o usar variables de entorno:

```bash
export GEMINI_MODEL="gemini-1.5-pro"
git-split --provider gemini
```

## Personalización Avanzada

### Configuración de Base de Datos

La base de datos se almacena en:
```
~/.git-split/api_keys.db
```

Para cambiar la ubicación, modifica el código en `src/storage/api_key_repository.py`.

### Configuración de Timeouts

Actualmente no hay configuración de timeouts, pero puedes modificar el código en los providers.

### Configuración de Prompts

Los prompts están en `src/prompts/templates.py`. Puedes modificar estos archivos para personalizar cómo el LLM analiza y clasifica los cambios.

### Configuración de Logging

Para habilitar logging detallado, modifica el código para usar el módulo `logging` de Python.

## Mejores Prácticas de Configuración

1. **Usa la base de datos de API keys**: Más seguro y permite rotación automática
2. **Añade múltiples keys**: Para rotación automática cuando se alcanzan límites
3. **Usa nombres descriptivos**: Facilita la gestión de múltiples keys
4. **Revisa regularmente**: Usa `git-split api-key list` para ver el estado
5. **Elimina keys no usadas**: Mantén la base de datos limpia
6. **Configura espera automática**: Ajusta `API_KEY_WAIT_MINUTES` según tus necesidades

## Verificación de Configuración

### Verificar API Keys

```bash
git-split api-key list
```

### Verificar Ollama

```bash
git-split ollama status
```

### Verificar Variables de Entorno

```bash
# macOS/Linux
env | grep -E "(GOOGLE_API_KEY|OPENAI_API_KEY|OLLAMA_BASE_URL)"

# Windows (PowerShell)
Get-ChildItem Env: | Where-Object {$_.Name -like "*API*"}
```

### Probar Configuración

```bash
# Probar con un diff pequeño
echo "test" > test.txt
git add test.txt
git-split --target main --use-llm --provider gemini
git reset HEAD test.txt
rm test.txt
```

## Solución de Problemas de Configuración

### API Key No Funciona

1. Verifica que la key esté correcta: `git-split api-key list`
2. Prueba la key manualmente con el proveedor
3. Verifica que no haya alcanzado su límite
4. Elimina y vuelve a añadir la key

### Ollama No Se Detecta

1. Verifica que Ollama esté corriendo: `ollama serve`
2. Verifica que tengas modelos: `ollama list`
3. Prueba manualmente: `ollama run llama3.2:3b`

### Variables de Entorno No Se Usan

1. Verifica que las variables estén exportadas: `env | grep API`
2. Recarga la shell o reinicia la terminal
3. Verifica que no haya keys en la base de datos (tienen prioridad)

## Próximos Pasos

- Lee la [Guía del Usuario](./user-guide.md) para usar las funcionalidades
- Consulta [Uso Avanzado](./advanced-usage.md) para flujos complejos
- Revisa [Solución de Problemas](./troubleshooting.md) si hay problemas
