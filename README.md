# UTILITYnet enrollment funnel

Greenfield replacement for the legacy GWT signup wizard.

## Stack

- **Backend:** FastAPI + SQLite (`backend/`)
- **Frontend:** SvelteKit (`apps/sveltekit-enroll/`)
- **Config:** `config/funnel.yaml` (rates/enums — no legacy GWT RPC)
- **Legal copy:** [`legacy/*.html`](legacy/) served by `/api/legal/{slug}` (see [`content/legal/README.md`](content/legal/README.md))

## Development

### Backend (port 8000)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

### Frontend (port 5173)

Proxies `/api` to the backend via Vite.

```bash
cd apps/sveltekit-enroll
npm install --force   # Node 23 may require --force; prefer Node 20 LTS
npm run dev
```

Legal pages (`/legal/*`) read **`legacy/*.html` directly in SvelteKit** — no API required for Terms/FAQ/Privacy.

## Docker (production-style local demo)

One URL: nginx on port **8080** → SvelteKit (`/`) + FastAPI (`/api`).

```bash
# From repo root
docker compose build
docker compose up

# Open http://localhost:8080/enroll
```

Optional env (Mailgun, public URL for emails):

```bash
cp .env.docker.example .env.docker
# edit PUBLIC_APP_URL / MAIL_* then:
docker compose --env-file .env.docker up -d
```

SQLite lives in the Docker volume `enrollment_data`. To reset drafts: `docker compose down -v` (destructive).

### 502 Bad Gateway on the server

Nginx returns **502** when it cannot reach the **web** (SvelteKit) or **api** container.

On the VPS, from the project directory:

```bash
docker compose ps
docker compose logs web --tail 80
docker compose logs nginx --tail 30
curl -s -o /dev/null -w "enroll:%{http_code}\n" http://127.0.0.1:8080/enroll
```

| What you see | What to do |
|--------------|------------|
| `web` **Restarting** or **Exit** | Read `docker compose logs web` — often **build OOM** or `npm run build` failed. Try `docker compose build --no-cache web` (needs ~1–2 GB RAM free). |
| `web` **Up (healthy)** but curl not 200 | Check `HTTP_PORT` in `.env.docker`; host nginx must proxy to that port (default **8080**). |
| Port **80** already in use | Do not set `HTTP_PORT=80` if **host nginx** uses 80. Keep Docker on **8080** and proxy from host nginx to `127.0.0.1:8080`. |
| `web` recreated, nginx older (502 after `--build web`) | Nginx cached old container IP — run `docker compose restart nginx` or pull latest `deploy/nginx.conf` (dynamic DNS). |

Full reset (keeps DB volume):

```bash
docker compose --env-file .env.docker down
docker compose --env-file .env.docker up -d --build
```

Set `PUBLIC_APP_URL=https://your-real-domain` in `.env.docker` (used by API + SvelteKit `ORIGIN`).

## Tests

```bash
cd backend && source .venv/bin/activate && pytest
```

## Mail

Set `MAIL_DRIVER=log` (default) for local development. Use Mailgun env vars from `.env.example` in production.
