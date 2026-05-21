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

## Tests

```bash
cd backend && source .venv/bin/activate && pytest
```

## Mail

Set `MAIL_DRIVER=log` (default) for local development. Use Mailgun env vars from `.env.example` in production.
