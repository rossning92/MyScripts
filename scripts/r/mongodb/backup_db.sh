mkdir -p "${MY_DATA_DIR}/mongodb_backup/"
cd "${MY_DATA_DIR}/mongodb_backup/"

echo "Backup database \"${MONGO_DB_NAME}\"..."
mongodump --gzip --db=${MONGO_DB_NAME} --archive=${MONGO_DB_NAME}.gz
