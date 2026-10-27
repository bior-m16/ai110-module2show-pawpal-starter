"""PawPal+ logic layer: the backend classes behind the Streamlit UI.

Class stubs follow diagrams/uml.mmd. Behavior is not implemented yet.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Task:
    """One care activity for a single pet."""

    title: str
    pet_name: str
    duration_minutes: int
    priority: int
    scheduled_time: datetime
    frequency: str = "once"  # "once", "daily", or "weekly"
    completed: bool = False

    def mark_complete(self) -> Optional[Task]:
        """Mark this task done; return the next occurrence if it recurs, else None."""
        raise NotImplementedError


@dataclass
class Pet:
    """A pet and the tasks that belong to it."""

    name: str
    species: str
    age: int = 0
    notes: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet."""
        raise NotImplementedError

    def remove_task(self, task: Task) -> None:
        """Remove a task from this pet."""
        raise NotImplementedError

    def get_pending_tasks(self) -> list[Task]:
        """Return the tasks that are not yet completed."""
        raise NotImplementedError


@dataclass
class Owner:
    """A pet owner and their pets."""

    name: str
    available_minutes: int
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        raise NotImplementedError

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet from this owner."""
        raise NotImplementedError

    def get_all_tasks(self) -> list[Task]:
        """Return the tasks of every pet in one list."""
        raise NotImplementedError


class Scheduler:
    """Builds a daily plan from an owner's pets and tasks. Holds no data of its own."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def generate_plan(self) -> list[Task]:
        """Order pending tasks by priority and time and fit them into the available minutes."""
        raise NotImplementedError

    def detect_conflicts(self) -> list[tuple[Task, Task]]:
        """Return pairs of tasks whose scheduled times overlap."""
        raise NotImplementedError

    def explain_plan(self) -> str:
        """Explain why each task was placed where it was."""
        raise NotImplementedError
