# edp-alerts

Endpoint for the Event Driven Programming task "Build a basic alerting system".
Student dashboards (built with base44) send a POST with an emergency event name; the
app stores it and shows all alerts on a live board.

Live: https://edp-alerts.codewithpeter.com

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/alerts` (or `/`) | Store an alert. Body: `{"event": "fire", "student": "Full name 12345"}` |
| GET | `/alerts?limit=100` | Latest alerts as JSON |
| GET | `/` | Live board (refreshes every 2 s) |
| GET | `/health` | Health check |

- `event` is required (`eventName`, `event_name`, `type`, `name` also accepted). `student` is optional.
- Plain text and form-encoded bodies work too (`curl -d fire ...`).
- CORS is open (`*`), so it can be called from any browser app.

```bash
curl -X POST https://edp-alerts.codewithpeter.com/alerts \
  -H 'Content-Type: application/json' \
  -d '{"event": "fire", "student": "Jan Kowalski 12345"}'
```

```js
fetch("https://edp-alerts.codewithpeter.com/alerts", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ event: "flood", student: "Jan Kowalski 12345" }),
});
```

## Run locally

```bash
pip install -r requirements.txt
DB_PATH=./alerts.db uvicorn main:app --reload
```

## Deploy

Coolify, Dockerfile build pack, port 8000, persistent volume at `/data` (SQLite `alerts.db`).
