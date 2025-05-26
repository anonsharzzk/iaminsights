#!/bin/bash

# Cloud Access Visualizer Restore Script
# Usage: ./scripts/restore.sh backup_file.tar.gz

set -e

BACKUP_FILE="$1"
BACKUP_DIR="./backups"
CONTAINER_NAME="cloud-access-mongodb"

if [ -z "$BACKUP_FILE" ]; then
    echo "❌ Please specify a backup file to restore."
    echo "Usage: ./scripts/restore.sh backup_file.tar.gz"
    echo ""
    echo "Available backups:"
    ls -la "$BACKUP_DIR"/*.tar.gz 2>/dev/null || echo "   No backups found."
    exit 1
fi

# Check if backup file exists
if [ ! -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
    echo "❌ Backup file '$BACKUP_DIR/$BACKUP_FILE' not found."
    exit 1
fi

# Check if MongoDB container is running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "❌ MongoDB container '$CONTAINER_NAME' is not running."
    echo "   Please start the services first with: docker-compose up -d"
    exit 1
fi

echo "⚠️  WARNING: This will replace all existing data!"
read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Restore cancelled."
    exit 1
fi

echo "📦 Starting restore process..."

# Extract backup
RESTORE_NAME=$(basename "$BACKUP_FILE" .tar.gz)
cd "$BACKUP_DIR"
tar -xzf "$BACKUP_FILE"

# Copy backup to container
echo "📁 Copying backup to container..."
docker cp "$RESTORE_NAME" "$CONTAINER_NAME:/tmp/"

# Restore MongoDB
echo "🔄 Restoring MongoDB..."
docker exec "$CONTAINER_NAME" mongorestore \
    --authenticationDatabase admin \
    --username admin \
    --password cloudaccess123 \
    --db cloud_access \
    --drop \
    "/tmp/$RESTORE_NAME/cloud_access"

# Cleanup
rm -rf "$RESTORE_NAME"
docker exec "$CONTAINER_NAME" rm -rf "/tmp/$RESTORE_NAME"

echo "✅ Restore completed successfully!"
echo "🔄 Please restart the services to ensure everything is working:"
echo "   docker-compose restart"