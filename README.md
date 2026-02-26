# Waygo Backend

**Owner / Creator:** playfabauthenticatorsettings_ on Discord  
**Contact for anything related to this project:** playfabauthenticatorsettings_ on Discord

---

## ⚠️ LEGAL NOTICE — READ BEFORE DOING ANYTHING

This repository is **publicly visible for transparency only**.  
Public visibility does **NOT** grant you any license or permission to use this code.

**You MAY NOT:**
- Copy, clone, or fork this repository for your own use
- Use any part of this code in your own projects
- Redistribute, sell, or sublicense this software
- Deploy your own instance of this backend

**Unauthorized use will result in legal action. You will be sued.**

See [LICENSE](./LICENSE) for full terms.

---

## Waygo

Waygo is a proprietary real-time communication platform — servers, channels, messaging, and voice — built with FastAPI.

---

## Stack

- FastAPI + SQLAlchemy + Pydantic v2
- JWT authentication (access + refresh tokens)
- Bcrypt password hashing
- Mothership Key middleware (all requests validated)
- IP tracking + automatic IP banning on repeated unauthorized attempts
- SQLite (dev) / PostgreSQL (prod)

---

## Deployment (Vercel)

1. Push this repo to GitHub
2. Import into Vercel
3. Set these **Environment Variables** in Vercel dashboard (Settings → Environment Variables):

| Variable | Description |
|---|---|
| `DATABASE_URL` | Your DB connection string (e.g. `sqlite:///./waygo.db` or Postgres URL) |
| `SECRET_KEY` | Long random string for JWT signing |
| `MOTHERSHIP_KEY` | Your secret Mothership Key — keep this private |
| `ENVIRONMENT` | `production` |
| `ALLOWED_ORIGINS` | Your frontend URL or `*` |

> **Never put your Mothership Key in code or commit it to git.**  
> Always use Vercel Environment Variables.

4. Deploy. Homepage will show at your Vercel URL.

---

## Running Locally

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env and fill in your values
uvicorn app.main:app --reload
```

API docs: `http://localhost:8000/api/v1/docs`

---

## Mothership Key

Every API request must include the header:
```
X-Mothership-Key: YOUR-KEY-HERE
```

Wrong key → IP flagged → after 10 attempts → permanent IP ban.  
The key is set via environment variable `MOTHERSHIP_KEY` — never hardcoded.

---

*All rights reserved. playfabauthenticatorsettings_ on Discord.*
