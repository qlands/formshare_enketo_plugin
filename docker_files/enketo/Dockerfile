FROM kobotoolbox/enketo_express:1.86.2

ENV ENKETO_SRC_DIR=/srv/src/enketo_express

WORKDIR ${ENKETO_SRC_DIR}

RUN npm install -g grunt-cli pm2

COPY . ${ENKETO_SRC_DIR}

RUN npm install --production

# Persist the `secrets` directory so the encryption key remains consistent.
RUN mkdir -p ${ENKETO_SRC_DIR}/setup/docker/secrets
RUN mkdir ${ENKETO_SRC_DIR}/checksum
VOLUME ${ENKETO_SRC_DIR}/setup/docker/secrets
VOLUME ${ENKETO_SRC_DIR}/config
COPY ./docker_files/config.json ${ENKETO_SRC_DIR}/config

EXPOSE 8005
ENTRYPOINT ["/srv/src/enketo_express/setup/docker/start.sh"]