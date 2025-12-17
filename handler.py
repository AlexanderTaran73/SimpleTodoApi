import json
import logging
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Tuple, Optional, Dict, Any

from storage import TaskStorage

logger = logging.getLogger(__name__)


class TodoRequestHandler(BaseHTTPRequestHandler):

    storage = TaskStorage()

    def _send_response(self, status_code: int,
                       data: Optional[Any] = None,
                       content_type: str = "application/json") -> None:
        self.send_response(status_code)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")

        # Добавляем CORS заголовки для Postman
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

        self.end_headers()

        if data is not None:
            if content_type == "application/json":
                response = json.dumps(data, ensure_ascii=False).encode("utf-8")
            else:
                response = str(data).encode("utf-8")
            self.wfile.write(response)

    def _read_json_body(self) -> Optional[Dict]:
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return None

        try:
            body = self.rfile.read(content_length).decode("utf-8")
            logger.debug("Request body: %s", body)
            return json.loads(body) if body else None
        except json.JSONDecodeError as e:
            logger.warning("Invalid JSON in request: %s", e)
            return None
        except UnicodeDecodeError as e:
            logger.warning("Invalid encoding in request: %s", e)
            return None

    def _parse_path(self) -> Tuple[list, dict]:
        parsed = urlparse(self.path)
        path_parts = parsed.path.strip("/").split("/")
        query_params = parse_qs(parsed.query)
        return path_parts, query_params

    def do_OPTIONS(self) -> None:
        logger.info("OPTIONS %s from %s", self.path, self.client_address[0])
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        path_parts, _ = self._parse_path()

        if path_parts == ["tasks"]:
            logger.info("GET /tasks from %s", self.client_address[0])

            try:
                tasks = self.storage.get_all_tasks()
                tasks_data = [task.to_dict() for task in tasks]

                logger.debug("Returning %d tasks", len(tasks_data))
                self._send_response(200, tasks_data)

            except Exception as e:
                logger.error("Error getting tasks: %s", e, exc_info=True)
                self._send_response(500, {"error": "Internal server error"})

        else:
            logger.warning("GET %s - Not found", self.path)
            self._send_response(404, {"error": "Not found"})

    def do_POST(self) -> None:
        path_parts, _ = self._parse_path()

        if path_parts == ["tasks"]:
            client_ip = self.client_address[0]
            logger.info("POST /tasks from %s", client_ip)

            data = self._read_json_body()

            if not data:
                logger.warning("Empty or invalid JSON from %s", client_ip)
                self._send_response(400, {"error": "Invalid JSON"})
                return

            if "title" not in data:
                logger.warning("Missing title field from %s", client_ip)
                self._send_response(400, {"error": "Title is required"})
                return

            title = data.get("title", "")
            priority = data.get("priority", "normal")

            logger.debug("Creating task: title='%s', priority='%s'", title, priority)

            try:
                task = self.storage.create_task(title, priority)
                logger.info("Task created: ID=%d", task.id)
                self._send_response(201, task.to_dict())

            except ValueError as e:
                logger.warning("Validation error from %s: %s", client_ip, e)
                self._send_response(400, {"error": str(e)})
            except Exception as e:
                logger.error("Error creating task: %s", e, exc_info=True)
                self._send_response(500, {"error": "Internal server error"})

        elif len(path_parts) == 3 and path_parts[0] == "tasks" and path_parts[2] == "complete":
            try:
                task_id = int(path_parts[1])
                client_ip = self.client_address[0]
                logger.info("POST /tasks/%d/complete from %s", task_id, client_ip)

                if self.storage.complete_task(task_id):
                    logger.info("Task %d marked as completed", task_id)
                    self._send_response(200)
                else:
                    logger.warning("Task %d not found", task_id)
                    self._send_response(404)

            except ValueError:
                logger.warning("Invalid task ID: %s", path_parts[1])
                self._send_response(400, {"error": "Invalid task ID"})

        else:
            logger.warning("POST %s - Not found", self.path)
            self._send_response(404, {"error": "Not found"})

    def log_message(self, format: str, *args) -> None:
        logger.info("%s - %s", self.client_address[0], format % args)