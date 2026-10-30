# Render on the Mac: ssh casaos 'cat ~dgmneto/homelab/services/trmnl-ai/env.tpl' | op inject | ssh casaos 'sudo -u dgmneto sh -c "umask 077; cat > /home/dgmneto/homelab/services/trmnl-ai/.env"'
OPENROUTER_API_KEY={{ op://Homelab/OpenRouter - TRMNL/credential }}
OPENROUTER_MODEL=anthropic/claude-haiku-5.5
