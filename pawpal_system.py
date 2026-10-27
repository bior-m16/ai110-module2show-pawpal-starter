"""PawPal+ logic layer: the backend classes behind the Streamlit UI.

Classes follow diagrams/uml.mmd.

Conventions:
- priority is an int where a higher number is more urgent (1 = low, 2 = medium, 3 = high).
- scheduled_time is a task's start time. The plan respects it and only flags overlaps;
  it never moves a task.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, replace
from datetime import date, datetime, time, timedelta
from enum import IntEnum
from pathlib import Path
from typing import Optional

RECURRENCE = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}

# The hours of a day in which find_next_free_slot looks for room.
DAY_START = time(6, 0)
DAY_END = time(22, 0)


class Priority(IntEnum):
    """How urgent a task is. A higher number is more urgent, and each level is a plain int."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3

    @property
    def label(self) -> str:
        """Return the level as a word: "Low", "Medium" or "High"."""
        return self.name.capitalize()


def _end_time(task: Task) -> datetime:
    """Return when a task finishes: its start time plus its duration."""
    return task.scheduled_time + timedelta(minutes=task.duration_minutes)


def _overlaps(first: Task, second: Task) -> bool:
    """Return True if two tasks share time; back-to-back tasks do not overlap."""
    return first.scheduled_time < _end_time(second) and second.scheduled_time < _end_time(first)


