# Phonebook Application

A full-stack phonebook app built as a training project.

- **Backend:** Python + FastAPI + SQLAlchemy + PostgreSQL
- **Frontend:** Vue 3 + Vite + Vue Router + Axios
- **Deployment:** Docker Compose (backend, database, frontend services)

## Features

- JWT authentication (login with username or email, bcrypt password hashing)
- Add, view, update, and delete contacts (full CRUD via REST API)
- Dashboard with live statistics from the database
- Contact list with search (by name or phone number) and Google-style pagination
- **Import contacts from CSV and export contacts to CSV** (with a downloadable template, per-row validation reports, and duplicate handling)
- Input validation on both backend and frontend (E.164 phone format, unique phone/email)
- Responsive, modern dashboard UI (sidebar navigation, mobile hamburger menu)
- Seed script to create the first user and generate thousands of dummy contacts
- Auto-generated interactive API docs (Swagger UI)

## Architecture

```
+----------------+        /api/*         +----------------+        +----------------+
|   Frontend     | <-------------------> |    Backend     | <----> |   PostgreSQL   |
|  Vue 3/nginx   |   nginx proxy_pass    |  FastAPI :8000 |  db:   |   db :5432     |
|  http://:8080  |                       |                |  5432  |  (pgdata vol.) |
+----------------+                       +----------------+        +----------------+
```

All three services run in Docker Compose with `restart: unless-stopped`, so they
automatically come back after a Docker engine or Docker Desktop restart.

Authentication: the frontend stores the JWT in localStorage and sends it as a
`Authorization: Bearer <token>` header. All contact and stats endpoints require
a valid token; unauthenticated requests get `401` and the app redirects to
the login page. Passwords are stored as bcrypt hashes.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop) with the WSL 2 backend (Windows), or Docker Engine + Compose v2 (Linux/macOS)
- At least ~2 GB of free disk space for images and the database volume

## Quick start (Docker)

1. Create your environment file (database credentials):

   ```bash
   cp .env.example .env
   ```

2. Build the images:

   ```bash
   docker compose build
   ```

3. Start the application:

   ```bash
   docker compose up
   ```

   Or build and start in one step, detached (recommended):

   ```bash
   docker compose up --build -d
   ```

4. **Create the first user** (required before you can sign in):

   ```bash
   docker compose exec backend python seed.py --create-user --username demo
   ```

   You will be prompted for a password (or pass `--password 'your-password'`,
   or set the `SEED_PASSWORD` environment variable). Then sign in at
   <http://localhost:8080> with `demo` / your password.

5. (Optional) Generate dummy contacts for testing:

   ```bash
   docker compose exec backend python seed.py --count 1000
   ```

6. Open the application:

   | URL | What |
   | --- | --- |
   | <http://localhost:8080> | Frontend (Vue 3 app) |
   | <http://localhost:8000> | Backend API (FastAPI) |
   | <http://localhost:8000/docs> | Interactive Swagger API docs |

7. Stop the application:

   ```bash
   docker compose down
   ```

8. Stop the application **and delete all data** (removes the PostgreSQL volume):

   ```bash
   docker compose down -v
   ```

## Docker services

| Service   | Image / build        | Host port | Internal port | Notes                                    |
| --------- | -------------------- | --------- | ------------- | ---------------------------------------- |
| `frontend` | `./frontend` (Vite build → nginx) | 8080 → 80 | 80 | nginx proxies `/api/` to the backend     |
| `backend`  | `./backend` (Python 3.11-slim)   | 8000 → 8000 | 8000 | FastAPI/uvicorn; connects to PostgreSQL via the `db` service name |
| `db`       | `postgres:16-alpine`             | (internal) | 5432 | Persistent data in the `pgdata` volume; health-gated startup |

### PostgreSQL configuration

Configured through `.env` (see `.env.example`):

| Variable         | Default     | Where used                                              |
| ---------------- | ----------- | ------------------------------------------------------- |
| `POSTGRES_USER`  | `phonebook` | superuser created by the postgres image                 |
| `POSTGRES_PASSWORD` | `phonebook` | password for that user                              |
| `POSTGRES_DB`    | `phonebook` | database created on first startup                       |
| `SECRET_KEY`     | (empty)     | JWT signing key; set a long random string in `.env`     |

- The backend connects to `postgresql+psycopg2://<user>:<password>@db:5432/<db>` —
  the Compose **service name** `db`, never `localhost` (inside a container,
  `localhost` refers to the container itself).
- PostgreSQL data persists in the `phonebookpython_pgdata` Docker volume.
  `docker compose down` keeps the volume; `docker compose down -v` deletes it.
- The backend waits for PostgreSQL via `depends_on: condition: service_healthy`
  (`pg_isready` healthcheck), and creates the `contacts` and `users` tables on startup.
- If `SECRET_KEY` is empty, the backend generates an ephemeral random key on
  each start (fine for demos, but users must log in again after a restart).

## API reference

