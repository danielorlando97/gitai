#!/bin/bash
# Script de instalación para GitClassifier

echo "🔧 Instalando GitClassifier..."

# Instalar dependencias
pip install -qU -r requirements.txt

# Hacer el script ejecutable
chmod +x git_splitter.py

# Crear alias global (opcional)
read -p "¿Crear alias 'git-split' globalmente? (s/N): " create_alias

if [[ "$create_alias" == "s" || "$create_alias" == "S" ]]; then
    SCRIPT_PATH=$(pwd)/git_splitter.py
    ALIAS_CMD="alias git-split='python3 $SCRIPT_PATH'"
    
    # Detectar shell
    if [[ "$SHELL" == *"zsh"* ]]; then
        CONFIG_FILE="$HOME/.zshrc"
    elif [[ "$SHELL" == *"bash"* ]]; then
        CONFIG_FILE="$HOME/.bashrc"
    else
        CONFIG_FILE="$HOME/.profile"
    fi
    
    # Añadir alias si no existe
    if ! grep -q "alias git-split" "$CONFIG_FILE" 2>/dev/null; then
        echo "" >> "$CONFIG_FILE"
        echo "# GitClassifier alias" >> "$CONFIG_FILE"
        echo "$ALIAS_CMD" >> "$CONFIG_FILE"
        echo "✅ Alias añadido a $CONFIG_FILE"
        echo "   Ejecuta 'source $CONFIG_FILE' o reinicia tu terminal"
    else
        echo "ℹ️  El alias ya existe en $CONFIG_FILE"
    fi
fi

echo ""
echo "✅ Instalación completada!"
echo ""
echo "📝 Configuración necesaria:"
echo "   export GOOGLE_API_KEY='tu-api-key'  # Para Gemini (recomendado)"
echo "   # O"
echo "   export OPENAI_API_KEY='tu-api-key'  # Para OpenAI"
echo ""
echo "🚀 Uso:"
echo "   python3 git_splitter.py"
if [[ "$create_alias" == "s" || "$create_alias" == "S" ]]; then
    echo "   # O después de 'source $CONFIG_FILE':"
    echo "   git-split"
fi



