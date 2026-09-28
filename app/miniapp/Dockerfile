# MiniApp maxveryMAX. Контекст сборки — корень app/ (нужен shared/).
#   docker compose --profile full up --build   (см. app/docker-compose.yml)
# Стадия 1: сборка Vite, стадия 2: раздача nginx'ом + прокси /api → backend.
FROM node:20-alpine AS build

WORKDIR /build

# зависимости — отдельным слоем ради кэша
COPY miniapp/package.json miniapp/package-lock.json* ./miniapp/
RUN cd miniapp && (npm ci --no-audit --no-fund || npm install --no-audit --no-fund)

# общий код (shared/categories.ts) и исходники мини-аппа
COPY shared/ ./shared/
COPY miniapp/ ./miniapp/
RUN cd miniapp && npm run build

FROM nginx:1.27-alpine

COPY miniapp/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /build/miniapp/dist /usr/share/nginx/html

EXPOSE 80
