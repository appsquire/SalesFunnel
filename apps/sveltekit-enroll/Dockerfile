FROM node:20-bookworm-slim AS builder

WORKDIR /app

COPY apps/sveltekit-enroll/package.json apps/sveltekit-enroll/package-lock.json ./
RUN npm ci

COPY apps/sveltekit-enroll/ ./
RUN npm run build && npm prune --production && test -f build/index.js

FROM node:20-bookworm-slim

WORKDIR /app

ENV NODE_ENV=production \
	HOST=0.0.0.0 \
	PORT=3000 \
	LEGACY_CONTENT_DIR=/legacy

COPY --from=builder /app/build ./build
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
COPY legacy /legacy

EXPOSE 3000

CMD ["node", "build"]
