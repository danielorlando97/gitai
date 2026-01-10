# Arquitectura Modular - GitClassifier

## Principio Open/Closed

Esta estructura sigue el principio **Open/Closed**: abierto para extensión, cerrado para modificación.

## Estructura de Directorios

```
src/
├── models/          # Modelos de datos (Pydantic)
├── providers/       # LLM Providers (Strategy Pattern)
├── classifiers/     # Clasificadores (Strategy Pattern)
├── executors/       # Ejecutores (Strategy Pattern)
├── prompts/         # Gestión de prompts
├── storage/         # Persistencia (Repository Pattern)
├── detectors/       # Detección de recursos
├── services/        # Lógica de negocio
├── utils/           # Utilidades
└── cli/             # Interfaz de línea de comandos
```

## Patrones de Diseño

### 1. Strategy Pattern - Providers

**Extensión sin modificación**: Para añadir un nuevo provider LLM:

1. Crear `src/providers/nuevo_provider.py` que extienda `AbstractProvider`
2. Registrar en `src/providers/__init__.py`:
   ```python
   ProviderFactory.register("nuevo_provider", NuevoProvider)
   ```

**No necesitas modificar** código existente.

### 2. Strategy Pattern - Classifiers

**Extensión sin modificación**: Para añadir un nuevo clasificador:

1. Crear `src/classifiers/nuevo_classifier.py` que extienda `AbstractClassifier`
2. Usar en el código principal

### 3. Strategy Pattern - Executors

**Extensión sin modificación**: Para añadir un nuevo modo de ejecución:

1. Crear `src/executors/nuevo_executor.py` que extienda `AbstractExecutor`
2. Usar en el código principal

### 4. Factory Pattern - Providers

El `ProviderFactory` permite crear providers dinámicamente:

```python
from gitai.providers import ProviderFactory

provider = ProviderFactory.create(
    "gemini",
    model_name="models/gemini-2.5-flash-lite",
    key_manager=key_manager
)
```

### 5. Repository Pattern - Storage

La capa de almacenamiento está abstraída:

```python
from gitai.storage import APIKeyRepository

repo = APIKeyRepository()
keys = repo.list_all({"provider": "gemini"})
```

## Ejemplos de Extensión

### Añadir un nuevo Provider (ej: Anthropic Claude)

1. **Crear** `src/providers/claude.py`:
```python
from .base import AbstractProvider

class ClaudeProvider(AbstractProvider):
    provider_name = "claude"
    
    def get_client(self):
        # Implementación
        pass
    
    def invoke(self, prompt: str):
        # Implementación
        pass
    
    def supports_structured_output(self):
        return True
```

2. **Registrar** en `src/providers/__init__.py`:
```python
from .claude import ClaudeProvider
ProviderFactory.register("claude", ClaudeProvider)
```

3. **Usar**:
```python
provider = ProviderFactory.create("claude", ...)
```

**No modificaste ningún código existente.**

### Añadir un nuevo Classifier

1. **Crear** `src/classifiers/rule_based.py`:
```python
from .base import AbstractClassifier

class RuleBasedClassifier(AbstractClassifier):
    def identify_goals(self, hunks, user_context=None):
        # Implementación basada en reglas
        pass
    
    def classify_hunks(self, hunks, goals, user_context=None):
        # Implementación
        pass
```

2. **Usar** en el código principal sin modificar otros classifiers.

### Añadir un nuevo Executor

1. **Crear** `src/executors/dry_run.py`:
```python
from .base import AbstractExecutor

class DryRunExecutor(AbstractExecutor):
    def execute(self, plan, ...):
        # Solo muestra qué haría sin ejecutar
        pass
```

2. **Usar** sin modificar otros executors.

## Ventajas

1. **Extensibilidad**: Fácil añadir nuevas funcionalidades
2. **Mantenibilidad**: Código organizado y claro
3. **Testabilidad**: Cada componente se puede testear aisladamente
4. **Reutilización**: Componentes reutilizables
5. **Separación de responsabilidades**: Cada módulo tiene una función clara

## Migración

✅ **Migración completada**: Todo el código legacy ha sido eliminado y reemplazado por la nueva estructura modular.

La nueva arquitectura está completamente implementada y lista para usar:
1. Todos los módulos están implementados y funcionando
2. La CLI modular está operativa
3. Los servicios están disponibles
4. El código legacy ha sido completamente eliminado
