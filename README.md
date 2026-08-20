# motorshop_Backend

A REST API for the **MotoShop** web platform, built with **FastAPI** + **SQLAlchemy** and connected to a **PostgreSQL** database hosted on **Render**.

## Features

- ✅ Website content APIs (products, services, contact form)
- ✅ Admin dashboard statistics
- ✅ Authentication: register, login, forgot / reset password (JWT)
- ✅ CRUD operations for products and services (admin only)
- ✅ User profile management and admin user management
- ✅ Role-based access: `admin` and `user`

## Tech Stack

- **Framework:** FastAPI (Python 3.10+)
- **ORM:** SQLAlchemy 2.0
- **Database:** PostgreSQL 16 (Render)
- **Auth:** JWT (python-jose) + bcrypt password hashing
- **Validation:** Pydantic v2 + pydantic-settings

## Project Structure

```
Backend/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── api/v1/              # REST routers
│   │   ├── auth.py          # register, login, forgot/reset password, /me
│   │   ├── users.py         # profile + admin user management
│   │   ├── products.py      # product CRUD
│   │   ├── services.py      # service CRUD
│   │   ├── contacts.py      # contact form submit + admin list
│   │   ├── dashboard.py     # admin stats
│   │   └── deps.py          # JWT + role guards
│   ├── core/
│   │   ├── config.py        # settings read from file.env
│   │   └── security.py      # bcrypt + JWT helpers
│   ├── crud/                # database operations
│   ├── db/
│   │   ├── base.py          # engine / session / Base
│   │   └── init_db.py       # create tables + seed admin
│   ├── models/              # SQLAlchemy models
│   └── schemas/             # Pydantic schemas
├── file.env                 # environment variables (PostgreSQL connection)
├── requirements.txt
└── run.py                   # local dev server launcher
```

## Setup

```bash
cd Backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

## Configure `file.env`

Edit `file.env` and replace it with the **External Database URL** from Render
(Dashboard → your database → Connections → **External Database URL**):

```
DATABASE_URL=postgresql://bookstore_rxpj_user:YOUR_DATABASE_PASSWORD@dpg-...-a.<region>.postgres.render.com:5432/bookstore_rxpj
```

> ⚠️ The **internal** hostname shown in Render (e.g. `dpg-da2ma2gae00c73cg0q50-a`)
> is **not reachable from your computer** — it only works inside Render's own network.
> Copy the full **External Database URL** instead.

### Local testing without Render (SQLite)

To run the API right now without the Render database, open `file.env`, comment the
`DATABASE_URL=postgresql://...` line and uncomment:

```
DATABASE_URL=sqlite:///./local.db
```

## Run

```bash
python run.py                # http://127.0.0.1:8000
```

- Interactive API docs (Swagger UI): http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

First run creates all tables automatically. To also seed the default admin account:

```bash
python -m app.db.init_db
```

> Default admin: `admin@bookstore.com` / `admin123`  (change it after first login!)

## Deploy with Docker

The repo includes a `Dockerfile` (gunicorn + uvicorn workers) and a `.dockerignore`.

Build and run it locally:

```bash
docker build -t motorshop-backend .
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DATABASE \
  -e SECRET_KEY=change-me-to-a-long-random-string \
  motorshop-backend
```

> `file.env` is gitignored and **never** copied into the image. On the deploy
> platform (e.g. Render → your service → **Environment**), set the same variables
> as env vars: `DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`.
> The app starts even if the database is unreachable, so `/docs` is always available.

## API Overview

## API Overview

| Method | Endpoint                    | Access  | Description                    |
|--------|-----------------------------|---------|--------------------------------|
| POST   | /api/v1/auth/register       | Public  | Create a new account           |
| POST   | /api/v1/auth/login          | Public  | Login → JWT token              |
| POST   | /api/v1/auth/forgot-password| Public  | Get password reset token       |
| POST   | /api/v1/auth/reset-password | Public  | Reset password with token      |
| GET    | /api/v1/auth/me             | User    | Current user profile           |
| GET    | /api/v1/users               | Admin   | List all users                 |
| PATCH  | /api/v1/users/{id}          | Admin   | Update role / active status    |
| GET    | /api/v1/products            | Public  | List active products           |
| GET    | /api/v1/products/{id}       | Public  | Product detail                 |
| POST   | /api/v1/products            | Admin   | Create product                 |
| PUT    | /api/v1/products/{id}       | Admin   | Update product                 |
| DELETE | /api/v1/products/{id}       | Admin   | Delete product                 |
| GET    | /api/v1/services            | Public  | List active services           |
| POST/PUT/DELETE | /api/v1/services... | Admin   | Service CRUD                   |
| POST   | /api/v1/contacts            | Public  | Submit contact form            |
| GET    | /api/v1/contacts            | Admin   | List contact messages          |
| GET    | /api/v1/dashboard/stats     | Admin   | Admin dashboard statistics     |

### Login note

`/api/v1/auth/login` expects OAuth2 **form data** (`username` = email, `password` = password),
which matches the built-in **Authorize** button in Swagger UI.

### Forgot / reset password (demo mode)

`forgot-password` returns the reset token in the response body so you can test the
full flow without an email server. In production, email the link instead:
`http://localhost:3000/reset-password?token=<reset_token>`.

## Troubleshooting

### "This site can't be reached / 127.0.0.1 refused to connect"

The server is not running, or it crashed on startup. Start it and read the console output:

```bash
python run.py
```

If you see `Application startup failed` with
`could not translate host name "dpg-..."` or `password authentication failed`:

1. Your `DATABASE_URL` is using Render's **internal** hostname — replace it with the
   **External Database URL** (Connections → External Database URL).
2. Replace `YOUR_DATABASE_PASSWORD` with the real password.
3. **Or** use the SQLite fallback for local testing (see above) — the server will
   start instantly with no Render connection needed.

> The app is built so that even if the database is unreachable, the API server still
> starts (it logs a clear warning) so `/docs` is always accessible.

### Wrong port

Default port is `8000`. Open `http://127.0.0.1:8000/docs`, not `:80` or another port.

