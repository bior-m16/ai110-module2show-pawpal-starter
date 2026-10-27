"""PawPal+ logic layer: the backend classes behind the Streamlit UI.

Classes follow diagrams/uml.mmd.

Conventions:
- priority is an int where a higher number is more urgent (1 = low, 2 = medium, 3 = high).
- scheduled_time is a task's start time. The plan respects it and only flags overlaps;
  it never moves a task.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from typing import Optional

RECURRENCE = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}


def _end_time(task: Task) -> datetime:
    """Return when a task finishes: its start time plus its duration."""
    return task.scheduled_time + timedelta(minutes=task.duration_minutes)


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
        self.completed = True
        step = RECURRENCE.get(self.frequency)
        if step is None:
            return None
        return replace(self, scheduled_time=self.scheduled_time + step, completed=False)


@dataclass
class Pet:
    """A pet and the tasks that belong to it."""

    name: str
    species: str
    age: int = 0
    notes: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet and tag it with the pet's name."""
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task from this pet. Raises ValueError if it isn't there."""
        self.tasks.remove(task)

    def get_pending_tasks(self) -> list[Task]:
        """Return the tasks that are not yet completed."""
        return [t for t in self.tasks if not t.completed]

    def complete_task(self, task: Task) -> None:
        """Mark a task done and add its next occurrence to this pet if it recurs."""
        if task not in self.tasks:
            raise ValueError(f"{task.title!r} does not belong to {self.name}")
        next_task = task.mark_complete()
        if next_task is not None:
            self.add_task(next_task)


@dataclass
class Owner:
    """A pet owner and their pets."""

    name: str
    available_minutes: int
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        for task in pet.tasks:
            task.pet_name = pet.name
        self.pets.append(pet)

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet from this owner. Raises ValueError if it isn't there."""
        self.pets.remove(pet)

    def get_all_tasks(self) -> list[Task]:
        """Return the tasks of every pet in one list."""
        return [task for pet in self.pets for task in pet.tasks]


class Scheduler:
    """Builds a daily plan from an owner's pets and tasks. Holds no data of its own."""

    def __init__(self, owner: Owner) -> None:
        """Create a scheduler that plans for the given owner."""
        self.owner = owner

    def generate_plan(self) -> list[Task]:
        """Pick pending tasks across all pets by priority until the owner's time runs out.

        Higher priority wins, earlier scheduled time breaks ties. A task that doesn't
        fit is skipped so a shorter one can still use the remaining minutes. The chosen
        tasks come back in chronological order.
        """
        pending = [t for t in self.owner.get_all_tasks() if not t.completed]
        by_importance = sorted(pending, key=lambda t: (-t.priority, t.scheduled_time))

        chosen: list[Task] = []
        minutes_used = 0
        for task in by_importance:
            if minutes_used + task.duration_minutes <= self.owner.available_minutes:
                chosen.append(task)
                minutes_used += task.duration_minutes
        return sorted(chosen, key=lambda t: t.scheduled_time)

    def detect_conflicts(self, tasks: list[Task]) -> list[tuple[Task, Task]]:
        """Return pairs of the given tasks whose scheduled times overlap."""
        ordered = sorted(tasks, key=lambda t: t.scheduled_time)
        conflicts: list[tuple[Task, Task]] = []
        for i, first in enumerate(ordered):
            for second in ordered[i + 1:]:
                if second.scheduled_time >= _end_time(first):
                    break
                conflicts.append((first, second))
        return conflicts

    def explain_plan(self, plan: list[Task]) -> str:
        """Explain why each task in the given plan was placed where it was."""
        if not plan:
            return "No tasks were scheduled."

        lines = []
        for task in plan:
            lines.append(
                f"{task.scheduled_time:%H:%M} - {task.title} ({task.pet_name}, "
                f"{task.duration_minutes} min, priority {task.priority})"
            )

        used = sum(t.duration_minutes for t in plan)
        lines.append(
            f"Total {used} of {self.owner.available_minutes} available minutes. "
            "Tasks were chosen by priority, then earliest time, and listed in time order."
        )

        planned_ids = {id(t) for t in plan}
        left_out = [
            t for t in self.owner.get_all_tasks()
            if not t.completed and id(t) not in planned_ids
        ]
        for task in left_out:
            lines.append(
                f"Left out: {task.title} ({task.pet_name}, {task.duration_minutes} min) "
                "did not fit in the remaining time."
            )

        for first, second in self.detect_conflicts(plan):
            lines.append(
                f"Conflict: {first.title} ({first.pet_name}) overlaps "
                f"{second.title} ({second.pet_name})."
            )
        return "\n".join(lines)
