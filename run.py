import argparse
import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from server import run_server


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(),
            RotatingFileHandler(
                filename=logs_dir / "todo_api.log",
                maxBytes=5 * 1024 * 1024,  # 5MB
                backupCount=3,
                encoding='utf-8'
            )
        ]
    )

    logging.getLogger("http.server").setLevel(logging.WARNING)

    return logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="HTTP Server for managing todo list",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "-p", "--port",
        type=int,
        default=8000,
        help="Server port (default: 8000)"
    )

    parser.add_argument(
        "-H", "--host",
        type=str,
        default="localhost",
        help="Server host (default: localhost)"
    )

    parser.add_argument(
        "-l", "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: INFO)"
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress console output (logs only to file)"
    )

    args = parser.parse_args()

    logger = setup_logging(args.log_level)

    if args.quiet:
        for handler in logging.root.handlers:
            if isinstance(handler, logging.StreamHandler):
                logging.root.removeHandler(handler)

    try:
        logger.info("╔══════════════════════════════════════════╗")
        logger.info("║         Simple Todo Api v1.0             ║")
        logger.info("║         HTTP Task Management    :)       ║")
        logger.info("╚══════════════════════════════════════════╝")
        logger.info("")
        logger.info("Server URL: http://%s:%d", args.host, args.port)
        logger.info("Storage: tasks.txt")
        logger.info("Logs: logs/todo_api.log")
        logger.info("")
        logger.info("Available endpoints:")
        logger.info("  POST /tasks                 - Create new task")
        logger.info("  GET  /tasks                 - Get all tasks")
        logger.info("  POST /tasks/{id}/complete   - Mark task as completed")
        logger.info("")
        logger.info("Press Ctrl+C to stop the server")
        logger.info("=" * 50)

        logger.debug("Configuration details:")
        logger.debug("  Host: %s", args.host)
        logger.debug("  Port: %d", args.port)
        logger.debug("  Log level: %s", args.log_level)

        run_server(args.host, args.port)

    except KeyboardInterrupt:
        logger.info("")
        logger.info("Server stopped by user")
        sys.exit(0)

    except Exception as e:
        logger.critical("Failed to start server: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()