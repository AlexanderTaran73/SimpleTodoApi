import json
import os
import logging
from typing import List, Optional
from models import Task

logger = logging.getLogger(__name__)


class TaskStorage:

    def __init__(self, filename: str = "tasks.txt"):
        self.filename = filename
        self.tasks = {}
        self.next_id = 1
        self._load_tasks()

    def _load_tasks(self) -> None:
        if not os.path.exists(self.filename):
            logger.info("Storage file '%s' not found. Starting with empty task list.", self.filename)
            return

        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                tasks_data = json.load(f)

            task_count = 0
            for task_data in tasks_data:
                try:
                    task = Task.from_dict(task_data)
                    self.tasks[task.id] = task

                    if task.id >= self.next_id:
                        self.next_id = task.id + 1

                    task_count += 1

                except (KeyError, ValueError) as e:
                    logger.warning("Skipping invalid task data: %s. Error: %s", task_data, e)

            logger.info("Loaded %d tasks from '%s'", task_count, self.filename)

        except json.JSONDecodeError as e:
            logger.error("Invalid JSON in '%s': %s. Starting with empty list.", self.filename, e)
            self.tasks = {}
            self.next_id = 1
        except PermissionError as e:
            logger.error("Permission denied reading '%s': %s", self.filename, e)
            raise
        except Exception as e:
            logger.error("Unexpected error loading tasks: %s", e, exc_info=True)
            self.tasks = {}
            self.next_id = 1

    def save_tasks(self) -> bool:
        try:
            tasks_data = [task.to_dict() for task in self.tasks.values()]

            temp_filename = f"{self.filename}.tmp"
            with open(temp_filename, "w", encoding="utf-8") as f:
                json.dump(tasks_data, f, ensure_ascii=False, indent=2)

            os.replace(temp_filename, self.filename)

            logger.debug("Saved %d tasks to '%s'", len(self.tasks), self.filename)
            return True

        except PermissionError as e:
            logger.error("Permission denied writing to '%s': %s", self.filename, e)
            return False
        except Exception as e:
            logger.error("Error saving tasks: %s", e, exc_info=True)
            return False

    def create_task(self, title: str, priority: str = "normal") -> Task:
        if not title or not title.strip():
            logger.warning("Attempt to create task with empty title")
            raise ValueError("Task title cannot be empty")

        if priority not in ["low", "normal", "high"]:
            logger.warning("Invalid priority value: %s", priority)
            raise ValueError("Priority must be: low, normal or high")

        task = Task(
            title=title.strip(),
            priority=priority,
            task_id=self.next_id,
            is_done=False
        )

        self.tasks[self.next_id] = task
        self.next_id += 1

        if not self.save_tasks():
            logger.error("Failed to save task %d to file", task.id)

        logger.info("Created new task: %s", task)
        return task

    def get_all_tasks(self) -> List[Task]:
        return list(self.tasks.values())

    def get_task(self, task_id: int) -> Optional[Task]:
        return self.tasks.get(task_id)

    def complete_task(self, task_id: int) -> bool:
        task = self.get_task(task_id)
        if not task:
            logger.warning("Attempt to complete non-existent task ID: %d", task_id)
            return False

        if task.is_done:
            logger.debug("Task %d is already completed", task_id)
            return True

        task.complete()

        if not self.save_tasks():
            logger.error("Failed to save completion of task %d", task_id)

        logger.info("Task completed: %s", task)
        return True

    def get_stats(self) -> dict:
        total = len(self.tasks)
        completed = sum(1 for task in self.tasks.values() if task.is_done)

        return {
            "total_tasks": total,
            "completed_tasks": completed,
            "pending_tasks": total - completed,
            "next_id": self.next_id,
            "storage_file": self.filename
        }