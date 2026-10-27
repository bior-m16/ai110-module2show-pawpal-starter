"""PawPal+ logic layer: the backend classes behind the Streamlit UI.

Classes follow diagrams/uml.mmd.

Conventions:
- priority is an int where a higher number is more urgent (1 = low, 2 = medium, 3 = high).
- scheduled_time is a task's start time. The plan respects it and only flags overlaps;
  it never moves a task.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta
from typing import Optional

RECURRENCE = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}


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

    def mark_complete(self, now: Optional[datetime] = None) -> Optional[Task]:
        """Mark this task done; if it recurs, return a new task for its next occurrence.

        Daily tasks recur one day after today. Weekly tasks keep their weekday: the next
        one is the first same-weekday slot after today, however late or early this one
        was completed. A "once" task returns None. `now` defaults to the current time
        and exists so the date can be fixed in tests.
        """
        self.completed = True
        next_time = self._next_time((now or datetime.now()).date())
        if next_time is None:
            return None
        return replace(self, scheduled_time=next_time, completed=False)

    def _next_time(self, today: date) -> Optional[datetime]:
        """Return when this task next recurs after the given day, or None if it doesn't.

        Daily tasks start counting from `today` at the task's time of day. Weekly tasks
        start from the original date and step forward a week at a time until the date is
        after `today`, which keeps them on the same weekday.
        """
        step = RECURRENCE.get(self.frequency)
        if step is None:
            return None
        if self.frequency == "daily":
            anchor = datetime.combine(today, self.scheduled_time.time())
        else:
            anchor = self.scheduled_time  # weekly keeps its original weekday
        next_time = anchor + step
        while next_time.date() <= today:
            next_time += step
        return next_time


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
        pending = self._pending_on(day or date.today())
        by_importance = sorted(pending, key=lambda t: (-t.priority, t.scheduled_time))

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

        # Compare by identity: two tasks with identical fields are equal as dataclasses.
        planned_ids = {id(t) for t in plan}
        left_out = [
            t for t in self._pending_on(plan[0].scheduled_time.date())
            if id(t) not in planned_ids
        ]
        for task in left_out:
            lines.append(
                f"Left out: {task.title} ({task.pet_name}, {task.duration_minutes} min) "
                "did not fit in the remaining time."
            )

        for first, second in self.detect_conflicts(plan):
            lines.append(f"Conflict: {_describe_conflict(first, second)}")
        return "\n".join(lines)
