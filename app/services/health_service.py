from app.config.database import check_database_connection
import os

def get_health_status():
    return {"status": "ok"}

def get_readiness_status():
    check_database_connection()

    return {
        "status": "ready",
        "db": "connected",
    }

def get_version_status():
    return {
        "app": "task-api",
        "version": os.getenv("APP_VERSION", "local")
    }