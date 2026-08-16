#!/bin/sh
# Deploy the Rising Sun static site (both HTML files + img/) to the Hetzner server.
# Usage: ./deploy.sh            (run from anywhere; syncs this folder)
# Only changed files are transferred. Fill in the three settings below.
set -e
SERVER_USER="CHANGEME_USER"
SERVER_HOST="CHANGEME_HOST"           # e.g. 203.0.113.10 or example.com
WEB_ROOT="CHANGEME_WEBROOT"           # e.g. /var/www/html  -> site lives at /risingsun/

cd "$(dirname "$0")"
ssh "$SERVER_USER@$SERVER_HOST" "mkdir -p '$WEB_ROOT/risingsun'"
rsync -avz --delete --progress \
  --include='rising-sun-org-chart.html' \
  --include='rising-sun-atlas.html' \
  --include='img/***' \
  --exclude='*' \
  ./ "$SERVER_USER@$SERVER_HOST:$WEB_ROOT/risingsun/"
echo "Deployed. URLs:"
echo "  https://$SERVER_HOST/risingsun/rising-sun-org-chart.html"
echo "  https://$SERVER_HOST/risingsun/rising-sun-atlas.html"
