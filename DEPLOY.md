# Deploying NexusHub to a DigitalOcean droplet

Target: Ubuntu 24.04 LTS, 2 vCPU / 4 GB RAM / 120 GB disk (FRA1 or similar).
Outcome: the app runs at `http://<droplet-ip>`; all databases, MinIO, and the backend API are on a private Docker network and not exposed to the internet.

## 1. One-time droplet setup

SSH in as root (or a sudoer):

```bash
ssh root@<droplet-ip>
```

Install Docker Engine + the Compose plugin:

```bash
apt-get update
apt-get install -y ca-certificates curl
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable --now docker
```

Firewall — only HTTP(S) and SSH reach the internet:

```bash
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
```

## 2. Clone the repo

```bash
cd /opt
git clone git@github.com:kim0111/WorkWithUs.git
cd WorkWithUs
```

(If the droplet can't reach GitHub over SSH, clone via HTTPS with a personal access token.)

## 3. Configure secrets

Two `.env` files are required. Neither is tracked in git — create them from the examples:

```bash
cp .env.prod.example .env
cp backend/.env.prod.example backend/.env
```

Generate strong secrets. Use `-hex` (URL-safe [0-9a-f]) — base64 output contains `/`, `+`, `=` which break URL parsing when embedded in `DATABASE_URL`:

```bash
openssl rand -hex 32   # Postgres password
openssl rand -hex 32   # MinIO password
openssl rand -hex 48   # JWT SECRET_KEY
```

The `POSTGRES_PASSWORD` in root `.env` must equal the password inside `DATABASE_URL` in `backend/.env`. Likewise `MINIO_ROOT_USER`/`MINIO_ROOT_PASSWORD` must equal `MINIO_ACCESS_KEY`/`MINIO_SECRET_KEY`.

Edit both files:

- `.env` — set `POSTGRES_PASSWORD`, `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`.
- `backend/.env` — set `DATABASE_URL` (with the same Postgres password), `SECRET_KEY`, `MINIO_ACCESS_KEY`/`MINIO_SECRET_KEY` (match the root `.env`), and optional `SMTP_USER`/`SMTP_PASSWORD` if you want outbound email.

## 4. First deploy

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

First build takes a few minutes (Vue build + Python deps). Watch the logs:

```bash
docker compose -f docker-compose.prod.yml logs -f
```

On successful boot you should see backend `Uvicorn running on http://0.0.0.0:8000`, all 4 data services `service_healthy`, and caddy `certificate obtained successfully` for `nexus-hub.asia` (this only happens if the domain's A record already points at the droplet).

## 5. Verify

From your laptop:

```bash
curl -I https://nexus-hub.asia/                   # should return 200 over TLS
curl https://nexus-hub.asia/api/v1/projects/      # or any public endpoint
```

Open `https://nexus-hub.asia` in a browser — the Vue SPA loads, and its calls to `/api/v1/*` resolve through caddy to the backend. Caddy also auto-redirects HTTP → HTTPS and renews certificates in the background.

## 6. Deploying updates

```bash
cd /opt/WorkWithUs
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

`aerich upgrade` runs automatically on backend boot, so schema migrations apply on each deploy.

## 7. Domain + TLS

TLS is automatic — caddy provisions Let's Encrypt certificates on first boot and renews them in the background.

To add another domain or subdomain:

1. Add an `A` record at the DNS provider pointing to the droplet IP.
2. Add the hostname to the top line of `caddy/Caddyfile`, e.g. `nexus-hub.asia, www.nexus-hub.asia, app.nexus-hub.asia {`.
3. Redeploy: `docker compose -f docker-compose.prod.yml up -d --build caddy`. Caddy mints the new cert within ~20 seconds.

Certificate state persists in the `caddy_data` named volume. Never delete it casually — Let's Encrypt rate-limits new issuance per domain.

## 8. Exposing MinIO publicly (later)

If avatars/submissions need to be downloadable by browsers, MinIO has to be reachable from outside. Options:

- **Subdomain route**: add `files.nexus-hub.asia` DNS + a new site block in `caddy/Caddyfile` reverse-proxying to `minio:9000`. Object URLs become `https://files.nexus-hub.asia/bucket/key`.
- **Proxy through the backend**: have the backend return presigned URLs with a rewritten hostname. More work; gives you auth.

Neither is required for the MVP deploy — internal-only MinIO works as long as all file access happens via the backend.

## 9. Backups (manual, minimum viable)

Nightly cron on the droplet:

```bash
# /etc/cron.daily/nexushub-backup
set -e
cd /opt/WorkWithUs
ts=$(date +%Y%m%d)
docker compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U postgres platform_db | gzip > /opt/backups/pg-$ts.sql.gz
docker compose -f docker-compose.prod.yml exec -T mongo \
  mongodump --archive --gzip > /opt/backups/mongo-$ts.archive.gz
find /opt/backups -type f -mtime +14 -delete
```

Copy backups off-droplet (rsync or DO Spaces) so a droplet failure doesn't lose data.

## Troubleshooting

- **Backend crash on first boot, `Aerich` errors** — the DB may not be ready despite healthcheck; `docker compose logs backend` will show the real error. Re-run `docker compose up -d` once.
- **Backend crash, `Port could not be cast to integer value` / `Port is not an integer`** — the password inside `DATABASE_URL` contains a URL-special character (`/`, `+`, `=`, `@`, `:`) that breaks URL parsing. Regenerate passwords with `openssl rand -hex 32` (URL-safe hex only). You must also wipe the postgres volume (`docker compose -f docker-compose.prod.yml down -v`) if it was initialized with the bad password, then bring it back up.
- **502 from caddy on `/api/*`** — backend isn't listening yet. `docker compose logs backend` to see why.
- **Caddy can't get a certificate** — confirm DNS resolves to the droplet IP (`dig +short nexus-hub.asia`), ports 80 and 443 are reachable externally, and the domain is listed at the top of `caddy/Caddyfile`. Let's Encrypt rate limits: 5 failures/hour/account, 50 certificates/week/domain.
- **Out of memory** — 4 GB is tight with all four datastores. `docker stats` to confirm. MongoDB is usually the heaviest; set `--wiredTigerCacheSizeGB=0.5` in the mongo command if needed.
- **Email not delivered** — DigitalOcean blocks outbound SMTP (port 25/465/587) on new droplets. Use an ESP (SendGrid/Mailgun/Resend) over port 2525 or HTTPS API, or open a DO ticket to request SMTP unblock.
