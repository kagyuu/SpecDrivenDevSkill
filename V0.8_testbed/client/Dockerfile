# P302 (docs/P302-deliver.md 6章): distribution asset for the frontend
# service. Multi-stage: build the SPA with Node, then serve the static
# output with nginx (also acting as the same-origin reverse proxy to the
# backend - see nginx.conf and docs/P302-deliver.md 実行前チェック item 7).
#
# NOTE (docs/P302-deliver.md 実行前チェック item 6 / 9章): this Dockerfile was
# authored and reviewed for correctness, but its build/run has NOT been
# verified in this sandbox because the Docker CLI/daemon is not installed
# here (`docker --version` -> "command not found"). `npm run build` itself
# WAS verified directly on the host (not inside Docker) - see
# docs/P302-deliver.md 9章.

FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:1.27-alpine AS runtime
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
