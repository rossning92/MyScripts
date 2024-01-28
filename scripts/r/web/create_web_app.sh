set -e

if [[ -z "$GIT_REPO" ]]; then
    echo 'ERROR: must provide GIT_REPO'
    exit 1
fi
app_name="$(basename "$GIT_REPO")"

mkdir -p "$GIT_REPO"
cd "$GIT_REPO"

if [[ ! -f 'package.json' ]]; then
    # https://nextjs.org/docs/pages/api-reference/create-next-app
    yarn create next-app . --ts \
        --app \
        --eslint \
        --import-alias "@/*" \
        --src-dir \
        --tailwind \
        --use-yarn
fi

run_script r/web/add_daisyui_nextjs.sh

# Mongodb
yarn add mongodb@latest

if [[ ! -f ./src/lib/db.ts ]]; then
    mkdir -p ./src/lib/
    cat >./src/lib/db.ts <<EOF
import { Db, MongoClient } from "mongodb";

const dbName = "$app_name";

let db: Db;

export async function connectToDatabase() {
    if (!db) {
        const uri = "mongodb://127.0.0.1:27017";
        const client = new MongoClient(uri);
        await client.connect();
        db = client.db(process.env.DB_NAME || dbName);
        console.log("Connected to database.");
    }
    return db;
}
EOF
fi

PORT=3000 yarn run dev
