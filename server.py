import logging
from http.server import HTTPServer
import signal
import sys

from handler import TodoRequestHandler

logger = logging.getLogger(__name__)


class TodoServer:

    def __init__(self, host: str = "localhost", port: int = 8000):
        self.host = host
        self.port = port
        self.server = HTTPServer((host, port), TodoRequestHandler)
        self._setup_signal_handlers()

        logger.debug("TodoServer initialized: %s:%d", host, port)

    def _setup_signal_handlers(self) -> None:
        signal.signal(signal.SIGINT, self._shutdown_signal_handler)
        signal.signal(signal.SIGTERM, self._shutdown_signal_handler)

        logger.debug("Signal handlers configured")

    def _shutdown_signal_handler(self, signum: int, frame) -> None:
        signal_name = signal.Signals(signum).name
        logger.info("Received signal %s (%d). Shutting down gracefully...",
                    signal_name, signum)
        self.stop()

    def start(self) -> None:
        try:
            logger.info("Todo API Server starting on http://%s:%d", self.host, self.port)
            logger.info("Storage file: tasks.txt")
            logger.info("Ready to accept connections")

            self.server.serve_forever()

        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received in serve_forever")
            self.stop()
        except OSError as e:
            logger.error("OS error starting server: %s", e)
            if e.errno == 98:  # Address already in use
                logger.error("Port %d is already in use", self.port)
            raise
        except Exception as e:
            logger.error("Unexpected error starting server: %s", e, exc_info=True)
            raise

    def stop(self) -> None:
        logger.info("Shutting down server...")

        try:
            self.server.server_close()
            logger.info("Server socket closed")

            if hasattr(self.server, 'socket'):
                logger.debug("Server was bound to: %s", self.server.socket.getsockname())

        except Exception as e:
            logger.error("Error during server shutdown: %s", e)
        finally:
            logger.info("Todo API Server stopped")
            sys.exit(0)


def run_server(host: str = "localhost", port: int = 8000) -> None:
    try:
        server = TodoServer(host, port)
        server.start()

    except KeyboardInterrupt:
        logger.info("Server stopped via KeyboardInterrupt in run_server")
    except OSError as e:
        logger.error("Failed to start server on %s:%d: %s", host, port, e)
        raise
    except Exception as e:
        logger.critical("Unexpected error in run_server: %s", e, exc_info=True)
        raise


if __name__ == "__main__":
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info("Todo API Server")
    logger.info("================")
    logger.info("For full functionality, use: python run.py")
    logger.info("")

    try:
        run_server()
    except KeyboardInterrupt:
        logger.info("Server stopped")
        sys.exit(0)
    except Exception as e:
        logger.error("Failed to start server: %s", e)
        sys.exit(1)