def _describe_conflict(first: Task, second: Task) -> str:
    """Return a one-line description of two overlapping tasks, noting if they share a pet."""
    scope = "same pet" if first.pet_name == second.pet_name else "different pets"
    return (
        f"{first.title} ({first.pet_name}, {first.scheduled_time:%H:%M}-{_end_time(first):%H:%M}) "
        f"overlaps {second.title} ({second.pet_name}, "
        f"{second.scheduled_time:%H:%M}-{_end_time(second):%H:%M}) [{scope}]"
    )


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

    @property
    def priority_label(self) -> str:
        """Return the priority as a word ("Low", "Medium", "High"), or the number if unknown."""
        try:
            return Priority(self.priority).label
        except ValueError:
            return str(self.priority)

    def mark_complete(self, now: Optional[datetime] = None) -> Optional[Task]:
        """Mark this task done; if it recurs, return a new task for its next occurrence.

        Daily tasks recur one day after today. Weekly tasks keep their weekday: the next
        one is the first same-weekday slot after today, however late or early this one
        was completed. A "once" task returns None, and so does a task that was already
        completed, so completing it twice can't create duplicate occurrences. `now`
        defaults to the current time and exists so the date can be fixed in tests.
        """
        if self.completed:
            return None
        self.completed = True
        next_time = self._next_time((now or datetime.now()).date())
        if next_time is None:
            return None
        return replace(self, scheduled_time=next_time, completed=False)

    def to_dict(self) -> dict:
        """Return this task as plain JSON-friendly data (the time becomes an ISO string)."""
        return {
            "title": self.title,
            "pet_name": self.pet_name,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority,
            "scheduled_time": self.scheduled_time.isoformat(),
            "frequency": self.frequency,
            "completed": self.completed,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Task:
        """Rebuild a task from to_dict() data. Raises KeyError, TypeError or ValueError if invalid."""
        return cls(
            title=str(data["title"]),
            pet_name=str(data["pet_name"]),
            duration_minutes=int(data["duration_minutes"]),
            priority=int(data["priority"]),
            scheduled_time=datetime.fromisoformat(data["scheduled_time"]),
            frequency=str(data.get("frequency", "once")),
            completed=bool(data.get("completed", False)),
        )

    def _next_time(self, today: date) -> Optional[datetime]:
        """Return when this task next recurs after the given day, or None if it doesn't.

        Daily tasks recur one day after `today` at the task's time of day. Weekly tasks
        recur at `scheduled_time + k weeks`, using the smallest k >= 1 whose date is after
        `today`; that keeps them on the same weekday however late or early they were
        completed. k comes from one division, so it takes the same time for a task a day
        late or a hundred weeks late.
        """
        step = RECURRENCE.get(self.frequency)
        if step is None:
            return None
        if self.frequency == "daily":
            return datetime.combine(today, self.scheduled_time.time()) + step
        weeks_late = (today - self.scheduled_time.date()).days // 7
        return self.scheduled_time + step * max(1, weeks_late + 1)

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

    def complete_task(self, task: Task, now: Optional[datetime] = None) -> None:
        """Mark a task done and add its next occurrence to this pet if it recurs.

        Raises ValueError if the task doesn't belong to this pet.
        """
        if task not in self.tasks:
            raise ValueError(f"{task.title!r} does not belong to {self.name}")
        next_task = task.mark_complete(now)
        if next_task is not None:
            self.add_task(next_task)

    def to_dict(self) -> dict:
        """Return this pet, with all of its tasks, as plain JSON-friendly data."""
        return {
            "name": self.name,
            "species": self.species,
            "age": self.age,
            "notes": self.notes,
            "tasks": [task.to_dict() for task in self.tasks],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Pet:
        """Rebuild a pet and its tasks from to_dict() data."""
        return cls(
            name=str(data["name"]),
            species=str(data["species"]),
            age=int(data.get("age", 0)),
            notes=str(data.get("notes", "")),
            tasks=[Task.from_dict(item) for item in data.get("tasks", [])],
        )


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

    def filter_tasks(
        self, pet_name: Optional[str] = None, completed: Optional[bool] = None
    ) -> list[Task]:
        """Return tasks across all pets, optionally only one pet's and/or one status.

        `pet_name=None` means every pet and `completed=None` means both statuses, so
        passing neither is the same as get_all_tasks(). Both given means both must match.
        """
        return [
            task
            for task in self.get_all_tasks()
            if (pet_name is None or task.pet_name == pet_name)
            and (completed is None or task.completed == completed)
        ]

    def to_dict(self) -> dict:
        """Return the owner, with every pet and task, as plain JSON-friendly data."""
        return {
            "name": self.name,
            "available_minutes": self.available_minutes,
            "pets": [pet.to_dict() for pet in self.pets],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Owner:
        """Rebuild an owner, their pets and tasks from to_dict() data."""
        owner = cls(name=str(data["name"]), available_minutes=int(data["available_minutes"]))
        for pet_data in data.get("pets", []):
            owner.add_pet(Pet.from_dict(pet_data))
        return owner

    def save_to_json(self, path: str | os.PathLike = "data.json") -> None:
        """Save the owner, pets and tasks to a JSON file.

        Writes to a temporary file first and then swaps it in, so a crash mid-write
        can't leave a half-written data file behind.
        """
        path = Path(path)
        temp = path.with_name(path.name + ".tmp")
        temp.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        os.replace(temp, path)

    @classmethod
    def load_from_json(cls, path: str | os.PathLike = "data.json") -> Optional[Owner]:
        """Load an owner from a JSON file; return None if the file doesn't exist yet.

        Raises ValueError if the file exists but is not valid PawPal+ data.
        """
        path = Path(path)
        if not path.exists():
            return None
        try:
            return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"{path.name} could not be read: {error!r}") from error


class Scheduler:
    """Builds a daily plan from an owner's pets and tasks. Holds no data of its own."""

    def __init__(self, owner: Owner) -> None:
        """Create a scheduler that plans for the given owner."""
        self.owner = owner

    @staticmethod
    def sort_by_time(tasks: list[Task]) -> list[Task]:
        """Return a new list of the tasks ordered by scheduled start time, earliest first.

        The original list is left unchanged, and tasks with the same time keep their
        existing relative order.
        """
        return sorted(tasks, key=lambda t: t.scheduled_time)

    @staticmethod
    def sort_by_priority(tasks: list[Task]) -> list[Task]:
        """Return a new list ordered by priority first (High, then Medium, then Low), then by time.

        Tasks with the same priority are ordered by scheduled start time, earliest first.
        """
        return sorted(tasks, key=lambda t: (-t.priority, t.scheduled_time))

    def _pending_on(self, day: date) -> list[Task]:
        """Return the owner's pending tasks, across all pets, that start on the given day."""
        return [
            t for t in self.owner.filter_tasks(completed=False)
            if t.scheduled_time.date() == day
        ]

    def generate_plan(self, day: Optional[date] = None) -> list[Task]:
        """Pick one day's pending tasks across all pets by priority until time runs out.

        Defaults to today. Higher priority wins, earlier scheduled time breaks ties. A
        task that doesn't fit is skipped so a shorter one can still use the remaining
        minutes. The chosen tasks come back in chronological order.
        """
        by_importance = self.sort_by_priority(self._pending_on(day or date.today()))

        chosen: list[Task] = []
        minutes_used = 0
        for task in by_importance:
            if minutes_used + task.duration_minutes <= self.owner.available_minutes:
                chosen.append(task)
                minutes_used += task.duration_minutes
        return self.sort_by_time(chosen)

    def detect_conflicts(self, tasks: list[Task]) -> list[tuple[Task, Task]]:
        """Return pairs of the given tasks whose scheduled times overlap.

        Tasks are sorted by start time and each one is compared only with the tasks that
        start before it ends, so this is O(n log n) plus the number of conflicts. Tasks
        that run back to back (one ends exactly when the next starts) do not conflict.
        """
        ordered = self.sort_by_time(tasks)
        conflicts: list[tuple[Task, Task]] = []
        for i, first in enumerate(ordered):
            for second in ordered[i + 1:]:
                if not _overlaps(first, second):
                    break  # sorted by start, so no later task can overlap `first` either
                conflicts.append((first, second))
        return conflicts

    def conflict_warnings(self, tasks: Optional[list[Task]] = None) -> list[str]:
        """Return a warning message for every overlapping pair; never raises, empty if none.

        Checks the owner's pending tasks unless a list is given. Overlaps are found for
        the same pet or different pets, since the owner can't do two things at once.
        """
        if tasks is None:
            tasks = self.owner.filter_tasks(completed=False)
        return [
            f"Warning: {_describe_conflict(first, second)}"
            for first, second in self.detect_conflicts(tasks)
        ]

    def conflicts_for(self, task: Task) -> list[Task]:
        """Return the owner's pending tasks that the given task overlaps.

        Meant for checking a task before it is added, so the owner can be warned. The
        task itself is never counted as its own conflict.
        """
        return [
            existing
            for existing in self.owner.filter_tasks(completed=False)
            if existing is not task and _overlaps(task, existing)
        ]

    def find_next_free_slot(
        self,
        duration_minutes: int,
        day: Optional[date] = None,
        after: Optional[datetime] = None,
        ignore: Optional[Task] = None,
    ) -> Optional[datetime]:
        """Return the earliest start time on `day` with `duration_minutes` of free time, or None.

        Looks between DAY_START and DAY_END (06:00-22:00), and not before `after` if given.
        Sweeps the day's pending tasks in time order, keeping a cursor at the end of
        everything seen so far; the first gap before the next task (or before the end of
        the day) that is long enough is the answer. `ignore` leaves one task out, so an
        existing task can be asked where it could move to. Touching tasks leave no gap.
        """
        day = day or date.today()
        needed = timedelta(minutes=duration_minutes)
        limit = datetime.combine(day, DAY_END)
        cursor = datetime.combine(day, DAY_START)
        if after is not None:
            cursor = max(cursor, after)

        busy = self.sort_by_time(
            [
                t for t in self.owner.filter_tasks(completed=False)
                if t is not ignore and _end_time(t) > cursor and t.scheduled_time < limit
            ]
        )
        for task in busy:
            if cursor + needed <= min(task.scheduled_time, limit):
                return cursor
            cursor = max(cursor, _end_time(task))
        return cursor if cursor + needed <= limit else None

    def explain_plan(self, plan: list[Task]) -> str:
        """Explain why each task in the given plan was placed where it was."""
        if not plan:
            return "No tasks were scheduled."
        lines = [
            f"{task.scheduled_time:%H:%M} - {task.title} ({task.pet_name}, "
            f"{task.duration_minutes} min, priority {task.priority_label})"
            for task in plan
        ]
        return "\n".join(lines + self.plan_notes(plan))

    def plan_notes(self, plan: list[Task]) -> list[str]:
        """Return the lines that explain a plan beyond its task list.

        These are the minutes used out of the available minutes, any pending task that
        was left out because it didn't fit, and any conflicts inside the plan.
        """
        if not plan:
            return []

        used = sum(t.duration_minutes for t in plan)
        lines = [
            f"Total {used} of {self.owner.available_minutes} available minutes. "
            "Tasks were chosen by priority (High first), then earliest time, and listed in time order."
        ]

        # Compare by identity: two tasks with identical fields are equal as dataclasses.
        planned_ids = {id(t) for t in plan}
        left_out = [
            t for t in self._pending_on(plan[0].scheduled_time.date())
            if id(t) not in planned_ids
        ]
        for task in left_out:
            lines.append(
                f"Left out: {task.title} ({task.pet_name}, {task.priority_label} priority, "
                f"{task.duration_minutes} min) did not fit in the remaining time."
            )

        for first, second in self.detect_conflicts(plan):
            lines.append(f"Conflict: {_describe_conflict(first, second)}")
        return lines
