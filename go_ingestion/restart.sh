#!/usr/bin/env bash
set -e

echo "📦 Pulling latest code..."
cd ~/researchq/go_ingestion
git pull

echo "🔨 Building binary..."
CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags="-s -w" -o paper_ingestion ./

echo "🚚 Installing binary..."
sudo cp paper_ingestion /usr/local/bin/paper_ingestion
sudo chmod +x /usr/local/bin/paper_ingestion

echo "🔁 Restarting systemd service..."
sudo systemctl daemon-reload
sudo systemctl restart paper-ingestion

echo "📡 Service status:"
sudo systemctl status paper-ingestion --no-pager