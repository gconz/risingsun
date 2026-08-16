#!/bin/sh
# Deploy the Rising Sun static site.
#   ./deploy.sh            -> commit any changes and push to GitHub Pages (default)
#   ./deploy.sh hetzner    -> rsync to the Hetzner server (fill in the CHANGEME values first)
# Live: https://gconz.github.io/risingsun/rising-sun-org-chart.html
#       https://gconz.github.io/risingsun/rising-sun-atlas.html
set -e
cd "$(dirname "$0")"

if [ "$1" = "hetzner" ]; then
  SERVER_USER="CHANGEME_USER"
  SERVER_HOST="CHANGEME_HOST"         # e.g. 203.0.113.10 or example.com
  WEB_ROOT="CHANGEME_WEBROOT"         # e.g. /var/www/html  -> site lives at /risingsun/
  ssh "$SERVER_USER@$SERVER_HOST" "mkdir -p '$WEB_ROOT/risingsun'"
  rsync -avz --delete --progress \
    --include='rising-sun-org-chart.html' --include='rising-sun-atlas.html' \
    --include='img/***' --exclude='*' \
    ./ "$SERVER_USER@$SERVER_HOST:$WEB_ROOT/risingsun/"
  echo "Deployed to https://$SERVER_HOST/risingsun/"
  exit 0
fi

git add -A
git diff --cached --quiet && echo "Nothing changed." || git commit -m "Update site $(date +%Y-%m-%d)"
git push origin main
echo "Pushed. GitHub Pages rebuilds in ~1 minute:"
echo "  https://gconz.github.io/risingsun/rising-sun-org-chart.html"
echo "  https://gconz.github.io/risingsun/rising-sun-atlas.html"
