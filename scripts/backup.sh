#!/bin/bash

# Cloud Access Visualizer Backup Script
# Usage: ./scripts/backup.sh [backup_name]

set -e

BACKUP_NAME=${1:-"backup_$(date +%Y%m%d_%H%M%S)"}
BACKUP_DIR="./backups"
CONTAINER_NAME="cloud-access-mongodb"

echo "💾 Starting backup process..."

# Check if MongoDB container is running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "❌ MongoDB container '$CONTAINER_NAME' is not running."
    echo "   Please start the services first with: docker-compose up -d"
    exit 1
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Create MongoDB backup
echo "📦 Creating MongoDB backup..."
docker exec "$CONTAINER_NAME" mongodump \
    --authenticationDatabase admin \
    --username admin \
    --password cloudaccess123 \
    --db cloud_access \
    --out "/tmp/$BACKUP_NAME"

# Copy backup from container to host
echo "📁 Copying backup files..."
docker cp "$CONTAINER_NAME:/tmp/$BACKUP_NAME" "$BACKUP_DIR/"

# Create compressed archive
echo "🗜️  Compressing backup..."
cd "$BACKUP_DIR"
tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"
rm -rf "$BACKUP_NAME"

# Cleanup container backup
docker exec "$CONTAINER_NAME" rm -rf "/tmp/$BACKUP_NAME"

echo "✅ Backup completed successfully!"
echo "📂 Backup location: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
echo ""
echo "📖 To restore this backup, use:"
echo "   ./scripts/restore.sh ${BACKUP_NAME}.tar.gz"