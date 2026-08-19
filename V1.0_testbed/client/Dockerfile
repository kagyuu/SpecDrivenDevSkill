# client/Dockerfile — フロントエンド(React + TypeScript + Vite、ADR-001)。
# マルチステージビルド: Node.jsでビルドし、nginxで静的配信+/apiリバースプロキシ(nginx.conf参照)。
# docs/P302-deliver.md 作成時点ではDocker CLI自体がビルド環境に存在せず、実際のビルド・起動確認は
# できていない(docs/P302-deliver.md §9「最終確認結果」参照)。

FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:1.27-alpine AS runtime
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=5 \
  CMD wget -q -O /dev/null http://localhost/ || exit 1
