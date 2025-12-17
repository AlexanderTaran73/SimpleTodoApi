import logging

logger = logging.getLogger(__name__)


class Task:

    VALID_PRIORITIES = {"low", "normal", "high"}

    def __init__(self, title: str, priority: str = "normal",
                 task_id: int = None, is_done: bool = False):
        if not title or not title.strip():
            logger.error("Attempt to create task with empty title")
            raise ValueError("Task title cannot be empty")

        if priority not in self.VALID_PRIORITIES:
            logger.error("Invalid priority: %s", priority)
            raise ValueError(f"Priority must be one of: {', '.join(self.VALID_PRIORITIES)}")

        self.title = title
        self.priority = priority
        self.id = task_id
        self.is_done = is_done

        logger.debug("Task object created: %s", self)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "priority": self.priority,
            "isDone": self.is_done
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Task':
        try:
            task = cls(
                title=data["title"],
                priority=data.get("priority", "normal"),
                task_id=data["id"],
                is_done=data.get("isDone", False)
            )
            logger.debug("Task created from dict: %s", task)
            return task
        except KeyError as e:
            logger.error("Missing required field in task data: %s", e)
            raise
        except ValueError as e:
            logger.error("Invalid data in task dict: %s", e)
            raise

    def complete(self) -> None:
        if not self.is_done:
            self.is_done = True
            logger.debug("Task marked as completed: %s", self)
        else:
            logger.debug("Task already completed: %s", self)

    def __repr__(self) -> str:
        return f"Task(id={self.id}, title='{self.title}', priority='{self.priority}', is_done={self.is_done})"

    def __str__(self) -> str:
        status = "✓" if self.is_done else "✗"
        return f"[{status}] {self.id}: {self.title} ({self.priority})"