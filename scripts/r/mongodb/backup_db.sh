mkdir -p ~/mongodb_backups/
cd ~/mongodb_backups/

echo "Backup database {{MONGO_DB_NAME}}"
mongodump --gzip --db={{MONGO_DB_NAME}} --archive={{MONGO_DB_NAME}}.gz
