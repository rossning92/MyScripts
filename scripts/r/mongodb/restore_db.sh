set -e
cd "${MY_DATA_DIR}/mongodb_backup/"

echo "Restore database ${MONGO_DB_NAME} from ${MONGO_DB_NAME}.gz"
mongorestore --drop --gzip --archive=${MONGO_DB_NAME}.gz