| Method | Endpoint            | Description                                            | Auth |
| ------ | ------------------- | ------------------------------------------------------ | ---- |
| GET    | `/health`           | Health check                                           | —    |
| POST   | `/auth/login`       | Login with username or email, returns a JWT            | —    |
| GET    | `/auth/me`          | Currently logged-in user                               | ✓    |
| POST   | `/auth/logout`      | Logout (client discards the token)                     | —    |
| GET    | `/stats`            | Dashboard statistics + 5 most recent contacts          | ✓    |
| GET    | `/contacts`         | List contacts (`page`, `page_size`, `q` params; total in `X-Total-Count` header) | ✓ |
| POST   | `/contacts`         | Add a new contact                                      | ✓ |
| POST   | `/contacts/import`  | Import contacts from an uploaded CSV file              | ✓ |
| GET    | `/contacts/export`  | Download contacts as CSV (`q` param filters the export) | ✓ |
| GET    | `/contacts/{id}`    | Retrieve a specific contact                            | ✓ |
| PUT    | `/contacts/{id}`    | Update a specific contact (only provided fields change) | ✓ |
| DELETE | `/contacts/{id}`    | Delete a specific contact                              | ✓ |

Call an authenticated endpoint with the header `Authorization: Bearer <access_token>`.

Request/response example (`POST /contacts`):

```json
{
  "name": "John Doe",
  "phone_number": "+1234567890",
  "email": "john@example.com",
  "address": "123 Main St"
}
```

Validation rules:
- `name` is required (max 255 chars)
- `phone_number` is required, unique, and must match E.164 format, e.g. `+1234567890`
- `email` is optional but must be a valid email and unique when provided
- `address` is optional

Error responses: `401` (not authenticated or bad credentials), `404` (contact not found), `409` (duplicate phone number or email),
`422` (validation error).

## Authentication

- **Login** — `POST /auth/login` with `{"username": "...", "password": "..."}`
  (the `username` field accepts a username *or* an email). Returns
  `{"access_token", "token_type": "bearer", "user": {...}}`.
- Passwords are hashed with **bcrypt**; only the hash is stored.
- Tokens are **JWTs** signed with `SECRET_KEY` (from `.env`) and expire
  after 12 hours. The frontend stores the token in localStorage and
  sends it on every request; a `401` response logs the user out.
- Contact and stats endpoints require the header
  `Authorization: Bearer <token>`.

**Create the first/demo user** (there are no users by default):

```bash
docker compose exec backend python seed.py --create-user --username demo
# prompts for a password, or use:
docker compose exec backend python seed.py --create-user --username demo --password 'your-password'
```

## Seeding dummy data

`backend/seed.py` generates realistic dummy contacts with Faker.
Phone numbers and emails are generated uniquely, so existing
contacts are never duplicated or modified.

```bash
docker compose exec backend python seed.py --count 100     # 100 contacts
docker compose exec backend python seed.py --count 1000    # 1,000 contacts
docker compose exec backend python seed.py --count 5000    # 5,000 contacts
```

Both actions can be combined:

```bash
docker compose exec backend python seed.py --create-user --username demo --count 1000
```

Without Docker (from the `backend` folder, with the venv active):

```bash
python seed.py --create-user --username demo
python seed.py --count 1000
```

The seed operation is manual — it never runs automatically on startup.

## CSV import & export

### Importing contacts

On the **Contacts** page, click **Import CSV** and choose a `.csv` file
(UTF-8 encoded). A sample template is available via the **CSV template**
link next to the page-size selector. The CSV must have a header row with
these columns:

```csv
name,phone_number,email,address
Rahul Sharma,+919876543210,rahul@example.com,Pune
Amit Patil,+919876543211,amit@example.com,Mumbai
```

| Column        | Required | Rules (same as the web form)                              |
| ------------- | -------- | --------------------------------------------------------- |
| `name`        | Yes      | 1–255 characters                                          |
| `phone_number`| Yes      | Unique, E.164 format (`+` followed by 1–15 digits)        |
| `email`       | No       | Valid email, unique when provided; empty cell = no email  |
| `address`     | No       | Free text; empty cell = no address                        |

Column names are matched case-insensitively and tolerate surrounding
whitespace; extra columns are ignored, and `email`/`address` columns may
be omitted entirely.

**How results are reported.** After the import the page shows a summary
with the total rows processed, contacts imported, duplicates skipped, and
failed rows — plus a per-row error list with the file row number and the
validation reason. Invalid rows are never silently skipped.

**Duplicates.** Rows whose phone number or email already exists (or appears
twice in the same file) are counted as duplicates and skipped — they do
not abort the import, and existing contacts are never modified.

**Limits.** Uploads are capped at **5 MB** and **5,000 rows** per file
(larger files are rejected with `413`). All valid, non-duplicate rows are
inserted in a **single transaction** — a database error rolls back the
entire import, so the phonebook never ends up partially updated.

### Exporting contacts

