#!/bin/bash

# Convenience wrapper for start_api.sh
# This allows running from project root: ./start.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"${SCRIPT_DIR}/scripts/start_api.sh"
