#!/usr/bin/env bash
# =============================================================================
# Docker Credential Helper Fix Script
# =============================================================================
# This script fixes the common Docker credential helper error:
# "exec: docker-credential-desktop: executable file not found in $PATH"
#
# Usage: ./scripts/fix_docker_credentials.sh
# =============================================================================

set -e

echo "🔧 Fixing Docker credential helper configuration..."
echo ""

# Create Docker config directory if it doesn't exist
if [ ! -d "$HOME/.docker" ]; then
    echo "📁 Creating ~/.docker directory..."
    mkdir -p "$HOME/.docker"
fi

# Backup existing config if present
if [ -f "$HOME/.docker/config.json" ]; then
    echo "💾 Backing up existing config to ~/.docker/config.json.backup..."
    cp "$HOME/.docker/config.json" "$HOME/.docker/config.json.backup"
fi

# Create clean config without credential helper
echo "✍️  Creating new Docker config without credential helper..."
cat > "$HOME/.docker/config.json" << 'EOF'
{
  "auths": {},
  "currentContext": "default"
}
EOF

echo ""
echo "✅ Docker credential configuration fixed!"
echo ""
echo "📋 Your new config at ~/.docker/config.json:"
cat "$HOME/.docker/config.json"
echo ""
echo "🚀 You can now run: docker compose up -d"
echo ""
