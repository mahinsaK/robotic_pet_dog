#!/bin/bash

# setup_ngrok_relay.sh - Quick global access setup

echo "🌐 Setting up ngrok tunnel for global robot access"
echo "=================================================="

# Install ngrok if not present
if ! command -v ngrok &> /dev/null; then
    echo "📥 Installing ngrok..."
    if [[ $(uname -m) == "aarch64" ]]; then
        wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-arm64.tgz
        tar xvzf ngrok-v3-stable-linux-arm64.tgz
    else
        wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
        tar xvzf ngrok-v3-stable-linux-amd64.tgz
    fi
    sudo mv ngrok /usr/local/bin/
    echo "✅ ngrok installed"
fi

echo "🔧 Setup Instructions:"
echo "1. Sign up at https://ngrok.com (free account)"
echo "2. Get your authtoken from https://dashboard.ngrok.com/get-started/your-authtoken"
echo "3. Run: ngrok config add-authtoken YOUR_TOKEN"
echo "4. Start relay server: python3 relay_server.py"
echo "5. In new terminal, run: ngrok tcp 8765"
echo "6. Use the ngrok URL in your mobile app"
echo ""
echo "Example ngrok output:"
echo "tcp://0.tcp.ngrok.io:12345 -> localhost:8765"
echo "Use: ws://0.tcp.ngrok.io:12345 in mobile app"
echo ""
echo "⚠️  Free ngrok URLs change when restarted"
echo "💰 Paid ngrok plans provide permanent domains"
