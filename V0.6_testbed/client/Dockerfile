# client/Dockerfile — 会議室予約システム フロントエンド(ビルド不要のプレーンHTML/CSS/JS)
#
# ★P302作成★ 本サンドボックスにはDockerデーモンが存在しないため未検証(server/Dockerfileと同様)。
# フロントエンドはnpmビルドを持たない静的ファイル一式のため、静的ファイルサーバーで配信する。

FROM python:3.11-slim

WORKDIR /srv

COPY index.html ./
COPY css ./css
COPY js ./js

EXPOSE 8080

CMD ["python3", "-m", "http.server", "8080", "--directory", "/srv"]
