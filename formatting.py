"""Presentation helpers: color-coded badges, task emojis and tables for the terminal and the app.

Nothing here changes the scheduling logic; it only turns tasks into readable text.
"""

from __future__ import annotations

from tabulate import tabulate

from pawpal_system import Priority, Task

PRIORITY_BADGES = {
    Priority.LOW: "🟢 Low",
    Priority.MEDIUM: "🟡 Medium",
    Priority.HIGH: "🔴 High",
}

# The first keyword found in a task's title picks its emoji. Tasks have no "type" field,
# so the type is guessed from the title.
TASK_EMOJIS = [
    (("walk", "run", "jog"), "🦮"),
    (("feed", "breakfast", "dinner", "meal", "treat"), "🍖"),
    (("med", "pill", "insulin"), "💊"),
    (("vet", "checkup", "vaccine"), "🩺"),
    (("groom", "bath", "brush", "nail"), "🧼"),
    (("play", "toy", "fetch"), "🎾"),
    (("train", "class", "learn"), "🎓"),
]
DEFAULT_EMOJI = "🐾"


def priority_badge(priority: int) -> str:
    """Return a color-coded priority such as "🔴 High"; unknown numbers show as "⚪ 7"."""
    try:
        return PRIORITY_BADGES[Priority(priority)]
    except ValueError:
        return f"⚪ {priority}"


def status_badge(task: Task) -> str:
    """Return "✅ Done" for a finished task and "⏳ Pending" for one still to do."""
    return "✅ Done" if task.completed else "⏳ Pending"


def task_emoji(title: str) -> str:
    """Return an emoji for a task based on keywords in its title, or a paw print if none match."""
    lowered = title.lower()
    for keywords, emoji in TASK_EMOJIS:
        if any(word in lowered for word in keywords):
            return emoji
    return DEFAULT_EMOJI


def task_rows(tasks: list[Task], show_date: bool = False, show_status: bool = True) -> list[dict]:
    """Turn tasks into table rows (one dict per task) with badges and emojis applied."""
    time_format = "%a %H:%M" if show_date else "%H:%M"
    rows = []
    for task in tasks:
        row = {
            "Time": f"{task.scheduled_time:{time_format}}",
            "Task": f"{task_emoji(task.title)} {task.title}",
            "Pet": task.pet_name,
            "Min": task.duration_minutes,
            "Priority": priority_badge(task.priority),
        }
        if show_status:
            row["Status"] = status_badge(task)
        rows.append(row)
    return rows


def tasks_table(tasks: list[Task], show_date: bool = False, show_status: bool = True) -> str:
    """Return the tasks as a boxed text table (built with tabulate), or "(none)" if empty."""
    if not tasks:
        return "(none)"
    return tabulate(
        task_rows(tasks, show_date, show_status),
        headers="keys",
        tablefmt="rounded_outline",
        colalign=("left", "left", "left", "right", "left") + (("left",) if show_status else ()),
    )
