"""EDP alerts: receives emergency events from student dashboards and shows them live."""

import json
import os
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qsl

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

DB_PATH = Path(os.environ.get("DB_PATH", "/data/alerts.db"))
EVENT_KEYS = ("event", "eventName", "event_name", "type", "name")
STUDENT_KEYS = ("student", "from", "author")

app = FastAPI(title="EDP Alerts")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """create table if not exists alerts (
            id integer primary key autoincrement,
            created_at text not null,
            event text not null,
            student text,
            payload text,
            origin text,
            user_agent text
        )"""
    )
    return conn


def clip(value, limit: int = 200) -> str | None:
    return None if value is None else str(value)[:limit]


def parse_body(raw: str) -> dict:
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {"event": parsed}
    except json.JSONDecodeError:
        form = dict(parse_qsl(raw))
        if form:
            return form
        return {"event": raw.strip()} if raw.strip() else {}


def first(payload: dict, keys: tuple[str, ...]):
    return next((payload[k] for k in keys if payload.get(k) not in (None, "")), None)


@app.post("/alerts")
@app.post("/")
async def create_alert(request: Request):
    raw = (await request.body())[:5000].decode(errors="replace")
    payload = parse_body(raw)
    event = clip(first(payload, EVENT_KEYS), 100)
    if not event:
        return JSONResponse(
            {
                "ok": False,
                "error": 'Missing "event". Send JSON like '
                '{"event": "fire", "student": "Jan Kowalski 12345"}',
            },
            status_code=400,
        )
    created_at = datetime.now(UTC).isoformat(timespec="seconds")
    with closing(db()) as conn, conn:
        cur = conn.execute(
            "insert into alerts (created_at, event, student, payload, origin, user_agent)"
            " values (?, ?, ?, ?, ?, ?)",
            (
                created_at,
                event,
                clip(first(payload, STUDENT_KEYS), 100),
                json.dumps(payload),
                clip(request.headers.get("origin")),
                clip(request.headers.get("user-agent")),
            ),
        )
    return {"ok": True, "received": event, "id": cur.lastrowid, "at": created_at}


@app.get("/alerts")
def list_alerts(limit: int = 100):
    with closing(db()) as conn:
        rows = conn.execute(
            "select id, created_at, event, student, origin from alerts order by id desc limit ?",
            (min(max(limit, 1), 1000),),
        ).fetchall()
    return {"ok": True, "count": len(rows), "alerts": [dict(r) for r in rows]}


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/", response_class=HTMLResponse)
def board():
    return (Path(__file__).parent / "board.html").read_text()
