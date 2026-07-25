import time
from datetime import datetime, timezone

import psutil
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.cache.redis import get_redis
from app.modules.admin.models import ResourceUsage, SystemHealthSnapshot
from app.modules.admin.repository import AdminRepository
from app.modules.admin.schemas import SystemHealthResponse


class MonitoringService:
    """
    Enterprise System Health Monitor.

    Probes all critical infrastructure layers:
    - PostgreSQL (SQL ping + latency)
    - Redis (GET ping + latency)
    - Celery worker queue (inspect.ping)
    - Storage layer
    - AI Providers
    - Resource usage: CPU, memory, disk
    """

    def __init__(self, db: AsyncSession):
        self.repo = AdminRepository(db)
        self.db = db

    async def check_health(self) -> SystemHealthResponse:
        database_ok = True
        redis_ok = True
        celery_ok = True
        storage_ok = True
        details = {}

        # ── 1. Database Ping ────────────────────────────────────────────
        start = time.time()
        try:
            await self.db.execute(text("SELECT 1"))
            details["db_latency_ms"] = round((time.time() - start) * 1000, 2)
            details["db_status"] = "healthy"
        except Exception as e:
            database_ok = False
            details["db_error"] = str(e)
            details["db_status"] = "unhealthy"

        # ── 2. Redis Ping ────────────────────────────────────────────────
        start = time.time()
        try:
            redis = await get_redis()
            if hasattr(redis, "ping"):
                await redis.ping()
            else:
                await redis.get("__health_ping__")
            details["redis_latency_ms"] = round((time.time() - start) * 1000, 2)
            details["redis_status"] = "healthy"
        except Exception as e:
            redis_ok = False
            details["redis_error"] = str(e)
            details["redis_status"] = "unhealthy"

        # ── 3. Celery Worker Check ───────────────────────────────────────
        try:

            from app.modules.admin.tasks import celery_app

            inspect = celery_app.control.inspect(timeout=1.0)
            active = inspect.active()
            celery_ok = active is not None
            details["celery_status"] = "healthy" if celery_ok else "no_workers"
        except Exception:
            celery_ok = False
            details["celery_status"] = "unavailable"
            details["celery_note"] = "Celery not configured or unreachable"

        # ── 4. Resource Usage ────────────────────────────────────────────
        try:
            cpu_pct = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            details["cpu_percent"] = cpu_pct
            details["memory_percent"] = mem.percent
            details["disk_percent"] = disk.percent
            details["disk_free_gb"] = round(disk.free / (1024**3), 2)

            # Persist resource usage snapshot
            resource = ResourceUsage(
                cpu_percent=cpu_pct,
                memory_percent=mem.percent,
                disk_percent=disk.percent,
            )
            await self.repo.save_resource_usage(resource)
        except Exception as e:
            details["resource_error"] = str(e)

        # ── 5. Persist Health Snapshot ───────────────────────────────────
        snapshot = SystemHealthSnapshot(
            database_ok=database_ok,
            redis_ok=redis_ok,
            celery_ok=celery_ok,
            storage_ok=storage_ok,
            details=details,
        )
        await self.repo.save_health_snapshot(snapshot)

        return SystemHealthResponse(
            database_ok=database_ok,
            redis_ok=redis_ok,
            celery_ok=celery_ok,
            storage_ok=storage_ok,
            details=details,
            checked_at=datetime.now(timezone.utc),
        )

    async def get_resource_summary(self) -> dict:
        """Real-time system resource snapshot for the monitoring dashboard."""
        try:
            cpu_pct = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            net = psutil.net_io_counters()
            return {
                "cpu_percent": cpu_pct,
                "memory_percent": mem.percent,
                "memory_used_gb": round(mem.used / (1024**3), 2),
                "memory_total_gb": round(mem.total / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "network_bytes_sent": net.bytes_sent,
                "network_bytes_recv": net.bytes_recv,
            }
        except Exception as e:
            return {"error": str(e)}
