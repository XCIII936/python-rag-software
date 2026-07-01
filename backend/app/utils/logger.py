"""System logging utility that writes to the system_logs table."""

import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.log import SystemLog

# Standard Python logger
logger = logging.getLogger("course_agent")
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setFormatter(
    logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
)
logger.addHandler(console_handler)


def log_to_db(
    level: str,
    module: str,
    message: str,
    action: str = None,
    user_id: int = None,
    ip_address: str = None,
    request_path: str = None,
    duration_ms: int = None,
):
    """Write a log entry to the system_logs table."""
    try:
        db = SessionLocal()
        log_entry = SystemLog(
            level=level,
            module=module,
            action=action,
            message=message,
            user_id=user_id,
            ip_address=ip_address,
            request_path=request_path,
            duration_ms=duration_ms,
        )
        db.add(log_entry)
        db.commit()
        db.close()
    except Exception as e:
        logger.error(f"Failed to write log to DB: {e}")


def log_info(module: str, message: str, **kwargs):
    """Log an INFO level message."""
    logger.info(f"[{module}] {message}")
    log_to_db("INFO", module, message, **kwargs)


def log_warning(module: str, message: str, **kwargs):
    """Log a WARNING level message."""
    logger.warning(f"[{module}] {message}")
    log_to_db("WARNING", module, message, **kwargs)


def log_error(module: str, message: str, **kwargs):
    """Log an ERROR level message."""
    logger.error(f"[{module}] {message}")
    log_to_db("ERROR", module, message, **kwargs)
