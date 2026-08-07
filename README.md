# Relay

Real-time chat rooms built with **Django**, **Channels**, and **Daphne**. Open a room, pick a display name, and messages broadcast live over WebSockets — with history persisted in SQLite.

![Relay stack](https://img.shields.io/badge/Django-5.2-092E20?logo=django) ![Channels](https://img.shields.io/badge/Channels-4-3B82F6) ![ASGI](https://img.shields.io/badge/ASGI-Daphne-orange)

## Features

- Named chat rooms with slug URLs
- Live WebSocket messaging and join/leave presence
- Message history stored in the database
- Guest display names (session-based, no account required)
- Responsive UI with connection status

## Quick start

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000), set a display name, create or join a room, and open the same room in a second browser tab to see live chat.

Optional env vars (see `.env.example`):

| Variable | Default | Purpose |
|----------|---------|---------|
| `DJANGO_SECRET_KEY` | insecure dev key | Django secret |
| `DJANGO_DEBUG` | `1` | Debug mode |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated hosts |
| `DJANGO_CORS_ALLOWED_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Allowed frontend origins |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Trusted browser origins |
| `DATABASE_URL` | unset | Postgres connection URL (e.g. from Neon/Render) |
| `REDIS_URL` | unset | Redis connection URL for Channels (optional) |
| `SMS_BACKEND` | auto-detected | `"afromessage"`, `"twilio"`, or `"console"` |
| `AFROMESSAGE_TOKEN` | unset | AfroMessage API token ([afromessage.com](https://afromessage.com)) |
| `AFROMESSAGE_IDENTIFIER_ID` | unset | Short-code identifier (if you have multiple) |
| `AFROMESSAGE_SENDER` | unset | Verified sender name (required outside beta) |
| `TWILIO_ACCOUNT_SID` | unset | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | unset | Twilio auth token |
| `TWILIO_PHONE_NUMBER` | unset | Twilio sending number |

## Architecture

```
Browser ──HTTP──▶ Django views (lobby / room)
       └─WebSocket─▶ ChatConsumer
                         │
                         ├─ channel layer group (broadcast)
                         └─ SQLite (Room, Message)
```

- **HTTP** — create rooms, set display name, render chat UI with recent history
- **WebSocket** — `ws/chat/<room_slug>/` joins a Channels group, fans out messages, and saves each message to the DB
- **Channel layer** — `InMemoryChannelLayer` for local demos (swap to Redis for multi-process deploy)

## Tests

```bash
python manage.py test chat
```

## Production notes

- Set a strong `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, and real `DJANGO_ALLOWED_HOSTS`
- If your frontend is on Vercel, set `DJANGO_CORS_ALLOWED_ORIGINS` and `DJANGO_CSRF_TRUSTED_ORIGINS` to the Vercel app URL
- Replace the in-memory channel layer with Redis (`channels-redis`) when running more than one worker
- Serve behind an ASGI server (Daphne / Uvicorn) with a reverse proxy that supports WebSockets
- For Render backend deployments, choose the repository root: `/home/chere970/projects/chat`

## License

MIT
