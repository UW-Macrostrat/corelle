#!/bin/sh

# If CORELLE_API_URL is set in the environment, substitute it in index.html
if [ -n "$CORELLE_API_URL" ]; then
  echo "Substituting CORELLE_API_URL in index.html"
  sed -i "s|window.corelleAPIBaseURL = null|window.corelleAPIBaseURL = '$CORELLE_API_URL'|g" index.html
else
  echo "CORELLE_API_URL is not set, using default value."
fi

# Start caddy
caddy run --config /etc/caddy/Caddyfile --adapter caddyfile
