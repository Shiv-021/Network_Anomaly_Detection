"""
config/logging_config.py
==========================
Centralised logging setup.

Call configure_logging() once at process startup (from backend/app/factory.py).
After that, every module can do:

    import logging
    logger = logging.getLogger("anomaly-api")

Outputs:
  - Console   : human-readable text
  - logs/nad.log : newline-delimited JSON, rotated at 10 MB (5 backups kept)
"""

import json
import logging
import logging.handlers
import os
import traceback as _tb


class _JsonFormatter(logging.Formatter):
    """Emit each log record as a single-line JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts":      self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level":   record.levelname,
            "logger":  record.name,
            "message": record.getMessage(),
            "module":  record.module,
            "func":    record.funcName,
            "line":    record.lineno,
        }
        if record.exc_info:
            payload["exc"] = _tb.format_exception(*record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> None:
    """
    Configure root logger:
      - Console handler : readable text format
      - File handler    : JSON, rotated at 10 MB, 5 backups kept
    Level controlled by LOG_LEVEL env var (default INFO).
    """
    # Import here to avoid circular import at module load time
    from config.settings import LOG_DIR

    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    os.makedirs(LOG_DIR, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(level)

    # Console handler (human-readable)
    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)-8s] %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    root.addHandler(console)

    # File handler (JSON, rotating)
    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(LOG_DIR, "nad.log"),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(_JsonFormatter())
    root.addHandler(file_handler)

    # Quiet down Flask's built-in request logger (we log via middleware instead)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
