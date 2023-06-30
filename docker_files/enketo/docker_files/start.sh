#!/bin/bash
set -e
if ! [ -f "${ENKETO_SRC_DIR}/config/config.json" ]; then
  cp ${ENKETO_SRC_DIR}/first_config/config.json ${ENKETO_SRC_DIR}/config/config.json
  cp ${ENKETO_SRC_DIR}/first_config/config.json ${ENKETO_SRC_DIR}/config/default-config.json
  cp ${ENKETO_SRC_DIR}/first_config/express.js ${ENKETO_SRC_DIR}/config/express.js
  cp ${ENKETO_SRC_DIR}/first_config/sample.env ${ENKETO_SRC_DIR}/config/sample.env
  cp ${ENKETO_SRC_DIR}/first_config/build.js ${ENKETO_SRC_DIR}/config/build.js
fi

source /etc/profile

cd ${ENKETO_SRC_DIR}/

# Create a config. file if necessary.
python setup/docker/create_config.py

# Run Enketo via PM2 Runtime (To support sigterm handling and
# logs are exposed e.g. via `docker logs enketoexpress_enketo_1`).
exec pm2-runtime app.js -n enketo
