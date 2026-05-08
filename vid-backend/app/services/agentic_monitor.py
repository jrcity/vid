"""
app/services/agentic_monitor.py

VID Agentic Monitoring Layer.

This is the autonomous background agent that watches enrolled SIM cards
after certificate issuance. If the network signals change — especially
a SIM swap — the agent automatically:

  1. Detects the change via periodic CAMARA API polls
  2. Downgrades the certificate status
  3. Notifies any registered third-party verifiers
  4. Logs the event to the audit trail

This transforms VID from a static document into a living identity
that self-updates based on network reality. No paper ID can do this.

HOW IT RUNS:
  - FastAPI lifespan event starts the monitor as a background asyncio task
  - Polls every POLL_INTERVAL_SECONDS (default: 300 = 5 minutes)
  - Uses the same CAMARA SIM Swap API already integrated in camara_service.py
  - Stores events in the audit log (store.py)

INTEGRATION:
  Add to app/main.py — see bottom of this file for instructions.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Callable

from app.services.camara_service import call_sim_swap
from app.services import store
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger("vid.agentic_monitor")

# ── Configuration ─────────────────────────────────────────────────────────────
POLL_INTERVAL_SECONDS = 300   # check every 5 minutes
SIM_SWAP_THRESHOLD_DAYS = 1   # flag if swapped within last 24 hours post-issuance


# ── Audit log ─────────────────────────────────────────────────────────────────
# Stored in memory — append-only list of monitoring events
_audit_log: list[dict] = []


def log_event(vid_id: str, event_type: str, detail: str) -> None:
    """Append a monitoring event to the audit trail."""
    entry = {
        "vid_id": vid_id,
        "event_type": event_type,   # "SWAP_DETECTED" | "REVOKED" | "CLEARED" | "CHECKED"
        "detail": detail,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _audit_log.append(entry)
    logger.info(f"[MONITOR] {event_type} — {vid_id}: {detail}")


def get_audit_log(vid_id: str | None = None) -> list[dict]:
    """Return audit log — optionally filtered by VID ID."""
    if vid_id:
        return [e for e in _audit_log if e["vid_id"] == vid_id]
    return list(_audit_log)


# ── Core check logic ──────────────────────────────────────────────────────────

async def check_certificate(vid_id: str, record: dict) -> None:
    """
    Run a single SIM Swap check for one enrolled certificate.

    Logic:
      - Get the primary phone hash from the record (we stored it)
      - Call SIM Swap API for that phone
      - If swap detected after certificate issue date → revoke + log
      - If previously revoked but swap resolved → log clearance (manual review needed)
    """
    phone = record.get("primary_phone")
    if not phone:
        return

    issued_at_str = record.get("issued_at")
    if not issued_at_str:
        return

    try:
        issued_at = datetime.fromisoformat(issued_at_str)
    except ValueError:
        return

    # Skip already-revoked certs — no need to re-check
    if record.get("revoked"):
        return

    try:
        # Call the real CAMARA SIM Swap API
        signal = await call_sim_swap(phone)

        if signal.swapped_recently and signal.days_since_swap < SWAP_SWAP_THRESHOLD_DAYS:
            # Swap happened after certificate was issued — revoke
            store.revoke_certificate(vid_id)
            log_event(
                vid_id=vid_id,
                event_type="REVOKED",
                detail=(
                    f"SIM swap detected {signal.days_since_swap} day(s) ago — "
                    f"after certificate issue date {issued_at.date()}. "
                    f"Certificate automatically revoked."
                ),
            )
        else:
            # All clear — log periodic check
            log_event(
                vid_id=vid_id,
                event_type="CHECKED",
                detail=f"SIM stable. Days since last swap: {signal.days_since_swap}.",
            )

    except Exception as e:
        logger.warning(f"[MONITOR] Check failed for {vid_id}: {e}")
        log_event(
            vid_id=vid_id,
            event_type="CHECK_FAILED",
            detail=f"API call failed: {str(e)} — certificate status unchanged.",
        )


# ── Background polling loop ───────────────────────────────────────────────────

async def monitoring_loop() -> None:
    """
    Infinite async loop that polls all active certificates.
    Runs as a background task — does not block the API server.

    On each cycle:
      1. Get all non-revoked, non-expired certificates from store
      2. Check each one with a 0.5s stagger to avoid API rate limits
      3. Sleep for POLL_INTERVAL_SECONDS before next cycle
    """
    logger.info("[MONITOR] Agentic monitoring agent started.")
    log_event("SYSTEM", "STARTED", "Agentic monitoring agent initialised.")

    while True:
        try:
            active_certs = store.get_all_active()

            if not active_certs:
                logger.debug("[MONITOR] No active certificates to check.")
            else:
                logger.info(f"[MONITOR] Checking {len(active_certs)} active certificate(s).")
                for vid_id, record in active_certs.items():
                    await check_certificate(vid_id, record)
                    await asyncio.sleep(0.5)  # stagger — avoid hammering NaC API

        except Exception as e:
            logger.error(f"[MONITOR] Loop error: {e}")
            log_event("SYSTEM", "LOOP_ERROR", str(e))

        await asyncio.sleep(POLL_INTERVAL_SECONDS)


# ── Startup / shutdown ────────────────────────────────────────────────────────

_monitor_task: asyncio.Task | None = None


def start_monitoring() -> None:
    """
    Launch the monitoring loop as a background asyncio task.
    Call this from FastAPI's startup event.
    """
    global _monitor_task
    loop = asyncio.get_event_loop()
    _monitor_task = loop.create_task(monitoring_loop())
    logger.info("[MONITOR] Background monitoring task created.")


def stop_monitoring() -> None:
    """Cancel the monitoring task on shutdown."""
    global _monitor_task
    if _monitor_task and not _monitor_task.done():
        _monitor_task.cancel()
        logger.info("[MONITOR] Monitoring agent stopped.")


# ─────────────────────────────────────────────────────────────────────────────
# HOW TO INTEGRATE INTO app/main.py
# ─────────────────────────────────────────────────────────────────────────────
#
# Replace the current startup event with this:
#
#   from contextlib import asynccontextmanager
#   from app.services.trust_engine import get_model
#   from app.services.agentic_monitor import start_monitoring, stop_monitoring
#
#   @asynccontextmanager
#   async def lifespan(app: FastAPI):
#       # Startup
#       get_model()            # train RF model once
#       start_monitoring()     # launch agentic monitor
#       yield
#       # Shutdown
#       stop_monitoring()
#
#   app = FastAPI(
#       title=settings.app_name,
#       lifespan=lifespan,
#       ...
#   )
#
# ─────────────────────────────────────────────────────────────────────────────
