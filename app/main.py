import os
import psycopg2
from fastapi import FastAPI, HTTPException


app = FastAPI(
    title="Task API Platform",
    version="0.1.0",
)

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/readyz")
def readyz():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "db"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "taskdb"),
            user=os.getenv("DB_USER", "taskuser"),
            password=os.getenv("DB_PASSWORD", "taskpass"),
            connect_timeout=3,
        )

        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
            cur.fetchone()

        conn.close()

        return {
            "status": "ready",
            "db": "connected",
        }

    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "db": "disconnected",
                "error": str(e),
            },
        )