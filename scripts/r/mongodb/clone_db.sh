mongodump --archive --db=$SRC_DB | mongorestore --archive --nsFrom="$SRC_DB.*" --nsTo="$DEST_DB.*"