Click **Export CSV** on the Contacts page. The backend generates a
`phonebook-export-<date>.csv` and downloads it. The export contains
**every contact you are authorized to access** — not just the current
page — and respects an active search (only matching contacts are
exported). Empty result sets download a header-only CSV.

**CSV formula-injection protection:** values beginning with `=`, `+`, `-`,
or `@` (which includes every phone number, since they start with `+`) are
prefixed with a single quote (`'`) so spreadsheet applications treat them
as text instead of formulas. The data itself is preserved — Excel, LibreOffice
and Google Sheets display the value unchanged. Note that re-importing an
exported file requires removing that leading quote from the phone numbers
first, because the importer validates the strict E.164 format.

Both endpoints are also available via the API:

```bash
# Import (multipart form field "file")
curl -X POST http://localhost:8000/contacts/import \
  -H "Authorization: Bearer <token>" -F "file=@contacts.csv"

# Export (optionally filtered: ?q=Rahul)
curl http://localhost:8000/contacts/export \
  -H "Authorization: Bearer <token>" -o phonebook-export.csv
```

## Local development (without Docker)

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt

# Point at a local PostgreSQL (create the database first)
set DATABASE_URL=postgresql+psycopg2://phonebook:phonebook@localhost:5432/phonebook   # Windows
export DATABASE_URL=postgresql+psycopg2://phonebook:phonebook@localhost:5432/phonebook  # macOS/Linux

uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` requests to `http://localhost:8000`.

### Tests

```bash
cd backend
python -m pytest          # 50 tests, uses an in-memory SQLite DB (test-only)
```

Or inside the running container:

```bash
docker compose exec backend python -m pytest
```

## Project structure

```
PhonebookPython/
├── docker-compose.yml        # backend + db + frontend services
├── .env.example              # environment variables (database credentials, SECRET_KEY)
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── seed.py               # seed script: --create-user and --count N
│   ├── app/
│   │   ├── main.py           # FastAPI app + REST endpoints (auth + contacts + stats)
│   │   ├── models.py         # SQLAlchemy Contact and User models
│   │   ├── schemas.py        # Pydantic validation schemas
│   │   ├── crud.py           # database operations (incl. search/pagination/stats)
│   │   ├── auth.py           # bcrypt hashing, JWT creation/verification
│   │   └── database.py       # engine, session, Base (DATABASE_URL from env)
│   └── tests/                # pytest suite (in-memory SQLite, test-only)
└── frontend/
    ├── Dockerfile            # builds with Vite, serves with nginx
    ├── nginx.conf            # SPA routing + /api proxy to backend
    └── src/
        ├── api.js            # axios wrapper (Bearer token interceptor)
        ├── auth.js           # authentication state (token in localStorage)
        ├── router.js         # routes + auth guard (unauthenticated → /login)
        ├── App.vue           # app shell: sidebar (desktop) / hamburger (mobile)
        └── views/            # Dashboard, ContactList, ContactDetail, CreateContact, Profile, Login
```

## Troubleshooting

- **"Docker Desktop is unable to start" / WSL bootstrap errors (`0xc00000fd`, `0xc0000409`)**:
  1. Quit Docker Desktop fully (right-click the tray icon → Quit, or
     `Get-Process "Docker Desktop","com.docker.backend" | Stop-Process -Force` in PowerShell).
  2. Run `wsl --shutdown`.
  3. If it persists, reset the corrupted Docker WSL distro:
     `wsl --unregister docker-desktop` (this only wipes Docker's own WSL state —
     images/volumes — and Docker Desktop recreates it on next launch).
  4. Start Docker Desktop again and wait ~1–2 minutes for the engine.
  5. Re-run `docker compose up --build`.

- **"There is not enough space on the disk"** (Docker Desktop crash):
  Docker Desktop writes its WSL data disk and logs to the system drive. Free up
  space (clear `%TEMP%`, `npm cache clean --force`, remove old WSL data disks with
  `wsl --unregister <name>` for distros you no longer need) and restart Docker
  Desktop. Note where the data disk lives:
  `Get-ItemProperty "HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss\*" | Select-Object DistributionName, BasePath`.

- **Backend returns 500 right after `docker compose restart db`**: transient —
  PostgreSQL needs a few seconds to accept connections. Wait ~10 seconds and retry.

- **Port already in use:** change the host ports in `docker-compose.yml`
  (`"8000:8000"`, `"8080:80"`).

- **Reset the database:** `docker compose down -v` (deletes the `pgdata` volume),
  then `docker compose up --build`.

- **Check logs:** `docker compose logs backend`, `docker compose logs db`,
  `docker compose logs frontend`.

- **Verify PostgreSQL directly:**
  `docker compose exec db psql -U phonebook -d phonebook -c "SELECT * FROM contacts;"`

## Possible enhancements

- Pinia state management, unit tests for the frontend, and the
  `vue-phone-number-input` component for richer phone input. A basic GitHub
  Actions CI workflow for the backend tests is included in `.github/workflows`.
