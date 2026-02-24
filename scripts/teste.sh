#!/usr/bin/env bash
# Script Shell de teste - Orca (Linux/macOS)

echo "Script teste.sh executado em $(date)"
LOG_DIR="$(dirname "$0")"
echo "Executado em $(date)" >> "$LOG_DIR/teste_exec.log"
exit 0
