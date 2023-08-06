set -e
mkdir -p ~/mongodb_backups/
cd ~/mongodb_backups/

echo "Restore database {{MONGO_DB_NAME}} from {{MONGO_DB_NAME}}.gz"
mongorestore --drop --gzip --archive={{MONGO_DB_NAME}}.gz
