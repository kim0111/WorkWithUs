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
ufw allow 443/tcp   # reserved for later, once TLS is in place
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

Generate strong secrets:

```bash
openssl rand -base64 32   # Postgres password
openssl rand -base64 32   # MinIO password
openssl rand -base64 48   # JWT SECRET_KEY
```

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

On successful boot you should see backend `Uvicorn running on http://0.0.0.0:8000` and all 4 data services `service_healthy`.

## 5. Verify

From your laptop:

```bash
curl http://<droplet-ip>/api/v1/health   # or any public endpoint
curl -I http://<droplet-ip>/             # should return 200 with nginx
```

Open `http://<droplet-ip>` in a browser — the Vue SPA loads, and its calls to `/api/v1/*` resolve through nginx to the backend.

## 6. Deploying updates

```bash
cd /opt/WorkWithUs
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

`aerich upgrade` runs automatically on backend boot, so schema migrations apply on each deploy.

## 7. Adding a domain + TLS (later)

When a DNS record points at the droplet:

1. Add a `server_name yourdomain.com;` line to `nginx/nginx.conf`.
2. Swap the `nginx` service image for one that bundles Certbot, or add a sidecar. Recommended approach:
   - Add a `certbot` service sharing `/etc/letsencrypt` with nginx.
   - Run `docker compose run --rm certbot certonly --webroot ...` once to mint the cert.
   - Add a 443 listener to `nginx.conf` and redirect 80 → 443.

Alternatively, swap nginx for Caddy — it handles TLS automatically with a one-line config.

## 8. Exposing MinIO publicly (later)

If avatars/submissions need to be downloadable by browsers, MinIO has to be reachable from outside. Options:

- **Subdomain route**: add `files.yourdomain.com` → nginx → `minio:9000`. Object URLs become `https://files.yourdomain.com/bucket/key`.
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
- **502 from nginx on `/api/*`** — backend isn't listening yet. `docker compose logs backend` to see why.
- **Out of memory** — 4 GB is tight with all four datastores. `docker stats` to confirm. MongoDB is usually the heaviest; set `--wiredTigerCacheSizeGB=0.5` in the mongo command if needed.
- **Frontend shows but API calls 404** — nginx config missing or mis-ordered; the WebSocket `location ~ ^/api/v1/chat/ws/` block must appear before the generic `/api/` block.
