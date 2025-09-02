FROM node:20 AS builder

# The following build sequence is adapted from the Macrostrat web repository
# Install rsync
RUN apt-get update && apt-get install -y rsync

ENV NODE_ENV=production

WORKDIR /usr/src/app
COPY .yarn/releases .yarn/releases
COPY .yarnrc.yml yarn.lock package.json ./

# Copy only the elements needed for a Yarn install to take advantage of
# Docker's layer caching
# This is complex because we are working with multiple workspaces.

# Copy package JSON files with wildcards
# This scoops up all package.json files in the directory and subdirectories
# to deal with Yarn workspaces. However it requires BUILDKIT to be enabled,
# which is done by setting DOCKER_BUILDKIT=1 in the environment
RUN --mount=type=bind,target=/docker-context \
    cd /docker-context/; \
    find . -name "package.json" -mindepth 0 -maxdepth 5 -exec cp --parents "{}" /usr/src/app/ \;

# Load the cache from the previous build
RUN --mount=type=cache,target=/yarn-cache \
     rsync -a /yarn-cache/ .yarn/cache/ \
  && yarn install --immutable \
  && rsync -a .yarn/cache/ /yarn-cache

# # Remove rsync
RUN apt-get remove -y rsync

COPY . ./

ENV NODE_ENV=development

RUN yarn run build:demo-app

FROM caddy:2.10-alpine AS production

COPY --from=builder /usr/src/app/packages/demo-app/dist /usr/share/caddy

WORKDIR /usr/share/caddy

COPY docker-command.sh /run/docker-command.sh

EXPOSE 80

CMD ["/run/docker-command.sh"]

