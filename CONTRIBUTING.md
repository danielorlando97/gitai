# Guía de Contribución

¡Gracias por tu interés en contribuir a GitClassifier! Esta guía te ayudará a entender cómo puedes contribuir al proyecto.

## Estructura del Proyecto

GitClassifier sigue una arquitectura modular basada en patrones de diseño:

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

## Cómo Contribuir

### 1. Reportar Bugs

Si encuentras un bug, por favor:
1. Verifica que no haya un issue existente
2. Crea un nuevo issue con:
   - Descripción clara del problema
   - Pasos para reproducir
   - Comportamiento esperado vs actual
   - Versión de Python y sistema operativo

### 2. Sugerir Funcionalidades

Las sugerencias son bienvenidas:
1. Abre un issue con la etiqueta "enhancement"
2. Describe la funcionalidad propuesta
3. Explica el caso de uso

### 3. Contribuir Código

#### Configuración del Entorno

```bash
# Clonar el repositorio
git clone <repo-url>
cd git-ai

# Instalar dependencias
pip install -r requirements.txt

# Hacer el script ejecutable
chmod +x src/main.py
```

#### Estándares de Código

- **Líneas de código**: Máximo 89 caracteres (incluyendo espacios y tabs)
- **Idioma**: Todo el código y comentarios en inglés
- **Comentarios**: Solo cuando la lógica es compleja o confusa
- **Minimalismo**: Evitar código redundante u obvio

#### Proceso de Pull Request

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Realiza tus cambios siguiendo los estándares
4. Asegúrate de que el código funciona correctamente
5. Commit tus cambios (`git commit -m 'Añade nueva funcionalidad'`)
6. Push a tu fork (`git push origin feature/nueva-funcionalidad`)
7. Abre un Pull Request

## Extender el Proyecto

GitClassifier está diseñado para ser extensible. Aquí te mostramos cómo añadir nuevas funcionalidades:

### Añadir un Nuevo Provider LLM

1. Crear `src/providers/claude.py`:

```python
from .base import AbstractProvider

class ClaudeProvider(AbstractProvider):
    provider_name = "claude"
    
    def get_client(self):
        # Implementación del cliente
        pass
    
    def invoke(self, prompt: str):
        # Implementación de invoke
        pass
    
    def supports_structured_output(self):
        return True
```

2. Registrar en `src/providers/__init__.py`:

```python
from .claude import ClaudeProvider
ProviderFactory.register("claude", ClaudeProvider)
```

3. ¡Listo! El provider estará disponible automáticamente.

**No necesitas modificar ningún código existente.**

### Añadir un Nuevo Classifier

1. Crear `src/classifiers/rule_based.py`:

```python
from .base import AbstractClassifier
from ..models.hunk import Hunk
from ..models.goal import Goal

class RuleBasedClassifier(AbstractClassifier):
    """Classifier basado en reglas."""
    
    def identify_goals(
        self,
        hunks: List[Hunk],
        user_context: Optional[str] = None
    ) -> List[Goal]:
        # Implementación
        pass
    
    def classify_hunks(
        self,
        hunks: List[Hunk],
        goals: List[Goal],
        user_context: Optional[str] = None
    ) -> Dict[int, Dict]:
        # Implementación
        pass
```

2. Exportar en `src/classifiers/__init__.py` si es necesario.

### Añadir un Nuevo Executor

1. Crear `src/executors/interactive.py`:

```python
from .base import AbstractExecutor

class InteractiveExecutor(AbstractExecutor):
    """Executor interactivo con confirmación por commit."""
    
    def execute(
        self,
        plan: Dict[int, Dict],
        rollback_point: Optional[str] = None,
        test_command: Optional[str] = None,
        generate_pr: bool = False,
        llm_client: Optional[Any] = None,
        user_description: Optional[str] = None,
        provider: str = "gemini",
        key_manager: Optional[Any] = None
    ) -> bool:
        # Implementación
        pass
```

2. Exportar en `src/executors/__init__.py` si es necesario.

### Añadir un Nuevo Comando CLI

1. Crear `src/cli/commands/config.py`:

```python
from .base import BaseCommand
import argparse

class ConfigCommand(BaseCommand):
    """Command for configuration management."""
    
    name = "config"
    description = "Gestiona la configuración"
    
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument('--show', action='store_true')
    
    def execute(self, args: argparse.Namespace) -> int:
        # Implementación
        return 0
```

2. Registrar en `src/cli/commands/__init__.py`:

```python
from .config import ConfigCommand
__all__ = [..., "ConfigCommand"]
```

3. Añadir al array de comandos en `src/main.py`:

```python
commands = [
    SplitCommand(),
    APIKeyCommand(),
    OllamaCommand(),
    ConfigCommand()  # Nuevo comando
]
```

### Añadir un Nuevo Detector

1. Crear `src/detectors/custom.py`:

```python
from .base import AbstractDetector

class CustomDetector(AbstractDetector):
    """Custom resource detector."""
    
    def detect_resources(self) -> Tuple[float, int, Optional[float], Optional[str]]:
        # Implementación
        pass
```

2. Registrar en `src/detectors/factory.py`:

```python
from .custom import CustomDetector
DetectorFactory.register("custom", CustomDetector)
```

## Ejemplos de Uso de la API

### Usar un Provider

```python
from gitai.providers import ProviderFactory
from gitai.storage import APIKeyRepository

# Crear key manager
key_manager = APIKeyRepository()

# Crear provider
provider = ProviderFactory.create(
    "gemini",
    model_name="models/gemini-2.5-flash-lite",
    key_manager=key_manager
)

# Usar provider
client = provider.get_client()
response = provider.invoke("Hello, world!")
```

### Usar un Classifier

```python
from gitai.classifiers import SemanticClassifier
from gitai.models.hunk import Hunk
from gitai.storage import APIKeyRepository

# Crear classifier
key_manager = APIKeyRepository()
classifier = SemanticClassifier(
    provider="gemini",
    key_manager=key_manager
)

# Identificar objetivos
hunks = [Hunk(file="test.py", content="...")]
goals = classifier.identify_goals(hunks, user_context="Refactoring")

# Clasificar hunks
plan = classifier.classify_hunks(hunks, goals)
```

### Usar un Executor

```python
from gitai.executors import NormalExecutor, StepByStepExecutor
from gitai.utils.git import get_current_head

# Crear executor
executor = NormalExecutor()

# Ejecutar plan
rollback_point = get_current_head()
success = executor.execute(
    plan=plan,
    rollback_point=rollback_point,
    test_command="pytest"
)
```

## Testing

Aunque la capa de tests aún no está implementada, cuando añadas nuevas funcionalidades:

1. Asegúrate de probar manualmente tu código
2. Verifica que no rompes funcionalidad existente
3. Prueba casos edge y errores

## Documentación

- **Código**: Comentarios en inglés, solo cuando sea necesario
- **Docstrings**: Usa docstrings para clases y funciones públicas
- **README**: Actualiza el README si añades funcionalidades importantes

## Preguntas

Si tienes preguntas sobre cómo contribuir:
1. Revisa la documentación existente (README.md, ARCHITECTURE.md)
2. Abre un issue con la etiqueta "question"
3. Revisa issues existentes que puedan tener respuestas

## Reconocimientos

¡Gracias por contribuir a GitClassifier! Cada contribución, por pequeña que sea, es valiosa.
