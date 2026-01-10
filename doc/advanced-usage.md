# Uso Avanzado

Esta guía cubre flujos de trabajo avanzados, automatización, y mejores prácticas para usuarios experimentados.

## Tabla de Contenidos

1. [Automatización y Scripting](#automatización-y-scripting)
2. [Flujos de Trabajo Complejos](#flujos-de-trabajo-complejos)
3. [Integración con CI/CD](#integración-con-cicd)
4. [Optimización de Performance](#optimización-de-performance)
5. [Mejores Prácticas](#mejores-prácticas)
6. [Casos de Uso Avanzados](#casos-de-uso-avanzados)

## Automatización y Scripting

### Scripts de Automatización

#### Script Básico

```bash
#!/bin/bash
# split-changes.sh

BRANCH="${1:-main}"
PROVIDER="${2:-gemini}"

git-split \
  --target "$BRANCH" \
  --use-llm \
  --provider "$PROVIDER" \
  --execute \
  --generate-pr \
  --test-cmd "pytest"
```

Uso:
```bash
chmod +x split-changes.sh
./split-changes.sh main gemini
```

#### Script con Validación

```bash
#!/bin/bash
# split-with-validation.sh

set -e  # Salir en error

BRANCH="${1:-main}"
PROVIDER="${2:-gemini}"

# Verificar que hay cambios
if ! git diff --quiet "$BRANCH"; then
  echo "📦 Procesando cambios..."
  
  git-split \
    --target "$BRANCH" \
    --use-llm \
    --provider "$PROVIDER" \
    --execute \
    --generate-pr \
    --test-cmd "pytest"
  
  echo "✅ Cambios procesados exitosamente"
else
  echo "⚠️  No hay cambios para procesar"
  exit 0
fi
```

#### Script con Contexto desde Archivo

```bash
#!/bin/bash
# split-with-context.sh

BRANCH="${1:-main}"
PROVIDER="${2:-gemini}"
CONTEXT_FILE="${3:-.git-split-context.txt}"

if [ ! -f "$CONTEXT_FILE" ]; then
  echo "⚠️  Archivo de contexto no encontrado: $CONTEXT_FILE"
  exit 1
fi

git-split \
  --target "$BRANCH" \
  --use-llm \
  --provider "$PROVIDER" \
  --user-context "$CONTEXT_FILE" \
  --execute \
  --generate-pr
```

### Integración con Git Hooks

#### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Solo ejecutar si hay cambios sin commitear
if ! git diff --cached --quiet; then
  echo "💡 Tip: Usa 'git-split' para organizar tus commits"
fi

exit 0
```

#### Post-commit Hook

```bash
#!/bin/bash
# .git/hooks/post-commit

# Generar resumen si existe PR_SUMMARY.md
if [ -f "PR_SUMMARY.md" ]; then
  echo "📝 Resumen de PR disponible en PR_SUMMARY.md"
fi
```

### Python Scripts

#### Script Python Básico

```python
#!/usr/bin/env python3
"""Script para automatizar git-split."""

import subprocess
import sys

def run_split(target="main", provider="gemini", execute=True):
    """Ejecutar git-split con opciones."""
    cmd = [
        "git-split",
        "--target", target,
        "--use-llm",
        "--provider", provider,
    ]
    
    if execute:
        cmd.append("--execute")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error: {result.stderr}", file=sys.stderr)
        return False
    
    print(result.stdout)
    return True

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "main"
    provider = sys.argv[2] if len(sys.argv) > 2 else "gemini"
    
    success = run_split(target, provider)
    sys.exit(0 if success else 1)
```

## Flujos de Trabajo Complejos

### Flujo: Feature Branch Completo

```bash
#!/bin/bash
# workflow-feature-branch.sh

FEATURE_BRANCH="feature/nueva-funcionalidad"
MAIN_BRANCH="main"

# 1. Crear y cambiar a feature branch
git checkout -b "$FEATURE_BRANCH"

# 2. Hacer cambios...
# (editar archivos)

# 3. Organizar commits con git-split
git-split \
  --target "$MAIN_BRANCH" \
  --use-llm \
  --provider gemini \
  --mode step-by-step \
  --generate-pr

# 4. Push a remoto
git push origin "$FEATURE_BRANCH"

# 5. Crear PR (usando PR_SUMMARY.md si existe)
if [ -f "PR_SUMMARY.md" ]; then
  gh pr create --title "Nueva funcionalidad" --body-file PR_SUMMARY.md
fi
```

### Flujo: Refactorización Grande

Para refactorizaciones grandes, usa modo paso a paso:

```bash
# 1. Crear rama de refactorización
git checkout -b refactor/autenticacion

# 2. Hacer cambios...

# 3. Organizar con contexto detallado
cat > .refactor-context.txt << EOF
Este PR refactoriza completamente el sistema de autenticación:
- Migración de sesiones a JWT tokens
- Nuevo sistema de permisos basado en roles
- Actualización de todas las rutas protegidas
- Tests actualizados para nuevo sistema
EOF

git-split \
  --target main \
  --use-llm \
  --provider gemini \
  --user-context .refactor-context.txt \
  --mode step-by-step \
  --test-cmd "pytest tests/test_auth.py" \
  --generate-pr
```

### Flujo: Hotfix Rápido

Para hotfixes, usa modo normal con ejecución automática:

```bash
# 1. Crear rama hotfix
git checkout -b hotfix/critical-bug main

# 2. Aplicar fix...

# 3. Organizar y ejecutar automáticamente
git-split \
  --target main \
  --use-llm \
  --provider gemini \
  --mode normal \
  --execute \
  --test-cmd "pytest tests/"

# 4. Merge rápido a main
git checkout main
git merge --no-ff hotfix/critical-bug
```

## Integración con CI/CD

### GitHub Actions

```yaml
name: Auto Split Commits

on:
  push:
    branches: [ feature/* ]

jobs:
  split-commits:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Configure API key
        env:
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
        run: |
          echo "$GOOGLE_API_KEY" | git-split api-key add gemini "CI Key"
      
      - name: Split commits
        run: |
          git-split \
            --target main \
            --use-llm \
            --provider gemini \
            --execute \
            --generate-pr
      
      - name: Upload PR summary
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: pr-summary
          path: PR_SUMMARY.md
```

### GitLab CI

```yaml
split-commits:
  image: python:3.9
  before_script:
    - pip install -r requirements.txt
    - export GOOGLE_API_KEY=$GOOGLE_API_KEY
  script:
    - git-split --target main --use-llm --provider gemini --execute
  artifacts:
    paths:
      - PR_SUMMARY.md
    when: always
```

## Optimización de Performance

### Selección de Modelo

Para cambios grandes, usa modelos más potentes:

```bash
# Cambios pequeños (< 10 hunks)
export GEMINI_MODEL="gemini-1.5-flash"
git-split --provider gemini

# Cambios grandes (> 50 hunks)
export GEMINI_MODEL="gemini-1.5-pro"
git-split --provider gemini
```

### Uso de Contexto

Proporcionar contexto mejora la precisión y reduce iteraciones:

```bash
# Crear archivo de contexto
cat > .context.txt << EOF
Este PR implementa:
1. Nuevo sistema de notificaciones
2. Actualización de UI para notificaciones
3. Tests para nuevo sistema
EOF

git-split --user-context .context.txt --provider gemini
```

### Batch Processing

Para múltiples ramas:

```bash
#!/bin/bash
# process-multiple-branches.sh

BRANCHES=("feature/1" "feature/2" "feature/3")

for branch in "${BRANCHES[@]}"; do
  echo "📦 Procesando $branch..."
  git checkout "$branch"
  
  git-split \
    --target main \
    --use-llm \
    --provider gemini \
    --execute \
    --generate-pr
  
  echo "✅ $branch procesado"
done
```

## Mejores Prácticas

### 1. Commits Atómicos

El LLM funciona mejor cuando los cambios son organizados. Si tienes cambios muy grandes, considera dividirlos manualmente primero.

### 2. Contexto Detallado

Siempre proporciona contexto cuando sea posible:

```bash
git-split --user-context "Descripción detallada de los cambios"
```

### 3. Revisión del Plan

Siempre revisa el Git Plan antes de ejecutar, especialmente en cambios importantes:

```bash
# No usar --execute para revisar primero
git-split --target main --use-llm --provider gemini
# Revisar plan, luego ejecutar manualmente
```

### 4. Tests Automáticos

Siempre ejecuta tests después de los commits:

```bash
git-split --test-cmd "pytest" --execute
```

### 5. Múltiples API Keys

Para proyectos grandes, añade múltiples API keys:

```bash
git-split api-key add gemini "Key 1"
git-split api-key add gemini "Key 2"
git-split api-key add gemini "Key 3"
```

### 6. Modo Paso a Paso para Cambios Críticos

Para cambios críticos, usa modo paso a paso:

```bash
git-split --mode step-by-step --test-cmd "pytest"
```

## Casos de Uso Avanzados

### Análisis de PRs Externos

```bash
# 1. Obtener diff de PR
gh pr diff 123 > pr-123.patch

# 2. Analizar sin aplicar
git-split \
  --diff-file pr-123.patch \
  --use-llm \
  --provider gemini \
  --skip-git-check
```

### Reorganización de Historial

```bash
# 1. Crear rama desde punto anterior
git checkout -b reorganize <commit-sha>

# 2. Reset suave para mantener cambios
git reset --soft main

# 3. Reorganizar con git-split
git-split \
  --target main \
  --use-llm \
  --provider gemini \
  --mode step-by-step
```

### Migración de Código Legacy

```bash
# 1. Crear contexto de migración
cat > migration-context.txt << EOF
Migración de código legacy:
- Convertir funciones a clases
- Actualizar sintaxis antigua
- Añadir type hints
- Actualizar tests
EOF

# 2. Organizar migración
git-split \
  --target main \
  --use-llm \
  --provider gemini \
  --user-context migration-context.txt \
  --mode step-by-step \
  --test-cmd "pytest tests/"
```

### Integración con Code Review

```bash
#!/bin/bash
# pre-review-split.sh

# Organizar commits antes de code review
git-split \
  --target main \
  --use-llm \
  --provider gemini \
  --generate-pr

# Abrir PR con resumen
if [ -f "PR_SUMMARY.md" ]; then
  gh pr create --body-file PR_SUMMARY.md
fi
```

## Troubleshooting Avanzado

### Debugging de Clasificación

Si la clasificación no es correcta:

1. **Añade más contexto**:
   ```bash
   git-split --user-context "Contexto muy detallado..."
   ```

2. **Usa modelo más potente**:
   ```bash
   export GEMINI_MODEL="gemini-1.5-pro"
   ```

3. **Revisa y edita el plan manualmente**:
   ```bash
   git-split --edit-plan
   ```

### Optimización de Costos

Para reducir costos:

1. **Usa Ollama local** cuando sea posible
2. **Usa modelos económicos** (gemini-1.5-flash, gpt-4o-mini)
3. **Agrupa cambios pequeños** antes de ejecutar
4. **Revisa el plan** antes de ejecutar para evitar iteraciones

### Manejo de Errores en Scripts

```bash
#!/bin/bash
set -e  # Salir en error
set -o pipefail  # Capturar errores en pipes

# Función de cleanup
cleanup() {
  if [ $? -ne 0 ]; then
    echo "❌ Error detectado, haciendo rollback..."
    git reset --soft HEAD~1  # Ajustar según necesidad
  fi
}

trap cleanup EXIT

# Tu código aquí
git-split --execute
```

## Próximos Pasos

- Consulta la [Referencia de CLI](./cli-reference.md) para opciones específicas
- Lee [Solución de Problemas](./troubleshooting.md) para problemas comunes
- Revisa [Guía del Usuario](./user-guide.md) para funcionalidades básicas
