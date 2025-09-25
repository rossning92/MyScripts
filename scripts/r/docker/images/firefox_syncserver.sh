set -e

# https://github.com/mozilla-services/syncserver?tab=readme-ov-file#runner-under-docker
sudo mkdir -p /syncserver
sudo chown 1001:1001 /syncserver

docker run \
	-v /syncserver:/data \
	-p 5000:5000 \
	-e SYNCSERVER_PUBLIC_URL=http://localhost:5000 \
	-e SYNCSERVER_SECRET=98bfafcd5891bd5c3f2910aa6e312ef009e99185 \
	-e SYNCSERVER_SQLURI=sqlite:////data/syncserver.db \
	-e SYNCSERVER_BATCH_UPLOAD_ENABLED=true \
	-e SYNCSERVER_FORCE_WSGI_ENVIRON=false \
	-e PORT=5000 \
	mozilla/syncserver:latest
